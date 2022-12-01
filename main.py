import subprocess
from os import listdir, getenv, mkdir, remove, walk
from os.path import isfile, join, isdir
from pathlib import Path
import logging
import glob
import json
import math
import geopandas as gpd

import string
import random


def check_output_dir(path):
    """
    Check output directory exists and create if not
    """
    if isdir(path) is False:
        mkdir(path)
    else:
        files = [f for f in listdir(path) if isfile(join(path, f))]
        for file in files:
            remove(join(path,file))
    return


def output_file_name(input_path, output_name, number_of_input_files):
    """
    Set the name for the output file from each clip process
    If more than 1 input file to be clipped, default behaviour should be used
    If only one input file passed, and output file name not set, use default behavior
    If only one input file passed, and the output file name is passed, use output file name
    """
    input_path, input_extension = input_path.split('.')
    input_name = input_path.split('/')[-1]
    if number_of_input_files > 1 or output_name is None:
        output_file = input_name + '_clip.' + input_extension
    else:
        output_file = output_name

    return output_file


def fetch_clip_file():
    """
    Check the clip extents directory for a file to clip the input data with.

    Return None is no file found.
    """
    clip_file = []  # set in case no file is passed
    extensions = ['gpkg', 'shp', 'txt']
    for extension in extensions:

        for file in glob.glob(join(data_path, input_dir, clip_extent_dir, "*.%s" % extension)):
            clip_file.append(file)

    return clip_file


def get_data_type(file, vector_types, raster_types):
    """
    Get the data type, raster or vector, of the clip file
    """

    # get the file extension to identify data type
    extension_text = file.split('.')[-1]

    # set the data type
    if extension_text in raster_types:
        return 'raster'
    elif extension_text in vector_types:
        return 'vector'
    else:
        return None


def filter_input_files(input_file_list, file_extensions):
    """
    Get those files from the list of input files where the file extensions is recognised as a raster or vector data type

    """
    verified_file_list = []

    # loop through the files
    for file in input_file_list:
        # fetch file extension
        file_extension = file.split('.')[-1].lower()

        # check if file extension in defined set of usable file types
        if file_extension in file_extensions:
            verified_file_list.append(file)

    return verified_file_list


def find_extents_file(name, path):
    for root, dirs, files in walk(path):
        if name in files:
            return join(root, name)
            

def get_crs_of_data(file, vector=False):
    """
    Find the crs of the file. Checks that it exists and return it for any further required checks.
    """

    if vector is False:
        info = subprocess.run(["gdalinfo", "-json", file], stdout=subprocess.PIPE)#.stdout.splitlines()
        print('**********')
        #print(info.stdout.decode("utf-8"))
        info = info.stdout.decode("utf-8")
        #info = info.replace('\n','')
        info_ = json.loads(info)
        #print(info_.keys())
        if 'coordinateSystem' in info_.keys():
            proj = info_['coordinateSystem']['wkt'].split(',')[0].replace('PROJCRS[', '').replace('"', '')
        else:
            # no projection information available
            proj = None

    elif vector is True:
        info = subprocess.run(["ogrinfo", "-ro", "-so", "-al", file], stdout=subprocess.PIPE)#, "glasgow_city_centre_lad"])

        info = info.stdout
        info = info.decode("utf-8").split('\n')
        for line in info:
            if 'PROJCRS' in line:
                proj = line.replace('PROJCRS[', '').replace('"', '').replace(',', '')

    return proj


# Round minima down and maxima up to nearest km
def round_down(val, round_val):
    """Round a value down to the nearst value as set by the round val parameter"""
    return math.floor(val / round_val) * round_val


def round_up(val, round_val):
    """Round a value up to the nearst value as set by the round val parameter"""
    return math.ceil(val / round_val) * round_val


def round_bbox_extents(extents, round_to):
    """Round extents
    extents: a list of 4 values which are the 2 corners/extents of a layer
    rount_to: an integer value in base 0 in meters to round the extents too
    """

    xmin = round_down(extents[0], round_to)
    ymin = round_down(extents[2], round_to)
    xmax = round_up(extents[1], round_to)
    ymax = round_up(extents[3], round_to)

    return [xmin, xmax, ymin, ymax]

