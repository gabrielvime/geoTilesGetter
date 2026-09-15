from pathlib import Path
from pystac_client import Client
import rasterio
from rasterio.features import rasterize
import numpy as np
from shapely.geometry import box

'''
Get CBERS imagery from a shape with optional polygon border overlay
'''

def getData(shape_file, shapefile_name, draw_polygon=True, polygon_color='red', line_width=2, expand_factor=1.30):

    output_dir = Path("CBERS_Imagery")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f'loading polygon...')
    gdf = shape_file
    bbox = gdf.total_bounds

    # API STAC do INPE
    print(f'connecting to INPE...')
    catalog = Client.open("https://data.inpe.br/bdc/stac/v1")

    search = catalog.search(
        collections=["CB4A-WPM-PCA-FUSED-1"],
        bbox=bbox,
        datetime="2022-08-01/2026-08-30",
    )

    items = list(search.items())

    if not items:
        print("Nenhuma cena encontrada para os parâmetros informados.")
        return

    success = False

    for item in items:
        asset_key = next(
            (k for k in ["visual", "data", "render"] if k in item.assets),
            list(item.assets.keys())[0],
        )
        asset_href = item.assets[asset_key].href

        try:
            with rasterio.open(asset_href) as src:
                # Reprojetar o polígono para o CRS nativo do raster
                gdf_proj = gdf.to_crs(src.crs)

                raster_box = box(*src.bounds)
                if not gdf_proj.geometry.unary_union.intersects(raster_box):
                    continue

                # Calcular limites do polígono e expandir 30% a partir do centro
                minx, miny, maxx, maxy = gdf_proj.total_bounds
                width = maxx - minx
                height = maxy - miny

                cx = (minx + maxx) / 2
                cy = (miny + maxy) / 2

                exp_width = width * expand_factor
                exp_height = height * expand_factor

                exp_minx = cx - (exp_width / 2)
                exp_maxx = cx + (exp_width / 2)
                exp_miny = cy - (exp_height / 2)
                exp_maxy = cy + (exp_height / 2)

                # Criar janela retangular expandida
                window = rasterio.windows.from_bounds(
                    exp_minx, exp_miny, exp_maxx, exp_maxy, src.transform
                )

                cropped_image = src.read(window=window, boundless=True, fill_value=0)
                cropped_transform = rasterio.windows.transform(window, src.transform)

                # --- DESENHO DO POLÍGONO ---
                if draw_polygon:
                    # Cria linhas/bordas a partir dos polígonos
                    boundaries = gdf_proj.geometry.boundary
                    
                    # Se a linha for mais larga que 1px, aplica buffer
                    if line_width > 1:
                        pixel_size = abs(cropped_transform.a)
                        boundaries = boundaries.buffer(line_width * pixel_size)

                    # Define a cor RGB (valores de 0 a 255)
                    colors = {
                        'red': (255, 0, 0),
                        'yellow': (255, 255, 0)
                    }
                    rgb_color = colors.get(polygon_color.lower(), (255, 0, 0))

                    # Cria máscara booleana rasterizando as geometrias
                    mask_shape = (cropped_image.shape[1], cropped_image.shape[2])
                    polygon_mask = rasterize(
                        shapes=boundaries,
                        out_shape=mask_shape,
                        transform=cropped_transform,
                        fill=0,
                        default_value=1,
                        dtype=np.uint8
                    ) > 0

                    # Aplica a cor em cada banda do array RGB recortado
                    num_channels = cropped_image.shape[0]
                    for band_idx in range(min(num_channels, 3)):
                        cropped_image[band_idx][polygon_mask] = rgb_color[band_idx]

                out_meta = src.meta.copy()
                out_meta.update({
                    "height": cropped_image.shape[1],
                    "width": cropped_image.shape[2],
                    "transform": cropped_transform,
                })

                output_filename = output_dir / f"{shapefile_name}_cbers_{item.id}.tif"
                with rasterio.open(output_filename, "w", **out_meta) as dest:
                    dest.write(cropped_image)

                print(
                    f"Sucesso! Imagem salva como {output_filename} usando a cena: {item.id}"
                )
                success = True
                break

        except Exception as e:
            print(f"Tentativa falhou na cena {item.id}: {e}")
            continue

    if not success:
        print("Erro: Nenhuma cena encontrada possui sobreposição geométrica direta.")