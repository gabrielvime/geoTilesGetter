import satellite, polygon, config, xyzTiles
import geopandas as gpd
import os
from pathlib import Path
import argparse

def main(source):

    shapes_list = os.listdir(config.SHAPE_PATH)
    for shape in shapes_list:

        shapefile_name = Path(shape).stem
        gdf = polygon.gdf4326(config.SHAPE_PATH + '/' + shape)        

        if source == 'cbers': 
            satellite.getData(gdf, shapefile_name, source, getAll=False)

        elif source == 'google':                                                
            print(f'getting Google XYZ Tiles...')
            xyzTiles.getData(geometryData=gdf, source=source, shapefile_name=shapefile_name, draw_polygon=False)
            
        elif source == 'sentinel2':
            satellite.getData(gdf, shapefile_name=shapefile_name, source=source, getAll=False, draw_polygon=False)
        
        elif source=='bing':
            xyzTiles.getData(geometryData=gdf, shapefile_name=shapefile_name, source=source)
        
        elif source=='arcgis':
            xyzTiles.getData(geometryData=gdf, shapefile_name=shapefile_name, source=source, draw_polygon=True)


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='get sattellite imagery from desired source')

    parser.add_argument('--source', type=str, required=True, help='cbers, google, ...')

    args = parser.parse_args()

    main(source=args.source)

    