# file paths
data_path = '/data'
input_dir = 'inputs'
clip_extent_dir = 'clip_extent'
data_to_clip_dir = 'clip'
output_dir = 'outputs'

# check output dir exists and create if not
check_output_dir(join(data_path, output_dir))

# check dir for log file exists
#check_output_dir(join(data_path, output_dir, 'log'))

logger = logging.getLogger('tool-clip')
logger.setLevel(logging.INFO)
log_file_name = 'tool-clip-%s.log' %(''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6)))
fh = logging.FileHandler( Path(join(data_path, output_dir)) / log_file_name)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

logger.info('Log file established!')

# list of default options
defaults = {
    'output_crs': '27700',
    'crs_bng' : 'OSGB 1936 / British National Grid',
    'cut_to_bounding_box': True
}

# list of accepted file types for data being clipped
raster_accepted = ['asc', 'tiff', 'geotiff', 'jpeg']
vector_accepted = ['shp', 'gpkg', 'geojson']

# get folder structure - debugging only
logger.info(glob.glob(join(data_path,'*'), recursive=True))
logger.info(glob.glob('---'))
logger.info(glob.glob(join(data_path,input_dir,'*'), recursive=True))


## START SETTING UP THE PARAMETERISATION
# Search for input files whicha re to be clipped
input_files = []
# loop through the input/clip director for files and files in sub folders
for root, dirs, files in walk(join(data_path, input_dir, data_to_clip_dir)):
    for file in files:
        # record any files found
        input_files.append(join(root,file))

# if no input files found, terminate
if len(input_files) == 0:
    print('Error! No input files found! Terminating')
    logger.info('Error! No input files found! Terminating!')
    exit(2)

logger.info('Input files found: %s' %input_files)

# filter the input files to check that are valid
input_files = filter_input_files(input_files, vector_accepted+raster_accepted)
if len(input_files) == 0:
    print('Error! No input files given specified data format! Terminating!')
    logger.info('Error! No input files given specified data format! Terminating!')
    exit(2)

logger.info('Verified input files: %s' %input_files)
print('Verified input files: %s' %input_files)


# get extents for clip - file or defined extents
# check the data slot (inputs/clip_extent) for a spatial file
clip_file = fetch_clip_file()
if len(clip_file) > 0:
    pass
else:
    clip_file = None
print('Clip files is:', clip_file)
logger.info('Clip file: %s' % clip_file)

# check if file passed from previous step and in a different folder than expected
outcome = [find_extents_file('extents.txt', data_path)]
logger.info(' Found an extents.txt file')
print('Found a extents.txt file')
if outcome[0] is not None:
    clip_file = outcome

logger.info('Clip file set to: %s' %clip_file)

# defined extents
# a user may pass some defined extents as text. these are only used
# if no other method identified from the files found
extent = None
if clip_file is None or len(clip_file) == 0: #if not files passed expect an env to be passed defining the extents
    extent = getenv('extent')
    if extent == '' or extent == 'None': # if no extent passed
        extent = None
    
    print('Extent: %s' % extent)
    logger.info('Extent: %s' % extent)


# if no extent string set, presume file is passed and read in. if no file, return an error and exit
if extent is None and len(clip_file) == 1 and clip_file != None:
    # if a text bounds file passed, convert to extent text so can use that existing method
    # xmin,ymin,xmax,ymax
    print('Reading extents file')
    cf_ext = clip_file[0].split('.')[1]
    print(cf_ext)
    if cf_ext == 'txt':
        with open(join(data_path, input_dir, clip_file[0])) as ef:
            extent = ef.readline()
        clip_file = None

print('Extent set as:', extent)
print('Clip file is:', clip_file)

# no data to allow a file to be clipped has been found. exit.
if extent is None and clip_file is None:
    # if neither a clip file set or an extent passed
    print('Error! No clip_file var or extent var passed. Terminating!')
    logger.info('Error: No clip file found and no extent defined. At least one is required. Terminating!')
    exit(2)

# check if the clip file is still in a list format - it no longer needs to be
if clip_file is not None and len(clip_file) > 0:
    clip_file = clip_file[0]

# GET USER SENT PARAMETERS
# CLIP_TO_EXTENT_BOX
# get if cutting to shapefile or bounding box of shapefile (if extent shapefile passed)
clip_to_extent_bbox = getenv('clip_to_extent_bbox')
if clip_to_extent_bbox is None:
    cut_to_bounding_box = defaults['cut_to_bounding_box']
