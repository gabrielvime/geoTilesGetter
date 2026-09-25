import os
from io import BytesIO
from pathlib import Path
import mercantile
import numpy as np
import rasterio
from rasterio.transform import from_bounds
import requests
from PIL import Image
from shapely.geometry import box
import geopandas as gpd
from concurrent.futures import ThreadPoolExecutor, as_completed

import polygon, config

def fetch_single_tile(t, source):
    """Baixa um único tile individualmente."""
    if source == 'google':
        url = config.google(t.x, t.y, t.z)
    elif source == 'arcgis':
        url = config.arcgis(t.x, t.y, t.z)
    elif source == 'bing':
        url = config.bing(t.x, t.y, t.z)
    else:
        return t, None

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return t, Image.open(BytesIO(response.content))
    except Exception:
        pass
    return t, None


def getData(geometryData, shapefile_name, source, draw_polygon=True):
    gdf = geometryData

    # 1. Converter polígono para EPSG:3857 (metros)
    gdf_3857 = gdf.to_crs("EPSG:3857")
    minx, miny, maxx, maxy = gdf_3857.total_bounds

    cx = (minx + maxx) / 2
    cy = (miny + maxy) / 2

    # Ajuste o pixel_size para o sensor CBERS desejado:
    # 2.0 para CBERS-4A WPM (pancromática/fundida)
    # 8.0/16.0 para CBERS MUX
    pixel_size_meters = getattr(config, 'PIXEL_SIZE', 2.0)
    side_meters = config.RESOLUTION * pixel_size_meters * config.EXPAND_FACTOR

    target_minx = cx - (side_meters / 2)
    target_maxx = cx + (side_meters / 2)
    target_miny = cy - (side_meters / 2)
    target_maxy = cy + (side_meters / 2)

    # 2. Converter caixa para lat/lon (EPSG:4326)
    target_box_3857 = box(target_minx, target_miny, target_maxx, target_maxy)
    box_4326 = gpd.GeoSeries([target_box_3857], crs="EPSG:3857").to_crs("EPSG:4326").iloc[0]
    w_lon, s_lat, e_lon, n_lat = box_4326.bounds

    tiles = list(mercantile.tiles(w_lon, s_lat, e_lon, n_lat, config.ZOOM))

    min_x = min(t.x for t in tiles)
    max_x = max(t.x for t in tiles)
    min_y = min(t.y for t in tiles)
    max_y = max(t.y for t in tiles)

    img_w = (max_x - min_x + 1) * 256
    img_h = (max_y - min_y + 1) * 256
    mosaic = Image.new("RGB", (img_w, img_h))

    ntiles = len(tiles)
    print(f"getting {ntiles} scenes in parallel from {config.SOURCES.get(source)}...")

    # 3. Download paralelo utilizando 16 threads
    with ThreadPoolExecutor(max_workers=32) as executor:
        futures = [executor.submit(fetch_single_tile, t, source) for t in tiles]
        
        completed = 0
        for future in as_completed(futures):
            t, tile_img = future.result()
            if tile_img:
                px = (t.x - min_x) * 256
                py = (t.y - min_y) * 256
                mosaic.paste(tile_img, (px, py))
            completed += 1
            if completed % 20 == 0 or completed == ntiles:
                print(f"downloaded {completed}/{ntiles} tiles...")

    # 4. Ajuste dos limites e recorte exato
    top_left_bounds = mercantile.xy_bounds(min_x, min_y, config.ZOOM)
    bottom_right_bounds = mercantile.xy_bounds(max_x, max_y, config.ZOOM)

    tile_west = top_left_bounds.left
    tile_north = top_left_bounds.top
    tile_east = bottom_right_bounds.right
    tile_south = bottom_right_bounds.bottom

    res_x = (tile_east - tile_west) / img_w
    res_y = (tile_north - tile_south) / img_h

    crop_left = int(round((target_minx - tile_west) / res_x))
    crop_top = int(round((tile_north - target_maxy) / res_y))
    crop_right = int(round((target_maxx - tile_west) / res_x))
    crop_bottom = int(round((tile_north - target_miny) / res_y))

    cropped_mosaic = mosaic.crop((crop_left, crop_top, crop_right, crop_bottom))

    # 5. Redimensionamento final para 1024x1024
    target_size = (config.RESOLUTION, config.RESOLUTION)
    cropped_mosaic = cropped_mosaic.resize(target_size, Image.Resampling.LANCZOS)

    transform = from_bounds(target_minx, target_miny, target_maxx, target_maxy, config.RESOLUTION, config.RESOLUTION)
    arr = np.array(cropped_mosaic)

    if draw_polygon:
        print("drawing polygon...")
        arr = polygon.draw(image=arr, shape=geometryData, transform=transform, xyz=True, crs="EPSG:3857")

    tif_meta = {
        "driver": "GTiff",
        "height": config.RESOLUTION,
        "width": config.RESOLUTION,
        "count": 3,
        "dtype": "uint8",
        "crs": "EPSG:3857",
        "transform": transform,
    }

    output_filepath = f"{config.SOURCE_OUTPUT.get(source)}/{shapefile_name}_z{config.ZOOM}.tif"

    print(f"exporting to {output_filepath}...")
    with rasterio.open(output_filepath, "w", **tif_meta) as dst:
        dst.write(arr[:, :, 0], 1)
        dst.write(arr[:, :, 1], 2)
        dst.write(arr[:, :, 2], 3)

    print("done")