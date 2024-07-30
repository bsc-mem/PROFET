################################################################################
# Copyright (c) 2023, Barcelona Supercomputing Center
#                     Contact: mariana.carmin [at] bsc [dot] es
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.

#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.

#     * Neither the name of the copyright holder nor the names
#       of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
################################################################################

import os
import numpy as np
import math
import warnings
import json
from bisect import bisect

from .metrics import Bandwidth, Latency, Frequency


class BadFileFormatError(Exception):
    """ Deals with bad file format for bandwidth-latency files. """
    def __init__(self, file):
        self.file = file

    def __str__(self):
        return f'Bandwidth-latency file {self.file} has incorrect format'


class OvershootError(Exception):
    """
    Deals with bandwidths larger than the largest recorded bandwidth for
    a given curve.
    """
    def __init__(self, read_ratio: float, requested_bw: Bandwidth):
        self.read_ratio = read_ratio
        self.requested_bw = requested_bw

    def __str__(self):
        return (f'Cannot estimate the latency for bandwidth {self.requested_bw} '
                f'using a bandwidth-latency curve for a read ratio of '
                f'{self.read_ratio:.2%}. The provided bandwidth is larger than the '
                'largest recorded bandwidth for said curve.')


class RatioRangesError(Exception):
    """ Deals with read ratios outside the expected range. """
    def __init__(self, read_ratio: float):
        self.read_ratio = read_ratio

    def __str__(self):
        # if self.read_ratio % 2 != 0:
        #     return f'Read ratio has to be an even value. The given read ratio is {self.read_ratio}%.'
        # elif self.read_ratio < 50:
        #     return f'Read ratios under 50% are not currently supported. The given read ratio is {self.read_ratio}%.'
        if self.read_ratio < 0:
            return ('Read ratios under 0 are not possible. '
                    f'The given read ratio is {self.read_ratio:.2f}.')
        elif self.read_ratio > 1:
            return ('Read ratios over 1 are not possible. '
                    f'The given read ratio is {self.read_ratio:.2f}.')
        else:
            return f'Unknown error for the given read ratio of {self.read_ratio:.2f}.'


class ReadRatioMismatchError(Exception):
    """
    Deals with read ratios that are too far from the ones computed in
    the curves.
    """
    def __init__(self, read_ratio: float, curve_read_ratio: float):
        self.read_ratio = read_ratio
        self.curve_read_ratio = curve_read_ratio

    def __str__(self):
        return (f'The given read ratio of {self.read_ratio:.2f} may be too far '
                f'from the ones computed in the curves. Using closest read '
                f'ratio of {self.curve_read_ratio:.2f}.')


def bw_overshoot_warning(read_ratio: int, requested_bw: Bandwidth) -> None:
    """
    Deals with bandwidths larger than the largest recorded bandwidth for
    a given curve.
    """
    warn = (f'Cannot estimate latency for bandwidth {requested_bw} using '
            f'bandwidth-latency curve for a read ratio of {read_ratio:.2f}. '
            'Provided bandwidth larger than the largest recorded bandwidth '
            'for said curve.')
    warnings.warn(warn)


def bw_high_warning(
    read_ratio: float,
    requested_bw: Bandwidth ,
    max_bw: Bandwidth,
    max_lat: Latency
) -> None:
    if requested_bw.unit != max_bw.unit:
        requested_bw = requested_bw.as_unit(max_bw.unit)
    over_bw_factor = 1 - (requested_bw.value / max_bw.value) * 100
    warn = (f'Cannot estimate latency for bandwidth {requested_bw} using '
            f'bandwidth-latency curve for a read ratio of {read_ratio:.2f}. '
            'The provided bandwidth is larger than the largest recorded '
            f'bandwidth for said curve by a factor of {over_bw_factor:.2%}.'
            f'Using latency of {max_lat}, corresponding to the maximum latency.')
    warnings.warn(warn)


def bw_low_warning(requested_bw: Bandwidth, lead_off_latency: Latency) -> None:
    """
    Deals with bandwidths smaller than the smallest recorded bandwidth
    for a given curve.
    """
    warn = (f'Provided bandwidth {requested_bw} maller than the smallest '
            'recorded bandwidth for the curve. Using latency of '
            f'{lead_off_latency}, corresponding to the lead-off-latency.')
    warnings.warn(warn)


def read_ratio_mismatch_warning(read_ratio: float, curve_read_ratio: float) -> None:
    """
    Deals with read ratios that are too far from the ones computed in
    the curves.
    """
    warn = (f'The given read ratio of {read_ratio:.2f} may be too far from the '
            'ones computed in the curves. Using closest read ratio of '
            f'{curve_read_ratio:.2f}.')
    warnings.warn(warn)


def zero_bw_warning():
    """ Deals with bandwidths equal to 0. """
    warn = f'Bandwidth equals 0. Latency is undefined. Returning `None` instead.'
    warnings.warn(warn)


def check_ratio(read_ratio: int) -> bool:
    """ Checks if read ratio is within the expected range. """
    if read_ratio > 1 or read_ratio < 0:
        raise RatioRangesError(read_ratio)
    return True


class Curve:
    """
    Curve class for a given read ratio curve (bandwidth and latency points).
    """

    def __init__(
        self,
        read_ratio: float,
        bws: list[Bandwidth],
        lats: list[Latency],
        display_warnings: bool = True
    ) -> None:
        if len(bws) == 0 or len(lats) == 0:
            raise Exception('Bandwidths and latencies should not be empty.')
        if len(bws) != len(lats):
            raise Exception('Number of bandwidths and latencies should be the same.')
        
        check_ratio(read_ratio)
        self.read_ratio = read_ratio
        # self.closest_read_ratio = self._get_closest_read_ratio(read_ratio)
        self.display_warnings = display_warnings
        self.bws = sorted(bws)
        self.lats = lats
        self.bws_values = [bw.value for bw in self.bws]
        self.lats_values = [lat.value for lat in self.lats]
        # Check that all bandwidths and latencies have the same units
        for bw, lat in zip(self.bws, self.lats):
            bw.check_same_unit(bws[0])
            lat.check_same_unit(lats[0])
        # Factor to allow a limit of % overshoot (measured bw over max bw)
        self.bw_grace_factor = 0.05
        
        # Set fixed values for max bandwidth, max latency and lead-off latency
        self.max_bw = self._get_max_bw()
        self.max_lat = self._get_max_lat()
        self.lead_off_lat = self._get_lead_off_lat()

    def get_lat(
        self,
        bw: Bandwidth,
        unit: str = None,
        freq: Frequency = None
    )-> Latency:
        """
        Latency for provided bandwidth.
        Linear interpolation is used to calculate latency between two
        recorded points.

        If provided bandwidth is smaller than the smallest recorded
        sample, the latency corresponding to the smallest recorded
        bandwidth is returned.
        The rationale is that curve at this point is usually constant.

        If provided banwdith is larger than the largest recorded sample,
        an exception is thrown.
        The rationale is that the curve beyond the max bandwidth is
        exponential and it is difficult to find a good estimate for latency.

        Args:
            bw (Bandwidth): bandwidth
            unit (str, optional): units of the returned latency.
                Defaults to None.
                If None, latency is returned in the same units as the
                latencies given at object initialization.
            freq (Frequency, optional): memory frequency (only needed
                when latency units are in time units, e.g. ns, us, s).

        Returns:
            latency (Latency): latency for the given bandwidth.
        """
        if unit is not None and unit != 'cycles' and freq is None:
            raise Exception(f'Frequency must be provided when the desired '
                            'units are time.')
        
        if bw.value == 0:
            # Special case when bandwidth equals 0, latency is undefined
            if self.display_warnings:
                zero_bw_warning()
            return None

        # Assure bandwidth is in MBps for the curves
        if bw.unit != 'MBps':
            bw = bw.as_unit('MBps')

        if bw.value < self.bws[0].value:
            # Show warning and return lead-off lat when bw is below-off the curve
            if self.display_warnings:
                bw_low_warning(bw, lead_off_latency=self.lats[0])
            return self.lats[0]

        # Warning: Comparing BW's values instead of BW objects for efficiency
        # Warning: Assuming both values have the same units
        if bw.value >= self.max_bw.value:
            if bw > self.max_bw * (1 + self.bw_grace_factor):
                # Raise exception when bandwidth is too above the curve
                raise OvershootError(self.read_ratio, bw)
            # Return max lat when bandwidth is max or slightly above the curve
            max_lat = self.get_max_lat()
            if self.display_warnings:
                bw_high_warning(self.read_ratio, bw, self.max_bw, max_lat)
            return max_lat

        i = self._get_bw_posterior_index(bw)

        # Renaming variables to easily read the linear interpolation formula
        x = bw.value
        x1, y1 = self.bws[i - 1].value, self.lats[i - 1].value
        x2, y2 = self.bws[i].value, self.lats[i].value
        # Linear interpolation
        lat_value = y1 + (x - x1) / (x2 - x1) * (y2 - y1)

        lat = Latency(lat_value, 'cycles')
        if unit == 'cycles' or (unit is None and self.lats[0].unit == 'cycles'):
            # If unit is cycles, return calculated lat (already in cycles)
            return lat
        elif unit is None:
            # Return lat in the same units as the lats given at object init
            return lat.as_unit(self.lats[0].unit, freq)
        return lat.as_unit(unit, freq)
    
    def get_max_bw(self, unit: str = None) -> Bandwidth:
        """
        Maximum recorded bandwidth for the given curve.

        Args:
            unit (str, optional): units of the returned bandwidth.
                Defaults to None.
                If None, bandwidth is returned in the same units as the
                bandwidths given at object initialization.

        Returns:
            max_bw (Bandwidth): maximum recorded bandwidth for the given curve.
        """
        if unit is None:
            return self.max_bw
        return self.max_bw.as_unit(unit)

    def get_max_lat(self, unit: str = None, freq: Frequency = None) -> Latency:
        """
        Maximum recorded latency for the given curve.

        Args:
            unit (str, optional): units of the returned latency.
                Defaults to None.
                If None, latency is returned in the same units as the
                latencies given at object initialization.
            freq (Frequency, optional): memory frequency (only needed
                when latency units are in time units, e.g. ns, us, s).
        
        Returns:
            max_lat (Latency): maximum recorded latency for the given curve.
        """
        if unit is None:
            return self.max_lat
        return self.max_lat.as_unit(unit, freq)

    def get_lead_off_lat(
        self, unit: str = None,
        freq: Frequency = None
    ) -> Latency:
        """
        Lead-off (minimum) latency for the given curve.

        Args:
            unit (str, optional): units of the returned latency.
                Defaults to None.
                If None, latency is returned in the same units as the
                latencies given at object initialization.
            freq (Frequency, optional): memory frequency (only needed
                when latency units are in time units, e.g. ns, us, s).
        
        Returns:
            lead_off_lat (Latency): lead-off (minimum) latency for the
                given curve.
        """
        if unit is None:
            return self.lead_off_lat
        return self.lead_off_lat.as_unit(unit, freq)
    
    def get_stress_score(
        self,
        bw: Bandwidth,
        lat: Latency = None,
        lead_off_lat: Latency = None,
        max_lat: Latency = None
    ) -> float:
        """
        Stress score for the given bandwidth.

        Args:
            bw (Bandwidth): bandwidth.
            lat (Latency): latency.
            lead_off_lat (Latency): lead-off (minimum) latency.
            max_lat (Latency): maximum latency.

        Returns:
            stress_score (float): stress score for the given bandwidth.
        """
        if bw.value == 0:
            return 0
        
        if bw.unit != self.bws[0].unit:
            bw = bw.as_unit(self.bws[0].unit)
        idx = self._get_bw_posterior_index(bw)
        if idx >= len(self.bws):
            return None

        if lat is None:
            lat = self.get_lat(bw, 'cycles')
        if lead_off_lat is None:
            lead_off_lat = self.get_lead_off_lat('cycles')
        if max_lat is None:
            max_lat = self.get_max_lat('cycles')
        # Couldn't we assume that idx - 1 has lower BW and latency than idx?
        bw_prev, bw_post, lat_prev, lat_post = self._get_pre_and_post_bw_and_lat(idx)
        # prev and post bw are in MB/s
        return self._stress_score_computation(max_lat, lead_off_lat, lat,
                                              bw_prev, bw_post, lat_prev, lat_post)
    
    def get_bws(self, unit: str = None) -> list[Bandwidth]:
        """
        Bandwidths of the curve.

        Args:
            unit (str, optional): units of the returned bandwidths.
                Defaults to None.
                If None, bandwidhts are returned in the same units as
                the bandwidths given at object initialization.

        Returns:
            bws (list[Bandwidth]): bandwidths of the curve.
        """
        if unit is None:
            return self.bws
        return [bw.as_unit(unit) for bw in self.bws]
    
    def get_lats(self, unit: str = None, freq: Frequency = None) -> list[Latency]:
        """
        Latencies of the curve.

        Args:
            unit (str, optional): units of the returned latencies.
                Defaults to None.
                If None, latencies are returned in the same units as the
                latencies given at object initialization.
            freq (Frequency, optional): memory frequency (only needed
                when latency units are in time units, e.g. ns, us, s).

        Returns:
            lats (list[Latency]): latencies of the curve.
        """
        if unit is None:
            return self.lats
        return [lat.as_unit(unit, freq) for lat in self.lats]

    def get_curve_bws_lats(
        self,
        bw_unit: str = None,
        lat_unit: str = None,
        freq: Frequency = None
    ) -> list[tuple[Bandwidth, Latency]]:
        """
        Bandwidths and latencies of the curve.

        Args:
            bw_unit (str, optional): units of the returned bandwidths.
                Defaults to None.
                If None, bandwidhts are returned in the same units as
                the bandwidths given at object initialization.
            lat_unit (str, optional): units of the returned latencies.
                Defaults to None. If None, latency is returned in the
                same units as the latencies given at object initialization.
            freq (Frequency, optional): memory frequency (only needed
                when latency units are in time units, e.g. ns, us, s).

        Returns:
            curve_bw_lats (list[tuple[Bandwidth, Latency]]): bandwidths
                and latencies of the curve in a list of tuples for each
                bw-lat pair.
        """
        bws = self.get_bws(bw_unit)
        lats = self.get_lats(lat_unit, freq)
        return list(zip(bws, lats))
    
    def _get_max_bw(self) -> Bandwidth:
        """
        Maximum recorded bandwidth for the given curve.

        Returns:
            max_bw (Bandwidth): maximum recorded bandwidth for the given curve.
        """
        return self.bws[-1]

    def _get_max_lat(self) -> Latency:
        """
        Maximum recorded latency for the given curve.
        
        Returns:
            max_lat (Latency): maximum recorded latency for the given curve.
        """
        return max(self.lats)

    def _get_lead_off_lat(self) -> Latency:
        """
        Lead-off (minimum) latency for the given curve.
        
        Returns:
            lead_off_lat (Latency): lead-off (minimum) latency for the given curve.
        """
        min_bw_idx = np.argmin(self.bws)
        return self.lats[min_bw_idx]

    def _get_bw_posterior_index(self, bw: Bandwidth) -> int:
        """
        Posterior index of the bandwidth in the curve.

        Args:
            bw (Bandwidth): bandwidth.

        Returns:
            idx (int): posterior index of the bandwidth in the curve.
        """
        # Assume all self.bws are in the same unit
        bw.check_same_unit(self.bws[0])
        # Get the index of the first bw in the curve that is > than the given bw
        # Assuming self.bws are sorted in ascending order
        post_idx = bisect(self.bws_values, bw.value)
        return post_idx

    def _get_pre_and_post_bw_and_lat(
        self,
        idx: int
    ) -> tuple[Bandwidth, Bandwidth, Latency, Latency]:
        """
        Bandwidths and latencies of the point before and after the given index.

        Args:
            idx (int): index of the bandwidth in the curve

        Returns:
            (tuple[Bandwidth, Bandwidth, Latency, Latency]): previous
                and posterior bandwidths and latencies bandwidths and
                latencies of the point before and after the given index.
        """
        if idx == 0:
            # If idx is 0, there is no point before it
            return self.bws[0], self.bws[0], self.lats[0], self.lats[0]

        x1 = self.bws[idx].value
        x2 = self.bws[idx - 1].value

        xmin, xmax = min(x1, x2), max(x1, x2)
        imin, imax = 0, 0

        if xmin == x1:
            imin, imax = idx, idx - 1
        else:
            imin, imax = idx - 1, idx

        ymin, ymax = self.lats[imin].value, self.lats[imax].value
        # These correspond to bw_prev, bw_post, lat_prev, lat_post
        bw_unit = self.bws[0].unit
        lat_unit = self.lats[0].unit
        return (Bandwidth(xmin, bw_unit),
                Bandwidth(xmax, bw_unit),
                Latency(ymin, lat_unit),
                Latency(ymax, lat_unit))

    def _stress_score_computation(
        self,
        max_latency: Latency,
        lead_off_latency: Latency,
        latency: Latency,
        bw_prev: Bandwidth,
        bw_post: Bandwidth,
        lat_prev: Latency,
        lat_post: Latency
    ) -> float:
        """
        Computes the stress score for the given latencies and bandwidths.

        Args:
            max_latency (Latency): maximum latency of the curve.
            lead_off_latency (Latency): lead-off latency of the curve.
            latency (Latency): latency for the given bandwidth.
            bw_prev (Bandwidth): bandwidth of the point before the given bandwidth.
            bw_post (Bandwidth): bandwidth of the point after the given bandwidth.
            unit (str): units of bandwidth of the given bandwith.
            lat_prev (Latency): latency of the point before the given bandwidth.
            lat_post (Latency): latency of the point after the given bandwidth.

        Returns:
            score (float): stress score for the given latencies and bandwidths.
        """
        latency_variables = (max_latency.unit, lead_off_latency.unit,
                             latency.unit, lat_prev.unit, lat_post.unit)
        if any(unit != 'cycles' for unit in latency_variables):
            raise ValueError('Latencies should be in cycles for computing '
                             'stress score.')
        # prev and post BWs are expected in GB/s for properly calculating the angle
        if bw_prev.unit != 'GBps':
            bw_prev = bw_prev.as_unit('GBps')
        if bw_post.unit != 'GBps':
            bw_post = bw_post.as_unit('GBps')
        angle = math.degrees(math.atan2((lat_post.value - lat_prev.value),
                                        (bw_post.value - bw_prev.value)))
        score_angle = angle / 90
        lat_diff = latency.value - lead_off_latency.value
        max_min_lat_diff = max_latency.value - lead_off_latency.value
        score_latency = lat_diff / max_min_lat_diff
        lat_factor = 0.8
        score = lat_factor * score_latency + (1 - lat_factor) * score_angle
        # Score 1 is the worst and 0 is the best
        return score


