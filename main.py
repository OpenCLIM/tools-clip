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


def output_file_name(input_file):
    input_name, input_extension = input_file.split('.')

    #print('Input name:', input_name)
    output_file = input_name + '_clip.' + input_extension
    #print('Output file:', output_file)

    return output_file


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
fh = logging.FileHandler( Path(join(data_path, output_dir, 'log')) / 'transformer.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

logger.info('Log file established!')

# a list of default options
defaults = {
    'data_type': 'vector',
    'output_crs': '27700'
}

# get input file(s)
print(data_path)
print(input_dir)
print(join(data_path, input_dir))
input_files = [f for f in listdir(join(data_path, input_dir)) if isfile(join(data_path, input_dir, f))]
print(input_files)
logger.info('Input files: %s' %input_files)

data_type = getenv('data_type') # one of: 'clip', 're-project'
if data_type is None: # grab the default if the var hasn't been passed
    print('Warning! No data_type var passed, using default - vector')
    data_type = defaults['data_type']
logger.info('Data type: %s' %data_type)


logger.info('Running a clip')

# get extents for clip - file or defined extents
# clip area file
for file in glob.glob(join(data_path, clip_extent_dir,"*.shp")):
    clip_file = file

print('clip files is:', clip_file)
logger.info('Clip file: %s' % clip_file)

# defined extents
extent = getenv('extent')
if extent is not None:
    extent = extent.split(',')
logger.info('Extent: %s' % extent)

if clip_file is None and extent is None:
    print('Error! No clip_file var or extent var passed. Terminating!')
    exit(2)

# output file
output_file = getenv('output_file')
logger.info('Output file: %s' % output_file)
if output_file is None:
    print('Warning! No output file var passed.')
    output_file = 'clip_result'
    #exit(2)

# run clip process
if data_type == 'vector':
    print('Running vector clip')
    logger.info('Using vector methods')
    print(join(data_path, output_dir, output_file))
    if clip_file is not None:
        logger.info('Using clip file method')
        logger.info("Running....")
        subprocess.run(["ogr2ogr", "-clipsrc", join(data_path, input_dir, clip_file), "-f", "GPKG",
                        join(data_path, output_dir, 'data', output_file), join(data_path, input_dir, input_file)])
        logger.info("....completed processing")

    elif extent is not None:
        print('Running extent method')
        logger.info('Using extent method')
        logger.info("Running....")
        subprocess.run(["ogr2ogr", "-spat", *extent, "-f", "GPKG", join(data_path, output_dir, 'data', output_file),
                        join(data_path, input_dir, input_file)])
        logger.info("....completed processing")

elif data_type == 'raster':
    print('Running raster clip')
    for input_file in input_files:
        print('Running for input:', input_file)

        output_file = output_file_name(input_file)

        logger.info('Using raster methods')
        if extent is not None:
            logger.info("Using extent method")

            logger.info("Running....")
            subprocess.run(["gdalwarp", "-te", *extent, join(data_path, input_dir, input_file),
                            join(data_path, output_dir, 'data', output_file)])
            logger.info("....completed processing")

        elif clip_file is not None:
            print("Using clip file method")

            logger.info("Using clip file method")

            subprocess.run(["gdalwarp", "-cutline", clip_file, join(data_path, input_dir, input_file),
                            join(data_path, output_dir, 'data', output_file)])

            logger.info("Raster clip method completed. Output saved (%s)" %join(data_path, output_dir, 'data', output_file))
            print(join(data_path, output_dir, 'data', output_file))

# check output file is written...... and if not return an error
files = [f for f in listdir(join(data_path, output_dir, 'data')) if
         isfile(join(data_path, output_dir, 'data', f))]
logger.info('Files in output dir: %s' % files)

print('Completed running clip')
logger.info('Completed running clip. Stopping tool.')


