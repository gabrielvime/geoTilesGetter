import googlexyz, cbers, loadPolygon
import geopandas as gpd
import os
import googlexyz, cbers, loadPolygon
from pathlib import Path


if __name__ == "__main__":

    '''
    SOURCES:
    0 - CBERS-4A
    1 - Google XYZ Tiles
    '''

    #### SETUP ####
    
    # shapes location
    shapefile_path = 'shapes'

    # CBERS CONFIGURATION

    
    
    # SOURCES
    source = 0
    zoom = 16 #for google xyz tiles

    shapes_list = os.listdir(shapefile_path)
    for shape in shapes_list:

        shapefile_name = Path(shape).stem
        gdf = loadPolygon.getGDF('shapes/' + shape)        

        if source == 0: 
            print(f'getting CBERS Imagery...')
            # messing with EXPAND FACTOR not recommended
            cbers.getData(gdf, shapefile_name, getAll=True, TARGET_SIZE=1080)

        elif source == 1:
            print(f'getting Google XYZ Tiles...')
            googlexyz.getData(gdf, zoom, shapefile_name, True, "red", 2, 1.10)

        #getGeoTiles.getData(shapefile_path + "/" + shape, zoom)
    