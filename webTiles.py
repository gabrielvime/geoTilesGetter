import os
from io import BytesIO
from pathlib import Path
import mercantile
import numpy as np
import rasterio
from rasterio.transform import from_bounds
from rasterio.windows import from_bounds as window_from_bounds
from rasterio.warp import transform_bounds
from rasterio.enums import Resampling
from rasterio.io import MemoryFile
import requests
from PIL import Image

import polygon, config

def getData(gdf, shapefile_name, source):
   
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    minx, miny, maxx, maxy = polygon.window(gdf, None, min_max=True, crs='EPSG:3857')

    bounds_3857 = transform_bounds("EPSG:4326", "EPSG:3857", minx, miny, maxx, maxy)
    exp_minx, exp_miny, exp_maxx, exp_maxy = bounds_3857    

    print("fetching XYZ tiles for expanded bounds...")
    tiles = list(mercantile.tiles(minx, miny, maxx, maxy, config.ZOOM))

    min_x = min(t.x for t in tiles) - 1
    max_x = max(t.x for t in tiles) + 1
    min_y = min(t.y for t in tiles) - 1
    max_y = max(t.y for t in tiles) + 1

    print("creating mosaic...")
    img_w = (max_x - min_x + 1) * 256
    img_h = (max_y - min_y + 1) * 256
    
    mosaic = Image.new("RGB", (img_w, img_h))

    total_tiles = (max_x - min_x + 1) * (max_y - min_y + 1)
    i = 1
    for ty in range(min_y, max_y + 1):
        for tx in range(min_x, max_x + 1):
            print(f"Tile {i} of {total_tiles}")


            # ==============================================================================
            # LEGAL DISCLAIMER: COMMERCIAL TILE SERVERS (GOOGLE / BING)
            # ==============================================================================
            # This project does not provide or distribute URLs for proprietary map services. 
            # Automated access (scraping) and bulk downloading of commercial tiles may 
            # violate the providers' Terms of Service (ToS) and copyright laws. 
            # 
            # By manually configuring the URLs below, you (the end-user) assume FULL 
            # legal and technical responsibility for your actions, including IP bans or 
            # legal liabilities. The author of this script assumes zero responsibility.
            # ==============================================================================

            
            if source == 'google':
                url = f""
            elif source == 'bing':
                qk = mercantile.quadkey(tx, ty, config.ZOOM)
                url = f""
                
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                tile_img = Image.open(BytesIO(response.content))
                px = (tx - min_x) * 256
                py = (ty - min_y) * 256
                mosaic.paste(tile_img, (px, py))
            else:
                print(f"STATUS {response.status_code} in {tx},{ty}")
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

    print("Resampling to target resolution...")
    if config.SQUARE:
        out_w = config.RESOLUTION
        out_h = config.RESOLUTION
    else:
        geo_w = exp_maxx - exp_minx
        geo_h = exp_maxy - exp_miny
        scale = config.RESOLUTION / max(geo_w, geo_h)
        out_w = int(geo_w * scale)
        out_h = int(geo_h * scale)


    meta = {
        "driver": "GTiff",
        "height": img_h,
        "width": img_w,
        "count": 3,
        "dtype": "uint8",
        "crs": "EPSG:3857",
        "transform": transform,
    }

    with MemoryFile() as memfile:
        with memfile.open(**meta) as dataset:
            dataset.write(arr[:, :, 0], 1)
            dataset.write(arr[:, :, 1], 2)
            dataset.write(arr[:, :, 2], 3)
            
            window = window_from_bounds(exp_minx, exp_miny, exp_maxx, exp_maxy, dataset.transform)
            
            cropped_image = dataset.read(
                window=window, 
                out_shape=(3, out_h, out_w),
                resampling=Resampling.bilinear,
                boundless=True, fill_value=0
            )
            
            transform_final = rasterio.transform.from_bounds(
                exp_minx, exp_miny, exp_maxx, exp_maxy, 
                out_w, out_h
            )

    # polygon draw
    if config.DRAW_POLYGON:
        print(f'drawing polygon...')
        arr = polygon.draw(
            image=arr, 
            shape=gdf, 
            transform=transform, 
            xyz=True, 
            crs="EPSG:3857")

    output_filepath = config.SOURCES.get(source)[1] + '/' f"{shapefile_name}_z{config.ZOOM}.tif"

    print(f"exporting to {output_filepath}...")
    with rasterio.open(output_filepath, "w", **meta) as dst:
        dst.write(arr[:, :, 0], 1)
        dst.write(arr[:, :, 1], 2)
        dst.write(arr[:, :, 2], 3)

    print("done")