from pathlib import Path
from pystac_client import Client
import rasterio
from rasterio.features import rasterize
import numpy as np
from shapely.geometry import box, shape

import validate, polygon

'''
Get CBERS imagery from a shape with optional polygon border overlay
'''

def getData(shape_file, shapefile_name, getAll=True, draw_polygon=False, polygon_color='red', line_width=1, EXPAND_FACTOR=1.00, TARGET_SIZE=952):

    output_dir = Path("CBERS_Imagery")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f'loading polygon...')
    gdf = shape_file
    bbox = gdf.total_bounds
    print(f'shape: {shapefile_name}')

    # API STAC do INPE
    print(f'connecting to source...')
    catalog = Client.open("https://data.inpe.br/bdc/stac/v1")

    search = catalog.search(
        collections=["CB4A-WPM-PCA-FUSED-1"],
        bbox=bbox,
        datetime="2022-08-01/2026-08-30",
        query={"eo:cloud_cover": {"lt": 5} })

    items = list(search.items())
    
    print()
    print(f'getting scenes from:')
    print(f'collection: {items[0].collection_id}')
    print(f'datetime:{items[0].datetime} to {items[len(items) - 1].datetime}')
    print(f'local: {shapefile_name}')
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
        
        print(f'processing {item.id}')

        ###
        # verify if received data is valid
        # print(f'verifing received scene data...')
        # item_footprint = shape(item.geometry)
        # if not gdf.geometry.unary_union.within(item_footprint):
        #     print(f'no valide data...')
        #     continue

        asset_key = next(
            (k for k in ["visual", "data", "render"] if k in item.assets),
            list(item.assets.keys())[0],
        )
        asset_href = item.assets[asset_key].href

        try:
            with rasterio.open(asset_href) as src:
                
                gdf = gdf.to_crs(src.crs)

                print(f'calculating scene bounds...')
                # calculates width and height
                minx, miny, maxx, maxy = gdf.total_bounds
                width = maxx - minx
                height = maxy - miny

                # centers
                cx = (minx + maxx) / 2
                cy = (miny + maxy) / 2

                # calculates square size
                pixel_size = src.res[0]
                square = TARGET_SIZE * pixel_size * EXPAND_FACTOR

                # new bounds
                exp_minx = cx - (square / 2)
                exp_maxx = cx + (square / 2)
                exp_miny = cy - (square / 2)
                exp_maxy = cy + (square / 2)
                
                window = rasterio.windows.from_bounds(
                    exp_minx, exp_miny, exp_maxx, exp_maxy, src.transform
                )

                ###
                # crop image
                print(f'croping image...')
                cropped_image = src.read(window=window, boundless=True, fill_value=0)
                cropped_image = cropped_image[:,:TARGET_SIZE, :TARGET_SIZE]
                

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


                cropped_transform = rasterio.windows.transform(window, src.transform)

                ###
                # draw polygon
                if draw_polygon:

                    cropped_image = polygon.draw(cropped_image, gdf, cropped_transform, polygon_color, line_width)

                #     # Cria linhas/bordas a partir dos polígonos

                #     print(f'drawing polygon...')
                #     boundaries = gdf.geometry.boundary
                    
                #     # Se a linha for mais larga que 1px, aplica buffer
                #     if line_width > 1:
                #         pixel_size = abs(cropped_transform.a)
                #         boundaries = boundaries.buffer(line_width * pixel_size)

                #     # Define a cor RGB (valores de 0 a 255)
                #     colors = {
                #         'red': (255, 0, 0),
                #         'yellow': (255, 255, 0)
                #     }
                #     rgb_color = colors.get(polygon_color.lower(), (255, 0, 0))

                #     # Cria máscara booleana rasterizando as geometrias
                #     mask_shape = (cropped_image.shape[1], cropped_image.shape[2])
                #     polygon_mask = rasterize(
                #         shapes=boundaries,
                #         out_shape=mask_shape,
                #         transform=cropped_transform,
                #         fill=0,
                #         default_value=1,
                #         dtype=np.uint8
                #     ) > 0

                #     # Aplica a cor em cada banda do array RGB recortado
                #     num_channels = cropped_image.shape[0]
                #     for band_idx in range(min(num_channels, 3)):
                #         cropped_image[band_idx][polygon_mask] = rgb_color[band_idx]



                ###
                # file saving
                print(f'saving file...')
                out_meta = src.meta.copy()
                out_meta.update({
                    "height": cropped_image.shape[1],
                    "width": cropped_image.shape[2],
                    "transform": cropped_transform,
                })

                output_filename = output_dir / f"{shapefile_name}_{item.id}_scene{scene}.tif"
                with rasterio.open(output_filename, "w", **out_meta) as dest:
                    dest.write(cropped_image)

                print(f'saved as {output_filename} with scene {item.id}')
                success = True

                if getAll == False:
                    break
                print()
                scene += 1
                

        except Exception as e:
            print(f"failed in {item.id}: {e}")
            continue

    
    print(f'finished')

    if not success:
        print("error: no scene found")
