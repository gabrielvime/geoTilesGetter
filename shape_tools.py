import geopandas as gpd
import os
import rasterio
from rasterio.features import rasterize
import numpy as np
from rasterio.warp import transform_bounds

import config

'''
ShapeFile functions
'''


def gdf(shape_file):
    '''
    Get GeoPandas GeoDataFrame in WGS84
    '''

    shapefile_path = shape_file
    gdf = gpd.read_file(shapefile_path)

    if gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")
    
    return gdf


def draw(image, shape, transform, xyz=False, crs="EPSG:4326"):
    """
    Draw polygon shape
    """
    # Cria linhas/bordas a partir dos polígonos

    shape = shape.to_crs(crs)
    boundaries = shape.geometry.boundary
    
    # Se a linha for mais larga que 1px, aplica buffer
    if config.POLYGON_WIDTH > 1:
        pixel_size = abs(transform.a)
        boundaries = boundaries.buffer(config.POLYGON_WIDTH * pixel_size)

    # Define a cor RGB (valores de 0 a 255)
    colors = {
        'red': (255, 0, 0),
        'yellow': (255, 255, 0),
        'blue': (255, 255, 255)
    }
    rgb_color = colors.get(config.POLYGON_COLOR.lower(), (255, 0, 0))
    
    # Cria máscara booleana rasterizando as geometrias
    if xyz:
        mask_shape = (image.shape[0], image.shape[1])
    else:    
        mask_shape = (image.shape[1], image.shape[2])

    polygon_mask = rasterize(
        shapes=boundaries,
        out_shape=mask_shape,
        transform=transform,
        fill=0,
        default_value=1,
        dtype=np.uint8
    ) > 0

    # Aplica a cor em cada banda do array RGB recortado
    for band_idx in range(3):
        if xyz:
            image[:, :, band_idx][polygon_mask] = rgb_color[band_idx]
        else:
            image[band_idx][polygon_mask] = rgb_color[band_idx]
        
    return image

def window(shape, src, max_size=True, min_max=False, crs="EPSG:4326"):
    '''
    Return bounding window fo given gdf shape
    if min_max, return minX, maX, minY, maxY
    '''
    
    if crs=='EPSG:3857':
        shape = shape.to_crs(crs)

    # calculates width and height
    minx, miny, maxx, maxy = shape.total_bounds
    width = maxx - minx
    height = maxy - miny

    # centers
    cx = (minx + maxx) / 2
    cy = (miny + maxy) / 2

    pixel_size = 1 if not hasattr(src, 'res') else src.res[0]

    if config.SQUARE:

        square = max(width, height) * config.EXPAND_FACTOR if config.MAX_SIZE else config.RESOLUTION * pixel_size * config.EXPAND_FACTOR

        exp_minx = cx - (square / 2)
        exp_maxx = cx + (square / 2)
        exp_miny = cy - (square / 2)
        exp_maxy = cy + (square / 2)

    else:

        expand = max(width, height) - min(height, width) if config.MAX_SIZE else 0 #(config.RESOLUTION - min(width, height)) * pixel_size
        exp_minx = cx - (((width + expand) * config.EXPAND_FACTOR) / 2) 
        exp_maxx = cx + (((width + expand) * config.EXPAND_FACTOR) / 2) 
        exp_miny = cy - (((height + expand) * config.EXPAND_FACTOR) / 2)
        exp_maxy = cy + (((height + expand) * config.EXPAND_FACTOR) / 2)
   
    if shape.crs == 'EPSG:3857':
        bounds = transform_bounds(shape.crs, 'EPSG:4326', exp_minx, exp_miny, exp_maxx, exp_maxy)
        exp_minx, exp_miny, exp_maxx, exp_maxy = bounds
    
    
    if min_max:
        return exp_minx, exp_miny, exp_maxx, exp_maxy

    window = rasterio.windows.from_bounds(
        exp_minx, exp_miny, exp_maxx, exp_maxy, src.transform
    )

    return window
