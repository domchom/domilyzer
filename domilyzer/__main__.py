"""Entry point.

The conversion now runs *inside* the GUI window (on a worker thread, streaming
progress + log into the window), and the Bruker / Flamingo / Olympus windows
switch between each other via ``runner.main``. Set ``MANUAL_TEST`` to run a
single conversion headlessly against ``TEST_FOLDER`` without opening any window.
"""

import numpy as np

from domilyzer.runner import main, run_conversion

# ---- headless manual test (no GUI) ----
MANUAL_TEST = False
TEST_FOLDER = "/Users/domchom/Desktop/test"
TEST_MICROSCOPE = "Bruker"  # 'Bruker' | 'Flamingo' | 'Olympus'


def _manual_test():
    red = np.zeros((3, 256), dtype="uint8"); red[0] = np.arange(256, dtype="uint8")
    green = np.zeros((3, 256), dtype="uint8"); green[1] = np.arange(256, dtype="uint8")
    blue = np.zeros((3, 256), dtype="uint8"); blue[2] = np.arange(256, dtype="uint8")
    magenta = np.zeros((3, 256), dtype="uint8")
    magenta[0] = np.arange(256, dtype="uint8"); magenta[2] = np.arange(256, dtype="uint8")

    run_conversion(
        parent_folder_path=TEST_FOLDER,
        microscope_type=TEST_MICROSCOPE,
        max_project=True,
        avg_project=False,
        single_plane=False,
        auto_metadata_extract=True,
        folder_of_folders=False,
        ch1_lut=red, ch2_lut=green, ch3_lut=blue, ch4_lut=magenta,
        test=True,
    )


if __name__ == "__main__":
    if MANUAL_TEST:
        _manual_test()
    else:
        main()
    print("Done with script!")