elif clip_to_extent_bbox == 'clip-to-bounding-box':
    cut_to_bounding_box = True
elif clip_to_extent_bbox == 'clip-to-vector-outline':
    cut_to_bounding_box = False
else:
    print(clip_to_extent_bbox)

# OUTPUT_FILE
# this is only used if a single input file is passed
output_file = getenv('output_file')
print('Output file: %s' % output_file)
logger.info('Output file: %s' % output_file)
if len(input_files) > 1:
    logger.info('Setting output file var as None as more than one input file passed')
    output_file = None
elif output_file is None or output_file == 'None':
    logger.info('No output file var passed')
    output_file = None
elif output_file[0] == '' or output_file == '[]': # needed on DAFNI
    print('Warning! Empty output file var passed.')
    logger.info('Empty output file var passed')
    output_file = None

# SAVE_LOGFILE
save_logfile = getenv('save_logfile') # get the type of data to be clipped. raster or vector
if save_logfile is None: # grab the default if the var hasn't been passed
    print('Warning! No save_logfile env passed. Default, False, will be used.')
    save_logfile = False
elif save_logfile.lower() == 'true':
    save_logfile = True
elif save_logfile.lower() == 'false':
    save_logfile = False
else:
    print('Error! Incorrect setting for save logfile parameter (%s)' %save_logfile)
    logger.info('Error! Incorrect setting for save logfile parameter (%s)' % save_logfile)


# ROUND EXTENTS
# get the round extents option
round_extents = getenv('round_extents') # get the rounds_extents parameter value
if round_extents is None or round_extents == 'None' or round_extents == 0:
    print('Warning! No round_extents env passed. No rounding will be applied.')
    round_extents = False
else:
    try:
        # convert the option to an integer
        # this should be in meters e.g. 1000m = 1km
        round_extents = int(round_extents)
    except:
        print('Error! Incorrect setting for save logfile parameter (%s)' %save_logfile)
        logger.info('Error! Incorrect setting for save logfile parameter (%s)' % save_logfile)
        exit()

# END OF PARAMETER FETCHING
# START RUNNING THE PROCESSING

