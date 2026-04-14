import os
import csv
import numpy as np
from osgeo import gdal
from pathlib import Path

# ===============================
# CONFIGURACIÓN
# ===============================
INPUT_DIR = Path( "/home/elpd/HID-608/landsat2025_dr030/")
OUTPUT_CSV = "/home/elpd/HID-608/landsat2025_dr030.csv"

NODATA_VALUE = 1
CLOUD_BIT_MASK = 8  # 0b1000 → bit 3

# ===============================
# FUNCIÓN DE CÁLCULO
# ===============================
def calcular_cloud_cover_qb(qb_path):
    ds = gdal.Open(str(qb_path), gdal.GA_ReadOnly)
    if ds is None:
        raise RuntimeError(f"No se pudo abrir {qb_path}")

    band = ds.GetRasterBand(1)
    qb = band.ReadAsArray()

    # Máscara de píxeles válidos (igual que en QGIS)
    valid_mask = qb != NODATA_VALUE
    valid_pixels = np.count_nonzero(valid_mask)

    if valid_pixels == 0:
        return 0.0

    # ===== MÉTODO QGIS =====
    cloud_mask = (qb & CLOUD_BIT_MASK) > 0
    cloud_pixels = np.count_nonzero(cloud_mask & valid_mask)

    porcentaje = (cloud_pixels / valid_pixels) * 100
    return round(porcentaje, 2)

# ===============================
# EJECUCIÓN EN LOTE
# ===============================
results = []

for qb_file in sorted(INPUT_DIR.glob("*.tif")):
    porcentaje = calcular_cloud_cover_qb(qb_file)
    results.append([qb_file.name, porcentaje])
    print(f"{qb_file.name} → {porcentaje}%")

# ===============================
# EXPORTAR CSV
# ===============================
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["imagen", "porcentaje_nubes"])
    writer.writerows(results)

print("\nCSV generado correctamente:")
print(OUTPUT_CSV)

