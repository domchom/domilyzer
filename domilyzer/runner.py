"""Conversion orchestration + mode loop.

``run_conversion`` performs the file-conversion work for one microscope mode --
the logic that used to live inline in ``__main__.main``. It is plain and
print-driven so it works both headless and inside the GUI (which captures stdout
into its log and runs it on a worker thread).

``main`` runs the persistent GUI loop: it opens the window for the current mode
and, when that window asks to switch microscopes, opens the next one -- so the
Bruker / Flamingo / Olympus GUIs behave like tabs rather than one-shot dialogs.
"""

import os
import shutil
import timeit

from domilyzer.functions_gui.general_functions import (
    initializeOutputFolders,
    initializeLogFile,
    saveLogFile,
    createImageJMetadataTags,
)
from domilyzer.workflows.bruker_workflow import processBrukerImages
from domilyzer.workflows.olympus_workflow import processOlympusImages
from domilyzer.workflows.flamingo_workflow import processFlamingoImages


def _projection_type(max_project, avg_project):
    """Resolve the mutually-exclusive projection checkboxes into the string the
    workflows expect (``'max'`` / ``'avg'`` / ``None``)."""
    if max_project:
        print('Max projection selected. Saving max projections.')
        return 'max'
    if avg_project:
        print('Avg projection selected. Saving avg projections.')
        return 'avg'
    print('Neither max nor avg projection selected. Saving full hyperstacks. '
          'This might take a while!')
    return None


def run_conversion(*, parent_folder_path, microscope_type, max_project, avg_project,
                   single_plane, auto_metadata_extract, folder_of_folders,
                   ch1_lut, ch2_lut, ch3_lut, ch4_lut, test=False):
    """Convert every movie under *parent_folder_path* for one microscope mode.

    Prints progress as it goes (the GUI captures this into its log). Returns the
    populated ``log_details`` dict (or ``None`` in test mode)."""
    start_time = timeit.default_timer()
    projection_type = _projection_type(max_project, avg_project)

    imagej_tags = createImageJMetadataTags(
        LUTs={'LUTs': [ch1_lut, ch2_lut, ch3_lut, ch4_lut]}, byteorder='>')

    # Folder-of-folders runs (and every non-Flamingo run) enumerate subfolders;
    # a single Flamingo movie processes the parent folder directly.
    use_subfolders = folder_of_folders or microscope_type != 'Flamingo'

    image_folders = None
    if use_subfolders:
        image_folders = sorted(
            f for f in os.listdir(parent_folder_path)
            if os.path.isdir(os.path.join(parent_folder_path, f)) and not f.startswith('!')
        )
        if not image_folders:
            raise FileNotFoundError(
                "No image subfolders found in the selected folder. Select the parent "
                "folder that contains the per-movie folders."
            )

    processed_images_path = parent_folder_path
    metadata_csv_path = None
    scope_folders_path = None
    log_file_path = None
    log_details = None
    if not test:
        processed_images_path, scope_folders_path = initializeOutputFolders(
            parent_folder_path=parent_folder_path)
        metadata_csv_path = os.path.join(processed_images_path, "!image_metadata.csv")
        log_file_path, log_details = initializeLogFile(processed_images_path=processed_images_path)

    if microscope_type == 'Bruker':
        log_details, _ = processBrukerImages(
            parent_folder_path=parent_folder_path,
            image_folders=image_folders,
            processed_images_path=processed_images_path,
            metadata_csv_path=metadata_csv_path,
            microscope_type=microscope_type,
            projection_type=projection_type,
            single_plane=single_plane,
            auto_metadata_extract=auto_metadata_extract,
            test=test,
            imagej_tags=imagej_tags,
            log_details=log_details,
        )
    elif microscope_type == 'Olympus':
        processOlympusImages(
            parent_folder_path=parent_folder_path,
            processed_images_path=processed_images_path,
            microscope_type=microscope_type,
            projection_type=projection_type,
            imagej_tags=imagej_tags,
            image_folders=image_folders,
            test=test,
        )
    elif microscope_type == 'Flamingo':
        processFlamingoImages(
            parent_folder_path=parent_folder_path,
            projection_type=projection_type,
            processed_images_path=processed_images_path,
            imagej_tags=imagej_tags,
            image_folders=image_folders if folder_of_folders else None,
        )
    else:
        raise ValueError(f"Unknown microscope type: {microscope_type!r}")

    # Move the now-processed scope folders aside and save the log.
    if use_subfolders and not test and image_folders:
        for folder_name in image_folders:
            try:
                shutil.move(os.path.join(parent_folder_path, folder_name),
                            os.path.join(scope_folders_path, folder_name))
            except Exception as e:
                print(f"Could not move {folder_name}: {e}")
            for oif_file in [f for f in os.listdir(parent_folder_path) if f.endswith('.oif')]:
                shutil.move(os.path.join(parent_folder_path, oif_file),
                            os.path.join(scope_folders_path, oif_file))
        if log_details is not None:
            log_details["Time Elapsed"] = f"{timeit.default_timer() - start_time:.2f} seconds"
            saveLogFile(log_file_path, log_details)

    print(f'Time elapsed: {timeit.default_timer() - start_time:.2f} seconds')
    return log_details


def main():
    """Persistent GUI loop: open the current mode's window, and when it asks to
    switch microscopes, open the next one. Exits when a window is closed without
    requesting a switch."""
    # Imported here so headless `run_conversion` users don't need a display.
    from domilyzer.functions_gui.gui import BaseGUI, FlamingoGUI, OlympusGUI

    gui_for_mode = {
        "Bruker": BaseGUI,
        "Flamingo": FlamingoGUI,
        "Olympus": OlympusGUI,
    }

    mode = "Bruker"
    while mode is not None:
        gui = gui_for_mode[mode]()
        gui.mainloop()
        mode = getattr(gui, "next_mode", None)


if __name__ == "__main__":
    main()
