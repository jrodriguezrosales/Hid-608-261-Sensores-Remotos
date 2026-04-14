from qgis.core import QgsProject, QgsGeometry, QgsPointXY, QgsWkbTypes
from qgis.utils import iface

#función que selecciona poligonos del borde
def seleccionar_poligonos_borde():
    # 1. Obtener la capa activa
    layer = iface.activeLayer()
    
    if not layer:
        print("Error: No hay capa seleccionada.")
        return

    # 2. Obtener las coordenadas del rectángulo envolvente (extent)
    ext = layer.extent()
    xmin = ext.xMinimum()
    xmax = ext.xMaximum()
    ymin = ext.yMinimum()
    ymax = ext.yMaximum()

    # 3. Construir la geometría de LÍNEA del borde manualmente
    # Creamos una lista de puntos que recorren el rectángulo y lo cierran
    puntos_borde = [
        QgsPointXY(xmin, ymin),
        QgsPointXY(xmax, ymin),
        QgsPointXY(xmax, ymax),
        QgsPointXY(xmin, ymax),
        QgsPointXY(xmin, ymin) # Volvemos al inicio para cerrar
    ]
    
    boundary_geom = QgsGeometry.fromPolylineXY(puntos_borde)
    
    # 4. Crear un buffer (margen) pequeño
    # Al ser UTM (metros), usamos 0.1m para asegurar que detecte el contacto
    boundary_buffer = boundary_geom.buffer(0.1, 5)

    edge_polygons_ids = []
    
    print("Analizando geometría...")

    # 5. Iterar y buscar intersecciones
    # Usamos getFeatures() para recorrer todo
    for feature in layer.getFeatures():
        geom = feature.geometry()
        
        # Si la geometría es válida y toca nuestro buffer del borde
        if geom and geom.intersects(boundary_buffer):
            edge_polygons_ids.append(feature.id())

    # 6. Resultados y Selección
    count = len(edge_polygons_ids)
    
    # Limpiar selección previa
    layer.removeSelection()
    
    if count > 0:
        layer.selectByIds(edge_polygons_ids)
        print("-" * 30)
        print(f"ÉXITO: Se encontraron {count} polígonos externos.")
        print("Se han seleccionado en amarillo en el mapa.")
        print("-" * 30)
    else:
        print("No se encontraron polígonos que toquen el borde.")

# Ejecutar la función
seleccionar_poligonos_borde()