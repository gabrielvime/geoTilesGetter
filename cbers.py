from pathlib import Path
from pystac_client import Client
import rasterio
from rasterio.features import rasterize
import numpy as np
from shapely.geometry import box, shape

import validate, polygon, config

'''
Get CBERS imagery from a shape with optional polygon border overlay
'''

def getData(shape_file, shapefile_name, getAll=True, draw_polygon=False, polygon_color='red', line_width=1):

    output_dir = Path("CBERS_Imagery")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f'loading polygon...')
    gdf = shape_file
    bbox = gdf.total_bounds
    print(f'shape: {shapefile_name}')

    # API STAC do INPE
    print(f'connecting to source...')
    # catalog = Client.open("https://data.inpe.br/bdc/stac/v1")

    # search = catalog.search(
    #     collections=["CB4A-WPM-PCA-FUSED-1"],
    #     bbox=bbox,
    #     datetime="2022-08-01/2026-08-30",
    #     query={"eo:cloud_cover": {"lt": 5} })

    # items = list(search.items())
    items = config.cbers(bbox)
    
    print()
    print(f'getting scenes from:')
    print(f'collection: {items[0].collection_id}')
    print(f'datetime:{items[0].datetime} to {items[len(items) - 1].datetime}')
    print(f'shape: {shapefile_name}')
    print()

    if not items:
        print(f'no scenes obtained from given parameters')
        return

    success = False
    print(f'total scenes received: {len(items)}')
    print(f'processing fromm newest to oldest...')    
    items.sort(key=lambda x: x.datetime, reverse=True)
    
    for item in items:

        scene = 1
        
        print()
        print(f'processing {item.id}')

        asset_key = next(
            (k for k in ["visual", "data", "render"] if k in item.assets),
            list(item.assets.keys())[0],
        )
        asset_href = item.assets[asset_key].href

        try:
            with rasterio.open(asset_href) as src:
                
                gdf = gdf.to_crs(src.crs)

                print(f'calculating scene bounds...')
                # get polygon window
                window = polygon.window(gdf, src)

                # crop image
                print(f'croping image...')
                cropped_image = src.read(window=window, boundless=True, fill_value=0)
                cropped_image = cropped_image[:,:config.RESOLUTION, :config.RESOLUTION]
                

                # image validations
                     
                print(f'checking cloud cover...')
                if not validate.cloudFilter(cropped_image, cloud_threshold=0.15):
                    print(f'cloud covered...')
                    print(f'skipping...')
                    continue
                
                print(f'verifing data integrity...')
                if not validate.dataIntegrity(cropped_image, threshold=0.05):
                    print(f'scene integrity compromissed..')
                    print(f'skipping...')
                    continue


                transform = rasterio.windows.transform(window, src.transform)

                ###
                # draw polygon
                if draw_polygon:
                    print(f'drawing polygon...')
                    cropped_image = polygon.draw(cropped_image, gdf, transform, polygon_color, line_width)


                ###
                # file saving
                print(f'saving file...')
                out_meta = src.meta.copy()
                out_meta.update({
                    "height": cropped_image.shape[1],
                    "width": cropped_image.shape[2],
                    "transform": transform,
                })

                output_filename = output_dir / f"{shapefile_name}_{item.id}_scene{scene}.tif"
                with rasterio.open(output_filename, "w", **out_meta) as dest:
                    dest.write(cropped_image)

                print(f'saved as {output_filename} with scene {item.id}')
                print()
                success = True

                if success and getAll == False:
                    break
                print()
                scene += 1
                
        except Exception as e:
            print(f"failed in {item.id}: {e}")
            continue

    
    print(f'finished')

    if not success:
        print("error: no scene found")
