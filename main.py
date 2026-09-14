import getGeoTiles
import geopandas as gpd
import os

if __name__ == "__main__":

    shapefile_path = "testShapes"
    zoom = 16

    if os.path.isdir(shapefile_path):
        shapes_list = os.listdir(shapefile_path)
        for shape in shapes_list:
            getGeoTiles.getData(shapefile_path + "/" + shape, zoom)
    else:
        getGeoTiles.getData(shapefile_path, zoom)