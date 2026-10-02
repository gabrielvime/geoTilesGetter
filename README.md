# geoTilesGetter

**An automated geospatial pipeline for retrieving, processing, and formatting high-resolution satellite imagery and web map tiles.**

`geoTilesGetter` is an educational Proof of Concept (PoC) designed to streamline the extraction of spatial data from raw geospatial APIs. Dealing with satellite and web map data often involves complex coordinate reference system (CRS) transformations, spatial distortions, and radiometric inconsistencies. This tool automates the heavy lifting - such as mathematical quality filtering, virtual cropping, and precise image resampling - allowing users to quickly obtain clean, analysis-ready image arrays from specific geographic coordinates.

### Key Features

* **Multi-Source Data Retrieval:** Seamlessly queries Open Data STAC catalogs (e.g., CBERS-4A WPM, Sentinel-2 L2A) and calculates precise bounding boxes for fetching XYZ Tile mapping services.
* **Algorithmic Quality Control:** Implements pure NumPy-based mathematical filters to automatically evaluate and reject scenes based on cloud cover thresholds, dense shadows, atmospheric haze, and image blur.
* **Precision Cropping & Resampling:** Outputs images in strict, configurable pixel dimensions. It utilizes memory-mapped virtual cropping and bilinear resampling to prevent pixel distortion, stretching, or empty borders.
* **Automated Geoprocessing:** Natively handles CRS conversions (e.g., EPSG:4326 to UTM or EPSG:3857) and burns vector geometries (polygons) directly onto the raster arrays for visual reference.
* **Containerized Environment:** Fully isolated architecture orchestrated via Docker Compose and `uv` for lightning-fast Python dependency management, avoiding host-level permission conflicts.

### Tech Stack

* **Geospatial & Vector:** `rasterio`, `geopandas`, `shapely`, `mercantile`
* **Data Retrieval:** `pystac-client`, `requests`
* **Array Processing:** `numpy`, `Pillow`
* **Infrastructure:** Docker, `uv`

### How It Works

Provide `geoTilesGetter` with a GeoJSON or Shapefile containing the target coordinates. The pipeline will:
1. Connect to the specified STAC catalog or Tile Server.
2. Expand the geographic boundaries to capture the surrounding context.
3. Filter out low-quality scenes (clouds, haze).
4. Download the raw arrays, reproject them, and resample the target area to the exact requested resolution.
5. Draw the target vector boundaries directly onto the image arrays.
6. Export the final, accurately georeferenced `.tif` files.

## Getting Started


Adjust `config.py` to your work

To start, run the following command adjusting 'DESIRED_SOURCE' to your desired source ('cbers', 'bing', 'google', 'sentinel2'):
```
docker compose run --rm geotilesgetter python main.py --source='DESIRED_SOURCE'
```

## Imagery
### Bing Maps Satellite Imagery

