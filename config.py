from pystac_client import Client

RESOLUTION = 1080   # final square resolution
EXPAND_FACTOR = 1.0       # expansion factor (1.0 means original size)

def cbers(bbox):
    catalog = Client.open("https://data.inpe.br/bdc/stac/v1")

    search = catalog.search(
        collections=["CB4A-WPM-PCA-FUSED-1"],
        bbox=bbox,
        datetime="2022-08-01/2026-08-30",
        query={"eo:cloud_cover": {"lt": 5} })

    return list(search.items())
