############################################################
# Script para generar una malla a partir de una
# capa raster de tipo Byte
# 
# Para usarlo, seleccione la capa y ejecute el script
#
# Autor: Felipe Pedraza Oropeza
# Fecha: 20-abril-2023 
############################################################
from qgis.PyQt.QtCore import QVariant
# Función para generar la malla
def gen_grd():
# Se define la capa activa
  layer = iface.activeLayer()
# Se checa que la capa activa sea válida
  if layer==None:
    return(1)
# Se checa que la capa activa sea de tipo raster
  if (layer.type()!=QgsMapLayerType.RasterLayer):
    return(2)
# Se checa que la capa activa tenga una sola banda
  if (layer.bandCount()!=1):
    return(3)
# Se checa que la capa activa tenga pixels cuadrados
  ps=layer.rasterUnitsPerPixelX()
  if (layer.rasterUnitsPerPixelX()!=ps):
    return(4)
# Se definen los datos de la capa
  provider = layer.dataProvider()
# Se define el extent, coordenadas extremas, de la capa
  extent = provider.extent()
# Se define el número de renglones
  rows = layer.height()
# Se define el número de columnas
  cols = layer.width()
# Se define el bloque de datos
  block = provider.block(1, extent, cols, rows)
# Se define el arreglo de bytes de la capa
  ba = bytes(block.data())
# Se genera la malla
  grd = QgsVectorLayer("Polygon", layer.name()+"_grd", "memory")
# Se le asigna el mismo sistema de coordenadas que el de la capa activa  
  grd.setCrs(layer.crs())
# Se definen los datos de la malla
  dp = grd.dataProvider()
# Se definen el atributo de la malla
  dp.addAttributes([QgsField("CLASE", QVariant.Int, len = 3)])
  grd.updateFields()
# Se procesan los bytes
  k = 0
  yf = extent.yMaximum()
  for i in range(rows):     # Se procesan los renglones
    xi = extent.xMinimum()
    yi = yf - ps
    for j in range(cols):   # Se procesan las columnas
      xf = xi + ps
      ft = QgsFeature()
      ft.setGeometry(QgsGeometry.fromRect(QgsRectangle(xi,yi,xf,yf)))
      ft.setAttributes([ba[k]])
      dp.addFeature(ft)
      xi=xf
      k +=1
    yf = yi  

# Se agrega la capa vectorial    
  grd.commitChanges()
  grd.updateExtents()
  QgsProject.instance().addMapLayer(grd)
  
err_code = gen_grd()
print(err_code)
