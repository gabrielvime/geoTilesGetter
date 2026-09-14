import geopandas as gpd
import os


def getGDF(shape_file):
    '''
    Get GeoPandas GeoDataFrame in EPSG:4326
    '''

    shapefile_path = shape_file
    gdf = gpd.read_file(shapefile_path)

    if gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")
    
    return gdf


