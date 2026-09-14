import googlexyz, cbers, loadPolygon
import geopandas as gpd
import os
import googlexyz, cbers, loadPolygon


if __name__ == "__main__":

    '''
    SOURCES:
    0 - CBERS-4A
    1 - Google XYZ Tiles
    '''

    #### SETUP ####
    
    # shapes location
    shapefile_path = 'shapes/'
    
    # SOURCES
    source = 0
    zoom = 16 #for google xyz tiles

    shapes_list = os.listdir(shapefile_path)
    for shape in shapes_list:

        gdf = loadPolygon.getGDF(shape)
        shapefile_name = Path(shape).stem

        if source == 0: 
            print(f'getting CBERS Imagery...')
            cbers.getData(shape, shapefile_name)

        elif source == 1:
            print(f'getting Google XYZ Tiles...')
            googlexyz.getData(shape, zoom, shapefile_name)

        #getGeoTiles.getData(shapefile_path + "/" + shape, zoom)
    