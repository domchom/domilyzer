import os
import csv
import shutil
import tifffile
import numpy as np
import xml.etree.ElementTree as ET

def determineImageTypeBruker(folder_path: str, 
                             projection_type: str, 
                             single_plane: bool = False
                             ) -> tuple:
    """
    Determine the image type based on the folder contents.
    
    Parameters:
    folder_path (str): Path to the folder containing the images.
    projection_type (str): Type of projection ('max' or 'avg').
    single_plane (bool): Whether the images are single plane or not.
    
    Returns:
    tuple: A tuple containing the image type and a list of file paths.
    """
    # Get all the tif files in the folder
    folder_tif_filenames = [os.path.join(folder_path, file) for file in os.listdir(folder_path) if file.endswith('.tif')]

    if single_plane is False:
        # If last tif file is 'Cycle00001', then just a single frame
        last_file_name = folder_tif_filenames[-1]
        single_timepoint = True if last_file_name.split('_')[-3] == 'Cycle00001' else False

        # Collect all files in the folder for specific image types
        if single_timepoint:
            if projection_type == 'max':
                image_type = "multi_plane_single_timepoint_max_project"
            elif projection_type == 'avg':
                image_type = "multi_plane_single_timepoint_avg_project"
            else:
                image_type = "multi_plane_single_timepoint"
                
        else:
            if projection_type == 'max':
                image_type = "multi_plane_multi_timepoint_max_project"
            elif projection_type == 'avg':
                image_type = "multi_plane_multi_timepoint_avg_project"
            else:
                image_type = "multi_plane_multi_timepoint"
    else:
        image_type = "single_plane"
        
    # Sort files to ensure correct order
    folder_tif_filenames.sort()
        
    return image_type, folder_tif_filenames

def convertImagesToNumpyArraysBruker(channel_filenames: dict) -> dict:
    """ 
    Convert images to numpy arrays for each channel.
    
    Parameters:
    channel_filenames (dict): A dictionary where keys are channel names and values are lists of file paths.
    
    Returns:
    dict: A dictionary where keys are channel names and values are lists of numpy arrays.
    """
    # Read/create images for each channel
    channel_image_arrays = {}
    for channel_name, files in channel_filenames.items():
        try:
            channel_image_arrays[channel_name] = [tifffile.imread(file, is_ome=False) for file in files]
        except Exception as e:
            print(f"Error reading TIFF file for channel {channel_name}: {e}")
            return None, None

    return channel_image_arrays

def adjustNumpyArrayAxesBruker(hyperstack: np.array,
                               image_type: str
                               ) -> tuple:
    """
    Adjust the axes of the numpy array based on the image type.

    Parameters:
    hyperstack (np.array): The numpy array representing the image stack.
    image_type (str): The type of the image stack.

    Returns:
    tuple: A tuple containing the adjusted hyperstack and the updated image type.
    """
    if image_type == "multi_plane_multi_timepoint" or image_type == "multi_plane_single_timepoint":
        hyperstack = np.moveaxis(hyperstack, [0, 1, 2, 3, 4], [0, 2, 1, 3, 4])

    elif image_type == "single_plane":
        if len(hyperstack.shape) == 5:
            hyperstack = np.moveaxis(hyperstack, [0, 1, 2, 3, 4], [1, 2, 0, 3, 4])
            image_type = "single_plane_multi_frame"
        elif len(hyperstack.shape) == 4:
            image_type = "single_plane_single_frame"

    return hyperstack, image_type

def projectNumpyArraysBruker(hyperstack: np.array, 
                             image_type: str, 
                             projection_type: str
                             ) -> np.array:
    """
    Project the numpy arrays based on the image type and projection type.
    
    Parameters:
    hyperstack (np.array): The numpy array representing the image stack.
    image_type (str): The type of the image stack.
    projection_type (str): The type of projection ('max' or 'avg').
    
    Returns:
    np.array: The projected numpy array.
    """
    if projection_type == 'max' and "single_plane" not in image_type:
        hyperstack = np.max(hyperstack, axis = 2)
    if projection_type == 'avg' and "single_plane" not in image_type:
        hyperstack = np.mean(hyperstack, axis = 2)
        hyperstack = np.round(hyperstack).astype(np.uint16) 
        
    return hyperstack

