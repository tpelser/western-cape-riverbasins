import geopandas as gpd
import os
import matplotlib.pyplot as plt
import rasterio
import numpy as np
from rasterio.plot import show
import rpy2.robjects as ro
from rpy2.robjects.packages import importr
import rpy2.robjects.numpy2ri as numpy2ri

def file_exists(file_path):
    return os.path.exists(file_path)

def load_or_process_rivers(western_cape, river_path, clipped_rivers_path):
    if file_exists(clipped_rivers_path):
        print("Loading existing clipped river data...")
        return gpd.read_file(clipped_rivers_path)
    
    print("No clipped data found. Loading original data and clipping...")
    rivers_gdf = gpd.read_file(river_path).to_crs(western_cape.crs)
    clipped_rivers = gpd.overlay(rivers_gdf, western_cape, how='intersection')
    clipped_rivers.to_file(clipped_rivers_path)
    print("Clipped river data saved.")
    return clipped_rivers

def load_or_process_basins(western_cape, basin_path, clipped_basins_path):
    if file_exists(clipped_basins_path):
        print("Loading existing clipped basin data...")
        return gpd.read_file(clipped_basins_path)
    
    print("No clipped data found. Loading original data and clipping...")
    basin_gdf = gpd.read_file(basin_path).to_crs(western_cape.crs)
    clipped_basins = gpd.overlay(basin_gdf, western_cape, how='intersection')
    clipped_basins.to_file(clipped_basins_path)
    print("Clipped basin data saved.")
    return clipped_basins

def adjust_river_widths(rivers_clipped_to_basins, width_mapping, default_width):
    rivers_clipped_to_basins['width'] = rivers_clipped_to_basins['ORD_FLOW'].map(width_mapping).fillna(default_width)
    return rivers_clipped_to_basins

def generate_color_palette(n_colors, data, column_name):
    # Access the colormap
    palette = plt.colormaps['Dark2']  
    unique_ids = data[column_name].unique()

    # Use indexing to get the color, and normalize the index within the range of the colormap
    return {id: palette(i / n_colors) for i, id in enumerate(unique_ids)}


# Function to clip rivers to basins and save
def clip_rivers_to_basins_and_save(rivers, basins, output_path):
    if file_exists(output_path):
        print("Loading existing rivers clipped to basins data...")
        return gpd.read_file(output_path)

    print("Clipping rivers to basins and saving...")
    rivers_clipped_to_basins = gpd.overlay(rivers, basins, how='intersection')
    rivers_clipped_to_basins.to_file(output_path)
    print("Rivers clipped to basins data saved.")
    return rivers_clipped_to_basins


def dem_to_matrix(dem_path):
    """
    Reads a DEM file and converts it into a matrix.

    Parameters:
    dem_path (str): Path to the DEM file.

    Returns:
    numpy.ndarray: Matrix representation of the DEM.
    """
    with rasterio.open(dem_path) as src:
        dem_matrix = src.read(1)  # Read the first (and usually only) band
    return dem_matrix

def process_and_save_rivers(rivers_clipped_to_basins, final_shapefile_path, width_mapping, default_width=0):
    """
    Process and save the rivers shapefile, or load it if it already exists.

    Parameters:
    rivers_clipped_to_basins (GeoDataFrame): The GeoDataFrame to process.
    final_shapefile_path (str): Path to the final shapefile.
    width_mapping (dict): Mapping from ORD_FLOW values to width.
    default_width (int): Default width to use if no mapping is found.

    Returns:
    GeoDataFrame: The processed or loaded rivers shapefile.
    """
    if file_exists(final_shapefile_path):
        print("Loading existing final rivers shapefile...")
        return gpd.read_file(final_shapefile_path)
    
    print("Processing and saving final rivers shapefile...")

    # Adjust river widths
    rivers_clipped_to_basins = adjust_river_widths(rivers_clipped_to_basins, width_mapping, default_width)

    # Save the adjusted rivers as a shapefile
    rivers_clipped_to_basins.to_file(final_shapefile_path)
    print("Final rivers with adjusted widths saved as shapefile.")

    return rivers_clipped_to_basins

