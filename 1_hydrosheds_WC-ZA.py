import geopandas as gpd
import os
from shapely.wkt import loads
from shapely.geometry import Polygon
import requests
import zipfile
import pandas as pd
import rasterio
import elevation
from elevation import clip
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

cwd = os.getcwd()

# Load South Africa Western Cape shapefile
western_cape_path = os.path.join(cwd, "data", "Western_Cape", "shp_Western_Cape_GID_1.shp")
western_cape = gpd.read_file(western_cape_path)

# Load DEM file
dem_path = os.path.join(cwd, "data", "DEM", "western_cape_DEM.tif")
#dem_cape = rasterio.open(dem_path)

# load river data 
print("reading river data...")
river_path = os.path.join(cwd, "data", "HydroRIVERS_v10_af_shp", "HydroRIVERS_v10_af.shp")
clipped_rivers_WC = None

# if data/clipped/HydroRIVERS_v10_af_WC.shp exists, load it
if os.path.exists(os.path.join(cwd, "data", "clipped", "Western_Cape_rivers.shp")):
    clipped_rivers_WC = gpd.read_file(os.path.join(cwd, "data", "clipped", "Western_Cape_rivers.shp"))
    print("clipped data loaded.")
else:
    print("no clipped data found. loading original data...")
    gdf = gpd.read_file(river_path)
    print("original data loaded.")

# if clipped data doesnt exist, clip it
if clipped_rivers_WC is None:
    print("clipping data...")
    ### TRY THE INTERSECTION OVERLAY METHOD ###
    print("performing additional clipping...")
    # Ensure both GeoDataFrames use the same coordinate reference system (CRS)
    rivers_gdf = gdf.to_crs(western_cape.crs)

    # Perform the spatial intersection (clipping)
    clipped_rivers_WC = gpd.overlay(rivers_gdf, western_cape, how='intersection')

    # Save the clipped rivers
    clipped_rivers_WC.to_file(os.path.join(cwd, "data", "clipped", "Western_Cape_rivers.shp"))

    print("clipped data saved.")

#### QUICK PLOT TO CHECK THAT RIVERS LOADED PROPERLY ####
# # Clip the South Africa shapefile to the Western Cape bounding box
# print("plotting...")
# # Plotting
# fig, ax = plt.subplots(figsize=(10, 10))

# # Plot the clipped South Africa (Western Cape) shapefile
# western_cape.plot(ax=ax, color='red')

# # Replace with gdf_WC or gdf_filtered based on which one you prefer to use
# clipped_rivers_WC.plot(ax=ax, color='blue')

# plt.show()


## Load the basin data
    
print("reading basin data...")
basin_path = os.path.join(cwd, "data", "hybas_af_lev04_v1c", "hybas_af_lev04_v1c.shp")
clipped_basins_WC = None

# if data/clipped/HydroRIVERS_v10_af_WC.shp exists, load it
if os.path.exists(os.path.join(cwd, "data", "clipped", "Western_Cape_basins.shp")):
    clipped_basins_WC = gpd.read_file(os.path.join(cwd, "data", "clipped", "Western_Cape_basins.shp"))
    print("clipped data loaded.")
else:
    print("no clipped data found. loading original data...")
    gdf = gpd.read_file(basin_path)
    print("original data loaded.")

# if clipped data doesnt exist, clip it
if clipped_basins_WC is None:
    print("clipping data...")
    ### TRY THE INTERSECTION OVERLAY METHOD ###
    print("performing additional clipping...")
    # Ensure both GeoDataFrames use the same coordinate reference system (CRS)
    basin_gdf = gdf.to_crs(western_cape.crs)

    # Perform the spatial intersection (clipping)
    clipped_basins_WC = gpd.overlay(basin_gdf, western_cape, how='intersection')

    # Save the clipped rivers
    clipped_basins_WC.to_file(os.path.join(cwd, "data", "clipped", "Western_Cape_basins.shp"))

    print("clipped basin data saved.")


if not os.path.exists(os.path.join(cwd, "data", "clipped", "Western_Cape_rivers_to_basins.shp")):
    # Clip rivers to the clipped hydrobasins
    print("clipping rivers to basins...")
    rivers_clipped_to_basins = gpd.overlay(clipped_rivers_WC, clipped_basins_WC, how='intersection')

    ## save clipped rivers to basins
    rivers_clipped_to_basins.to_file(os.path.join(cwd, "data", "clipped", "Western_Cape_rivers_to_basins.shp"))
else:
    rivers_clipped_to_basins = gpd.read_file(os.path.join(cwd, "data", "clipped", "Western_Cape_rivers_to_basins.shp"))
    print("clipped rivers to basins loaded.")

print("generating palette...")
### CREATE A PALETTE ###
# Generate a color palette
n_colors = 10
palette = plt.cm.get_cmap('Dark2', n_colors)

# Create a dictionary mapping HYBAS_ID to colors
unique_hybas_ids = rivers_clipped_to_basins['HYBAS_ID'].unique()
color_map = {hybas_id: palette(i) for i, hybas_id in enumerate(unique_hybas_ids)}


### JOIN THE PALETTE TO THE BASIN DATA ###
# Add a 'color' column to the river basin data
rivers_clipped_to_basins['color'] = rivers_clipped_to_basins['HYBAS_ID'].map(color_map)


### TRANSFORM CRS (OPTIONAL) ###
# Transform CRS (example using Lambert CRS)
# lambert_crs = "+proj=laea +lat_0=52 +lon_0=10 +x_0=4321000 +y_0=3210000 +datum=WGS84 +units=m +no_defs"
# rivers_clipped_to_basins_gdf = rivers_clipped_to_basins.to_crs(lambert_crs)
# hydrobasin_clipped_gdf = hydrobasin_clipped_gdf.to_crs(lambert_crs)

print("adjusting river widths...")
### ADJUST RIVER WIDTHS ###
# Adjust river width based on an attribute (e.g., 'ORD_FLOW')
width_mapping = {
    3: 14,
    4: 12,
    5: 10,
    6: 8,
    7: 7,
    8: 6
}
default_width = 0

rivers_clipped_to_basins['width'] = rivers_clipped_to_basins['ORD_FLOW'].map(width_mapping).fillna(default_width)


# # Open the raster file
# with rasterio.open(dem_path) as src:
#     # Read the raster data as a matrix
#     elevation_matrix = src.read(1)  

