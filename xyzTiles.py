import os
from io import BytesIO
from pathlib import Path
#import geopandas as gpd
import mercantile
import numpy as np
#import pyproj
import rasterio
#from rasterio.features import rasterize
from rasterio.transform import from_bounds
import requests
from PIL import Image

import polygon, config

def getData(geometryData,shapefile_name, source, draw_polygon=True):
   
    gdf = geometryData

    minx, maxx, miny, maxy = polygon.window(gdf, None, min_max=True, xyz=True)

    print("fetching XYZ tiles for expanded bounds...")
    tiles = list(mercantile.tiles(minx, miny, maxx, maxy, config.ZOOM))

    min_x = min(t.x for t in tiles)
    max_x = max(t.x for t in tiles)
    min_y = min(t.y for t in tiles)
    max_y = max(t.y for t in tiles)

    print("creating mosaic...")
    img_w = (max_x - min_x + 1) * 256
    img_h = (max_y - min_y + 1) * 256
    mosaic = Image.new("RGB", (img_w, img_h))

    i = 1
    ntiles = len(tiles)
    print("downloading Google Satellite XYZ Tiles...")
    for t in tiles:
        print(f"tile {i} of {ntiles}")
        url = f"https://mt0.google.com/vt/lyrs=s&x={t.x}&y={t.y}&z={t.z}"
        response = requests.get(url)

        if response.status_code == 200:
            tile_img = Image.open(BytesIO(response.content))
            px = (t.x - min_x) * 256
            py = (t.y - min_y) * 256
            mosaic.paste(tile_img, (px, py))
        else:
            print(f"STATUS: {response.status_code}")
            return

        i += 1

    print("calculating spatial bounds...")
    top_left_bounds = mercantile.xy_bounds(min_x, min_y, config.ZOOM)
    bottom_right_bounds = mercantile.xy_bounds(max_x, max_y, config.ZOOM)

    west = top_left_bounds.left
    north = top_left_bounds.top
    east = bottom_right_bounds.right
    south = bottom_right_bounds.bottom

    transform = from_bounds(west, south, east, north, img_w, img_h)

    arr = np.array(mosaic)

    # polygon draw
    if draw_polygon:
        print(f'drawing polygon...')
        arr = polygon.draw(image=arr, shape=geometryData, transform=transform, xyz=True, crs="EPSG:3857")

    tif_meta = {
        "driver": "GTiff",
        "height": img_h,
        "width": img_w,
        "count": 3,
        "dtype": "uint8",
        "crs": "EPSG:3857",
        "transform": transform,
    }

    output_filepath = config.SOURCE_OUTPUT.get(source) + '/' f"{shapefile_name}_z{config.ZOOM}.tif"

    print(f"exporting to {output_filepath}...")
    with rasterio.open(output_filepath, "w", **tif_meta) as dst:
        dst.write(arr[:, :, 0], 1)
        dst.write(arr[:, :, 1], 2)
        dst.write(arr[:, :, 2], 3)

    print("done")