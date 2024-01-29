import geopandas as gpd
import os
import matplotlib.pyplot as plt
import numpy as np
import zipfile
import requests

def download_and_unzip(url, extract_to):
    # Create directory if it doesn't exist
    if not os.path.exists(extract_to):
        os.makedirs(extract_to)

    # Download the file
    local_filename = url.split('/')[-1]
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        path_to_zip_file = os.path.join(extract_to, local_filename)
        with open(path_to_zip_file, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                f.write(chunk)

    # Unzip the file
    with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

    # Remove the zip file after extraction
    os.remove(path_to_zip_file)

# define a function to download a file
def download_file(url, download_to):
    # Download the file
    local_filename = url.split('/')[-1]
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        path_to_file = os.path.join(download_to, local_filename)
        with open(path_to_file, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                f.write(chunk)

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
clipped_rivers_path = os.path.join(cwd, "data", "clipped", "Western_Cape_rivers.shp")
clipped_basins_path = os.path.join(cwd, "data", "clipped", "Western_Cape_basins.shp")

##############################
####### MAIN WORKFLOW ########

####### download and extract files ########
### 1 GADM shapefile
url = 'https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_ZAF_shp.zip'
extract_to = 'data/download'
download_and_unzip(url, extract_to)

### extract the Western Cape shapefile
# load South Africa shapefile gadm41_ZAF_1.shp (level 1 is provicial level)
south_africa = gpd.read_file(os.path.join(extract_to, 'gadm41_ZAF_1.shp'))

# extract the Western Cape shapefile
western_cape = south_africa[south_africa['NAME_1'] == 'Western Cape']

# save the Western Cape shapefile
western_cape_path = os.path.join(cwd, "data", "Western_Cape", "shp_Western_Cape_GID_1.shp")
western_cape.to_file(western_cape_path)

### 2 HydroBASINS shapefile
url = 'https://data.hydrosheds.org/file/HydroBASINS/standard/hybas_af_lev04_v1c.zip'
extract_to = 'data/hybas_af_lev04_v1c'
download_and_unzip(url, extract_to)

### 3 HydroRIVERS shapefile
url = 'https://data.hydrosheds.org/file/HydroRIVERS/HydroRIVERS_v10_af_shp.zip'
extract_to = 'data/HydroRIVERS_v10_af_shp'
download_and_unzip(url, extract_to)

## Limpopo golf course hdr file (for high-quality rendering)
url = "https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/4k/limpopo_golf_course_4k.hdr"
download_to = 'data'
download_file(url, download_to)

## 3 cleanup
# delete the download folder
os.rmdir('data/download')

####### perform processing and clipping ########
# load western cape shapefile
western_cape = gpd.read_file(western_cape_path)

# Load or process river and basin data
clipped_rivers = load_or_process_rivers(western_cape, river_path, clipped_rivers_path)
clipped_basins = load_or_process_basins(western_cape, basin_path, clipped_basins_path)



