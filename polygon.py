import geopandas as gpd
import os
import rasterio
from rasterio.features import rasterize
import numpy as np

import config

'''
Polygon functions
'''


def gdf4326(shape_file):
    '''
    Get GeoPandas GeoDataFrame in WGS84
    '''

    shapefile_path = shape_file
    gdf = gpd.read_file(shapefile_path)

    if gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")
    
    return gdf


def draw(image, shape, transform, xyz=False, crs="EPSG:4326"):
    '''
    Draw polygon shape
    '''
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
        'yellow': (255, 255, 0)
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
    #num_channels = image.shape[0]
    
    for band_idx in range(3):
        if xyz:
            image[:, :, band_idx][polygon_mask] = rgb_color[band_idx]
        else:
            image[band_idx][polygon_mask] = rgb_color[band_idx]
        

    return image

def window(shape, src, min_max=False, xyz=False):
    '''
    Return bounding window fo given gdf shape
    if min_max, return minX, maX, minY, maxY
    '''

    # calculates width and height
    minx, miny, maxx, maxy = shape.total_bounds
    width = maxx - minx
    height = maxy - miny

    # centers
    cx = (minx + maxx) / 2
    cy = (miny + maxy) / 2

    # calculates square size

    if xyz:
        exp_minx = cx - ((width * config.EXPAND_FACTOR) / 2)
        exp_maxx = cx + ((width * config.EXPAND_FACTOR) / 2)
        exp_miny = cy - ((height * config.EXPAND_FACTOR) / 2)
        exp_maxy = cy + ((height * config.EXPAND_FACTOR) / 2)
   
    else:
        pixel_size = src.res[0]
        square = config.RESOLUTION * pixel_size * config.EXPAND_FACTOR
        
        exp_minx = cx - (square / 2)
        exp_maxx = cx + (square / 2)
        exp_miny = cy - (square / 2)
        exp_maxy = cy + (square / 2)
        
    if min_max:
        return exp_minx, exp_maxx, exp_miny, exp_maxy

    window = rasterio.windows.from_bounds(
        exp_minx, exp_miny, exp_maxx, exp_maxy, src.transform
    )

    return window
