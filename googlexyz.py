import os
import pyproj

# Descobre automaticamente o caminho correto do PROJ no seu ambiente Python
proj_data_path = pyproj.datadir.get_data_dir()

# Define as variáveis de ambiente necessárias para sobrepor o caminho do PostgreSQL
os.environ["PROJ_LIB"] = proj_data_path
os.environ["PROJ_DATA"] = proj_data_path

from io import BytesIO
import geopandas as gpd
import mercantile
import numpy as np
import rasterio
from rasterio.transform import from_bounds
import requests
from PIL import Image
import os
from pathlib import Path

def getData(geometryData, z):
#POLYGONS
#shapefile_path = "processo_850092_2020.zip"
  shapefile_path = shape_file

  shapefile_name = Path(shape_file).stem
 
  gdf = gpd.read_file(shapefile_path)

  #CRS EPSG:4326
  if gdf.crs != "EPSG:4326":
    gdf = gdf.to_crs("EPSG:4326")


  minx, miny, maxx, maxy = gdf.total_bounds
  zoom = z  # Adjust zoom level for desired resolution

  print(f'fetching XYZ tiles to polygons...')

  tiles = list(mercantile.tiles(minx, miny, maxx, maxy, zoom))

  min_x = min(t.x for t in tiles)
  max_x = max(t.x for t in tiles)
  min_y = min(t.y for t in tiles)
  max_y = max(t.y for t in tiles)

  print(f'creating mosaic...')
  img_w = (max_x - min_x + 1) * 256
  img_h = (max_y - min_y + 1) * 256
  mosaic = Image.new("RGB", (img_w, img_h))

  i=1
  ntiles = len(tiles)
  print(f'downloading Google Sallite XYZ Tiles...')
  for t in tiles:
    print(f'tile {i} of {ntiles}')
    url = f"https://mt0.google.com/vt/lyrs=s&x={t.x}&y={t.y}&z={t.z}"
    response = requests.get(url)
    if response.status_code == 200:
      print (f'STATUS: 200 OK')
      tile_img = Image.open(BytesIO(response.content))
      px = (t.x - min_x) * 256
      py = (t.y - min_y) * 256
      mosaic.paste(tile_img, (px, py))
    else:
      print(f'STATUS: {response.status_code}')
      exit()

    i+=1

  # 5. Calculate precise spatial bounds using corner tile limits 
  print(f'calculating spacial bounds...')
  top_left_bounds = mercantile.xy_bounds(min_x, min_y, zoom)
  bottom_right_bounds = mercantile.xy_bounds(max_x, max_y, zoom)

  west = top_left_bounds.left
  north = top_left_bounds.top
  east = bottom_right_bounds.right
  south = bottom_right_bounds.bottom

  transform = from_bounds(west, south, east, north, img_w, img_h)

  tif_meta = {
      "driver": "GTiff",
      "height": img_h,
      "width": img_w,
      "count": 3,
      "dtype": "uint8",
      "crs": "EPSG:3857",  # Web Mercator aligns with Google tiles
      "transform": transform,
  }

  #georeferenced GeoTIFF
  print(f'exporting...')
  with rasterio.open(f"{shapefile_name}_{z}.tif", "w", **tif_meta) as dst:
    arr = np.array(mosaic)
    dst.write(arr[:, :, 0], 1)
    dst.write(arr[:, :, 1], 2)
    dst.write(arr[:, :, 2], 3)

  print(f'done')
