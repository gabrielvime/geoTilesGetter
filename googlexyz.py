import os
import pyproj
from pathlib import Path

# Redireciona o PROJ para usar os arquivos do ambiente virtual (venv)
# e ignora a instalação global do PostgreSQL/PostGIS
proj_data_path = pyproj.datadir.get_data_dir()
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

def getData(geometryData, z, shapefile_name):
    output_dir = Path("Google_Imagery")
    output_dir.mkdir(parents=True, exist_ok=True)
    # Usa diretamente o GeoDataFrame que veio do main.py
    gdf = geometryData.copy()

    # Conversão de CRS para EPSG:4326
    if gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")

    minx, miny, maxx, maxy = gdf.total_bounds
    zoom = z

    print('fetching XYZ tiles to polygons...')
    tiles = list(mercantile.tiles(minx, miny, maxx, maxy, zoom))

    min_x = min(t.x for t in tiles)
    max_x = max(t.x for t in tiles)
    min_y = min(t.y for t in tiles)
    max_y = max(t.y for t in tiles)

    print('creating mosaic...')
    img_w = (max_x - min_x + 1) * 256
    img_h = (max_y - min_y + 1) * 256
    mosaic = Image.new("RGB", (img_w, img_h))

    i = 1
    ntiles = len(tiles)
    print('downloading Google Satellite XYZ Tiles...')
    for t in tiles:
        print(f'tile {i} of {ntiles}')
        url = f"https://mt0.google.com/vt/lyrs=s&x={t.x}&y={t.y}&z={t.z}"
        response = requests.get(url)
        
        if response.status_code == 200:
            print('STATUS: 200 OK')
            tile_img = Image.open(BytesIO(response.content))
            px = (t.x - min_x) * 256
            py = (t.y - min_y) * 256
            mosaic.paste(tile_img, (px, py))
        else:
            print(f'STATUS: {response.status_code}')
            return  # Retorna em vez de matar o script inteiro com exit()

        i += 1

    print('calculating spatial bounds...')
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
        "crs": "EPSG:3857",
        "transform": transform,
    }

    # Define o caminho completo de saída dentro da pasta 'resultados'
    output_filepath = output_dir / f"{shapefile_name}_{z}.tif"

    print(f'exporting to {output_filepath}...')
    with rasterio.open(output_filepath, "w", **tif_meta) as dst:
        arr = np.array(mosaic)
        dst.write(arr[:, :, 0], 1)
        dst.write(arr[:, :, 1], 2)
        dst.write(arr[:, :, 2], 3)

    print('done')