import processing
import os

# ============================================================
# CONFIGURACIÓN
# ============================================================
carpeta_trabajo = r"C:\HID-608\landsat_2025_full\mios\Ejemplo"

# Bandas YA recortadas
b4 = os.path.join(carpeta_trabajo, "20251021_L8_dr030-20_221_4RED.tif")
b5 = os.path.join(carpeta_trabajo, "20251021_L8_dr030-20_221_5NIR.tif")

dr030_mask = os.path.join(carpeta_trabajo, "dr030-20_221_msk.tif")

# Prefijo para productos
prefijo = "20251021_L8_dr030-20_221"

# Productos intermedios
p_red = os.path.join(carpeta_trabajo, f"{prefijo}_4REDp.tif")
p_nir = os.path.join(carpeta_trabajo, f"{prefijo}_5NIRp.tif")

c_red = os.path.join(carpeta_trabajo, f"{prefijo}_4REDc.tif")
c_nir = os.path.join(carpeta_trabajo, f"{prefijo}_5NIRc.tif")

ndvi = os.path.join(carpeta_trabajo, f"{prefijo}_NDVIg.tif")
mask_bs = os.path.join(carpeta_trabajo, f"{prefijo}_msk_bs.tif")
mask_sl = os.path.join(carpeta_trabajo, f"{prefijo}_sl_msk.tif")

red_bs = os.path.join(carpeta_trabajo, f"{prefijo}_4REDbs.tif")
nir_bs = os.path.join(carpeta_trabajo, f"{prefijo}_5NIRbs.tif")

# ============================================================
# FUNCIÓN CALCULADORA GDAL
# ============================================================
def calc_raster(input_a, output, formula, input_b=None, rtype=5, nodata=None):
    params = {
        'INPUT_A': input_a,
        'BAND_A': 1,
        'FORMULA': formula,
        'OUTPUT': output,
        'RTYPE': rtype,
    }
    if input_b is not None:
        params['INPUT_B'] = input_b
        params['BAND_B'] = 1
    if nodata is not None:
        params['NO_DATA'] = nodata

    processing.run("gdal:rastercalculator", params)

# ============================================================
# VERIFICACIÓN INICIAL
# ============================================================
for archivo in [b4, b5, dr030_mask]:
    if not os.path.exists(archivo):
        raise FileNotFoundError(f"No existe: {archivo}")

# ============================================================
# PASO 2 — Corrección reflectancia
# ============================================================
print("Paso 2: Corrección reflectancia...")
calc_raster(b4, p_red, 'A*0.0000275-0.2', rtype=5)
calc_raster(b5, p_nir, 'A*0.0000275-0.2', rtype=5)
print("OK")

# ============================================================
# PASO 3 — Corrección rango [0,1]
# ============================================================
print("Paso 3: Corrección [0,1]...")

expr_01 = '((A >= 0) & (A <= 1)) * A + (A > 1) + (A < 0) * 0'

calc_raster(p_red, c_red, expr_01, rtype=5)
calc_raster(p_nir, c_nir, expr_01, rtype=5)

print("OK")

# ============================================================
# PASO 4 — NDVIg (GRASS i.vi)
# ============================================================
print("Paso 4: NDVIg...")

processing.run("grass7:i.vi", {
    'red': c_red,
    'nir': c_nir,
    'viname': 9,  # NDVI
    'output': ndvi,
    'GRASS_REGION_CELLSIZE_PARAMETER': 0,
    'GRASS_SNAP_TOLERANCE_PARAMETER': -1,
    'GRASS_MIN_AREA_PARAMETER': 0.0001,
})

print("OK")

# ============================================================
# PASO 4a — Máscara suelo desnudo
# ============================================================
print("Paso 4a: Máscara suelo desnudo...")

calc_raster(
    ndvi,
    mask_bs,
    'logical_and(greater_equal(A,0.05), less(A,0.2))',
    rtype=1,
    nodata=0
)

print("OK")

# ============================================================
# PASO 4b — DR030 × msk_bs
# ============================================================
print("Paso 4b: DR030 × msk_bs...")

calc_raster(
    dr030_mask,
    mask_sl,
    'A*B',
    input_b=mask_bs,
    rtype=1,
    nodata=0
)

if not os.path.exists(mask_sl):
    raise FileNotFoundError("No se generó sl_msk")

print("OK")

# ============================================================
# PASO 5 — Aplicar máscara (A*B EXACTO COMO PDF)
# ============================================================
print("Paso 5: Aplicar máscara a RED y NIR...")

calc_raster(c_red, red_bs, 'A*B', input_b=mask_sl, rtype=5)
calc_raster(c_nir, nir_bs, 'A*B', input_b=mask_sl, rtype=5)

print("=======================================")
print("PROCESO COMPLETADO — REPLICA EXACTA")
print("=======================================")