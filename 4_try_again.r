##################################################

libs <- c(
  "tidyverse", "sf", "giscoR",
  "elevatr", "terra", "rayshader",
  "magick"
)

installed_libs <- libs %in% rownames(
  installed.packages()
)

if (any(installed_libs == FALSE)) {
  install.packages(
    libs[!installed_libs]
  )
}

invisible(lapply(
  libs, library,
  character.only = TRUE
))

sf::sf_use_s2(FALSE)

print("Libraries loaded successfully")

#############################################
########### GLOBAL SETTNGS ##################
crs_lambert <- "+proj=laea +lat_0=52 +lon_0=10 +x_0=4321000 +y_0=3210000 +datum=WGS84 +units=m +no_frfs"
crs_utm34s <- "+proj=utm +zone=34 +south +datum=WGS84 +units=m +no_defs"
crs_epsg2053 <- "+proj=lcc +lat_1=-28 +lat_2=-32 +lat_0=-30 +lon_0=29 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
crs_epsg22234 <- "+proj=utm +zone=34 +south +ellps=WGS72 +units=m +no_defs"


###########################################
##### SHP FILE STUFF ######################

### Western Cape shapefile ##
# Set the path to your Western Cape shapefile
wc_shapefile_path <- "data/Western_Cape/shp_Western_Cape_GID_1.shp"
state_sf <- sf::st_read(wc_shapefile_path)

#### RIVERS ####
# Set the path to your rivers file
rivers_file_path <- "data/clipped/Western_Cape_rivers.shp"
state_rivers <- sf::st_read(rivers_file_path)

#### BASINS ####
# Set the path to your basins file
basins_file_path <- "data/clipped/Western_Cape_basins.shp"
state_basin <- sf::st_read(basins_file_path) |>
  sf::st_intersection(state_sf) |>
  dplyr::select(HYBAS_ID)

##### TRANSFORM CRS #####

# TRANSFORM SHAPEFILE CRS
state_rivers_transformed <- sf::st_transform(state_rivers, crs_epsg22234)
state_basin_transformed <- sf::st_transform(state_basin, crs_epsg22234)

print(str(state_rivers_transformed))
print(str(state_basin_transformed))

#### CLIP RIVERS TO BASINS ####
state_river_basin <- sf::st_intersection(
  state_rivers_transformed,
  state_basin_transformed
)

unique(state_river_basin$HYBAS_ID)

print(str(state_river_basin))

################################################
####### PALETTE STUFF ##########################
num_unique_ids <- length(unique(state_river_basin$HYBAS_ID))

palette <- hcl.colors(
  n = num_unique_ids,
  palette = "Earth"
) |>
  sample()

names(palette) <- unique(
  state_river_basin$HYBAS_ID
)

pal <- as.data.frame(
  palette
) |>
  tibble::rownames_to_column(
    "HYBAS_ID"
  ) |>
  dplyr::mutate(
    HYBAS_ID = as.numeric(HYBAS_ID)
  )

state_river_basin_pal <- state_river_basin |>
  dplyr::left_join(
    pal,
    by = "HYBAS_ID"
  )

state_basin_pal <- sf::st_transform(
  state_basin,
  crs = crs_epsg22234
) |>
  dplyr::inner_join(
    pal,
    by = "HYBAS_ID"
  ) |>
  dplyr::mutate(
    HYBAS_ID = as.factor(HYBAS_ID)
  )

print(unique(state_river_basin$HYBAS_ID))
print(palette)

################################################
########## WIDTH STUFF #########################

unique(state_river_basin_pal$ORD_FLOW)

state_river_width <- state_river_basin_pal |>
  dplyr::mutate(
    width = as.numeric(
      ORD_FLOW
    ),
    width = dplyr::case_when(
      width == 3 ~ 14 * 2,
      width == 4 ~ 12 * 2,
      width == 5 ~ 10 * 2,
      width == 6 ~ 8 * 2,
      width == 7 ~ 7 * 2,
      width == 8 ~ 6 * 2,
      TRUE ~ 0
    )
  ) |>
  sf::st_as_sf() |>
  sf::st_transform(crs = crs_epsg22234)


print(unique(state_river_width$width))

##############################################
############## DEM STUFF #####################

# Set the path to your DEM file
dem_file_path <- "data/DEM/western_cape_DEM.tif"

# Read the DEM raster file
elevation_raster <- rast(dem_file_path)

# Optionally reproject if needed (replace 'crs_lambert' with your desired CRS)
elevation_raster <- terra::project(elevation_raster, crs_epsg22234)

# Convert the raster to a matrix for further processing or visualization
elevation_matrix <- rayshader::raster_to_matrix(elevation_raster)

print(summary(elevation_raster))
print(dim(elevation_matrix))

##############################################
############## PLOT STUFF ####################

########### RENDER SCENE #####################
h <- nrow(elevation_raster)
w <- ncol(elevation_raster)

print("rendering scene")

elevation_matrix |>
  rayshader::height_shade(
    texture = colorRampPalette(
      c(
        "grey90", "grey60"
      )
    )(256),
  ) |>
  rayshader::add_overlay(
    rayshader::generate_polygon_overlay(
      geometry = state_basin_pal,
      extent = elevation_raster,
      heightmap = elevation_matrix,
      linecolor = palette,
      palette = palette,
      data_column_fill = "HYBAS_ID"
    ), alphalayer = .6
  ) |>
  rayshader::add_overlay(
    rayshader::generate_line_overlay(
      geometry = state_river_width,
      extent = elevation_raster,
      heightmap = elevation_matrix,
      color = "darkblue", #color = state_river_width$palette,
      linewidth = state_river_width$width,
      data_column_width = "width"
    ), alphalayer = 1
  ) |>
  rayshader::plot_3d(
    elevation_matrix,
    zscale = 10,
    solid = FALSE,
    shadow = FALSE,
    windowsize = c(w / 5, h / 5),
    zoom = .515,
    phi = 45,
    theta = 135
  )

rayshader::render_camera(
  phi = 89,
  zoom = .675,
  theta = 0
)
print("Starting high-quality rendering")

##### RENDER OBJECT ######
rayshader::render_highquality(
  filename = "output/western_cape_riverbasins.png",
  preview = TRUE,
  light = FALSE,
  environment_light = "data/limpopo_golf_course_4k.hdr",
  rotate_env = 0,
  intensity_env = .85,
  ground_material = rayrender::diffuse(
    color = "grey10",
  ),
  interactive = FALSE,
  parallel = TRUE,
  width = w / 2,
  height = h / 2
)
print("Rendering completed")