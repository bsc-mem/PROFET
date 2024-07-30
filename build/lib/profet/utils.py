from os import path
import pandas as pd

def load_cpi(profiling_dir: str):
    """
    Reads a file containing average CPIs per benchmark from the given directory.
    It assumes that the file is called average_cpi.csv
    If the file does not exist, it first computes it using the traces in the directory.
    If the traces are not present, the error is reported.

    Args:
        profiling_dir (str): Path to the directory containing the profiling data.

    Returns:
        The Pandas Series indexed by benchmark name, so it can be used as CPI[bench] from the outside code.
    """
    cpi_file_path = path.join(profiling_dir, 'average_cpi.csv')
    if not path.exists(cpi_file_path):
        # File does not exist. Try to create it from traces. Fail if not possible.
        # TODO: Complete implementation
        print(f"ERROR: CPI file missing - {cpi_file_path}")
        exit()
    else:
        df = pd.read_csv(cpi_file_path, sep='\s+', index_col='benchmark', comment='#')
        return df['CPI']