cwd = os.getcwd()
western_cape_path = os.path.join(cwd, "data", "Western_Cape", "shp_Western_Cape_GID_1.shp")
dem_path = os.path.join(cwd, "data", "DEM", "western_cape_DEM.tif")
river_path = os.path.join(cwd, "data", "HydroRIVERS_v10_af_shp", "HydroRIVERS_v10_af.shp")
basin_path = os.path.join(cwd, "data", "hybas_af_lev05_v1c", "hybas_af_lev05_v1c.shp")
clipped_rivers_path = os.path.join(cwd, "data", "clipped", "Western_Cape_rivers.shp")
clipped_basins_path = os.path.join(cwd, "data", "clipped", "Western_Cape_basins.shp")
rivers_to_basins_path = os.path.join(cwd, "data", "clipped", "Western_Cape_rivers_to_basins.shp")
final_shapefile_path = os.path.join(cwd, "data", "clipped", "Final_Rivers_with_Widths.shp")

##############################
####### MAIN WORKFLOW ########

# load western cape shapefile
western_cape = gpd.read_file(western_cape_path)

# Load or process river and basin data
clipped_rivers = load_or_process_rivers(western_cape, river_path, clipped_rivers_path)
clipped_basins = load_or_process_basins(western_cape, basin_path, clipped_basins_path)

# Clip rivers to basins and save
rivers_clipped_to_basins = clip_rivers_to_basins_and_save(clipped_rivers, clipped_basins, rivers_to_basins_path)
    
# Adjust river widths and save, if necessary
width_mapping = {3: 14, 4: 12, 5: 10, 6: 8, 7: 7, 8: 6}
rivers_clipped_to_basins = process_and_save_rivers(rivers_clipped_to_basins, final_shapefile_path, width_mapping)


# # Generate color palette and join to basin data
# color_map = generate_color_palette(10, rivers_clipped_to_basins, 'HYBAS_ID')
# rivers_clipped_to_basins['color'] = rivers_clipped_to_basins['HYBAS_ID'].map(color_map)

# print("Final rivers to basins processing completed.")

# # Process the DEM file and convert it to a matrix
# elevation_matrix = dem_to_matrix(dem_path)

##############################
#### START TRYING TO PLOT ####

def rayshade_scene(elevation_matrix, basin_shapefile, river_shapefile, output_img_path):
    # Activate automatic conversion between NumPy arrays and R matrices
    numpy2ri.activate()
    
    # Import R packages
    rayshader = importr('rayshader')
    rgdal = importr('rgdal')

    # Transfer data to R
    ro.globalenv['elevation_matrix'] = elevation_matrix
    ro.globalenv['basin_shapefile'] = basin_shapefile
    ro.globalenv['river_shapefile'] = river_shapefile
    ro.globalenv['output_img'] = output_img_path

    # R code
    r_code = """
    # Load shapefiles
    basins <- rgdal::readOGR(basin_shapefile)
    rivers <- rgdal::readOGR(river_shapefile)

    # Elevation matrix to raster
    elev_raster <- matrix_to_raster(elevation_matrix)

    # Height shade
    height_shade <- rayshader::height_shade(elev_raster, texture = colorRampPalette(c("grey90", "grey60"))(256))

    # Add overlays
    height_shade %>%
      rayshader::add_overlay(rayshader::generate_polygon_overlay(geometry = basins, extent = elev_raster, heightmap = elevation_matrix, data_column_fill = "HYBAS_ID"), alphalayer = 0.6) %>%
      rayshader::add_overlay(rayshader::generate_line_overlay(geometry = rivers, extent = elev_raster, heightmap = elevation_matrix, data_column_width = "width"), alphalayer = 1) %>%
      rayshader::plot_3d(elev_raster, zscale = 10, windowsize = c(ncol(elev_raster) / 5, nrow(elev_raster) / 5), zoom = 0.515, phi = 85, theta = 0)

    # Save rendered scene
    rayshader::save_3dprint(output_img)
    """
    
    # Execute the R code
    ro.r(r_code)

    # Deactivate the numpy to R conversion
    numpy2ri.deactivate()

    return output_img_path
0
output_image = rayshade_scene(elevation_matrix, basin_path, final_shapefile_path, output_img_path)
print(f"Rendered image saved at {output_image}")
