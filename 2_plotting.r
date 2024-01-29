##################################################

libs <- c(
  "tidyverse", "sf", "giscoR",
  "elevatr", "terra", "rayshader",
  "magick", "ggplot2"
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

### GLOBAL SETTINGS ###
crs_epsg22234 <- "+proj=utm +zone=34 +south +ellps=WGS72 +units=m +no_defs"

###########################################
##### SHP FILE STUFF ######################

### Western Cape shapefile ##
# Set the path to your Western Cape shapefile
wc_shapefile_path <- "data/Western_Cape/shp_Western_Cape_GID_1.shp"
state_sf <- sf::st_read(wc_shapefile_path)

#### RIVERS ####
# Set the path to your rivers file
rivers_file_path <- "data/clipped_new/Western_Cape_rivers.shp"
state_rivers <- sf::st_read(rivers_file_path)

## Do transformations of CRS before clipping
state_sf_transformed <- sf::st_transform(state_sf, crs_epsg22234)

#### BASINS ####
# Set the path to your basins file
basins_file_path <- "data/clipped_new/Western_Cape_basins.shp"
state_basin <- sf::st_read(basins_file_path) 
state_basin_transformed <- sf::st_transform(state_basin, crs_epsg22234)

state_basin_transformed <- sf::st_intersection(
  state_sf_transformed,
  state_basin_transformed) |>
  dplyr::select(HYBAS_ID)

##### TRANSFORM CRS #####
# TRANSFORM SHAPEFILE CRS
state_rivers_transformed <- sf::st_transform(state_rivers, crs_epsg22234)

#### CLIP RIVERS TO BASINS ####
state_river_basin <- sf::st_intersection(
  state_rivers_transformed,
  state_basin_transformed
)

unique(state_river_basin$HYBAS_ID)
print(unique(state_river_basin$HYBAS_ID))

################################################
####### PALETTE STUFF ##########################

############## THIS IS NEW #####################
# Define custom river colors
custom_river_colors <- c("#4B7381", "#1d4567", "#317589", "#3c5c71", "#42362d", "#556B2F", "#436A72")
custom_hybas_ids <- c("1040012820", "1040014490", "1040014500", "1040014920", "1040014930", "1040015030", "1041626200")

# Create a named vector for custom river colors
named_custom_river_colors <- setNames(custom_river_colors, custom_hybas_ids)

############## END NEW #####################

num_unique_ids <- length(unique(state_river_basin$HYBAS_ID))

# create a palette
palette <- hcl.colors(
  n = num_unique_ids,
  palette = "Earth"
) |>
  sample()

print(palette)

names(palette) <- unique(
  state_river_basin$HYBAS_ID
)

# create a dataframe for the palette
pal <- as.data.frame(
  palette
) |>
  tibble::rownames_to_column(
    "HYBAS_ID"
  ) |>
  dplyr::mutate(
    HYBAS_ID = as.numeric(HYBAS_ID)
  )

# join the palette to the river basin shapefile
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

# ################################################
# ########## WIDTH STUFF #########################

unique(state_river_basin_pal$ORD_FLOW)

state_river_width <- state_river_basin_pal |>
  dplyr::mutate(
    width = as.numeric(
      ORD_FLOW
    ),
    width = dplyr::case_when(
      width == 3 ~ 9,
      width == 4 ~ 7,
      width == 5 ~ 6,
      width == 6 ~ 5,
      width == 7 ~ 4,
      width == 8 ~ 3,
      TRUE ~ 0
    )
  ) |>
  sf::st_as_sf() |>
  sf::st_transform(crs = crs_epsg22234)

# ##############################################
# ############## DEM STUFF #####################

# Set the path to your DEM file
dem_file_path <- "data/DEM/western_cape_DEM.tif"

# Read the DEM raster file
elevation_raster <- rast(dem_file_path)

# Optionally reproject if needed (replace 'crs_lambert' with your desired CRS)
elevation_raster <- terra::project(elevation_raster, crs_epsg22234)

# Downsample the raster to speed up rendering
downsample_factor <- 3
elevation_raster_downsampled <- aggregate(elevation_raster, fact = downsample_factor)

# Convert the raster to a matrix for further processing or visualization
elevation_matrix <- rayshader::raster_to_matrix(elevation_raster_downsampled <- aggregate(elevation_raster, fact = downsample_factor))
print(dim(elevation_matrix))

################ PLOTTING ######################
# ##### 2D PLOTTING SECTION FOR CHECK #####

# # Load ggplot2 from tidyverse
# library(ggplot2)

# # Base plot with state shapefile
# plot_2D <- ggplot() +
#   geom_sf(data = state_sf, fill = "white", color = "black") +
#   # Add basins with colors
#   geom_sf(data = state_basin_pal, aes(fill = HYBAS_ID), color = NA, alpha = 0.7) +
#   scale_fill_manual(values = palette) +
#   # add text for matching HYBAS_IDs 
#   geom_sf_text(data = state_basin_pal, aes(label = HYBAS_ID), color = "black", size = 2) +
#   geom_sf_text(data = state_basin_pal, aes(label = palette), color = "black", size = 3, nudge_y = -0.1) +
#   # Add rivers with varying widths
#   geom_sf(data = state_river_width, aes(color = HYBAS_ID, size = width), show.legend = 'line') +
#   scale_size_continuous(range = c(1, 14)) + # Adjust the range as per your data
  
#   # Theme and labels
#   theme_minimal() +
#   labs(title = "Rivers and Basins in Western Cape",
#        fill = "Basin ID",
#        color = "Basin ID",
#        size = "River Width")

# # Display the plot
# print(plot_2D)

# # Optionally save the plot
# ggsave("output/rivers_basins_2D_plot_lev04.png", plot_2D, width = 10, height = 8)


########## RENDER SCENE ########################
h <- nrow(elevation_raster_downsampled)
w <- ncol(elevation_raster_downsampled)

print("rendering scene...")

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
      color = ifelse(state_river_width$HYBAS_ID %in% names(named_custom_river_colors), 
                   named_custom_river_colors[as.character(state_river_width$HYBAS_ID)], 
                   "#44001B"), # Default color for other rivers
      linewidth = state_river_width$width,
      data_column_width = "width"
    ), alphalayer = 1
  ) |>
  rayshader::plot_3d(
    elevation_matrix,
    zscale = 25,
    solid = FALSE,
    shadow = FALSE,
    windowsize = c(w / 2, h / 2),
    zoom = .515,
    phi = 85,
    theta = 0,
    window = FALSE
  )

rayshader::render_camera(
  phi = 89,
  zoom = .675,
  theta = 0
)

print("Scene rendered")

##### RENDER OBJECT ######
print("Rendering...")
rayshader::render_highquality(
  filename = "output/western_cape_riverbasins_lev04.png",
  preview = FALSE,
  light = FALSE,
  environment_light = "data/limpopo_golf_course_4k.hdr",
  rotate_env = 30,
  intensity_env = .84,
  ground_material = rayrender::diffuse(
    color = "grey10",
  ),
  interactive = FALSE,
  parallel = TRUE,
  width = w,
  height = h
)
print("Rendering completed")