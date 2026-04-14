# ============================================================
#  PÍXELES CENTRALES DE CAPA RASTER ACTIVA — Consola QGIS
#  Pide cuántos píxeles quieres (1, 9, 25, 49…)
#  Retorna por cada uno: posición (col, fila), coordenadas e índice secuencial
# ============================================================

from qgis.core import QgsRasterLayer, QgsPointXY, QgsRaster
from math import floor, sqrt, ceil

# ── Función auxiliar: lado impar mínimo para contener N píxeles ──────────────
def lado_impar(n):
    """
    Devuelve el entero impar más pequeño L tal que L² >= n.
    Impar garantiza un píxel central exacto (sin ambigüedad).
    Ejemplos:  1→1,  4→3,  9→3,  10→5,  25→5,  26→7
    """
    L = ceil(sqrt(n))
    if L % 2 == 0:
        L += 1
    return L

# ── 1. Verificar capa activa ─────────────────────────────────────────────────
capa = iface.activeLayer()

if not capa or not isinstance(capa, QgsRasterLayer):
    print("⚠  No hay una capa raster activa. Selecciónala en el panel de capas.")
else:
    # ── 2. Pedir al usuario cuántos píxeles quiere ───────────────────────────
    try:
        n_input = 25
        if n_input < 1:
            raise ValueError
    except ValueError:
        print("⚠  Ingresa un número entero positivo.")
        n_input = None

    if n_input:
        # ── 3. Calcular tamaño del bloque cuadrado ───────────────────────────
        lado   = lado_impar(n_input)        # lado del bloque (siempre impar)
        total  = lado * lado                # píxeles reales que se reportarán
        radio  = lado // 2                  # píxeles a cada lado del centro

        if total != n_input:
            print(f"\n  ℹ  {n_input} no forma un cuadrado de lado impar.")
            print(f"     Se usará un bloque {lado}×{lado} = {total} píxeles (el mínimo cuadrado impar ≥ {n_input}).")

        # ── 4. Dimensiones y resolución del raster ───────────────────────────
        ncols  = capa.width()
        nfilas = capa.height()
        ext    = capa.extent()
        res_x  = capa.rasterUnitsPerPixelX()
        res_y  = capa.rasterUnitsPerPixelY()

        # ── 5. Píxel central del raster ──────────────────────────────────────
        col_c  = floor((ncols  - 1) / 2)
        fila_c = floor((nfilas - 1) / 2)

        # Verificar que el bloque cabe dentro del raster
        if col_c - radio < 0 or col_c + radio >= ncols or \
           fila_c - radio < 0 or fila_c + radio >= nfilas:
            print(f"\n⚠  El raster ({ncols}×{nfilas}) es demasiado pequeño "
                  f"para un bloque {lado}×{lado}.")
        else:
            proveedor = capa.dataProvider()

            # ── 6. Cabecera del reporte ──────────────────────────────────────
            sep  = "─" * 72
            sep2 = "┄" * 72
            print(f"\n{sep}")
            print(f"  Capa       : {capa.name()}")
            print(f"  SRC        : {capa.crs().authid()}")
            print(f"  Tamaño     : {ncols} cols × {nfilas} filas")
            print(f"  Resolución : {res_x:.6f} × {res_y:.6f} u/píxel")
            print(f"  Centro     : col {col_c}, fila {fila_c}")
            print(f"  Bloque     : {lado}×{lado}  ({total} píxeles, radio={radio})")
            print(sep)
            print(f"  {'#':>4}  {'Col':>6}  {'Fila':>6}  {'Índice seq.':>12}  "
                  f"{'Coord X':>18}  {'Coord Y':>18}  {'Valor B1':>12}")
            print(sep2)

            # ── 7. Iterar sobre el bloque (fila exterior, col interior) ──────
            num = 1
            for df in range(-radio, radio + 1):       # desplazamiento en fila
                for dc in range(-radio, radio + 1):   # desplazamiento en col
                    col  = col_c  + dc
                    fila = fila_c + df

                    # Coordenadas del centro del píxel
                    cx = ext.xMinimum() + (col  + 0.5) * res_x
                    cy = ext.yMaximum() - (fila + 0.5) * res_y

                    # Índice secuencial
                    idx = fila * ncols + col

                    # Valor del píxel (banda 1)
                    res = proveedor.identify(QgsPointXY(cx, cy),
                                             QgsRaster.IdentifyFormatValue)
                    val = res.results().get(1, "N/D")

                    # Marcar el centro exacto
                    marca = " ◀ centro" if dc == 0 and df == 0 else ""

                    print(f"  {num:>4}  {col:>6}  {fila:>6}  {idx:>12}  "
                          f"{cx:>18.6f}  {cy:>18.6f}  {str(val):>12}{marca}")
                    num += 1

            print(sep)
            print(f"  Total reportado: {total} píxeles  |  "
                  f"Bloque: cols [{col_c-radio}…{col_c+radio}]  "
                  f"filas [{fila_c-radio}…{fila_c+radio}]")
            print(sep)

            # ── 8. (Opcional) Marcar todos los píxeles en el mapa ────────────
            #  Descomenta para ver los puntos sobre el canvas:
            #
            # from qgis.gui import QgsVertexMarker
            # from qgis.PyQt.QtGui import QColor
            # for df in range(-radio, radio + 1):
            #     for dc in range(-radio, radio + 1):
            #         cx = ext.xMinimum() + (col_c + dc + 0.5) * res_x
            #         cy = ext.yMaximum() - (fila_c + df + 0.5) * res_y
            #         m = QgsVertexMarker(iface.mapCanvas())
            #         m.setCenter(QgsPointXY(cx, cy))
            #         color = QColor(0, 200, 100) if dc == 0 and df == 0 else QColor(255, 140, 0)
            #         m.setColor(color)
            #         m.setIconSize(10)
            #         m.setIconType(QgsVertexMarker.ICON_CROSS)
            #         m.setPenWidth(2)