# -*- coding: utf-8 -*-     # SE DEFINE LA CODIFICACIÓN UTF-8
#################################################################
# SCRIPT PARA GENERAR EL NOMBRE CORTO DE UNA IMAGEN LANDSAT     #
#                                                               #
# PARA UTILIZARLO COPIE EL NOMBRE COMPLETO DE LA IMAGEN, EN     # 
# NOTEPAD++, ASRGÚRESE QUE EL CURSOR ESTÁ EN LA MISMA LÍNEA QUE #
# EL NOMBRE Y EJECÚTELO EL COMANDO:                             #
# Plugins/Python Script/Scripts/L8-9_sn                         #
#################################################################
import os                   # Se importa la libreria del sistema operativo
from Npp import *			# Se importa la librería Npp

l = editor.getCurLine()	    # Se copia la línea actual (donde está el cursor)
fn, fe = os.path.splitext(l)# Se separan el nombre y la extensión
editor.documentEnd()		# Se posiciona el cursor al fin del documento
editor.newLine()			# Se genera una nueva línea
ini = editor.getLength()	# Se respalda el fin del documento
                            # Se Agrega el nombre corto
editor.addText(l[17:25]+"_"+l[0]+l[3]+"_"+l[11:13]+l[14:16]+"_"+l[6]+l[36]+l[39])
if fn[-2:].upper()=="QB":
  editor.addText("_QB")
elif fn[-2:].upper()=="B1":
  editor.addText("_1CAS")
elif fn[-2:].upper()=="B2":
  editor.addText("_2BLE")
elif fn[-2:].upper()=="B3":
  editor.addText("_3GRN")
elif fn[-2:].upper()=="B4":
  editor.addText("_4RED")
elif fn[-2:].upper()=="B5":
  editor.addText("_5NIR")
elif fn[-2:].upper()=="B6":
  editor.addText("_6SW1")
elif fn[-2:].upper()=="B7":
  editor.addText("_7SW2")
elif fn[-2:].upper()=="B8":
  editor.addText("_8PCM")
fin = editor.getLength()	# Se respalda el nuevo fin del documento
editor.setSel(ini,fin)		# Se selecciona el texto agregado
editor.copy()			    # Se copia el texto seleccionado
del l, fn, fe, ini, fin     # Se eliminan las variables utilizadas
