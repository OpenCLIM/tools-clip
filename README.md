# tools-clip
Provides a utility tool for clipping raster and vector spatial datasets on DAFNI. Outputs clipped files.

# Inputs
### Files
 * Input data files
   * description: Any data files which are to be clipped. Should match common data formats (rasters - .asc, .tiff, .geotiff; vector - .gpkg, .shp . geojson)
   * path: inputs/clip
   * required: true
 * Clip extent file
   * description: Either a spatial file to clip the input data with (GeoPackage or shapefile) or a text file defining the extent of the bounding box for the clip process.
   * path: inputs/clip_extent
   * required: false

### Parameters
 * output_file
   * description: The name to be given to the output file - only used if one input file passed, otherwise overridden and the default behaviour used. By default, and if multiple input files set, '_clip' will be appended to the name of the input dataset for the output file name.
   * type: string
   * required: false
 * extent
   * description: Should be formatted as `<xmin>,<ymin>,<xmax>,<ymax>` and in the same coordinate system as the data to clip.
   * type: string
   * required: false
 * round_extents
   * description: Round extents to clip a layer by to the nearst value (in meters), e.g. nearest 100, 1000
   * type: integer
   * required: false
 * clip_to_extent_bbox
   * type: string
   * description: If passing a vector file for the clip extent, clip to outline or clip to bounding box of vector data
   * default: clip-to-bounding-box
   * required: false
     * options:
       * clip-to-bounding-box
       * clip-to-vector-outline
 * save_logfile
   * type: string
   * description: Save logfile
   * default: 'False'
   * required: false

# Outputs
### Files
 * clipped datasets
 * logfile