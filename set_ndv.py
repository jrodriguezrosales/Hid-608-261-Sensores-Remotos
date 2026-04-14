import platform                 # Se importa la libreria para detectar el SO
import subprocess               # Se importa la librería de subprocesos
layer = iface.activeLayer()     # Se identifica la capa activa de QGIS
                                # Se genera la línea de comando
ndv = 0                         # Se define el No Data Value
src = layer.source()
nme = layer.name()
if platform.system().upper()=='LINUX':
  cmd = "gdal_edit.py -a_nodata " + str(ndv) + " " + src
else:
  cmd = "gdal_edit.bat -a_nodata " + str(ndv) + " " + src
                                # Se ejecuta el comando
subprocess.run ([x for x in cmd.split(" ") if x != ""])

QgsProject.instance().removeMapLayer(layer)
layer = iface.addRasterLayer(src,nme,"gdal")
iface.mapCanvas().refresh()