def writeMetadataCsvBruker(metadata: dict, 
                           metadata_csv_path: str, 
                           folder_name: str, 
                           log_details: dict
                           ) -> dict:
    """
    Write metadata to a CSV file.
    
    Parameters:
    metadata (dict): A dictionary containing the metadata to be written.
    metadata_csv_path (str): The path to the CSV file.
    folder_name (str): The name of the folder being processed.
    log_details (dict): A dictionary to store log details.
    
    Returns:
    dict: The updated log details.
    """
    if metadata is not None:
        # Prepare laser power headers and values
        laser_power_headers = [f"{value.split(':')[-1].strip()} power" for value in metadata['laser_power_values'].values()]
        # Prepare the column headers and values for laser power
        laser_power_headers = [f'{value.split(":")[-1].strip()} power' for value in metadata['laser_power_values'].values()]
        laser_powers = [value.split(':')[1].split(',')[0].strip() for value in metadata['laser_power_values'].values()]

        # Prepare the column headers and values for ND filters        
        nd_filter_headers = ['imaging light path', 'PA light path']
        nd_filter_values = [value.split(':')[-1].strip() for value in metadata['helios_nd_filter_values'].values()]

        # Check if the file exists and create headers if not
        try:
            with open(metadata_csv_path, 'r') as file:
                existing_headers = file.readline().strip().split(',')
        except FileNotFoundError:
            existing_headers = []

        if not existing_headers:
            # Write the headers
            with open(metadata_csv_path, 'w', newline='') as file:
                csv_writer = csv.writer(file)
                headers = ["Folder Name", "X microns per pixel", "Z microns per pixel", 
                        "Frame Rate", "Bit Depth", "Dwell Time", 
                        "Objective Lens Description"] + laser_power_headers + nd_filter_headers
                csv_writer.writerow(headers)

        # Write metadata to CSV
        with open(metadata_csv_path, 'a', newline='') as file:
            csv_writer = csv.writer(file)
            csv_writer.writerow([folder_name, 
                                metadata['X_microns_per_pixel'], 
                                metadata['Z_microns_per_pixel'],
                                metadata['framerate'],
                                    metadata['bit_depth'],
                                    metadata['dwell_time'],
                                    metadata['objective_lens_description']] + laser_powers + nd_filter_values)
        
    # Add folder name to log
    log_details['Files Processed'].append(folder_name)
    print(f"Successfully processed {folder_name}!")
        
    return log_details

