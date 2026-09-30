from pathlib import Path
import rasterio
from rasterio.features import rasterize
import numpy as np
from shapely.geometry import box, shape

import validate, polygon, config

'''
Get imagery from a shape with optional polygon border overlay
'''

def getData(shape_file, shapefile_name, source, getAll=True):

    print(f'loading polygon...')
    gdf = shape_file
    bbox = gdf.total_bounds
    print(f'shape: {shapefile_name}')

    # 
    print(f'connecting to source...')

    if source =='cbers':
        items = config.cbers(bbox)
    elif source == 'sentinel2':
        items = config.sentinel2(bbox=bbox)
    
    if not items:
        print(f'no scenes obtained from given parameters')
        return

    print()
    print(f'getting scenes from:')
    print(f'SOURCE: {config.SOURCES.get(source)[0]}')
    print(f'COLLECTION: {items[0].collection_id}')
    print(f'DATE FRAME:{items[0].datetime} to {items[len(items) - 1].datetime}')
    print(f'SHAPE: {shapefile_name}')
    print()


    success = False
    print(f'total scenes received: {len(items)}')
    print(f'processing fromm newest to oldest...')    
    items.sort(key=lambda x: x.datetime, reverse=True)
    
    for item in items:

        if source == 'sentinel2':
            if "visual" not in item.assets:
                continue

            asset_href = item.assets["visual"].href

        elif source == 'cbers':
            
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
                window = polygon.window(gdf, src, max_size=config.MAX_SIZE)

                # get image
                print(f'getting image...')
                image = src.read(window=window, boundless=True, fill_value=0)
                
                if not config.MAX_SIZE:
                    print(f'croping image...')
                    image = image[:,:config.RESOLUTION, :config.RESOLUTION]
                

                # image validations
                     
                print(f'checking cloud cover...')
                if not validate.cloudFilter(image, cloud_threshold=0.05, contrast_threshold=10.0, blur_threshold=10.0):
                    print(f'cloud covered...')
                    print(f'skipping...')
                    continue
                
                print(f'verifing data integrity...')
                if not validate.dataIntegrity(image, threshold=0.05):
                    print(f'scene integrity compromissed..')
                    print(f'skipping...')
                    continue

                transform = rasterio.windows.transform(window, src.transform)

                # draw polygon
                if config.DRAW_POLYGON:
                    print(f'drawing polygon...')
                    image = polygon.draw(image, gdf, transform,crs=gdf.crs)
                    

                ###
                # file saving
                print(f'saving file...')
                out_meta = src.meta.copy()
                out_meta.update({
                    "height": image.shape[1],
                    "width": image.shape[2],
                    "transform": transform,
                })

                output_filename = config.SOURCES.get(source)[1] + '/' + f"{shapefile_name}_{item.id}.tif"
                with rasterio.open(output_filename, "w", **out_meta) as dest:
                    dest.write(image)

                print(f'saved as {output_filename} with scene {item.id}')
                print()
                success = True

                if success and getAll == False:
                    break
                print()
                
                
        except Exception as e:
            print(f"failed in {item.id}: {e}")
            continue

    
    print(f'finished')

    if not success:
        print("error: no scene found")
