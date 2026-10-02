# geoTilesGetter
Scrap satellite imagery tiles from direct links. Scraps the most recent one available with the least amount of cloud cover.

## Getting Started

Change `source` value in `main` to choose satellite.
\
Adjust `config.py` to your work

To start, just run:
```
docker compose run --rm geotilesgetter python main.py --source='DESIRED_SOURCE'
```

## CBERS-4A

[CBERS-4A/WPM - Multispectral and Panchromatic Bands Fusioned](https://data.inpe.br/stac/browser/collections/CB4A-WPM-PCA-FUSED-1)

"This collection contains 2 meter high-resolution, RGB products, generated using the Principal Components Fusion (PCA) method, with values coded between 1 and 255, with 0 being reserved for 'No Data'. This product is derived from the original CBERS-4A WPM Level-4 Digital Number with 10 bit of quantization."

Provider: [National Institute of Space Research (INP)](https://data.inpe.br/)

License: [Creative-Commons-Attribution-4.0-International](https://creativecommons.org/licenses/by/4.0/legalcode.en)



## CONFIG 

### Window Config

`SQUARE`: if `True` the final imagery will be a square, if `False` the image will be in the shape's format.

`RESOLUTION`: defines the final imagery square size.

`MAX_SIZE`: if `True` the final imagery shorter size will be the original imagery bigger size, if `False` it will preserve the original shape size.