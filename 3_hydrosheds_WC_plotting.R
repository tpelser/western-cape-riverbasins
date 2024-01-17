##################################################

libs <- c(
  "tidyverse", "sf", "giscoR",
  "elevatr", "terra", "rayshader"
)

installed_libs <- libs %in% rownames(
  installed.packages()
)

if (any(installed_libs == F)) {
  install.packages(
    libs[!installed_libs]
)
}

invisible(lapply(
  libs, library,
  character.only = TRUE
))

sf::sf_use_s2(FALSE)

#############################################

# Set the path to your DEM file
dem_file_path <- "data/DEM/western_cape_DEM.tif"

# Read the DEM raster file
elevation_raster <- rast(dem_file_path)

# Optional: Transform CRS if needed
# crs_lambert <- "+proj=laea +lat_0=52 +lon_0=10 +x_0=4321000 +y_0=3210000 +datum=WGS84 +units=m +no_defs" # nolint
# elevation_raster <- project(elevation_raster, crs_lambert)

# Convert the raster to a matrix
elevation_matrix <- rayshader::raster_to_matrix(elevation_raster)

# Define the rayshade function
rayshade <- function(elmat, img_path=NULL, zscale=10, fov=0, theta=135, zoom=0.75, phi=45, windowsize=c(1000, 1000)) {
  # Output path
  if (is.null(img_path)) {
    img_path <- tempfile(fileext='.png')
  }

  # Load required package
  library(rayshader)

  # Convert array to matrix
  elmat <- as.matrix(elmat)

  # Rayshader rendering
  elmat %>%
    sphere_shade(texture = "desert") %>%
    add_water(detect_water(elmat), color = "desert") %>%
    add_shadow(ray_shade(elmat, zscale = zscale), 0.5) %>%
    add_shadow(ambient_shade(elmat), 0) %>%
    plot_3d(elmat, zscale = zscale, fov = fov, theta = theta, zoom = zoom, phi = phi, windowsize = windowsize)
  Sys.sleep(0.2)
  render_snapshot(img_path)

  return(img_path)
}

# Define the output directory and file path
output_dir <- "output"
output_file <- "test_1.png"
output_path <- file.path(output_dir, output_file)

# Create the output directory if it does not exist
if (!dir.exists(output_dir)) {
  dir.create(output_dir, recursive = TRUE)
}

# Call the rayshade function with the specified output path
output_image_path <- rayshade(elevation_matrix, img_path=output_path, zscale=3) # Adjust other parameters as needed

# Optionally, print the path to the output image
print(output_image_path)
