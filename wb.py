############################################################
# Script para generar el Working Box de una capa vectorial,
# alineada a una capa raster
# 
# Para usarlo, carge las dos capas y ejecute en script
#
# Autor: Felipe Pedraza Oropeza
# Fecha: 02-marzo-2022 
############################################################

from qgis.PyQt.QtCore import QVariant
# Se inicializa el código de error
err_code=0
# Se define el porcentaje de los márgenes
mp=20.0
mc='red';

# Se genera el Working Box
def gen_wb():
# Se define err_code como variable global
  global err_code
# Se asignan las capas visibles
  layers = qgis.utils.iface.mapCanvas().layers()
# Se verifica que hayan dos capas visibles
  if len(layers)!=2:
    err_code=1
    return()
# Se verifica que las primera capa sea de tipo vectorial
  if (layers[0].type()!=QgsMapLayerType.VectorLayer):
    err_code=2
    return()
# Se verifica que las segunda capa sea de tipo raster
  if (layers[1].type()!=QgsMapLayerType.RasterLayer):
    err_code=3
    return()
# Se verifica que las dos capas tengan el mismo CRS
# (Coordinate Reference System)
  if (layers[0].crs()!=layers[1].crs()):
    err_code=4
    return()
# Se verifica que la capa raster tenga pixels cuadrados
  ps=layers[1].rasterUnitsPerPixelX()
  if (layers[1].rasterUnitsPerPixelY()!=ps):
    err_code=5
    return()
# Se verifica que la capa raster contenga a la vectorial
  rex=layers[1].dataProvider().extent()
  if (not rex.contains(layers[0].dataProvider().extent())):
    err_code=6
    return()
# Se obtienen las coordenadas extremas de la capa vectorial
  vext=layers[0].extent()
# Se obtienen las coordenadas extremas de la capa raster
  rext=layers[1].extent()
# Se cnvierte el margen en porcentaje a decimal
  dm=mp/100.0
# Se calcula el márgen horizontal
  hm=(vext.xMaximum()-vext.xMinimum())*dm
# Se calcula el márgen vertical
  vm=(vext.yMaximum()-vext.yMinimum())*dm
# Se calculan las coordenadas extremas del WorkingBox
  xmin=vext.xMinimum()-hm
  xmin=math.floor((xmin-rext.xMinimum())/ps)*ps
  xmin=rext.xMinimum()+xmin
  xmax=vext.xMaximum()+hm
  xmax=math.ceil((xmax-rext.xMinimum())/ps)*ps
  xmax=rext.xMinimum()+xmax

  ymin=vext.yMinimum()-vm
  ymin=math.ceil((rext.yMaximum()-ymin)/ps)*ps
  ymin=rext.yMaximum()-ymin
  ymax=vext.yMaximum()+vm
  ymax=math.floor((rext.yMaximum()-ymax)/ps)*ps
  ymax=rext.yMaximum()-ymax
# Se genera la capa vectorial del WorkingBox
  vl=QgsVectorLayer("Polygon", "wb-"+str(int(mp))+"-"+str(int(ps)), "memory")
  vl.setCrs(layers[0].crs())
# Se define la simbología
  props = { 'color_border' : mc, 'style' : 'no', 'style_border' : 'solid' }
  symbol = QgsFillSymbol.createSimple(props)
  vl.renderer().setSymbol(symbol)
# Se definen los campos  
  dp=vl.dataProvider()
  dp.addAttributes([QgsField("VECTOR", QVariant.String, len = len(layers[0].name())),
                    QgsField("RASTER", QVariant.String, len = len(layers[1].name())),
                    QgsField("MARGEN", QVariant.Double, len = 6, prec = 2)])
  vl.updateFields()
# Se genera el WorkingBox  
  ft=QgsFeature()
# Se asigna la geometría y los atributos del WorkingBox 
  ft.setGeometry(QgsGeometry.fromRect(QgsRectangle(xmin,ymin,xmax,ymax)))
  ft.setAttributes([layers[0].name(),layers[1].name(), mp])
  dp.addFeature(ft)
# Se agrega la capa vectorial    
  vl.commitChanges()
  vl.updateExtents()
  QgsProject.instance().addMapLayer(vl)

r=gen_wb()
if err_code==0:
  print("OK")
elif err_code==1:
  print("ERROR: Número de capas visibles diferente de 2")
elif err_code==2:
  print("ERROR: La primera capa no es vectorial")
elif err_code==3:
  print("ERROR: La segunda capa no es raster")
elif err_code==4:
  print("ERROR: Las capas tienen diferente CRS")
elif err_code==5:
  print("ERROR: La capa raster no tiene pixels cuadrados")
elif err_code==6:
  print("ERROR: Las capa vectorial no está contenida en la capa raster")
