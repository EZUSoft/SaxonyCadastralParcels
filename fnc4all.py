# -*- coding: utf-8 -*-
"""
/***************************************************************************
 fnc4all
                                 A QGIS plugin
 CAIGOS-PostgreSQL/PostGIS in QGIS darstellen
                              -------------------
        begin                : 2016-04-18
        git sha              : $Format:%H$
        copyright            : (C) 2016 by EZUSoft
        email                : qgis (at) makobo.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from qgis.utils import os, sys
from PyQt4.QtCore import QSettings
from itertools import cycle, izip
from PyQt4.QtGui import QMessageBox,QApplication
from qgis.core import QgsMessageLog
import re
import time 
import os
import getpass
import traceback


def fncDebugMode(): 
    return False
    
glFehlerListe=[]
glHinweisListe=[]
def addFehler (Fehler): 
    if type(Fehler) == str:
        su=Fehler.decode("utf8")
    else:
        su=Fehler
    glFehlerListe.append (su)
def getFehler() :
    return glFehlerListe
def resetFehler() :
    global glFehlerListe
    glFehlerListe = []  
def addHinweis (Hinweis):
    if type(Hinweis) == str:
        su=Hinweis.decode("utf8")
    else:
        su=Hinweis
    glHinweisListe.append (su)
def getHinweis() :
    return glHinweisListe
def resetHinweis() :
    global glHinweisListe
    glHinweisListe = [] 


# unerwarteter LZF mit Sofortmeldung
""" Aufruf per:
except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    subLZF ("Irgendwas",exc_type, fname, exc_tb.tb_lineno)
"""
def subLZF(exc_type, fname, tb_lineno, Sonstiges = None):
    #http://stackoverflow.com/questions/1278705/python-when-i-catch-an-exception-how-do-i-get-the-type-file-and-line-number
    try:
        QgsMessageLog.logMessage( traceback.format_exc().replace("\n",chr(9))+ (chr(9) + Sonstiges) if Sonstiges else "", u'CaigosConnector:Fehler' )
    except:
        pass
    QMessageBox.critical( None,"PlugIn Laufzeitfehler" ,str(exc_type) + ": \nDatei: " + fname + "\nZeile: "+ str(tb_lineno) + ("\n" + Sonstiges) if Sonstiges else "")
    addFehler ("LZF:" + traceback.format_exc().replace("\n",chr(9)) + (chr(9) + Sonstiges) if Sonstiges else "")
    
def errbox (text,p=None):
    su=text
    if type(text) == str:
        su=text.decode("utf8")    
    QMessageBox.critical(None, "PlugIn Fehler", su)
    try:
        QgsMessageLog.logMessage( su, u'CaigosConnector:Fehler' )
    except:
        pass


def msgbox (text):
    su=text
    if type(text) == str:
        su=text.decode("utf8")    
    QMessageBox.information(None, "PlugIn Hinweis", su)
    try:
        QgsMessageLog.logMessage( su, u'CaigosConnector:Hinweise' )
    except:
        pass

def errlog(text,p=None):
    su=text
    if type(text) == str:
        su=text.decode("utf8")   
    if fncDebugMode():
        QMessageBox.information(None, "DEBUG:", su)
    
    try:
        QgsMessageLog.logMessage( su, u'CaigosConnector:Fehler' )
    except:
        pass



def debuglog(text,p=None):
    if fncDebugMode():
        su=text
        if type(text) == str:
            su=text.decode("utf8")   
        try:
            QgsMessageLog.logMessage( su, u'CaigosConnector:Debug' )
        except:
            pass

def fncBrowserID():
    s = QSettings( "EZUSoft", "CAIGOS-Konnektor" )
    s.setValue( "-id-", fncXOR(("CAIGOSConnektorID=%02i%02i%02i%02i%02i%02i") % (time.localtime()[0:6])) )
    return s.value( "–id–", "" ) 
    
def printlog(text,p=None):
    su=text
    if type(text) == str:
        su=text.decode("utf8")        
    try:
        print su
    except:
        try:
            print su.encode("utf-8")
        except:
            print "printlog:Fehler konnte nicht ausgegeben werden"

def fncKorrDateiName (OrgName,Ersatz="_"):
    NeuTex=""
    for i in range(len(OrgName)):
        if re.search("[/\\\[\]:*?|<>]",OrgName[i]):
            NeuTex=NeuTex+Ersatz
        else:
            NeuTex=NeuTex+OrgName[i]
    return NeuTex      

def fncDateCode():
    lt = time.localtime()
    return ("%02i%02i%02i") % (lt[0:3])  

def fncXOR(message, key=None):
    if key==None:
        key=fncDateCode()
    return  ''.join(("%0.1X" % (ord(c)^ord(k))).zfill(2) for c,k in izip(message, cycle(key)))


if __name__ == "__main__":
    addFehler ("ccc" )
    addFehler ("xxxx")
    print getFehler()
    resetFehler()
    print getFehler()




