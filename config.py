from pystac_client import Client

RESOLUTION = 1080           # final square resolution
EXPAND_FACTOR = 1.0         # expansion factor (1.0 means original size), not recommended to mess with this
SOURCES = {'cbers': 'CBERS-4A FUSED', 'sentinel2': 'Sentinel-2 L2A (AWS)', 'google': 'Google XYZ Tiles'}
SHAPE_PATH = 'shapes'


##### CBERS CONFIGURATIONS #####
def cbers(bbox):

    catalog = Client.open("https://data.inpe.br/bdc/stac/v1")

    search = catalog.search(
        collections=["CB4A-WPM-PCA-FUSED-1"],   # collection
        bbox=bbox,                              # bounding box
        datetime="2022-08-01/2026-08-30")       #time frame

    return list(search.items())


##### SENTINEL-2 CONFIGURATIONS #####
def sentinel2(bbox):
    catalog = Client.open("https://earth-search.aws.element84.com/v1")  

    search = catalog.search(
    collections=["sentinel-2-l2a"],
    bbox=bbox,
    datetime="2024-01-01/2026-12-31",
    query={"eo:cloud_cover": {"lt": 10}}  # cloud filter
    )

    return list(search.items())


### POLYGON DRAW SETTINGS ###
#settings ou configurations??? novamente, meu ingles é ruim
POLYGON_COLOR = 'red'
POLYGON_WIDTH = 1