def extractMetadataFromXMLBruker(xml_file_path: str, 
                                 log_params: dict
                                 ) -> tuple:
    """
    Extracts metadata from an XML file.

    Parameters:
    - xml_file (str): The path to the XML file.
    - log_params (dict): A dictionary to store any issues encountered during extraction.

    Returns:
    - bit_depth (str): The bit depth value extracted from the XML file.
    - dwell_time (str): The dwell time value extracted from the XML file.
    - helios_nd_filter_values (dict): A dictionary containing the Helios ND Filter values extracted from the XML file.
    - laser_power_values (dict): A dictionary containing the Laser Power values extracted from the XML file.
    - objective_lens_description (str): The objective lens description extracted from the XML file.
    - log_params (dict): The updated log_params dictionary with any issues encountered during extraction.
    """

    # Step 1: Make a copy of the XML file so we can update the xml version
    backup_file = xml_file_path + ".backup"
    try:
        shutil.copy(xml_file_path, backup_file)
    except Exception as e:
        log_params['Issues'] = f"Error creating a backup of the XML file: {str(e)}"
        return None, None, None, None, None, log_params

    # Step 2: Update the version in the backup file
    try:
        with open(backup_file, "r") as file:
            lines = file.readlines()
    
        # Remove the line directly after interlacedScanTrackLasers and interlacedScanTrackPowers elements because they have imcompatible XML syntax
        x=0
        for line in lines:
            if "interlacedScanTrackLasers" in line:
                del lines[x + 1]
            elif "interlacedScanTrackPowers" in line:
                del lines[x + 1]
            x+=1

        # Write the updated lines back to the backup file
        with open(backup_file, "w") as file:
            file.writelines(lines)
    except Exception as e:
        log_params['Issues'] = f"Error updating XML version in backup: {str(e)}"
        return None, log_params
    
    #Step 3: Parse the XML file
    tree = ET.parse(backup_file)
    root = tree.getroot()

    # get the bit depth with key="bitDepth"
    bit_depth_element = root.find("./PVStateShard/PVStateValue[@key='bitDepth']")
    if bit_depth_element is not None:
        bit_depth = bit_depth_element.attrib['value']
    else:
        log_params['Issues'] = "Bit Depth not found in the XML."

    # Find the PVStateValue element with key="dwellTime"
    dwell_time_element = root.find("./PVStateShard/PVStateValue[@key='dwellTime']")
    if dwell_time_element is not None:
        dwell_time = dwell_time_element.attrib['value']
    else:
        log_params['Issues'] = "Dwell time not found in the XML."

    # Find the PVStateValue element with key="heliosNDFilter"
    helios_nd_filter_element = root.find("./PVStateShard/PVStateValue[@key='heliosNDFilter']")
    if helios_nd_filter_element is not None:
        helios_nd_filter_values = {}
        for indexed_value in helios_nd_filter_element.findall("./IndexedValue"):
            index = indexed_value.attrib['index']
            value = indexed_value.attrib['description']
            helios_nd_filter_values[index] = value
    else:
        log_params['Issues'] = "Helios ND Filter values not found in the XML."

    # Find the PVStateValue element with key="laserPower"
    laser_power_element = root.find("./PVStateShard/PVStateValue[@key='laserPower']")
    if laser_power_element is not None:
        laser_power_values = {}
        for indexed_value in laser_power_element.findall("./IndexedValue"):
            index = indexed_value.attrib['index']
            value = indexed_value.attrib['value']
            description = indexed_value.attrib['description']
            laser_power_values[index] = f'value: {value}, description: {description}'
    else:
        log_params['Issues'] = "Laser Power values not found in the XML."

    # Find the PVStateValue element with key="objectiveLens"
    objective_lens_element = root.find("./PVStateShard/PVStateValue[@key='objectiveLens']")
    if objective_lens_element is not None:
        objective_lens_description = objective_lens_element.attrib['value']
    else:
        log_params['Issues'] = "Objective Lens description not found in the XML."

    # Find the frame rate
    frames = root.findall('.//Frame')
    absolute_times = {}
    for index, frame in enumerate(frames, start=1):
        absolute_time = frame.attrib.get('absoluteTime')
        files = frame.findall('File')
        for file in files:
            filename = file.attrib.get('filename')
            if "000001.ome.tif" in filename:
                name = int(filename.split("_")[-3].split("e")[-1])
                absolute_times[name] = absolute_time
    num_frames = len(absolute_times)
    total_time = float(absolute_times[num_frames])
    framerate = total_time / num_frames

    # Find the microns per pixel values
    microns_per_pixel_element = root.find(".//PVStateValue[@key='micronsPerPixel']")
    microns_per_pixel = {}
    for indexed_value in microns_per_pixel_element.findall("./IndexedValue"):
        axis = indexed_value.attrib["index"]
        value = float(indexed_value.attrib["value"])
        microns_per_pixel[axis] = value 

    # Step 4: Delete the backup file
    try:
        os.remove(backup_file)
    except Exception as e:
        log_params['Issues'] = f"Error deleting backup file: {str(e)}"
        
    metadata = {
        'bit_depth': bit_depth,
        'dwell_time': dwell_time,
        'helios_nd_filter_values': helios_nd_filter_values,
        'laser_power_values': laser_power_values,
        'objective_lens_description': objective_lens_description,
        'framerate': framerate,
        'X_microns_per_pixel': microns_per_pixel['XAxis'],
        'Y_microns_per_pixel': microns_per_pixel['YAxis'],
        'Z_microns_per_pixel': microns_per_pixel['ZAxis']
    }

    return metadata, log_params
