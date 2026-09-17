import googlexyz, cbers, polygon, config
import geopandas as gpd
import os
from pathlib import Path


if __name__ == "__main__":

    

    #### SETUP ####
    
    # shapes location
    #shapefile_path = 'shapes'

    # CBERS CONFIGURATION

    
    
    # choice source here
    source = 'sentinel2' 
    zoom = 16 #for google xyz tiles

    shapes_list = os.listdir(config.SHAPE_PATH)
    for shape in shapes_list:

        shapefile_name = Path(shape).stem
        gdf = polygon.gdf(config.SHAPE_PATH + '/' + shape)        

        if source == 'cbers': 
            #print(f'getting CBERS Imagery...')
            
            cbers.getData(gdf, shapefile_name, source, getAll=False, draw_polygon=False)

        elif source == 'google':
            print(f'getting Google XYZ Tiles...')
            googlexyz.getData(gdf, zoom, shapefile_name, True, "red", 2, 1.10)

        elif source == 'sentinel2':

            cbers.getData(gdf, shapefile_name=shapefile_name, source=source, getAll=False, draw_polygon=False)
        #getGeoTiles.getData(shapefile_path + "/" + shape, zoom)
    