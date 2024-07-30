import os
import subprocess
import contextlib


def run_tests():
    # Constants for colored output
    BAD_COL = '\033[0;31m'
    OK_COL = '\033[0;32m'
    NO_COL = '\033[0m'

    test_dir = 'tests/knl_ddr4-2400_mcdram'
    new_out_path = os.path.join(test_dir, 'new.out')
    expected_out_path = os.path.join(test_dir, 'expected.out')
    diff_path = os.path.join(test_dir, 'expected_vs_new.diff')

    # Remove the old out file if it exists
    if os.path.exists(new_out_path):
        os.remove(new_out_path)

    print("Remember to install PROFET with \"pip install .\" before running tests.")
    print("Running tests, please wait. The whole process should take less than 5 minutes.\n")

    # Run the test script and redirect output to new.out
    with open(new_out_path, 'w') as new_out_file:
        # Using contextlib for sending prints to stdout
        with contextlib.redirect_stdout(new_out_file):
            profet_root = f'{os.path.dirname(os.path.realpath(__file__))}/..'
            app_profiles_path = os.path.join(profet_root, 'tests/app_profiles/DDR4-2400_trace/')
            profiles = os.listdir(app_profiles_path)
            benchmarks = [d for d in profiles
                        if os.path.isdir(os.path.join(app_profiles_path, d))]

            for benchmark in benchmarks:
                print(benchmark, flush=True)

                run_file = f'profet'
                app_profile = os.path.join(app_profiles_path, benchmark)
                config = os.path.join(profet_root, 'configs/sample.json')
                mem_baseline = os.path.join(profet_root, 'tests/data/bw_lat_curves/ddr4.json')
                mem_target = os.path.join(profet_root, 'tests/data/bw_lat_curves/mcdram.json')

                call = f'{run_file} -w -a {app_profile} -c {config} --mem-base {mem_baseline} --mem-target {mem_target}'
                # os.system(call)
                # Redirecting stdout and stderr of the subprocess to the new_out_file
                subprocess.run(call, shell=True, stdout=new_out_file, stderr=new_out_file)

                if benchmark != benchmarks[-1]:
                    print('', flush=True)

    # Run diff command to compare expected and new outputs
    with open(diff_path, 'w') as diff_file:
        subprocess.run(['diff', '--ignore-all-space', '--suppress-common-lines',
                        expected_out_path, new_out_path], stdout=diff_file)

    # Print the test verdict
    if os.path.getsize(diff_path) == 0:
        print(f"{OK_COL}[ OK ]")
    else:
        print(f"{BAD_COL}[FAIL]")

    print(f"{NO_COL} {test_dir}")


if __name__ == '__main__':
    run_tests()

    





