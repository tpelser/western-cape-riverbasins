# Western Cape river basins 3D plot

This repository contains scripts for downloading, processing, and visualizing geographical data related to rivers and basins in the Western Cape region. The main focus is on handling shapefiles and raster data for rivers and basins, transforming coordinate systems, clipping geographical features, and creating a high-quality 3D plot using Rayshader. We use data from HydroSHEDS for rivers and basins, GADM for the Western Cape boundaries, and OpenTopography for Digital Elevation Model (DEM) data. 

NOTE: This repo is based on the tutorial by Milos Agathon: https://github.com/milos-agathon/3d-river-basin-map 

## Getting Started

### Prerequisites

- Python (3.x)
- R

### Installation
- Ensure Python and R are installed on your system.
- Install the required Python environment using the requirements.yml file (mamba is recommended)

### Usage
- **1_hydrosheds_WC.py:**
    - Download and unzip necessary data files (GADM shapefiles, HydroBASINS, HydroRIVERS, Limpopo golf course HDR file).
    - Processes and clips river and basin data to the Western Cape region.
    - Outputs shapefiles for rivers and basins in the Western Cape.

- **2_plotting.r:**
    - Handles CRS transformations.
    - Intersects river and basin shapefiles.
    - Generates custom color palettes and assigns them to basins and rivers.
    - Renders 2D and 3D visualizations of the data.

PLEASE ENSURE THAT YOU FIRST RUN THE PYTHON SCRIPT AND THEN THE R SCRIPT.

### Main Workflow
- **Data Acquisition:** Automated downloading and extraction of shapefiles and raster data relevant to the Western Cape.
- **Data Processing:** Clipping of rivers and basins data to the Western Cape region using geospatial analysis techniques.
- **Visualization:** Generating 2D and 3D high-quality renderings of the data. The final result is: