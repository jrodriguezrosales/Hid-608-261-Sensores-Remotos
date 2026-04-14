import os
import glob
import numpy as np
from osgeo import gdal
import processing
from qgis.core import QgsProject
from qgis.utils import iface

# ==========================================================
# 1. PARÁMETROS GLOBALES (solo modificar esta sección)
# ==========================================================
base_dir  = r"C:\HID-608\landsat_2025_full\tarea4\20251130"
mask_path = os.path.join(base_dir, "dr030-20_221_msk.tif")
extent    = "601995.0,673425.0,2035305.0,2098815.0"

NODATA = -9999.0

# Parámetros TSAVIt (modificar según imagen)
X_val = 1.5
a_val = 0.060912
s_val = 1.064151

# ----------------------------------------------------------
# DETECCIÓN AUTOMÁTICA de fecha y satélite
# ----------------------------------------------------------
# Fecha: se lee directamente del nombre de la carpeta final
fecha = os.path.basename(base_dir)          # ej. "20251224"

# Satélite: se inspecciona el prefijo del primer archivo de banda encontrado
#   LC08_... → Landsat 8 → "L8"
#   LC09_... → Landsat 9 → "L9"
_muestra = glob.glob(os.path.join(base_dir, "LC0*_B*.tif"))
if not _muestra:
    raise FileNotFoundError(
        "No se encontraron archivos de banda con prefijo LC08 o LC09 en:\n"
        f"  {base_dir}\n"
        "Verifica que la carpeta sea correcta."
    )
_prefijo = os.path.basename(_muestra[0])[:4]   # "LC08" o "LC09"
satelite = {"LC08": "L8", "LC09": "L9"}.get(_prefijo)
if satelite is None:
    raise ValueError(f"Prefijo de satélite no reconocido: '{_prefijo}' (se esperaba LC08 o LC09)")

# Prefijo base para todos los archivos de salida: ej. "20251224_L8"
pfx = f"{fecha}_{satelite}"

print("=" * 60)
print(f"  PROCESAMIENTO {satelite.replace('L','LANDSAT ')} – ÍNDICES DE VEGETACIÓN")
print(f"  Fecha imagen : {fecha}")
print(f"  Satélite     : {satelite}")
print(f"  Directorio   : {base_dir}")
print("=" * 60)

# ==========================================================
# 2. PRE-PROCESAMIENTO
# ==========================================================
band_files = []
for i in range(1, 8):
    match = glob.glob(os.path.join(base_dir, f"*_B{i}.tif"))
    if match:
        band_files.append(match[0])

# Nombres de salida generados automáticamente con pfx
merge_out = os.path.join(base_dir, f"{pfx}_2547_221_1-7.tif")
clip_out  = os.path.join(base_dir, f"{pfx}_dr030-20_221_1-7c.tif")
scale_out = os.path.join(base_dir, f"{pfx}_dr030-20_221_1-7d.tif")
gn_out    = os.path.join(base_dir, f"{pfx}_dr030-20_221_1-7gn.tif")

print(f"\n[1/7] Mosaico, recorte y corrección de reflectancia...")
print(f"      → {os.path.basename(merge_out)}")

processing.run("gdal:merge", {
    'INPUT': band_files, 'PCT': False, 'SEPARATE': True,
    'DATA_TYPE': 3, 'OUTPUT': merge_out
})
processing.run("gdal:cliprasterbyextent", {
    'INPUT': merge_out, 'PROJWIN': extent, 'DATA_TYPE': 0, 'OUTPUT': clip_out
})
# Decodificación: modelo lineal (GROUP = LEVEL2_SURFACE_REFLECTANCE_PARAMETERS)
processing.run("gdal:rastercalculator", {
    'INPUT_A': clip_out, 'BAND_A': 1,
    'FORMULA': 'A*0.0000275 - 0.2',
    'EXTRA': '--allBands=A', 'RTYPE': 5, 'OUTPUT': scale_out
})
# Acotar valores entre 0 y 1
processing.run("gdal:rastercalculator", {
    'INPUT_A': scale_out, 'BAND_A': 1,
    'FORMULA': '((A>=0) & (A<=1))*A + (A>1)*1 + (A<0)*0',
    'EXTRA': '--allBands=A', 'RTYPE': 5, 'OUTPUT': gn_out
})

# ==========================================================
# 3. EXTRACCIÓN DE BANDAS 4, 5, 6 y 7
# ==========================================================
print("[2/7] Extrayendo bandas 4, 5, 6 y 7...")

