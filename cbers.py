import geopandas as gpd
from pystac_client import Client
import rasterio
from rasterio.mask import mask
from shapely.geometry import box

import loadPolygon

'''
Get CBERS imagery from a shape
'''


# carregar area de interesse
def getData(shape_file, shapefile_name):

  print(f'loading polygon...')

  #gdf = loadPolygon.getGDF('shapes\processo_850092_2020.zip')
  gdf = shape_file
  bbox = gdf.total_bounds

  # API STAC do INPE (Brazil Data Cube)
  print(f'coonnecting to INPE...')
  catalog = Client.open("https://data.inpe.br/bdc/stac/v1")

  #coleção WPM Fused do CBERS-4A (Resolução de 2 metros)

  search = catalog.search(
      collections=["CB4A-WPM-PCA-FUSED-1"], # colecao
      bbox=bbox,
      datetime="2026-08-01/2026-08-30",  # intervalo das cenas
  )

  items = list(search.items())

  if not items:
    print("Nenhuma cena encontrada para os parâmetros informados.")
  else:
    success = False

    # validacao de sobreposicao: percorre as cenas econtradas (sem baixar nada) e repojeta o poligono para validar inerseção
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

          # Verificar sobreposição básica
          raster_box = box(*src.bounds)
          if not gdf_proj.geometry.unary_union.intersects(raster_box):
            continue

          # calcular limites do polígono e expandir 30% a partir do centro
          minx, miny, maxx, maxy = gdf_proj.total_bounds
          width = maxx - minx
          height = maxy - miny

          cx = (minx + maxx) / 2
          cy = (miny + maxy) / 2

          # Expandir dimensões em 30% (fator 1.30)
          exp_width = width * 1.30
          exp_height = height * 1.30

          exp_minx = cx - (exp_width / 2)
          exp_maxx = cx + (exp_width / 2)
          exp_miny = cy - (exp_height / 2)
          exp_maxy = cy + (exp_height / 2)

          # criar a janela retangular expandida no raster usando chamada explícita
          window = rasterio.windows.from_bounds(
              exp_minx, exp_miny, exp_maxx, exp_maxy, src.transform
          )

          # ler os dados da janela
          cropped_image = src.read(window=window, boundless=True, fill_value=0)
          cropped_transform = rasterio.windows.transform(window, src.transform)

          out_meta = src.meta.copy()
          out_meta.update({
              "height": cropped_image.shape[1],
              "width": cropped_image.shape[2],
              "transform": cropped_transform,
          })

          output_filename = f"{shapefile_name}_cbers_{item.id}.tif"
          with rasterio.open(output_filename, "w", **out_meta) as dest:
            dest.write(cropped_image)

          print(
              f"Sucesso! Imagem retangular expandida salva como"
              f" {output_filename} usando a cena: {item.id}"
          )
          success = True
          break

      except Exception as e:
        print(f"Tentativa falhou na cena {item.id}: {e}")
        continue

    if not success:
      print(
          "Erro: Nenhuma cena encontrada possui sobreposição geométrica direta"
          " com o polígono fornecido."
      )