logger.info('Starting to loop through files and running clip process')
# loop through each file to clip
for input_file in input_files:

    print('Input file is: %s' % input_file)
    # set the data type
    data_type = get_data_type(input_file, vector_types=vector_accepted, raster_types=raster_accepted)
    logger.info('Data type for file %s to be clipped identified as: %s' % (input_file, data_type))

    # get the crs of the input file
    input_crs = get_crs_of_data(join(data_path, input_dir, 'clip', input_file))
    if input_crs is None:
        print('Warning! No projection information could be found for the input file.')
        logger.info('Warning! No projection information could be found for the input file.')

        input_crs = defaults['crs_bng']
        print('Warning! Using default projection (british national grid) for input file.')
        logger.info('Warning! Using default projection (british national grid) for input file.')
		
    print('Input CRS is: %s' % input_crs)
    logger.info('Input CRS is: %s' % input_crs)

    # run clip process
    if data_type is None:
        logger.info('Data type could no be identified for the found input file %s. Skipping clip process for this file.' % input_file)
        print('Error. Data type is None')
    elif data_type == 'vector':
        print('Running vector clip')
        logger.info('Using vector methods')

        output_file_name_set = output_file_name(input_file, output_file, len(input_files))

        if clip_file is not None:
            logger.info('Using clip file method')
            logger.info("Running....")
            subprocess.run(["ogr2ogr", "-clipsrc", join(data_path, input_dir, clip_file), "-f", "GPKG",
                            join(data_path, output_dir, output_file_name_set), join(data_path, input_dir, input_file)])
            logger.info("....completed processing")

        elif extent is not None:
            print('Running extent method')

            if round_extents is not False:
                print('Rounding extents')
                extent = round_bbox_extents(extent, round_extents)

            logger.info('Using extent method')
            logger.info("Running....")
            subprocess.run(["ogr2ogr", "-spat", *extent, "-f", "GPKG", join(data_path, output_dir,output_file_name_set),
                            join(data_path, input_dir, input_file)])
            logger.info("....completed processing")

    elif data_type == 'raster':
        print('Running raster clip')
        print('Running for input:', input_file)

        output_file_name_set = output_file_name(input_file, output_file, len(input_files))

        logger.info('Using raster methods')
        if extent is not None:
            logger.info("Using extent method")
            print('Using extent method')
            print('Extents are: %s' %extents)

            if round_extents is not False:
                print('Rounding extents')
                extent = round_bbox_extents(extent, round_extents)

            logger.info("Running....")

            print('Running subprocess')
            extents = extent.split(",")
            subprocess.run(["gdalwarp", "-te", extents[0], extents[1], extents[2], extents[3], join(data_path, input_dir, data_to_clip_dir, input_file), join(data_path, output_dir, output_file_name_set)])
            #subprocess.run(["gdalwarp", "-te", *extent, join(data_path, input_dir, data_to_clip_dir, input_file),
            #                join(data_path, output_dir, output_file_name_set)])
            logger.info("....completed processing")

        elif clip_file is not None and len(clip_file) > 0:
            print("Using clip file method")
            logger.info("Using clip file method")

            # get crs of clip file
            clip_crs = get_crs_of_data(clip_file, vector=True)

            # if crs could not be found, return error
            if clip_crs is None:
                print('Error! No projection information could be found for the clip file.')
                logger.info('Error! No projection information could be found for the clip file.')
                exit()

            # need to check crs of clip file is same as that for the data being clipped
            if clip_crs != input_crs:
                print("Error! CRS of datasets do not match!!! (input: %s ; clip: %s)" %(input_crs, clip_crs))
                logger.info("Error! CRS of datasets do not match!!!")
                exit()

            if cut_to_bounding_box is False:
                # crop to the shapefile, not just the bounding box of the shapefile
                print('Clipping with cutline flag')
                command_output = subprocess.run(["gdalwarp", "-cutline", clip_file, "-crop_to_cutline", join(data_path, input_dir, data_to_clip_dir, input_file),
                     join(data_path, output_dir, output_file_name_set)])

            else:
                print('clipping with bounding box of vector data')
          
                print(join(data_path, input_dir, data_to_clip_dir, input_file))
                print(join(data_path, output_dir, output_file_name_set)
)
                # this should work but does not for some reason....
                #command_output = subprocess.run(["gdalwarp", "-cutline", clip_file, join(data_path, input_dir, data_to_clip_dir, input_file), join(data_path, output_dir, output_file_name_set)])
                # so instead using this....
                
                # read in shapefile
                t = gpd.read_file(clip_file)
                # get bounding box for shapefile
                bounds = t.geometry.total_bounds

                if round_extents is not False:
                    print('Rounding extents')
                    bounds = round_bbox_extents(bounds, round_extents)

                print('Using bounds:', bounds)
                # run clip
                subprocess.run(["gdalwarp", "-te", str(bounds[0]), str(bounds[1]), str(bounds[2]), str(bounds[3]), join(data_path, input_dir, data_to_clip_dir, input_file), join(data_path, output_dir, output_file_name_set)])

            # check the code returned from GDAL to see if an error occurred or not
            #if command_output.returncode == 1:
            #    print('Error! Clip did not run. Please check for common errors such as missing projection information.')
            #    logger.info('Error! Clip did not run for %s. Please check for common errors such as missing projection information.' % input_file)
            #elif command_output.returncode == 0:
            #    logger.info('Clip process ran without an error being returned (%s)' % input_file)

            # add check to see if file written to directory as expected
            if isfile(join(data_path, output_dir, output_file_name_set)):
                logger.info("Raster clip method completed. Output saved (%s)" %join(data_path, output_dir, output_file_name_set))
                print('Clip completed and file written (%s)' % join(data_path, output_dir, output_file_name_set))
            else:
                logger.info("Failed. Expected output not found (%s)" % join(data_path, output_dir, output_file_name_set))


# check output file is written...... and if not return an error?
files = [f for f in listdir(join(data_path, output_dir)) if
         isfile(join(data_path, output_dir, f))]
logger.info('Files in output dir: %s' % files)
print('Files in output dir: %s' % files)

print('Completed running clip')
logger.info('Completed running clip. Stopping tool.')

# final step - delete the log file is requested by user
if save_logfile is False:
    # delete log file dir
    remove(join(data_path, output_dir, log_file_name))

