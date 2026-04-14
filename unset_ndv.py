import platform                 # Se importa la libreria para detectar el SO
import subprocess               # Se importa la librería de subprocesos
layer = iface.activeLayer()     # Se identifica la capa activa de QGIS
                                # Se genera la línea de comando
src = layer.source()
nme = layer.name()
if platform.system().upper()=='LINUX':
  cmd = "gdal_edit.py -unsetnodata "+src
else:
  cmd = "gdal_edit.bat -unsetnodata "+src
                                # Se ejecuta el comando
subprocess.run ([x for x in cmd.split(" ") if x != ""])

QgsProject.instance().removeMapLayer(layer)
layer = iface.addRasterLayer(src,nme,"gdal")
iface.mapCanvas().refresh()