b_paths = {}
for b_num in [4, 5, 6, 7]:
    out_path = os.path.join(base_dir, f"{pfx}_dr030-20_221_B{b_num}gn.tif")
    b_paths[f"B{b_num}"] = out_path
    processing.run("gdal:translate", {
        'INPUT': gn_out, 'EXTRA': f'-b {b_num}', 'DATA_TYPE': 0, 'OUTPUT': out_path
    })

b4 = b_paths['B4']   # Rojo
b5 = b_paths['B5']   # NIR
b6 = b_paths['B6']   # SWIR 1
b7 = b_paths['B7']   # SWIR 2

# ==========================================================
# 4. REGRESIÓN LINEAL – cálculo automático de R²
#    Se ejecuta AQUÍ porque las bandas corregidas ya existen.
#    Regresión 1 : x = B5 (NIR),  y = B6 (SWIR 1)
#    Regresión 2 : x = B5 (NIR),  y = B7 (SWIR 2)
# ==========================================================
print("[3/7] Calculando regresiones lineales (R²)...")

def get_r_squared(path_x, path_y):
    """
    Calcula R² entre dos rasters ya corregidos.
    Filtra píxeles con valor <= 0 (bordes/NoData del working box)
    para no sesgar la correlación.
    """
    arr_x = gdal.Open(path_x).ReadAsArray().astype(np.float64)
    arr_y = gdal.Open(path_y).ReadAsArray().astype(np.float64)
    valid = (arr_x > 0) & (arr_y > 0) & np.isfinite(arr_x) & np.isfinite(arr_y)
    if np.sum(valid) < 2:
        print("  ⚠ No hay píxeles válidos suficientes para la regresión.")
        return 0.0
    corr_matrix = np.corrcoef(arr_x[valid], arr_y[valid])
    return float(corr_matrix[0, 1] ** 2)

r2_5_6 = get_r_squared(b5, b6)
r2_5_7 = get_r_squared(b5, b7)

print(f"      R² (B5 vs B6): {r2_5_6:.6f}")
print(f"      R² (B5 vs B7): {r2_5_7:.6f}")

if r2_5_7 >= r2_5_6:
    best_msit_name = 'MSIt7'
    print("      → Banda ganadora: B7  →  MSIt adaptativo = MSIt7")
else:
    best_msit_name = 'MSIt6'
    print("      → Banda ganadora: B6  →  MSIt adaptativo = MSIt6")

# ==========================================================
# FUNCIÓN AUXILIAR: calcula índice y aplica máscara DR030
# ==========================================================
def calc_index_and_mask(name, formula, input_A, input_B=None):
    """
    - NO_DATA declarado en ambos pasos: píxeles fuera del DR030
      quedan como NoData real (no como cero) → no entran en la media.
    - Máscara con numpy.where(B > 0, A, NODATA) en lugar de A*B.
    """
    tmp_path   = os.path.join(base_dir, f"{name}_temp.tif")
    # Nombre final: ej. "20251224_L8_dr030_221_NDVIg.tif"
    final_path = os.path.join(base_dir, f"{pfx}_dr030_221_{name}.tif")

    params = {
        'INPUT_A': input_A, 'BAND_A': 1,
        'FORMULA': formula,
        'NO_DATA': NODATA,
        'RTYPE': 5,
        'OUTPUT': tmp_path
    }
    if input_B:
        params.update({'INPUT_B': input_B, 'BAND_B': 1})
    processing.run("gdal:rastercalculator", params)

    # Enmascarar: fuera del DR030 → NoData (no cero)
    processing.run("gdal:rastercalculator", {
        'INPUT_A': tmp_path,  'BAND_A': 1,
        'INPUT_B': mask_path, 'BAND_B': 1,
        'FORMULA': f'numpy.where(B > 0, A, {NODATA})',
        'NO_DATA': NODATA,
        'RTYPE': 5,
        'OUTPUT': final_path
    })

    if os.path.exists(tmp_path):
        os.remove(tmp_path)

    iface.addRasterLayer(final_path, name)
    return final_path

# ==========================================================
# 5. ÍNDICES CLÁSICOS (SRg, NDVIg, SAVIg)
# ==========================================================
print("[4/7] Calculando SRg, NDVIg, SAVIg...")