[Bing Maps](https://www.bing.com/maps/)

This data source provides global high-resolution satellite and aerial imagery served via the Virtual Earth QuadKey tiling system. The product consists of 8-bit RGB JPEG tiles projected in Web Mercator (EPSG:3857), continuously updated through Microsoft's commercial spatial data partnerships.

**Usage Restrictions:** Microsoft restricts the automated extraction of its map tiles outside of its official API channels. Mass downloading, storing tiles in proprietary databases, or utilizing the visual data to train algorithms without an enterprise agreement constitutes a direct violation of the Bing Maps Terms of Use.

**Provider:** Microsoft Corporation.

### CBERS-4A

[CBERS-4A/WPM - Multispectral and Panchromatic Bands Fusioned](https://data.inpe.br/stac/browser/collections/CB4A-WPM-PCA-FUSED-1)

"This collection contains 2 meter high-resolution, RGB products, generated using the Principal Components Fusion (PCA) method, with values coded between 1 and 255, with 0 being reserved for 'No Data'. This product is derived from the original CBERS-4A WPM Level-4 Digital Number with 10 bit of quantization."

**Provider**: [National Institute of Space Research (INP)](https://data.inpe.br/)

**License**: [Creative-Commons-Attribution-4.0-International](https://creativecommons.org/licenses/by/4.0/legalcode.en)

### Google Maps Satellite Imagery

[Google Earth](https://www.google.com.br/earth/index.html)

This data source provides continuous, high-resolution global mosaic imagery delivered as pre-rendered XYZ map tiles. The imagery is a composite of aerial photogrammetry and commercial satellite sensors (e.g., Maxar, Airbus), dynamically scaled and projected in Web Mercator (EPSG:3857) as 8-bit RGB JPEG/PNG products.


**Usage Restrictions:** Google strictly prohibits unauthorized automated access (web scraping), bulk downloading for offline storage, and the creation of derivative works, which explicitly includes the training of Machine Learning or Artificial Intelligence models. Legal usage requires an active license via the Google Maps Platform API.

**Provider:** Google LLC.


### Sentinel-2

[Sentinel-2 Cloud-Optimized GeoTIFFs](https://registry.opendata.aws/sentinel-2-l2a-cogs/)

"The Sentinel-2 mission is a land monitoring constellation of two satellites that provide high resolution optical imagery and provide continuity for the current SPOT and Landsat missions. The mission provides a global coverage of the Earth's land surface every 5 days, making the data of great use in ongoing studies. This dataset is the same as the Sentinel-2 dataset, except the JP2K files were converted into Cloud-Optimized GeoTIFFs (COGs). Additionally, SpatioTemporal Asset Catalog metadata has were in a JSON file alongside the data, and a STAC API called Earth-search is freely available to search the archive. This dataset contains all of the scenes in the original Sentinel-2 Public Dataset and will grow as that does. L2A data are available from April 2017 over wider Europe region and globally since December 2018."

**Providers**: [AWS Registry of Open Data](https://registry.opendata.aws/), [Copernicus (ESA)](https://www.copernicus.eu/), [Element 84](https://element84.com/)

**License**: Access to Sentinel data is free, full and open for the broad Regional, National, European and International user community. View [Terms and Conditions](https://sentinels.copernicus.eu/documents/247904/690755/Sentinel_Data_Legal_Notice).


## CONFIG 

### Window Config

`SQUARE`: if `True` the final imagery will be a square, if `False` the image will be in the shape's format.

`RESOLUTION`: defines the final imagery square size.

`MAX_SIZE`: if `True` the final imagery shorter size will be the original imagery bigger size, if `False` it will preserve the original shape size.


## ⚠️ Legal Disclaimer and Terms of Use

This repository (`geoTilesGetter`) and its source code are distributed under the **MIT License**. Please note that this license applies **strictly to the software code** authored in this repository and **does not extend** to any data, images, or map tiles retrieved using the tool.

**1. Educational Purpose & No Included Endpoints**
This project is a Proof of Concept (PoC) developed strictly for educational and academic purposes in software engineering and geospatial mathematics. To ensure strict compliance with intellectual property rights, **this repository does not host, distribute, or contain any copyrighted imagery, nor does it include hardcoded URLs, access keys, or API endpoints for commercial providers** (such as Google Maps or Bing Maps). 

**2. User Responsibility and Provider Restrictions**
By configuring and using this tool, the end-user assumes all legal responsibilities for complying with the Terms of Service (ToS) of their manually configured data providers. Users must be aware that commercial providers generally strictly prohibit:
* Unauthorized automated access (web scraping) outside of official APIs.
* Bulk downloading for offline storage or proprietary databases.
* The creation of derivative works, which explicitly includes using proprietary map tiles for the training of Machine Learning or Artificial Intelligence models.

**3. Exemption of Liability**
The author of this repository is not affiliated with Google LLC, Microsoft Corporation, or any other commercial spatial data provider. The author **shall not be held liable** for any IP bans, account suspensions, DMCA takedowns, or legal actions arising from the unauthorized access, mass downloading, or misuse of copyrighted data by users of this software. The legal compliance of data acquisition and processing rests entirely with the end-user.