import os
from datetime import datetime
from io import BytesIO
from pathlib import Path
import geopandas as gpd
import mercantile
import numpy as np
import pyproj
import rasterio
from rasterio.features import rasterize
from rasterio.transform import from_bounds
import requests
from PIL import Image

proj_data_path = pyproj.datadir.get_data_dir()
os.environ["PROJ_LIB"] = proj_data_path
os.environ["PROJ_DATA"] = proj_data_path


def getData(
    geometryData,
    z,
    shapefile_name,
    draw_polygon=True,
    polygon_color="red",
    line_width=2,
    expand_factor=1.10,
    data_imagem=None,
):
    output_dir = Path("Google_Imagery")
    output_dir.mkdir(parents=True, exist_ok=True)

    if not data_imagem:
        data_imagem = datetime.now().strftime("%Y_%m")

    gdf = geometryData.copy()

    # 1. EXPANSÃO DO BOUNDING BOX
    if gdf.crs != "EPSG:4326":
        gdf_4326 = gdf.to_crs("EPSG:4326")
    else:
        gdf_4326 = gdf.copy()

    minx, miny, maxx, maxy = gdf_4326.total_bounds
    width = maxx - minx
    height = maxy - miny

    cx = (minx + maxx) / 2
    cy = (miny + maxy) / 2

    # Expande as dimensões a partir do centro pelo fator informado
    exp_minx = cx - ((width * expand_factor) / 2)
    exp_maxx = cx + ((width * expand_factor) / 2)
    exp_miny = cy - ((height * expand_factor) / 2)
    exp_maxy = cy + ((height * expand_factor) / 2)

    zoom = z

    print("fetching XYZ tiles for expanded bounds...")
    tiles = list(mercantile.tiles(exp_minx, exp_miny, exp_maxx, exp_maxy, zoom))

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
    top_left_bounds = mercantile.xy_bounds(min_x, min_y, zoom)
    bottom_right_bounds = mercantile.xy_bounds(max_x, max_y, zoom)

    west = top_left_bounds.left
    north = top_left_bounds.top
    east = bottom_right_bounds.right
    south = bottom_right_bounds.bottom

    transform = from_bounds(west, south, east, north, img_w, img_h)

    arr = np.array(mosaic)

    # 2. DESENHO OPCIONAL DO POLÍGONO
    if draw_polygon:
        gdf_3857 = gdf.to_crs("EPSG:3857")
        boundaries = gdf_3857.geometry.boundary

        if line_width > 1:
            pixel_size = abs(transform.a)
            boundaries = boundaries.buffer(line_width * pixel_size)

        colors = {"red": (255, 0, 0), "yellow": (255, 255, 0)}
        
        # Garante o tratamento do parâmetro de cor recebido como string
        color_key = str(polygon_color).lower()
        rgb_color = colors.get(color_key, (255, 0, 0))

        mask_shape = (img_h, img_w)
        polygon_mask = (
            rasterize(
                shapes=boundaries,
                out_shape=mask_shape,
                transform=transform,
                fill=0,
                default_value=1,
                dtype=np.uint8,
            )
            > 0
        )

        for band_idx in range(3):
            arr[:, :, band_idx][polygon_mask] = rgb_color[band_idx]

    tif_meta = {
        "driver": "GTiff",
        "height": img_h,
        "width": img_w,
        "count": 3,
        "dtype": "uint8",
        "crs": "EPSG:3857",
        "transform": transform,
    }

    output_filepath = output_dir / f"{shapefile_name}_z{z}_{data_imagem}.tif"

    print(f"exporting to {output_filepath}...")
    with rasterio.open(output_filepath, "w", **tif_meta) as dst:
        dst.write(arr[:, :, 0], 1)
        dst.write(arr[:, :, 1], 2)
        dst.write(arr[:, :, 2], 3)

    print("done")