class Curves:
    """
    Curves class for loading all the curve objects (bandwidth and
    latency points) from the curve files.
    It is assumed the curve files contain bandwidth data in MBps and
    latency data in cycles.
    """
    # Error for read ratios that are too far from the ones in the curves
    __MAX_READ_RATIO_PCT_DIFF = 10
    # Warning for read ratios that are a bit far from the ones in the curves
    __WARN_READ_RATIO_PCT_DIFF = 5

    def __init__(self, curves_path: str, display_warnings: bool = True):
        self.display_warnings = display_warnings
        self.curves = self._read_curves_file(curves_path)

    @property
    def max_read_ratio_pct_diff(self):
        return self.__MAX_READ_RATIO_PCT_DIFF
    
    @property
    def warn_read_ratio_pct_diff(self):
        return self.__WARN_READ_RATIO_PCT_DIFF

    def get_curve(self, read_ratio: float) -> Curve:
        """
        Returns the curve for the given read ratio.

        Args:
            read_ratio (float): read ratio.
        """
        closest_read_ratio = self._get_closest_read_ratio(read_ratio)
        return self.curves[closest_read_ratio]
    
    def get_read_ratios(self) -> list:
        """
        Returns read ratios of the curves.
        """
        return list(self.curves.keys())

    def get_lat(
        self,
        read_ratio: float,
        bw: Bandwidth,
        unit: str = 'cycles',
        freq: Frequency = None
    ) -> Latency:
        """
        Returns latency for given read ratio and bandwidth.

        Args:
            read_ratio (float): read ratio.
            bw (Bandwidth): bandwidth.
            unit (str, optional): units of the returned latency.
                Defaults to 'cycles'.
            freq (Frequency, optional): memory frequency (only needed
                when latency units are in time units, e.g. ns, us, s).
        """
        closest_read_ratio = self._get_closest_read_ratio(read_ratio)
        return self.curves[closest_read_ratio].get_lat(bw, unit, freq)

    def get_max_bw(self, read_ratio: float, unit: str = 'MBps') -> float:
        """
        Returns maximum recorded bandwidth for the given read ratio.

        Args:
            read_ratio (float): read ratio.
            unit (str, optional): units of the returned bandwidth.
                Defaults to 'MBps'.
        """
        closest_read_ratio = self._get_closest_read_ratio(read_ratio)
        return self.curves[closest_read_ratio].get_max_bw(unit)

    def get_max_lat(
        self,
        read_ratio: float,
        unit: str = 'cycles',
        freq: Frequency = None
    ) -> float:
        """
        Returns maximum recorded latency for the given read ratio.

        Args:
            read_ratio (float): read ratio.
            unit (str, optional): units of the returned latency.
                Defaults to 'cycles'.
            freq (Frequency, optional): memory frequency (only needed
                when latency units are in time units, e.g. ns, us, s).
        """
        closest_read_ratio = self._get_closest_read_ratio(read_ratio)
        return self.curves[closest_read_ratio].get_max_lat(unit, freq)

    def get_lead_off_lat(
        self,
        read_ratio: float,
        unit: str = 'cycles',
        freq: Frequency = None
    ) -> float:
        """
        Returns lead-off (minimum) latency for the given read ratio.

        Args:
            read_ratio (float): read ratio.
            unit (str, optional): units of the returned latency.
                Defaults to 'cycles'.
            freq (Frequency, optional): memory frequency (only needed
                when latency units are in time units, e.g. ns, us, s).
        """
        closest_read_ratio = self._get_closest_read_ratio(read_ratio)
        return self.curves[closest_read_ratio].get_lead_off_lat(unit, freq)

    def get_stress_score(self, read_ratio: float, bandwidth: Bandwidth) -> float:
        """
        Returns stress score for the given read ratio and bandwidth.

        Args:
            read_ratio (float): read ratio.
            bandwidth (Bandwidth): bandwidth.
        """
        closest_read_ratio = self._get_closest_read_ratio(read_ratio)
        return self.curves[closest_read_ratio].get_stress_score(bandwidth)
    
    def get_bws(self, unit: str = 'MBps') -> dict:
        """
        Returns bandwidths of the curves.

        Args:
            unit (str, optional): units of the returned bandwidths.
                Defaults to 'MBps'.
        """
        curves = {}
        for read_ratio, curve in self.curves.items():
            curves[read_ratio] = curve.get_bws(unit)
        return curves
    
    def get_lats(self, unit: str = 'cycles', freq: Frequency = None) -> dict:
        """
        Returns latencies of the curves.

        Args:
            unit (str, optional): units of the returned latencies.
                Defaults to 'cycles'.
            freq (Frequency, optional): memory frequency (only needed
                when latency units are in time units, e.g. ns, us, s).
        """
        curves = {}
        for read_ratio, curve in self.curves.items():
            curves[read_ratio] = curve.get_lats(unit, freq)
        return curves
    
    def get_curves_bws_lats(
        self,
        bw_unit: str = 'MBps',
        lat_unit: str = 'cycles',
        freq: Frequency = None
    ) -> dict:
        """
        Returns bandwidths and latencies in a list of tuples
        (bw-lat pairs) of the curves.

        Args:
            bw_unit (str, optional): units of the returned bandwidths.
                Defaults to 'MBps'.
            lat_unit (str, optional): units of the returned latencies.
                Defaults to 'cycles'.
            freq (Frequency, optional): memory frequency (only needed
                when latency units are in time units, e.g. ns, us, s).
        """
        curves = {}
        for read_ratio, curve in self.curves.items():
            curves[read_ratio] = curve.get_curve_bws_lats(bw_unit, lat_unit, freq)
        return curves
    
    def _read_json_curves(self, curves_file_path: str) -> dict:
        """
        Reads bandwidth-latency curves from a JSON file.

        Args:
            curves_file_path (str): path to the JSON file containing the curves.

        Returns:
            dictionary of curves, where keys are read ratios and values
                are Curve objects
        """
        with open(curves_file_path, 'r') as f:
            curves_json = json.load(f)
        curves = {}
        for read_ratio, curve in curves_json.items():
            # Convert read ratio from int to float
            read_ratio = round(int(read_ratio) / 100, 2)
            bws, lats = zip(*curve)
            bws = [Bandwidth(bw, 'MBps') for bw in bws]
            lats = [Latency(lat, 'cycles') for lat in lats]
            # Make sure BWs are ascendingly sorted (and latencies accordingly)
            lats = [x for _, x in sorted(zip(bws, lats))]
            bws = sorted(bws)
            curves[read_ratio] = Curve(read_ratio, bws, lats, self.display_warnings)
        return curves
    
    def _read_curves_file(self, curves_path: str) -> dict:
        """
        Reads bandwidth-latency curves from a file.

        Args:
            curves_path (str): path to the file containing the curves.

        Returns:
            dictionary of curves, where keys are read ratios and values
                are Curve objects
        """
        if curves_path.endswith('.json'):
            # If json has been specified for the curves
            return self._read_json_curves(curves_path)

        # If a directory has been specified for the curves
        if not os.path.isdir(curves_path):
            raise Exception(f'Path {curves_path} should be a directory or '
                            'a json file.')
        json_files = [f for f in os.listdir(curves_path) if f.endswith('.json')]
        if len(json_files) > 1:
            # If more than one json file in the directory
            raise Exception('Only one JSON file is allowed in the curves directory. '
                            f'Multiple JSON files found in: {curves_path}')
        if len(json_files) == 1:
            # Read single json file
            return self._read_json_curves(os.path.join(curves_path, json_files[0]))

        # TODO To be removed when all curves are jsons and this has been deprecated
        # Read all txt curve files in the directory
        curves = {}
        filenames = []
        for f in os.listdir(curves_path):
            if 'bwlat' in f and f.endswith('.txt'):
                filenames.append(f)
        for filename in filenames:
            with open(os.path.join(curves_path, filename)) as f:
                bws = []
                lats = []
                for line in f.readlines():
                    tokens = line.split()
                    if len(tokens) >= 2 and tokens[0][0] != '#':
                        bws.append(Bandwidth(float(tokens[0]), 'MBps'))
                        lats.append(Latency(float(tokens[1]), 'cycles'))
                if not len(bws) == len(lats) or len(bws) == 0 or len(lats) == 0:
                    raise BadFileFormatError(curves_path)
            read_ratio = int(filename.split('_')[1].replace('.txt', ''))
            # Make sure BWs are ascendingly sorted (and latencies accordingly)
            lats = [x for _, x in sorted(zip(bws, lats))]
            bws = sorted(bws)
            # Convert read ratio from int to float
            read_ratio = round(read_ratio / 100, 2)
            curves[read_ratio] = Curve(read_ratio, bws, lats, self.display_warnings)
        return curves
    
    def _get_closest_read_ratio(self, read_ratio: float):
        """
        Returns the closest read ratio in the curves for the given read ratio.

        Args:
            read_ratio (float): read ratio.

        Returns:
            closest_read_ratio (float): closest read ratio in the curves
                for the given read ratio.
        """
        rounded_rr = round(read_ratio, 2)
        if rounded_rr in self.curves:
            return rounded_rr
        
        if min(self.curves.keys()) >= 0.5 and read_ratio < 0.5:
            # Return 0.5 if all ratios are > 0.5 and the given ratio is < 0.5
            return 0.5
        
        # Get closest read ratio in the curves
        closest_read_ratio = min(self.curves.keys(), key=lambda x: abs(x - read_ratio))
        if abs(closest_read_ratio - read_ratio) > self.max_read_ratio_pct_diff:
            # Raise exception if the closest ratio is too far from the given one
            raise ReadRatioMismatchError(read_ratio, closest_read_ratio)

        is_warn = abs(closest_read_ratio - read_ratio) > self.warn_read_ratio_pct_diff
        if is_warn and self.display_warnings:
            # Give warning if the closest ratio is a bit far from the given one
            read_ratio_mismatch_warning(read_ratio, closest_read_ratio)

        return closest_read_ratio
