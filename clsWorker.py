# -*- coding: utf-8 -*-
"""
/***************************************************************************
 clsWorker
 30.07.18:
    Tabellennamen (Dateinamen) für sqlite maskiert: from \\\"' + Layer + '\\\""'
                                 A QGIS plugin
 Download Flurstücke Sachsen und Thüringen, Darstellung in QGIS und Konvertierung nach DXF
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
import uuid
# das einladen führt zu komischen Umlautfehlern im QGIS!!!!!
#from qgis.utils import *
from qgis.core import *
from glob import glob
import shutil 
import urllib
import zipfile
from itertools import cycle
import binascii
import re

try:
    from PyQt5 import QtGui
    from PyQt5.QtCore import QSettings
    from PyQt5.QtWidgets import QApplication,QMessageBox
    from urllib.request import urlretrieve 
    myqtVersion = 5
except:
    from PyQt4.QtGui import *
    from PyQt4.QtCore import Qt
    from PyQt4 import QtGui, uic
    from urllib import urlretrieve 
    myqtVersion = 4

try:
    from fnc4all import *
except:
    from .fnc4all import *

"""
# 23.02.17
# Processing erst in den Funktionen selbst laden, um den Start von QGIS zu beschleunigen
import processing
from processing.core.Processing import Processing
"""

try:
    from fnc4SaxonyCadastralParcels import *
except:
    from .fnc4SaxonyCadastralParcels import *

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

ixZipName=0;ixDatKuerz=1;ixQName=2;ixLName=3;ixDXFFarbe=4;ixF2L=5;ixLabel=6;ixLHoe=7;ixBName=8
def fncShapeDaten (sLandKenn):
    # Layer "Datenbank"
    #    0          1          2               3               4            5                       6                       7               8
    # zipname, dateikürzel, NameImQGISBaum, LayernameInDXF, DXFFarbe, "FlächeNachLinie", Optional: Beschriftung, Optional: Höhe, Optional: BeschLayer
    if sLandKenn == "SN": # in Sachsen sind die Dateinamen fest (ab 01.06.18 Name mit Punkt INSPIRE_cpParcelS --> INSPIRE.cpParcelS)
        allshpList=[
            ['INSPIRE.cpParcelS','(Flst)',u'Flurstück','Flurstuecksgrenze', None, True, 'LABEL as Beschr',3,'Flurstuecksnummer']
            ,
            ['INSPIRE.cpZoningS','(Gem)','Gemarkung','Gemarkungsgrenze', None, True, 'LABEL as Beschr',50,'Gemarkungsname']
            ,
            ['INSPIRE_cpParcelS','(Flst)',u'Flurstück','Flurstuecksgrenze', None, True, 'LABEL as Beschr',3,'Flurstuecksnummer']
            ,
            ['INSPIRE_cpZoningS','(Gem)','Gemarkung','Gemarkungsgrenze', None, True, 'LABEL as Beschr',50,'Gemarkungsname']
        ]
    if sLandKenn == "TH": # in den Thüringer Dateinamen sind GemSchl und Flurnummer enthalten
        allshpList=[
            ['*_gebaeudeBauwerk','(Geb)',u'Gebäude','Gebaeude', '12497369' , False]
            ,  
            ['*_katasterBezirk', '(Gem)','Gemarkung','Gemarkungsgrenze', None, True, "art || ': ' || ueboname as Beschr",50,'Gemarkungsname']
            , 
            ['*_flurstueck','(Flst)',u'Flurstück','Flurstuecksgrenze', None, True, 'flurstnr as Beschr',3,'Flurstuecksnummer']
        ] #,['*_nutzungFlurstueck','(Nutz)',u'Nutzung','Nutzung', True]] 
    return allshpList

def zipDownload(url,zipname):
    lok=EZUTempDir()
    # 14.02.18: In Thüringen klappt der Download oft erst im 2. Versuch
    #           obwohl ein Fehler kommt, hat der Download bei Tests trotzdem funktioniert
    #           --> nur Fehler werfen, wenn beim 2. Versuch die Datei nicht da
    try:
        urlretrieve ( url,lok+zipname)
        return lok+zipname
    except:
        pass
    try:
        urlretrieve ( url,lok+zipname)
        if fncDebugMode():
            addHinweis ("Download Gemarkung im 2. Versuch: " + zipname)
        return lok+zipname
    except:  
        if not os.path.isfile(lok+zipname):
            addFehler ("Fehler download Gemarkung: " + zipname)
            return None
        else:
            if fncDebugMode():
                addHinweis ("Download beim Gemarkung - Datei trotzdem vorhanden: " + zipname)
            return lok+zipname
            
def DownloadLand2Array (ansiDatName):
    #qDatName=ansiDatName.decode("cp1252").encode('utf-8')
    qDatName=bytearray(ansiDatName, 'utf-8').decode("cp1252")
    unzipdir = EZUTempDir() + "/unzip/"
    datDatName = unzipdir + qDatName
    zipDatName = unzipdir + qDatName + ".zip"
    url="http://www.makobo.de/data/" + qDatName + ".zip"
    try:
        if not os.path.exists(unzipdir):
            os.makedirs(unzipdir) 
        if not ClearDir(unzipdir):
            addFehler (unzipdir + ': ' + "konnte nicht geleert werden")
            return False
        if os.getenv('COMPUTERNAME') == 'PK811':
            shutil.copyfile('D:/Flurst4SNTH.zip/'+qDatName + ".zip",zipDatName)
        else:
            urlretrieve ( url,zipDatName)
        
        if not os.path.isfile(zipDatName):
            addFehler (zipDatName + ': download ist fehlgeschlagen') 
            return False
        zip_ref = zipfile.ZipFile(zipDatName, 'r')
        zip_ref.extractall(unzipdir)
        zip_ref.close()
        if not os.path.isfile(datDatName):
            addFehler (datDatName + ': UnZip ist fehlgeschlagen')
            return False
            
        # in Array übertragen
        fDatName  = open(datDatName, "r")
        arr=[]
        for zeile in fDatName:
            zeile=zeile.rstrip() # Zeilenende abschneiden
            if sys.version_info<(3,0,0):
                arr.append (''.join((chr(ord(c)^ord(k))) for c,k in zip(zeile.decode("hex"), cycle("makobo"))))
            else:
                arr.append (''.join((chr(ord(chr(c))^ord(k))) for c,k in zip(binascii.a2b_hex(zeile), cycle("makobo"))))
        fDatName.close()
        return arr

    except:
        errbox ('Download vom Makobo-Server fehlgeschlagen!\nBesteht eine Internetverbindung?')
        return False

        
def unzipShape4BL(shpList, unzipdir, zipdat, ShapePfad, ShapeName):
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

        
    Ges=0
    korrList=[]
    for shp in shpList:
        Anz=0;ShpKern=shp[0]
        for FAktDat in glob(unzipdir + ShpKern + '.*'):
            AktExt = os.path.splitext(os.path.basename(FAktDat))[1]
            NeuDat=ShapePfad + ShapeName + shp[1] + AktExt
            shutil.copyfile(FAktDat,NeuDat)
            # Gem/Flur bei TH abscheiden
            if shp[0][0:2] == '*_':
                NeuDat=os.path.split(FAktDat)[1]
                NeuDat=NeuDat[NeuDat.find('_')+1:]
                NeuDat=os.path.split(FAktDat)[0] + '/' + NeuDat
                shutil.move(FAktDat,NeuDat)
            Anz+=1
        if Anz == 0:
            addHinweis (ShpKern + ".*  in '" + zipdat + "' nicht gefunden")
        else:
            korrList.append(shp)
    return korrList

def dxf4Beschriftung (x,y,txt,handle,thoe='2.58759',layer='txtlayer'):
    must= (
"MTEXT"+ '\n'
"  5"+ '\n'
"%s"+ '\n'
"330"+ '\n'
"1"+ '\n'
"100"+ '\n'
"AcDbEntity"+ '\n'
"  8"+ '\n'
"%s" '\n'
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
"\\fMS Shell Dlg 2|i0|b0;\\H%s;%s " + '\n'
" 50"+ '\n'
"0.0"+ '\n'
" 41"+ '\n'
"8.17412830097370957"+ '\n'
" 71"+ '\n'
"     5"+ '\n'
"  7"+ '\n'
"STANDARD"+ '\n'
"  0" + '\n') % (str(handle),str(layer),str(x),str(y),str(thoe),str(txt))
    #if myqtVersion == 4: 
    #    return must.encode("cp1252")
    #else:
    #    return must
    return must


def genDXF4Gemarkung (uiParent, unzipDir, shpList, dxfDatNam):
    # Processing erst hier Laden, um den Start von QGIS zu beschleunigen
    import processing
    from processing.core.Processing import Processing
    uiParent.SetEinzelAktionText(tr("Generiere DXF Daten"))
    uiParent.SetEinzelAktionGesSchritte(len(shpList))
    

    korrDXFDatNam=(EZUTempDir() + str(uuid.uuid4()))    
    # shpList Aufbau:
    #     0         1             2                3             4                      5                 6                     7                   
    # zipname, dateikürzel, NameImQGISBaum, LayernameInDXF, "FlächeNachLinie", Optional: Beschriftung, Optional: Höhe, Optional: BeschLayer
    i=0;fertig=[]
    for sDat in shpList:
        uiParent.SetEinzelAktionAktSchritt(i)
        i=i+1
        Layer=sDat[ixZipName]
        if Layer[0:2]=='*_': Layer=Layer[2:]
        korrSHPDatNam= unzipDir + Layer + '.shp'
        if sDat[ixF2L]:
            opt = '-dialect sqlite -sql "SELECT \'' + sDat[ixLName] + '\' as Layer, ST_ExteriorRing(geometry) from \\\"' + Layer + '\\\""'
        else:
            opt = '-dialect sqlite -sql "SELECT \'' + sDat[ixLName] + '\' as Layer, geometry from \\\"' + Layer + '\\\""'
        if myqtVersion == 4:
            pAntw=processing.runalg('gdalogr:convertformat', korrSHPDatNam , 10, opt , korrDXFDatNam  + '_' + str(i) +'.dxf')
        else:
            pList={'INPUT':korrSHPDatNam,'OPTIONS':opt,'OUTPUT': korrDXFDatNam  + '_' + str(i) +'.dxf'}
            pAntw=processing.run('gdal:convertformat',pList)
        if pAntw is None:
            addFehler('gdalogr:convertformat -> '+opt)
        
        if len(sDat) > 6:
            # es ist eine Beschriftung zu generieren
            opt = '-lco SEPARATOR=TAB -lco GEOMETRY=AS_XYZ -dialect sqlite -sql "SELECT ST_PointOnSurface(geometry), ' + sDat[ixLabel] + ' from \\\"' + Layer + '\\\""'
            if myqtVersion == 4:
                pAntw=processing.runalg('gdalogr:convertformat', korrSHPDatNam , 12, opt , korrDXFDatNam  + '_' + str(i) +'.csv')
            else:
                pList={'INPUT':korrSHPDatNam,'OPTIONS':opt,'OUTPUT': korrDXFDatNam  + '_' + str(i) +'.csv'}
                pAntw=processing.run('gdal:convertformat',pList)
            if pAntw is None:
                errbox ('Fehler')
                addFehler(tr("process 'gdalogr:convertformat' could not start please restart QGIS"))   
            qDxfDat=korrDXFDatNam  + '_' + str(i) +'.dxf'
            qCsvDat=korrDXFDatNam  + '_' + str(i) +'.csv'
            zDxfDat=korrDXFDatNam  + '_(ges)' + str(i) +'.dxf'
            concatDXFBeschriftung(qDxfDat,qCsvDat,zDxfDat,sDat)
            fertig.append(zDxfDat)
        else:
            if not sDat[ixDXFFarbe] is None:
                #Aktuell nur neueHatchFarbe
                qDxfDat=korrDXFDatNam  + '_' + str(i) +'.dxf'
                zDxfDat=korrDXFDatNam  + '_(korr)' + str(i) +'.dxf'
                changeDXFAttribute(qDxfDat,zDxfDat,sDat)
                fertig.append(zDxfDat)

    uiParent.SetEinzelAktionText(tr("Erzeuge DXF Datei"))
    uiParent.SetEinzelAktionAktSchritt(i)
    mergeDXFFiles (uiParent,EZUTempDir(),fertig, dxfDatNam, True)
    
    #tmpDat = concatDXF(korrDXFDatNam  + '_1.dxf',korrDXFDatNam  + '_2.dxf', korrDXFDatNam  + '_3.csv')
    # hier gab es mit move ab und zu probleme
    # deshalb kopieren und anschließend löschen
    #shutil.copyfile (tmpDat, dxfDatNam )
    try:
        os.remove(tmpDat)
    except: 
        pass
 
def delUnzipIfUcan():
    tmp=EZUTempDir()
    for verz in glob(tmp +'*.unzip'):
        try:
            shutil.rmtree(verz)
        except:
            pass
    
    
def GemWorker(uiParent,qgisRootName, listZIPDatNam, expPfad, bSHPSave, bDXFSave, bMergeFlur):    
    # Processing erst hier Laden, um den Start von QGIS zu beschleunigen
    import processing
    from processing.core.Processing import Processing
    
    # -----------------------------------------------------------------------------------------------    
    # listZIPDatNam:
    #   http://geodownload.sachsen.de/inspire/cp_atom/gm_shape_25833/Gemarkung_Dittersdorf%20%282113%29	Dittersdorf (2113)
    # 1. Root erzeugen, wenn noch nicht vorhanden
    rNode=QgsProject.instance().layerTreeRoot()
    root = None
    for node in rNode.children(): # oberste Ebene in Schleife durchlaufen
        if str(type(node))  == "<class 'qgis._core.QgsLayerTreeGroup'>":
            if node.name() == qgisRootName:
                root = node
    if root is None:
        root = rNode.addGroup(qgisRootName)
    
    root.setExpanded(True)    

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
    #Processing.updateAlgsList()

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
    dxfMerge=[]
    for daten in listZIPDatNam:
        # Übergeben wird <LandKenn> + <MitFlur> + Datenzeile
        # - LandKenn und MitFlur von Datenzeile Trennen
        datZeile=daten.split("\t")
        sLandKenn = (datZeile[0])
        bMitFlur = (datZeile[1] == 'True')
        datZeile=datZeile[2:]
        
        idxDownloadURL = 0;idxWeiter = 1;idxLokName = 2;idxLand = 3;idxLK = 4;idxGemeinde = 5;idxGemarkung = 6;idxFlur = 7
        #http://geodownload.sachsen.de/inspire/cp_atom/gm_shape_25833/Gemarkung_Dittersdorf%20(2113).zip	-1	Dittersdorf (2113)	Sachsen	Erzgebirgskreis	Amtsberg	Dittersdorf (2113)
         

        AktLandkreis  = datZeile[idxLK]
        AktGemeinde   = datZeile[idxGemeinde]
        AktGemarkung  = datZeile[idxGemarkung]
        AktFlur = None
        if bMitFlur: AktFlur  = datZeile[idxFlur]
        
        url = datZeile[idxDownloadURL]
        url = url.encode("utf8") # die url kann Umlaute enthalten, welche codiert werden müssen    
        zip = datZeile[idxLokName]+'.zip'
        
        if not uiParent.isRunning():
            msgbox ("Nutzerabbruch")
            return False
        uiParent.SetEinzelAktionGesSchritte(StepCount4Datei)      
        uiParent.SetEinzelAktionAktSchritt(0) 
        i=i+1
        
        mldg="Import Gemarkung " + AktGemarkung
        if bMitFlur and AktFlur !='':
            mldg= mldg + " / " + AktFlur
        uiParent.SetDatAktionText(mldg)
        uiParent.SetDatAktionAktSchritt(i)

        if bSHPSave:
            AktShapeName = datZeile[idxLokName]
        else:
            AktShapeName = str(uuid.uuid4())    
                
        # 1. Download
        uiParent.SetEinzelAktionAktSchritt(1)
        uiParent.SetEinzelAktionText(tr("Download ZIP-Archiv vom Landesserver"))
        
        if os.getenv('COMPUTERNAME') == 'PK811':
            lokzip="d:/Flurst4SNTH.zip/" + sLandKenn + '/' + zip
        else:
            lokzip=zipDownload(url, zip)
        
        if lokzip is None:
            continue
        

        uiParent.SetEinzelAktionAktSchritt(2)
        uiParent.SetEinzelAktionText(tr("Verarbeite ZIP-Archiv"))

        # 2. Unzip
        # immer neues Verzeichnis, da vom Processing die Dateien manchmal gesperrt werden
        # außerdem der Versuch die alten aufzuräumen
        delUnzipIfUcan()
        unzipdir = EZUTempDir() + str(uuid.uuid4()) + ".unzip/"

        allShapeList=fncShapeDaten(sLandKenn)
        shpList = unzipShape4BL(allShapeList, unzipdir, lokzip, AktShapePfad, AktShapeName)
        if not shpList:
            continue
        # 3. QGIS Darstellung und CRS-Datei kopieren
        for sDat in shpList:
            kenn=sDat[ixDatKuerz]
            qmlDat = os.path.dirname(__file__) + "/qml/" + sLandKenn + kenn +'.qml'
            shutil.copyfile(qmlDat, AktShapePfad + AktShapeName + kenn +'.qml')
            
            qpjDat = os.path.dirname(__file__) + "/qpj/" + sLandKenn   + '.qpj'
            shutil.copyfile(qpjDat, AktShapePfad + AktShapeName + kenn + '.qpj') 

        # 4. DXF erzeugen
        if bDXFSave:
            genDXF4Gemarkung (uiParent, unzipdir, shpList, expPfad + datZeile[idxLokName] + '.dxf')
        
        # 5. Shape in QGIS einbinden
        # 5.1. Gruppe erzeugen bzw ermitteln
        #   (a) Gemarkung erzeugen
        tPfad=[];tPfad.append(AktLandkreis);tPfad.append(AktGemeinde);tPfad.append(AktGemarkung)
        gemNode, Anz = NodeCreateByFullName (tPfad,root)
        if Anz > 0: gemNode.setExpanded(False) # nur manipulieren, wenn neu erzeugt
        #   (b) evtl. Flur erzeugen - getrennt erzeugen, damit Flur nich ausgeklappt
        #   (c) hier auch zusammenzufassende DXF's ermitteln

        if bMitFlur and AktFlur !='': 
            if bDXFSave and bMergeFlur:
                dxfMerge.append(expPfad + datZeile[idxLokName] + '.dxf')
            tPfad.append(AktFlur)
            gemNode, Anz = NodeCreateByFullName (tPfad,root)
            if Anz > 0: gemNode.setExpanded(False) # nur manipulieren, wenn neu erzeugt
            
            
        # 5.2. Layer der Gruppe löschen
        gemNode.removeAllChildren()

        for sDat in shpList:
            Layer = QgsVectorLayer(AktShapePfad + AktShapeName + sDat[ixDatKuerz]+'.shp', u"Inspire "+ sDat[ixQName],"ogr")
            Layer.setProviderEncoding(u'UTF-8')
            if myqtVersion == 4:
                QgsMapLayerRegistry.instance().addMapLayer(Layer, False)
            else:
                QgsProject.instance().addMapLayer(Layer,False) 
            gemNode.insertLayer(0, Layer)

    if bDXFSave and len(dxfMerge) >0:
        uiParent.SetEinzelAktionText(tr("Flure zusammenfassen"))
        mergeDXFFlur(uiParent,dxfMerge,True)
        
    if len(getFehler()) > 0:
        errbox("\n\n".join(getFehler()))
        resetFehler()
    if len(getHinweis()) > 0:
        hinweislog("\n\n".join(getHinweis()))
        resetHinweis()        

    uiParent.FormRunning(False)
       
def mergeDXFFlur(uiParent, dxfList, bLoeschen):
    mergList=[]
    for dxf in dxfList:
        orgDXF=dxf
        Dat=os.path.basename(dxf)
        Ext=os.path.splitext(os.path.basename(Dat))[1]
        s=os.path.splitext(os.path.basename(Dat))[0].split("_")
        if len(s)==2:
            Gem = s[0]
            gemDXF=os.path.dirname(dxf) + '/' + s[0]+Ext
            Found=False
            for block in mergList:
                if block[0]==gemDXF:
                    block.append(orgDXF)
                    Found=True
            if not Found:
               mergList.append([gemDXF,orgDXF])    

    for block in mergList:
        if len(block) ==2:
            print ("move:",block[1],block[0])
            shutil.move(block[1],block[0])
        else:
            arr=[]
            for i in range(0,len(block)):
                if i > 0:
                    arr.append (block[i])
            mergeDXFFiles(uiParent, EZUTempDir(), arr, block[0], bLoeschen)

            
def changeDXFAttribute(qDxfDat,zDxfDat,sDat):
    fqDxfDat  = open(qDxfDat, "r")
    fzDxfDat  = open(zDxfDat, "w")

    #NeueHatchFarbe
    dxfArray=fqDxfDat.readlines()
    for aIdx in range(0,len(dxfArray)):  
        if dxfArray[aIdx].strip() == "HATCH":
            if dxfArray[aIdx-1].strip() == "0" and dxfArray[aIdx+1].strip() == "5":
                if dxfArray[aIdx+6].strip() != "AcDbEntity":
                    addFehler ("Fehler DXF-Analyse Zeile " + str(aIdx) + " :  <> 'AcDbEntity'")
                dxfArray[aIdx + 6] = "AcDbEntity\n420\n" + sDat[ixDXFFarbe] + '\n'
    fzDxfDat.writelines(dxfArray)
    fzDxfDat.close()
    fqDxfDat.close()    


def  handleHex2Long(hText):
    return long(hText,16)

def handleLong2Hex(hLong):
    return format(long(hLong),"X")

def concatDXFBeschriftung(qDxfDat,qCsvDat,zDxfDat,sDat):
    if os.path.isfile(zDxfDat):
        os.remove(zDxfDat)
    if myqtVersion == 5:
        fzDxfDat  = open(zDxfDat, "w",encoding='cp1252')
        csvArray=open(qCsvDat, "r", encoding='utf-8').readlines() # Utf8-Datei !!!!
        dxfArray=open(qDxfDat, "r", encoding='cp1252').readlines() # Ansi Datei 
    else:
        fzDxfDat  = open(zDxfDat, "w")
        csvArray=open(qCsvDat, "r").readlines() # Utf8-Datei !!!!
        dxfArray=open(qDxfDat, "r").readlines() # Ansi Datei 

    bStartFlENT = False
    h=0;z=0

    for aIdx in range(0,len(dxfArray)):
        # 1) Ermitteln des maximalen Handles und erweitern um Anzahl der CSV-Einträge
        if dxfArray[aIdx].rstrip() == "$HANDSEED" and dxfArray[aIdx - 1].strip() == "9" and dxfArray[aIdx + 1].strip() == "5":
            maxOldHandle = handleHex2Long(dxfArray[aIdx + 2])
            dxfArray[aIdx + 2] = handleLong2Hex(maxOldHandle + len(csvArray)-1) + '\n'

        # 2) Ermitteln der Startzeile der Entities
        if dxfArray[aIdx].rstrip() == "ENTITIES" and dxfArray[aIdx - 1].strip() == "2" and dxfArray[aIdx + 1].strip() == "0":
            bStartFlENT = True
        if dxfArray[aIdx].rstrip() == "ENDSEC" and dxfArray[aIdx - 1].strip() == "0" and dxfArray[aIdx + 1].strip() == "0"  and bStartFlENT:
            bStartFlENT = False
            # jetzt kann die Beschriftung  werden
            # 1. Gemarkung
            handle = maxOldHandle ; z = 0

            for cIdx in range(0,len(csvArray)):
                if myqtVersion == 5:
                    xZeile = csvArray[cIdx].rstrip() #bytearray(csvArray[cIdx].rstrip(), 'cp1252')
                else:
                    xZeile = csvArray[cIdx].rstrip().decode("utf-8").encode('cp1252')
                z=z+1
                if z > 1 :
                    xZeile=xZeile.split(chr(9))
                    #def dxf4Beschriftung (x,y,txt,handle,thoe='2.58759',layer='txtlayer'):
                    #print (xZeile[0],xZeile[1],xZeile[3], handleLong2Hex(handle),sDat[ixLHoe],sDat[ixBName])
                    fzDxfDat.write (dxf4Beschriftung(xZeile[0],xZeile[1],xZeile[3], handleLong2Hex(handle),sDat[ixLHoe],sDat[ixBName]))
                    handle = handle + 1
                
        fzDxfDat.write (dxfArray[aIdx])
    fzDxfDat.close()
    return True    
    
def mergeDXFFiles(uiParent, Pfad, dxfFiles,zDatNam, bLoeschen):
    # verbinden mehrerer DXF-Dateien, erste Datei liefert Header und Footer
    # minHandle,maxHandle,varHandle,lastLayer,layZusatzBlock
    bFirst=True
    uiParent.SetEinzelAktionGesSchritte(len(dxfFiles)+1)      
    i=0
    for dxfDat in dxfFiles:
        uiParent.SetEinzelAktionAktSchritt(i)
        i=i+1
        # 1. DXF in Header/Entities/Footer zerlegen und Handle umschreiben
        if bFirst:
            #fncSplitOgrDXF(quellDat, entDat, EntHandleStart = -1, bFirstDXF=False, headDat = None, footDat = None)
            handles = fncSplitOgrDXF(dxfDat, Pfad + "e.txt", -1, True, Pfad + "h.txt", Pfad + "f.txt")
            bFirst=False
        else:
            handles = fncSplitOgrDXF(dxfDat, Pfad + "e.txt", handles)


    # Schreiben GesamtDXF
    # HANDSEED in Header schreiben
    uiParent.SetEinzelAktionAktSchritt(i)
    dxfArray=open(Pfad + "h.txt", "r").readlines()
    for aIdx in range(0,len(dxfArray)):
        if dxfArray[aIdx].rstrip() == "$HANDSEED" and dxfArray[aIdx - 1].strip() == "9" and dxfArray[aIdx + 1].strip() == "5":
            dxfArray[aIdx + 2] = handleLong2Hex(handles) + '\n'

    open(zDatNam, "w").writelines(dxfArray)
    open(zDatNam, "a").writelines(open(Pfad + "e.txt", "r").readlines())
    open(zDatNam, "a").writelines(open(Pfad + "f.txt", "r").readlines())
 
    
    if bLoeschen: 
        for dxfDat in dxfFiles:
            os.remove (dxfDat)

    os.remove (Pfad + "h.txt")
    os.remove (Pfad + "e.txt")
    os.remove (Pfad + "f.txt")

def fncSplitOgrDXF(quellDat, entDat, EntHandleStart = -1, bFirstDXF=False, headDat = None, footDat = None):
    # 01.02.2018: Neue vereinfachte Version, Header und Fotter 1:1 übernehmen
    # alles relativ "grobschlächtig", da OGR-Struktur bekannt und es schnell gehen soll
    # DXF in eine Array zu bearbeiten schein in diesem Fall die beste Variante (gut Positionierbar)
    #Dim dxfArray() As String, i As Long, HndAktEnt As Long
    #Dim aIdx As Long, zStart As Long, zEnde As Long

    varHandle=0 
    HndAktEnt = EntHandleStart
    dxfArray=open(quellDat, "r").readlines()
    
    if bFirstDXF:
        if os.path.isfile(entDat): os.remove (entDat)
    if not footDat is None:
        if os.path.isfile(footDat): os.remove(footDat)
    if not headDat is None:
        if os.path.isfile(headDat): os.remove(headDat)

    
    
    # -----------------------------------
    # 1. Header
    # -----------------------------------  
    for aIdx in range(0,len(dxfArray)):
        # 1. maximal Handle ermitteln
        if dxfArray[aIdx].rstrip() == "$HANDSEED":
            if dxfArray[aIdx - 1].strip() == "9" and dxfArray[aIdx + 1].strip() == "5":
                varHandle = handleHex2Long(dxfArray[aIdx + 2])
                if HndAktEnt == -1: HndAktEnt = varHandle +1 # bei der ersten Datei ist Start das eigentliche Ende, da auch handle im Header vergeben werden
        
        # 2. Optional Header speichern
        if dxfArray[aIdx].rstrip() == "ENTITIES" and dxfArray[aIdx - 1].strip() == "2" and dxfArray[aIdx + 1].strip() == "0":
            idxEHeader=aIdx-1
            if not headDat is None:
                open(headDat, "a").writelines(dxfArray[0:idxEHeader])
            break
    
    # -----------------------------------
    # 2. Entities
    # -----------------------------------
    for aIdx in range(idxEHeader,len(dxfArray)):
        if dxfArray[aIdx].strip() == "5" and dxfArray[aIdx - 2].strip() == "0":
            # eine 5 mit zeile-2 als 0 gibt es auch sonst,
            # deshalb zusätzlich schaun, ob Zeile -1 eine Objektart "erkennbar" an mind 4 großen Buchstaben
            if len(dxfArray[aIdx - 1]) >= 4 and  not re.search("^[A-Z]*$",dxfArray[aIdx - 1]) is None:
                dxfArray[aIdx + 1] = handleLong2Hex(HndAktEnt) + '\n'
                HndAktEnt = HndAktEnt + 1
                        
        # Entities speichern
        if dxfArray[aIdx].rstrip() == "ENDSEC" and dxfArray[aIdx - 1].strip() == "0" and dxfArray[aIdx + 1].strip() == "0":
            idxEEntities=aIdx-1
            if bFirstDXF:
                open(entDat, "w").writelines('  2\nENTITIES\n')
            open(entDat, "a").writelines(dxfArray[idxEHeader+2:idxEEntities])
            break            
    
    # -----------------------------------
    # 3. Footer
    # -----------------------------------
    if not footDat is None:
        #ENDSEC kommt der Einfachkeit halber mit in den Footer
        open(footDat, "w").writelines(dxfArray[idxEEntities: len(dxfArray) + 1])

    return HndAktEnt

def mergeDXFFiles4Folder (globFolder,zDat):
    print (glob(globFolder))
    
    
if __name__ == "__main__":
    dummy=0
    arr=[u'D:/tar/Neuer Ordner/G\xf6dern (1132)_1.dxf', u'D:/tar/Neuer Ordner/G\xf6dern (1132)_2.dxf']
    z=u'D:/tar/Neuer Ordner/G\xf6dern (1132).dxf'
    #mergeDXFFiles(EZUTempDir(), arr, z, True)
    #mergeDXFFiles ("d:/tar/",glob("d:/tar/Neuer Ordner (2)/*.dxf"), 'd:/tar/merge' + str(myqtVersion) + '.dxf', False)
    #tAnsi=open("d:/ansi.txt", "r").readlines()[0]
    #tUtf8=open("d:/utf8.txt", "r").readlines()[0]
    #utf2ansi=(tUtf8.decode("utf-8").encode('cp1252'))
    #print(type(str(u"thoe")),type(utf2ansi),type(tUtf8))
    
    
    #dxf4Beschriftung ("x","y",utf2ansi,"handle",u'2.58759',layer='txtlayer')
    # ("test%stest%s") % ("abc",utf2ansi)
    #'741420.337901089', '5644302.7145', 'Flur: G\xc3\xb6\xc3\x9fnitz', u'45', 50, 'Gemarkungsname')
    """
    sDat=['*_flurstueck','(Flst)',u'Flurstück','Flurstuecksgrenze', None, True, 'flurstnr as Beschr',3,'Flurstuecksnummer']
    qDxfDat="d:/tar/02.dxf";qCsvDat="d:/tar/02.csv";zDxfDat='d:/tar/gen' + str(myqtVersion) + '.dxf'
    concatDXFBeschriftung(qDxfDat,qCsvDat,zDxfDat,sDat)
    """
    """
    sDat=['*_gebaeudeBauwerk','(Geb)',u'Gebäude','Gebaeude', '12497369' , False]
    qDxfDat="d:/tar/geb.dxf";zDxfDat='d:/tar/gen.dxf'
    #fncSplitOgrDXF     (quellDat,             entDat,    EntHandleStart,     bFirstDXF=False, headDat = None, footDat = None)

    print fncSplitOgrDXF("d:/tar/1.dxf", "d:/tar/e.txt", -1, True,        "d:/tar/h.txt", "d:/tar/f.txt")
    open("d:/tar/mytest.dxf", "w").writelines(open("d:/tar/h.txt", "r").readlines())
    open("d:/tar/mytest.dxf", "a").writelines(open("d:/tar/e.txt", "r").readlines())
    open("d:/tar/mytest.dxf", "a").writelines(open("d:/tar/f.txt", "r").readlines())
    #List.append( fncSplitOgrDXF("d:/tar/3.dxf", "d:/tar/h.txt","d:/tar/e.txt", "d:/tar/f.txt", False,  0))
    #print List
    if len(getFehler()) > 0:
        print("\n\n".join(getFehler()))
        resetFehler()
    if len(getHinweis()) > 0:
        print("\n\n".join(getHinweis()))
        resetHinweis() 

    arr=[]
    arr.append(u"d:/tar/Romschütz (1136)_1.dxf")
    arr.append(u"d:/tar/Romschütz (1136)_2.dxf")
    arr.append(u"d:/tar/Romschütz (1136)_3.dxf")
    mergeDXFFiles ("d:/tar/",arr, 'd:/tar/merge' + str(myqtVersion) + '.dxf', False)


    arr=DownloadLand2Array ("expSN.sDat")
    if len(getFehler()) > 0:
        print("\n\n".join(getFehler()))
        resetFehler()
    else:
        f=open("d:/tar/mytest.csv", "w")
        for zeile in arr:
            f.write (zeile+"\n")
    """    
        

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
    #print unzipShape4BL(zipdat, ShapePfad, ShapeName)