import os
import re
import csv
import zlib

from qgis.core import (
    QgsRasterLayer,
    QgsVectorLayer
)
import processing

# ================= CONFIGURACIÓN =================

# Directorio de entrada con las imágenes .tif
input_dir = "/home/elpd/HID-608/landsat2025"

# Archivo shapefile para la máscara
shapefile_path = "/home/elpd/HID-608/wb_30_20.shp"

# Directorio de salida
output_dir = "/home/elpd/HID-608/landsat2025_rst"

# CSV de control CRC
csv_path = os.path.join(output_dir, "/home/elpd/HID-608/control_crc_landsat.csv")

# ================= FUNCIONES =================

def calcular_crc32(file_path, chunk_size=8192):
    """
    Calcula la firma CRC-32 de un archivo.
    Retorna string hexadecimal en mayúsculas.
    """
    crc = 0
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            crc = zlib.crc32(chunk, crc)
    return format(crc & 0xFFFFFFFF, '08X')


def parse_landsat_filename(filename):
    """
    Extrae información del nombre de archivo Landsat.
    Ejemplo:
    LC08_L1TP_025047_20250106_20250111_02_T1_QB.tif
    """
    filename_no_ext = os.path.splitext(filename)[0]

    pattern = (
        r'L(C|E|0)(\d{2})_L1(T|G)(P|T)_'
        r'(\d{6})_(\d{8})_\d{8}_\d{2}_T\d_([a-zA-Z0-9]+)'
    )

    match = re.match(pattern, filename_no_ext)

    if not match:
        return None

    sat_num = match.group(2)
    path_row = match.group(5)
    acq_date = match.group(6)
    product = match.group(7)

    return {
        "satellite": f"L{sat_num}",
        "acquisition_date": acq_date,
        "path_row": path_row,
        "path_row_short": path_row[2:],
        "product": product.upper(),
        "original_name": filename_no_ext
    }


def generate_new_filename(metadata):
    """
    Genera el nuevo nombre .rst usando la lógica Notepad++
    """
    l = metadata["original_name"]

    try:
        fecha = l[17:25]
        satelite = l[0] + l[3]
        pathrow = l[11:13] + l[14:16]
        nivel = l[6] + l[36] + l[39]

        sufijo = l[-2:].upper()

        bandas = {
            "QB": "_QB",
            "B1": "_1CAS",
            "B2": "_2BLE",
            "B3": "_3GRN",
            "B4": "_4RED",
            "B5": "_5NIR",
            "B6": "_6SW1",
            "B7": "_7SW2",
            "B8": "_8PCM"
        }

        banda = bandas.get(sufijo, f"_{metadata['product']}")

        return f"{fecha}_{satelite}_{pathrow}_{nivel}{banda}.rst"

    except Exception:
        return (
            f"{metadata['acquisition_date']}_"
            f"{metadata['satellite']}_"
            f"{metadata['path_row_short']}_121_{metadata['product']}.rst"
        )


def crop_raster_with_mask_qgis(input_raster, output_raster, shapefile):
    """
    Recorta un raster usando máscara vectorial (GDAL vía QGIS)
    """
    raster_layer = QgsRasterLayer(input_raster, "input_raster")
    if not raster_layer.isValid():
        print(f"  ERROR: Raster inválido: {input_raster}")
        return False

    vector_layer = QgsVectorLayer(shapefile, "mask", "ogr")
    if not vector_layer.isValid():
        print(f"  ERROR: Shapefile inválido: {shapefile}")
        return False

    params = {
        "INPUT": raster_layer,
        "MASK": shapefile,
        "SOURCE_CRS": raster_layer.crs(),
        "TARGET_CRS": raster_layer.crs(),
        "CROP_TO_CUTLINE": True,
        "KEEP_RESOLUTION": True,   # preserva grilla Landsat
        "SET_RESOLUTION": False,
        "NODATA": None,
        "ALPHA_BAND": False,
        "OPTIONS": "",
        "DATA_TYPE": 0,
        "EXTRA": "",
        "OUTPUT": output_raster
    }

    try:
        processing.run("gdal:cliprasterbymasklayer", params)
        return os.path.exists(output_raster)
    except Exception as e:
        print(f"  ERROR en recorte: {e}")
        return False


# ================= EJECUCIÓN PRINCIPAL =================

def main():

    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(input_dir):
        print(f"ERROR: Directorio de entrada no existe: {input_dir}")
        return

    if not os.path.exists(shapefile_path):
        print(f"ERROR: Shapefile no encontrado: {shapefile_path}")
        return

    # Inicializar CSV si no existe
    if not os.path.exists(csv_path):
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "original_tif",
                "crc32_tif",
                "rst_recortado",
                "crc32_rst"
            ])

    image_files = [
        os.path.join(input_dir, f)
        for f in os.listdir(input_dir)
        if f.lower().endswith((".tif", ".tiff"))
    ]

    print(f"Imágenes encontradas: {len(image_files)}")
    print("-" * 50)

    processed = skipped = errors = 0

    for i, input_raster in enumerate(image_files, 1):
        fname = os.path.basename(input_raster)
        print(f"[{i}/{len(image_files)}] Procesando: {fname}")

        metadata = parse_landsat_filename(fname)
        if not metadata:
            print("  ERROR: Nombre Landsat no reconocido")
            errors += 1
            continue

        new_name = generate_new_filename(metadata)
        output_path = os.path.join(output_dir, new_name)

        if os.path.exists(output_path):
            print("  Saltado (ya existe)")
            skipped += 1
            continue

        print("  Recortando raster...")
        success = crop_raster_with_mask_qgis(
            input_raster, output_path, shapefile_path
        )

        if not success:
            errors += 1
            continue

        crc_tif = calcular_crc32(input_raster)
        crc_rst = calcular_crc32(output_path)

        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                fname,
                crc_tif,
                new_name,
                crc_rst
            ])

        print(f"  ✔ Guardado: {new_name}")
        print(f"    CRC32 TIF: {crc_tif}")
        print(f"    CRC32 RST: {crc_rst}")

        processed += 1
        print()

    print("=" * 50)
    print("PROCESO FINALIZADO")
    print(f"Procesados: {processed}")
    print(f"Saltados:   {skipped}")
    print(f"Errores:    {errors}")
    print(f"CSV:        {csv_path}")
    print("=" * 50)


# ================= EJECUTAR =================

print("SCRIPT LANDSAT – RECORTE + CRC")
print("=" * 50)
main()
