import geopandas as gpd
import os
import matplotlib.pyplot as plt
import numpy as np

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

cwd = os.getcwd()
western_cape_path = os.path.join(cwd, "data", "Western_Cape", "shp_Western_Cape_GID_1.shp")
dem_path = os.path.join(cwd, "data", "DEM", "western_cape_DEM.tif")
river_path = os.path.join(cwd, "data", "HydroRIVERS_v10_af_shp", "HydroRIVERS_v10_af.shp")
basin_path = os.path.join(cwd, "data", "hybas_af_lev04_v1c", "hybas_af_lev04_v1c.shp")
clipped_rivers_path = os.path.join(cwd, "data", "clipped_new", "Western_Cape_rivers.shp")
clipped_basins_path = os.path.join(cwd, "data", "clipped_new", "Western_Cape_basins.shp")

##############################
####### MAIN WORKFLOW ########

# load western cape shapefile
western_cape = gpd.read_file(western_cape_path)

# Load or process river and basin data
clipped_rivers = load_or_process_rivers(western_cape, river_path, clipped_rivers_path)
clipped_basins = load_or_process_basins(western_cape, basin_path, clipped_basins_path)