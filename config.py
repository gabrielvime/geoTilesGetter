from pystac_client import Client

RESOLUTION = 1080           # final square resolution
EXPAND_FACTOR = 1.3         # expansion factor (1.0 means original size), not recommended to mess with this
SOURCES = {'cbers': 'CBERS-4A FUSED', 'sentinel2': 'Sentinel-2 L2A (AWS)', 'google': 'Google XYZ Tiles', 'bing':'Bing'}
SHAPE_PATH = 'shapes'
ZOOM = 19            #XYZ Tiles Zoom
SOURCE_OUTPUT = {'cbers':'CBERS_Imagery', 'google':'Google_Imagery', 'sentinel2':'Sentinel2_Imagery', 'bing':'Bing_Imagery'}
### POLYGON DRAW SETTINGS ###
#settings ou configurations??? novamente, meu ingles é ruim
DRAW_POLYGON=False
POLYGON_COLOR = 'red'
POLYGON_WIDTH = 1
DATETIME='2022-08-01/2026-08-30'


##### CBERS CONFIGURATIONS #####
def cbers(bbox):

    catalog = Client.open("https://data.inpe.br/bdc/stac/v1")

    search = catalog.search(
        collections=["CB4A-WPM-PCA-FUSED-1"],   # collection
        bbox=bbox,                              # bounding box
        datetime=DATETIME)       #time frame

    return list(search.items())


##### SENTINEL-2 CONFIGURATIONS #####
def sentinel2(bbox):
    catalog = Client.open("https://earth-search.aws.element84.com/v1")  

    search = catalog.search(
    collections=["sentinel-2-l2a"],
    bbox=bbox,
    datetime=DATETIME,
    query={"eo:cloud_cover": {"lt": 10}}  # cloud filter
    )

    return list(search.items())


##### LANDSAT 8

def landsat8(bbox):
    catalog = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")  

    search = catalog.search(
    collections=["sentinel-2-l2a"],
    bbox=bbox,
    datetime=DATETIME,
    query={"eo:cloud_cover": {"lt": 10}}  # cloud filter
    )

    return list(search.items())


#### ARC-GIS
def arcgis(x, y, z):
    return f"[https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/](https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/){z}/{y}/{x}"

##### GOOGLE
def google(x, y, z):
    return f"https://mt0.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"

##### BING
def bing(x, y, z):

    quadkey = []
    
    for i in range(z, 0, -1):
        digit = 0
        mask = 1 << (i - 1)  
        
        if (x & mask) != 0:
            digit += 1
            
        if (y & mask) != 0:
            digit += 2
            
        quadkey.append(str(digit))
        
    q = ''.join(quadkey)

    #return f'[http://ecn.t3.tiles.virtualearth.net/tiles/a](http://ecn.t3.tiles.virtualearth.net/tiles/a){q}.jpeg?g=1'
    return f'[http://ecn.t3.tiles.virtualearth.net/tiles/a](http://ecn.t3.tiles.virtualearth.net/tiles/a){q}.jpeg?g=1'

