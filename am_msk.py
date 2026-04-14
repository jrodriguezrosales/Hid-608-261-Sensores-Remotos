# Función para calcular la regresión lineal simple
# de dos bandas contenidas en un stack-layer
err_code=0
# Se definen las bandas roja e infraroja cercana
pband=1
def get_slr():
# Se define err_code como variable global
  global err_code
# Se asignan las capas visibles
  layers = qgis.utils.iface.mapCanvas().layers()
# Se verifica que hayan dos capas visibles
  if len(layers)!=2:
    err_code=1
    return()
# Se verifica que las dos capas sean de tipo raster
  ok=QgsMapLayerType.RasterLayer
  if (layers[1].type()!=ok)or(layers[0].type()!=ok):
    err_code=2
    return()
# Se verifica que las dos capas tengan el mismo CRS
# (Coordinate Reference System)
  if (layers[1].crs()!=layers[0].crs()):
    err_code=3
    return()
# Se verifica la capa RED
  maxb=layers[1].bandCount()
  if (pband<0)or(pband>maxb):
    err_code=4
    return()
# Se verifica que la máscar tenga una sola banda
  if (layers[0].bandCount()!=1):
    err_code=6
    return()
# Se verifica que las dos capas tengan la misma extensión
  if (layers[1].extent()!=layers[0].extent()):
    err_code=7
    return()
# Se verifica que las dos capas tengan el mismo ancho
  if (layers[1].width()!=layers[0].width()):
    err_code=8
    return()
# Se verifica que las dos capas tengan la misma altura
  if (layers[1].height()!=layers[0].height()):
    err_code=9
    return()
  ext = layers[1].extent()
  rc = layers[1].height()
  cc = layers[1].width()
  red = layers[1].dataProvider().block(pband, ext, cc, rc)
  msk = layers[0].dataProvider().block(1, ext, cc, rc)
  n=0
  sx=0.0
  sy=0.0
  sxx=0.0
  syy=0.0
  sxy=0-0
  for i in range(rc):
    for j in range(cc):
      if msk.value(i,j)==1:
        x=red.value(i,j)
        sx+=x
        n+=1
  if n>0:
    return([n, sx/n])
  else:  
    err_code=10
    return()

r=get_slr()
if err_code==0:
  msk=qgis.utils.iface.mapCanvas().layers()[0].name()
  print("msk=%s n=%d AM=%0.15f"%(msk,r[0],r[1]))
elif err_code==1:
  print("ERROR: Número de capas visibles diferente de 2")
elif err_code==2:
  print("ERROR: No hay dos capas de tipo raster")
elif err_code==3:
  print("ERROR: Las capas tienen diferente CRS")
elif err_code==4:
  print("ERROR: Capa RED fuera de rango")
elif err_code==5:
  print("ERROR: Capa NIR fuera de rango")
elif err_code==6:
  print("ERROR: La máscara no es monobanda")
elif err_code==7:
  print("ERROR: Las dos capas no tienen la misma extension")
elif err_code==8:
  print("ERROR: Las dos capas no tienen el mismo ancho")
elif err_code==9:
  print("ERROR: Las dos capas no tienen la misma altura")
elif err_code==10:
  print("ERROR: No se encontraron datos para la regresión (n==0)")
