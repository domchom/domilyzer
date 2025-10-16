import os
import struct
import tifffile
import numpy as np

def initializeOutputFolders(parent_folder_path: str) -> tuple:
    '''
    Create the output folders for the processed images and the scope folders.
    '''
    processed_images_path = os.path.join(parent_folder_path, "!processed_images")
    os.makedirs(processed_images_path, exist_ok=True)
    
    scope_folders_path = os.path.join(parent_folder_path, "!scope_folders")
    os.makedirs(scope_folders_path, exist_ok=True)
    
    return processed_images_path, scope_folders_path

def initializeLogFile(processed_images_path: str) -> tuple:
    '''
    Set up the log file and parameters.
    '''
    log_file_path = os.path.join(processed_images_path, "!image_conversion_log.txt")
    log_details = {'Files Not Processed': [],
                   'Files Processed': [],
                   'Issues': [],
                   'Other Notes': [],}
    
    return log_file_path, log_details

def adjustImageJAxes(image_type: str) -> str:
    '''
    Determine the ImageJ axes of the image based on the image type.
    '''
    if 'max_project' in image_type:
        axes = 'TCYX' 
    elif 'avg_project' in image_type:
        axes = 'TCYX' 
    elif image_type == 'single_plane_single_frame': 
        axes = 'ZCYX' 
    elif image_type == 'single_plane_multi_frame':
        axes = 'TZCYX'
    else:
        axes = 'TZCYX'
                
    return axes

def organizeFilesByChannel(folder_tif_filenames: list, microscope_type: str) -> dict:
    """
    Organize files by channel based on the folder contents.
    
    Parameters:
    folder_path (list): List of file paths in the folder.
    microscope_type (str): Type of microscope ('Bruker' or 'Olympus').
    
    Returns:
    dict: A dictionary where keys are channel names and values are lists of file paths.
    """
    # Collect the files corresponding to each channel and put in dict
    channel_filenames = {}
    for file in folder_tif_filenames:
        if microscope_type == 'Bruker':
            channel_name = os.path.basename(file).split('_')[-2]
        elif microscope_type == 'Olympus':
            channel_name = os.path.basename(file).split('_')[1][:4]
        if channel_name not in channel_filenames:
            channel_filenames[channel_name] = []
        channel_filenames[channel_name].append(file)
        
    # Check last file size consistency
    for channel, files in channel_filenames.items():
        if len(files) > 1:
            sizes = [os.path.getsize(f) for f in files]
            if sizes[-1] != sizes[0]:  # compare last file size to the rest
                print(f"⚠️ Skipping last frame (incomplete frame)")
                files.pop(-1)
                
    return channel_filenames

def saveLogFile(
    logPath: str, 
    logParams: dict
) -> None:
    '''
    Creates a log file in the specified directory with the specified parameters.

    Parameters
    directory : str
        The directory in which to create the log file.
    logParams : dict
        A dictionary containing the parameters to be logged.
    '''
    logFile = open(logPath, "w")                                    
    for key, value in logParams.items():                            
        logFile.write('%s: %s\n' % (key, value))                    
    logFile.close()   
    
def saveImageJHyperstack(hyperstack: np.array,
                         axes: str, 
                         metadata: dict, 
                         image_output_name: str, 
                         imagej_tags: list = None
                         ) -> None:   
    """
    Save a hyperstack as a TIFF file with ImageJ metadata.
    
    Parameters
    hyperstack : np.array
        The hyperstack to be saved.
    axes : str
        The axes of the hyperstack (e.g., 'TCYX').
    metadata : dict
        Metadata to be included in the TIFF file.
    image_output_name : str
        The name of the output TIFF file.
    imagej_tags : list, optional
        Additional ImageJ metadata tags to be included in the TIFF file.
    """
    # Write the hyperstack to a TIFF file
    if metadata is None: # for the flamingo data for now, and if user does not want to save metadata
        saved_metadata = {
            'axes': axes,
            'unit': 'um',
            'mode': 'composite'
        }
    else:  # for the bruker data for now
        saved_metadata = {
            'axes': axes,
            'finterval': metadata['framerate'], 
            'unit': 'um',
            'mode': 'composite'
        }
    tifffile.imwrite(image_output_name, 
                    hyperstack, 
                    byteorder='>', 
                    imagej=True,
                    resolution=(1 / metadata['X_microns_per_pixel'], 1 / metadata['Y_microns_per_pixel']) if metadata else None,
                    metadata=saved_metadata, 
                    extratags=imagej_tags
                )
    

def createImageJMetadataTags(LUTs: dict, 
                             byteorder: str = '>'
                             ) -> tuple:
    """
    Return IJMetadata and IJMetadataByteCounts tags from metadata dict.

    The tags can be passed to the TiffWriter.save function as extratags.
    """
    header = [{'>': b'IJIJ', '<': b'JIJI'}[byteorder]]
    bytecounts = [0]
    body = []

    def writestring(data, byteorder):
        return data.encode('utf-16' + {'>': 'be', '<': 'le'}[byteorder])

    def writedoubles(data, byteorder):
        return struct.pack(byteorder+('d' * len(data)), *data)

    def writebytes(data, byteorder):
        return data.tobytes()

    metadata_types = (
        ('Info', b'info', 1, writestring),
        ('Labels', b'labl', None, writestring),
        ('Ranges', b'rang', 1, writedoubles),
        ('LUTs', b'luts', None, writebytes),
        ('Plot', b'plot', 1, writebytes),
        ('ROI', b'roi ', 1, writebytes),
        ('Overlays', b'over', None, writebytes))

    for key, mtype, count, func in metadata_types:
        if key not in LUTs:
            continue
        if byteorder == '<':
            mtype = mtype[::-1]
        values = LUTs[key]
        if count is None:
            count = len(values)
        else:
            values = [values]
        header.append(mtype + struct.pack(byteorder+'I', count))
        for value in values:
            data = func(value, byteorder)
            body.append(data)
            bytecounts.append(len(data))

    body = b''.join(body)
    header = b''.join(header)
    data = header + body
    bytecounts[0] = len(header)
    bytecounts = struct.pack(byteorder+('I' * len(bytecounts)), *bytecounts)
    return ((50839, 'B', len(data), data, True),
            (50838, 'I', len(bytecounts)//4, bytecounts, True))
