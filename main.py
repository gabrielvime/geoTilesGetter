import stac, polygon, config, webTiles
import geopandas as gpd
import os
from pathlib import Path
import argparse

def main(source):

    if source!='all':
        output_dir = Path(config.SOURCES.get(source)[1])
        output_dir.mkdir(parents=True, exist_ok=True)

    shapes_list = os.listdir(config.SHAPE_PATH)

    for shape in shapes_list:

        shapefile_name = Path(shape).stem
        gdf = polygon.gdf4326(config.SHAPE_PATH + '/' + shape)        

        satellites = ['cbers', 'sentinel2']
        xyz = ['google', 'bing']

        if source in satellites:
            stac.getData(gdf=gdf, 
            shapefile_name=shapefile_name, source=source, 
            getAll=False)
       
        elif source in xyz:
            webTiles.getData(gdf=gdf, 
            source=source, 
            shapefile_name=shapefile_name)
       
        elif source=='all':
            for s in satellites:
                output_dir = Path(config.SOURCES.get(s)[1])
                output_dir.mkdir(parents=True, exist_ok=True)
                stac.getData(gdf, shapefile_name, source=s, getAll=False)
            for s in xyz:
                output_dir = Path(config.SOURCES.get(s)[1])
                output_dir.mkdir(parents=True, exist_ok=True)
                webTiles.getData(geometryData=gdf, source=s, shapefile_name=shapefile_name)
       
        else:
            print(f'invalide source')
        

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='get sattellite imagery from desired source')

    parser.add_argument('--source', type=str, required=True, help='cbers, google, sentinel2...')

    args = parser.parse_args()

    main(source=args.source)

    