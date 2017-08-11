# -*- coding: utf-8 -*-
"""
/***************************************************************************
 clsWorker

                                 A QGIS plugin
 Download Flurstücke vom GeoSN, ADarstellung QGIS und Konvertierung nach DXF
                             -------------------
        begin                : 2017-08-08
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Mike Blechschmidt EZUSoft 
        email                : qgis@makobo.de
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

from random import randrange
import sys
from PyQt4.QtGui import *
from qgis.core import *

from qgis.utils import *
from fnc4all import *

import uuid
from PyQt4.QtCore import Qt
from PyQt4 import QtGui, uic
from PyQt4.QtSql import QSqlDatabase, QSqlQuery, QSqlError
from glob import glob
from shutil import copyfile, move, rmtree
import urllib
import zipfile

"""
# 23.02.17
# Processing erst in den Funktionen selbst laden, um den Start von QGIS zu beschleunigen
import processing
from processing.core.Processing import Processing
"""

def tr( message):
    """Get the translation for a string using Qt translation API.

    We implement this ourselves since we do not inherit QObject.

    :param message: String for translation.
    :type message: str, QString

    :returns: Translated version of message.
    :rtype: QString
    """
    # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
    return message #QCoreApplication.translate('clsWorker', message)


def zipDownload(key4download):
    # Schlüsselaufbau: url<tab>zipname
    dat = key4download.split(chr(9))

    lok=EZUTempDir()
    try:
        urllib.urlretrieve ( dat[0],lok+dat[1])
        return lok+dat[1]
    except:
        addFehler ("Fehler download Gemarkung: " + dat[1])
        return None

def unzipShape(unzipdir, zipdat, ShapePfad, ShapeName):
    try:
        if not os.path.exists(unzipdir):
            os.makedirs(unzipdir) 
        if not ClearDir(unzipdir):
            addFehler (unzipdir + ': ' + "konnte nicht geleert werden")
            return False
        
        zip_ref = zipfile.ZipFile(zipdat, 'r')
        zip_ref.extractall(unzipdir)
        zip_ref.close()
    except:
        addFehler (zipdat + ': UnZip fehlgeschlagen')
        return False
    
    Anz=0
    # 1. Flurstücke
    ShpKern="INSPIRE_cpParcelS"
    for FAktDat in glob(unzipdir + ShpKern + '.*'):
        AktDat = os.path.basename(FAktDat)
        NeuDat=ShapePfad + AktDat.replace(ShpKern,ShapeName + '(Flst)')
        copyfile(FAktDat,NeuDat)
        Anz+=1
    # 2. Gemarkung
    ShpKern="INSPIRE_cpZoningS"
    for FAktDat in glob(unzipdir + ShpKern + '.*'):
        AktDat = os.path.basename(FAktDat)
        NeuDat=ShapePfad + AktDat.replace(ShpKern,ShapeName + '(Gem)')
        copyfile(FAktDat,NeuDat)
        Anz+=1               
    return True

def dxf4FlNum (x,y,txt,handle):
    must= (
"MTEXT"+ '\n'
"  5"+ '\n'
"%s"+ '\n'
"330"+ '\n'
"1"+ '\n'
"100"+ '\n'
"AcDbEntity"+ '\n'
"  8"+ '\n'
"Flurstuecksnummer"+ '\n'
" 62"+ '\n'
"     7"+ '\n'
"370"+ '\n'
"     9"+ '\n'
"100"+ '\n'
"AcDbMText"+ '\n'
" 10"+ '\n'
"%s"+ '\n'
" 20"+ '\n'
"%s"+ '\n'
"  1"+ '\n'
"\\fMS Shell Dlg 2|i0|b0;\\H2.58759;%s " + '\n'
" 50"+ '\n'
"0.0"+ '\n'
" 41"+ '\n'
"8.17412830097370957"+ '\n'
" 71"+ '\n'
"     5"+ '\n'
"  7"+ '\n'
"STANDARD"+ '\n'
"  0" + '\n') % (handle,x,y,txt)
    return must

def concatDXF(GemDxfDat,FlDxfDat,FlCsvDat):
    DxfDat = EZUTempDir() + 'generierte.dxf'
    if os.path.isfile(DxfDat):
        os.remove(DxfDat)
    fDxfDat    = open(DxfDat, "w")
    fGemDxfDat = open(GemDxfDat, "r")
    fFlDxfDat  = open(FlDxfDat, "r")
    fFlCsvDat  = open(FlCsvDat, "r")
    
    StartFlENT = False
    h=0
    for Zeile in fFlDxfDat:
    # Ausgangspunkt ist die GemarkungsDXF
    # 1. Einbau der Layerdefinitionen
    # 2. Einbau der Gemarkungsgrenze
    # 3. Generieren der DXFTexte
        if Zeile[0:8] == "ENTITIES":
           StartFlENT = True
        if Zeile[0:10] == "LWPOLYLINE" and StartFlENT:
            h=0
        h=h+1
        if h==3:
            handle=Zeile[0:-1]
        if Zeile[0:6] == "ENDSEC" and StartFlENT:
            StartFlENT = False
            # jetzt kann geschrieben werden
            # 1. Gemarkung
            handle = int(handle,16)+10 # hexa in dezimal 
            StartGemENT = 0
            gh=0
            for xZeile in fGemDxfDat:
                if xZeile[0:8] == "ENTITIES":
                   StartGemENT = 1
                if StartGemENT > 0:
                    StartGemENT = StartGemENT + 1
                if StartGemENT > 3:
                    if xZeile[0:6] == "ENDSEC":
                        break
                    if xZeile[0:10] == "LWPOLYLINE": 
                        gh=0
                    gh=gh+1
                    if gh == 3:
                        fDxfDat.write (str(hex(handle))[2:]+'\n')
                        handle = handle + 1
                    else:
                        fDxfDat.write (xZeile)
            # 2. Flurstücksnummern
            z=0
            for xZeile in fFlCsvDat:
                z=z+1
                if z > 1 :
                    xZeile=xZeile[0:-1].split(chr(9))
                    fDxfDat.write (dxf4FlNum(xZeile[0],xZeile[1],xZeile[3], str(hex(handle))[2:]))
                    handle = handle + 1
                
        fDxfDat.write (Zeile)
    fDxfDat.close()
    fGemDxfDat.close()
    fFlDxfDat.close()
    fFlCsvDat.close()
    return DxfDat
    
def genDXF4Gemarkung (uiParent,unzipDir, dxfDatNam):
    # Processing erst hier Laden, um den Start von QGIS zu beschleunigen
    import processing
    from processing.core.Processing import Processing
    uiParent.SetEinzelAktionText(tr("Generiere DXF Daten"))
    uiParent.SetEinzelAktionAktSchritt(3)

    korrDXFDatNam=(EZUTempDir() + str(uuid.uuid4()))
    # 1. Gemarkung
    korrSHPDatNam=(unzipDir + "INSPIRE_cpZoningS.shp")
    opt = '-dialect sqlite -sql "SELECT \'Gemarkungsgrenze\' as Layer, ST_ExteriorRing(geometry) from INSPIRE_cpZoningS"'
    if processing.runalg('gdalogr:convertformat', korrSHPDatNam , 10, opt , korrDXFDatNam  + '_1.dxf') is None:
        errbox ('Fehler')
        addFehler(tr("process 'gdalogr:convertformat' could not start please restart QGIS"))
    
    # 2. Flurstücke
    korrSHPDatNam=(unzipDir + "INSPIRE_cpParcelS.shp")
    # 2.1. Flurstücksgrenzen
    opt = '-dialect sqlite -sql "SELECT \'Flurstuecksgrenze\' as Layer, ST_ExteriorRing(geometry) from INSPIRE_cpParcelS"'
    if processing.runalg('gdalogr:convertformat', korrSHPDatNam , 10, opt , korrDXFDatNam  + '_2.dxf') is None:
        errbox ('Fehler')
        addFehler(tr("process 'gdalogr:convertformat' could not start please restart QGIS"))
        
    # 3. Flurstücksnummern
    # 2.1. Flurstücksnummern
    opt = '-lco SEPARATOR=TAB -lco GEOMETRY=AS_XYZ -dialect sqlite -sql "SELECT ST_PointOnSurface(geometry), LABEL from INSPIRE_cpParcelS"'

    if processing.runalg('gdalogr:convertformat', korrSHPDatNam , 12, opt , korrDXFDatNam  + '_3.csv') is None:
        errbox ('Fehler')
        addFehler(tr("process 'gdalogr:convertformat' could not start please restart QGIS"))
    
    uiParent.SetEinzelAktionText(tr("Erzeuge DXF Datei"))
    uiParent.SetEinzelAktionAktSchritt(4)   
    tmpDat = concatDXF(korrDXFDatNam  + '_1.dxf',korrDXFDatNam  + '_2.dxf', korrDXFDatNam  + '_3.csv')
    #print (tmpDat, dxfDatNam ) 
    # hier gab es mit move ab und zu probleme
    # deshalb kopieren und anschließend löschen
    copyfile (tmpDat, dxfDatNam )
    try:
        os.remove(tmpDat)
    except: 
        pass
 
def delUnzipIfUcan():
    tmp=EZUTempDir()
    for verz in glob(tmp +'*.unzip'):
        try:
            rmtree(verz)
        except:
            pass
    
    
def GemWorker(uiParent,listZIPDatNam,expPfad, bSHPSave, bDXFSave):    
    # Processing erst hier Laden, um den Start von QGIS zu beschleunigen
    import processing
    from processing.core.Processing import Processing
    
    # -----------------------------------------------------------------------------------------------    
    qgisRootName="EZUFlurst4SN"   
    # 1. Root erzeugen, wenn noch nicht vorhanden
    rNode=QgsProject.instance().layerTreeRoot()
    root4Gem = None
    for node in rNode.children(): # oberste Ebene in Schleife durchlaufen
        if str(type(node))  == "<class 'qgis._core.QgsLayerTreeGroup'>":
            if node.name() == qgisRootName:
                root4Gem = node
    if root4Gem is None:
        root4Gem = rNode.addGroup(qgisRootName)
    root4Gem.setExpanded(True)    

    if bSHPSave:
        AktShapePfad = expPfad
    else:
        AktShapePfad = EZUTempDir()

    # -----------------------------------------------------------------------------------------------   
    # Initialisierung    
    # manchmal bleibt (bei mehrfachnutzung oder bei crash) irgend etwas hängen,
    # die beiden nachfolgenden Zeilen haben bei einem Test das Problem gefixt - konnte aber noch nicht wiederholt werden
    # recht zeitaufwändig
    uiParent.FormRunning(True)
    uiParent.SetEinzelAktionText("")
    uiParent.SetDatAktionText(tr("process init - please wait"))

    Processing.initialize()
    Processing.updateAlgsList()

    # -----------------------------------------------------------------------------------------------    
    # 3. Abarbeitung der Dateien
    i=0
    uiParent.SetDatAktionGesSchritte(len(listZIPDatNam))
    chkurl="http://www.makobo.de/links/GemList_SaxonyCadastralParcels.php?" + fncBrowserID() + "|" + str(len(listZIPDatNam)).strip()
    
    StepCount4Datei = 2
    if  bSHPSave:
        StepCount4Datei = StepCount4Datei + 1
    if  bDXFSave:
        StepCount4Datei = StepCount4Datei + 3
    try:
        urllib.urlretrieve (chkurl,EZUTempDir()+'test.zip')
    except:
        pass
    for dat in listZIPDatNam:
        if not uiParent.isRunning():
            msgbox ("Nutzerabbruch")
            return False
        
        uiParent.SetEinzelAktionGesSchritte(StepCount4Datei)      
        uiParent.SetEinzelAktionAktSchritt(0) 
        i=i+1
        # Schlüsselaufbau: url<tab>zipname
        AktGemName = dat.split(chr(9))[1]   
        AktGemName = AktGemName[0:-4]
        uiParent.SetDatAktionText(tr("Import Gemarkung: " + AktGemName))
        uiParent.SetDatAktionAktSchritt(i)

        if bSHPSave:
            AktShapeName = AktGemName
        else:
            AktShapeName = str(uuid.uuid4())    
        
        # ===============================
        # 0. Eventuelle QGIS-Einbindung löschen
        for node in root4Gem.children():
            if str(type(node))  == "<class 'qgis._core.QgsLayerTreeGroup'>":
                if node.name() == AktGemName:
                        root4Gem.removeChildNode(node)
        
        # 1. Download
        uiParent.SetEinzelAktionAktSchritt(1)
        uiParent.SetEinzelAktionText(tr("Download ZIP-Archiv vom GeoSN Server"))
        lokzip=zipDownload(dat)
        if lokzip is None:
            continue
            
        #lokzip="d:/Flurst4SN/" + dat.split(chr(9))[1]
        

        uiParent.SetEinzelAktionAktSchritt(2)
        uiParent.SetEinzelAktionText(tr("Verarbeite ZIP-Archiv"))

        # 2. Unzip
        # immer neues Verzeichnis, da vom Processing die Dateien manchmal gesperrt werden
        # außerdem der Versuch die alten aufzuräumen
        delUnzipIfUcan()
        unzipdir = EZUTempDir() + str(uuid.uuid4()) + ".unzip/"
        if not unzipShape(unzipdir, lokzip, AktShapePfad, AktShapeName):
            continue
        # 3. QGIS Darstellung kopieren
        qmlDat = os.path.dirname(__file__) + "/FlurstueckeAusSachsenShape.qml"
        copyfile(qmlDat, AktShapePfad + AktShapeName + '(Flst).qml')
        qmlDat = os.path.dirname(__file__) + "/GemarkungAusSachsenShape.qml"
        copyfile(qmlDat, AktShapePfad + AktShapeName + '(Gem).qml')     
        
        # 4. DXF erzeugen
        if bDXFSave:
            genDXF4Gemarkung (uiParent, unzipdir, expPfad + AktGemName + '.dxf')
        
        # 5. Shape in QGIS einbinden
        gemNode = root4Gem.addGroup(AktGemName)
        # 5.1. Flurstücke
        flLayer = QgsVectorLayer(AktShapePfad + AktShapeName + '(Flst).shp', u"Inspire Flurstücke","ogr")
        if myqtVersion == 4:
            QgsMapLayerRegistry.instance().addMapLayer(flLayer, False)
        else:
            QgsProject.instance().addMapLayer(flLayer,False) # ungetestet
        gemNode.insertLayer(0, flLayer)

        # 5.2. Gemarkung
        gemLayer = QgsVectorLayer(AktShapePfad + AktShapeName + '(Gem).shp', u"Inspire Gemarkung","ogr")
        if myqtVersion == 4:
            QgsMapLayerRegistry.instance().addMapLayer(gemLayer, False)
        else:
            QgsProject.instance().addMapLayer(gemLayer,False) # ungetestet
        gemNode.insertLayer(0, gemLayer)


    if len(getFehler()) > 0:
        errbox("\n\n".join(getFehler()))
        resetFehler()
    if len(getHinweis()) > 0:
        hinweislog("\n\n".join(getHinweis()))
        resetHinweis()        

    uiParent.FormRunning(False)
        

if __name__ == "__main__":
    dummy=0
    delUnzipIfUcan()
    """
    GemDxfDat="d:/tar/shp/8d2bf7e9-27bb-4a0c-8708-b3329b3c1077_1.dxf"
    FlDxfDat="d:/tar/shp/8d2bf7e9-27bb-4a0c-8708-b3329b3c1077_2.dxf"
    FlCsvDat="d:/tar/shp/8d2bf7e9-27bb-4a0c-8708-b3329b3c1077_3.csv"
    concatDXF(GemDxfDat,FlDxfDat,FlCsvDat)
    #KorrPrjDat ("d:/tar/x.dxf(GC)L.prj")
    zipdat="d:/tar/Gemarkung_Erlabrunn (7406).zip"
    ShapePfad="d:/tar/37/"
    ShapeName="Gemarkung_Erlabrunn (7406)"
    """
    #print unzipShape(zipdat, ShapePfad, ShapeName)