# SRg = B5 / B4  (A=B5, B=B4)
srg_formula = (
    'numpy.where(B > 0, '
    'A / numpy.where(B > 0, B, 1.0), '
    f'{NODATA})'
)
srg_path = calc_index_and_mask('SRg', srg_formula, input_A=b5, input_B=b4)

# NDVIg = (B5 - B4) / (B5 + B4)
ndvi_formula = (
    'numpy.where((A + B) != 0, '
    '(A - B) / numpy.where((A + B) != 0, A + B, 1.0), '
    f'{NODATA})'
)
ndvi_path = calc_index_and_mask('NDVIg', ndvi_formula, input_A=b5, input_B=b4)

# SAVIg = 1.5 * (B5 - B4) / (B5 + B4 + 0.5)   [L = 0.5]
savi_formula = '1.5 * (A - B) / (A + B + 0.5)'
savi_path = calc_index_and_mask('SAVIg', savi_formula, input_A=b5, input_B=b4)

# ==========================================================
# 6. MSIt – AMBAS VERSIONES  (MSIt6 = B6/B5  |  MSIt7 = B7/B5)
# ==========================================================
print("[5/7] Calculando MSIt6 (B6/B5) y MSIt7 (B7/B5)...")

msit_formula = (
    'numpy.where(B > 0, '
    'A / numpy.where(B > 0, B, 1.0), '
    f'{NODATA})'
)
msit6_path = calc_index_and_mask('MSIt6', msit_formula, input_A=b6, input_B=b5)
msit7_path = calc_index_and_mask('MSIt7', msit_formula, input_A=b7, input_B=b5)

# ==========================================================
# 7. TSAVIt – FÓRMULA ESTÁNDAR
#    TSAVI = s*(NIR - s*Red - a) / (a*NIR + Red - a*s + X*(1+s²))
#    NIR = B5  |  Rojo = B4  (NO es adaptativo)
# ==========================================================
print(f"[6/7] Calculando TSAVIt  (s={s_val}, a={a_val}, X={X_val})...")

a_s  = round(a_val * s_val, 8)
s2   = round(s_val * s_val, 8)
X_s2 = round(X_val * (1.0 + s2), 8)

# A = B5 (NIR)  |  B = B4 (Rojo)
tsavi_formula = (
    f"{s_val} * (A - {s_val} * B - {a_val}) / "
    f"({a_val} * A + B - {a_s} + {X_s2})"
)
tsavi_path = calc_index_and_mask('TSAVIt', tsavi_formula, input_A=b5, input_B=b4)

# ==========================================================
# 8. ESTADÍSTICAS DEL DR-030 (excluye píxeles NoData)
# ==========================================================
print("\n[7/7] Calculando estadísticas del DR-030...")

index_paths = {
    'SRg':    srg_path,
    'NDVIg':  ndvi_path,
    'SAVIg':  savi_path,
    'MSIt6':  msit6_path,
    'MSIt7':  msit7_path,
    'TSAVIt': tsavi_path,
}

print(f"\n{'Índice':<10} {'Media':>10} {'Mín':>10} {'Máx':>10} {'StdDev':>12}")
print("─" * 62)

results = {}
for name, path in index_paths.items():
    ds = gdal.Open(path)
    if ds is None:
        print(f"{name:<10}  ⚠ No se pudo abrir el archivo")
        continue
    band = ds.GetRasterBand(1)
    arr  = band.ReadAsArray().astype(np.float64)
    nd   = band.GetNoDataValue()
    ds   = None

    valid_mask = np.isfinite(arr) & (arr != NODATA)
    if nd is not None:
        valid_mask &= (arr != nd)
    valid = arr[valid_mask]

    if len(valid) > 0:
        mean_v = float(np.mean(valid))
        min_v  = float(np.min(valid))
        max_v  = float(np.max(valid))
        std_v  = float(np.std(valid))
        results[name] = mean_v
        marker = "  ◄ adaptativo" if name == best_msit_name else ""
        print(f"{name:<10} {mean_v:>10.6f} {min_v:>10.6f} {max_v:>10.6f} {std_v:>12.6f}{marker}")
    else:
        print(f"{name:<10}  ⚠ Sin píxeles válidos — revisa ruta o máscara")

print("\n" + "─" * 62)
print("ÍNDICES MEDIOS DEL DR-030 (2 decimales)")
if results:
    print("\t".join(results.keys()))
    print("\t".join(f"{v:.2f}" for v in results.values()))

print("\n" + "=" * 60)
print("  PROCESO COMPLETADO")
print("=" * 60)