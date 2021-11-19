import subprocess
from os import listdir, getenv, mkdir, remove
from os.path import isfile, join, isdir
from pathlib import Path
import logging
import glob


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


def output_file_name(input_name, output_name, number_of_input_files):
    """
    Set the name for the output file from each clip process
    If more than 1 input file to be clipped, default behaviour should be used
    If only one input file passed, and output file name not set, use default behavior
    If only one input file passed, and the output file name is passed, use output file name
    """
    input_name, input_extension = input_name.split('.')

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
    clip_file = None  # set in case no file is passed
    extensions = ['gpkg', 'shp']
    for extension in extensions:
        for file in glob.glob(join(data_path, clip_extent_dir, "*.%s" % extension)):
            clip_file = file

    return clip_file


def filter_input_files(input_file_list, data_type):
    """

    """

    if data_type == 'raster':
        file_extensions = ['asc', 'tiff', 'geotiff']
    elif data_type == 'vector':
        file_extensions = ['gpkg', 'shp', 'geojson']

    verified_file_list = []

    for file in input_file_list:
        file_extension = file.split('.')[-1].lower()
        print(file_extension)
        if file_extension in file_extensions:
            verified_file_list.append(file)

    return verified_file_list


# file paths
data_path = '/data'
input_dir = 'inputs'
clip_extent_dir = 'clip_extent'

output_dir = 'outputs'

# check output dir exists and create if not
check_output_dir(join(data_path, output_dir))
# chek dir for log file exists
check_output_dir(join(data_path, output_dir, 'log'))
# check output data dir exists
check_output_dir(join(data_path, output_dir, 'data'))

logger = logging.getLogger('transformer')
logger.setLevel(logging.INFO)
fh = logging.FileHandler( Path(join(data_path, output_dir, 'log')) / 'tool-clip.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

logger.info('Log file established!')

# a list of default options
defaults = {
    'data_type': 'vector',
    'output_crs': '27700'
}

# get data type
data_type = getenv('data_type') # get the type of data to be clipped. raster or vector
if data_type is None: # grab the default if the var hasn't been passed
    print('Warning! No data_type var passed, using default - vector')
    data_type = defaults['data_type']
logger.info('Data type to be clipped set as: %s' %data_type)

# get input file(s)
input_files = [f for f in listdir(join(data_path, input_dir)) if isfile(join(data_path, input_dir, f))]
if len(input_files) == 0:
    print('Error! No input files found! Terminating')
    logger.info('Error! No input files found! Terminating!')
    exit(2)

logger.info('Input files found: %s' %input_files)

input_files = filter_input_files(input_files, data_type)
if len(input_files) == 0:
    print('Error! No input files given specified data format! Terminating!')
    logger.info('Error! No input files given specified data format! Terminating!')
    exit(2)

logger.info('Verified input files: %s' %input_files)


# get extents for clip - file or defined extents
# clip area file
clip_file = fetch_clip_file()
print('clip files is:', clip_file)
logger.info('Clip file: %s' % clip_file)

# defined extents
extent = getenv('extent')
if extent == '' or extent == 'None': # if no extent passed
    extent = None
else:
    extent = extent.split(',')

print('Extent: %s' % extent)
logger.info('Extent: %s' % extent)

if clip_file is None and extent is None:
    # if neither a clip file set or an extent passed
    print('Error! No clip_file var or extent var passed. Terminating!')
    logger.info('Error: No clip file found and no extent defined. At least one is required. Terminating!')
    exit(2)


# output file - this is only used if a single input file is passed
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

# END OF PARAMETER FETCHING
# START RUNNING THE PROCESSING

# run clip process
if data_type == 'vector':
    print('Running vector clip')
    logger.info('Using vector methods')
    print(join(data_path, output_dir, output_file))
    for input_file in input_files:

        output_file_name_set = output_file_name(input_file, output_file, len(input_files))

        if clip_file is not None:
            logger.info('Using clip file method')
            logger.info("Running....")
            subprocess.run(["ogr2ogr", "-clipsrc", join(data_path, input_dir, clip_file), "-f", "GPKG",
                            join(data_path, output_dir, 'data', output_file_name_set), join(data_path, input_dir, input_file)])
            logger.info("....completed processing")

        elif extent is not None:
            print('Running extent method')
            logger.info('Using extent method')
            logger.info("Running....")
            subprocess.run(["ogr2ogr", "-spat", *extent, "-f", "GPKG", join(data_path, output_dir, 'data', output_file_name_set),
                            join(data_path, input_dir, input_file)])
            logger.info("....completed processing")

elif data_type == 'raster':
    print('Running raster clip')
    for input_file in input_files:
        print('Running for input:', input_file)

        output_file_name_set = output_file_name(input_file, output_file, len(input_files))

        logger.info('Using raster methods')
        if extent is not None:
            logger.info("Using extent method")
            print('Using extent method')
            logger.info("Running....")
            subprocess.run(["gdalwarp", "-te", *extent, join(data_path, input_dir, input_file),
                            join(data_path, output_dir, 'data', output_file_name_set)])
            logger.info("....completed processing")

        elif clip_file is not None:
            print("Using clip file method")
            logger.info("Using clip file method")

            subprocess.run(["gdalwarp", "-cutline", clip_file, join(data_path, input_dir, input_file),
                            join(data_path, output_dir, 'data', output_file_name_set)])

            # add check to see if file written to directory as expected
            if isfile(join(data_path, output_dir, 'data', output_file_name_set)):
                logger.info("Raster clip method completed. Output saved (%s)" %join(data_path, output_dir, 'data', output_file_name_set))
                print(join(data_path, output_dir, 'data', output_file_name_set))
            else:
                logger.info("Failed. Expected output not found (%s)" % join(data_path, output_dir, 'data', output_file_name_set))



# check output file is written...... and if not return an error?
files = [f for f in listdir(join(data_path, output_dir, 'data')) if
         isfile(join(data_path, output_dir, 'data', f))]
logger.info('Files in output dir: %s' % files)
print('Files in output dir: %s' % files)

print('Completed running clip')
logger.info('Completed running clip. Stopping tool.')


