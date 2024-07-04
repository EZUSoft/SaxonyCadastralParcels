# -*- coding: utf-8 -*-
"""
/***************************************************************************
 A QGIS plugin
SaxonyCadastralParcels: Download Flurstuecke Sachsen und Thueringen, Darstellung in QGIS und Konvertierung nach DXF
        copyright            : (C) 2020 by EZUSoft
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


























from random import randrange
import sys
import uuid


from qgis.core import *
from glob import glob
import shutil 
import urllib
import zipfile
from itertools import cycle
import binascii
import re
import os.path

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
    from modDownload import DownLoadOverQT
except:
    from .fnc4all import *
    from .modDownload import DownLoadOverQT

    








try:
    from fnc4SaxonyCadastralParcels import *
except:
    from .fnc4SaxonyCadastralParcels import *

def tr( message):











    return message 

ixZipName=0;ixDatKuerz=1;ixQName=2;ixLName=3;ixDXFFarbe=4;ixF2L=5;ixLabel=6;ixLHoe=7;ixBName=8
def fncShapeDaten (sLandKenn):



    if sLandKenn == "SN": 
        allshpList=[
            ['INSPIRE.cpParcelS','(Flst)',u'Flurstück','Flurstuecksgrenze', None, True, 'LABEL as Beschr',3,'Flurstuecksnummer']
            ,
            ['INSPIRE.cpZoningS','(Gem)','Gemarkung','Gemarkungsgrenze', None, True, 'LABEL as Beschr',50,'Gemarkungsname']
            ,
            ['INSPIRE_cpParcelS','(Flst)',u'Flurstück','Flurstuecksgrenze', None, True, 'LABEL as Beschr',3,'Flurstuecksnummer']
            ,
            ['INSPIRE_cpZoningS','(Gem)','Gemarkung','Gemarkungsgrenze', None, True, 'LABEL as Beschr',50,'Gemarkungsname']
        ]
    if sLandKenn == "TH": 
        allshpList=[
            ['*_gebaeudeBauwerk','(Geb)',u'Gebäude','Gebaeude', '12497369' , False]
            ,  
            ['*_katasterBezirk', '(Gem)','Gemarkung','Gemarkungsgrenze', None, True, "art || ': ' || ueboname as Beschr",50,'Gemarkungsname']
            , 
            ['*_flurstueck','(Flst)',u'Flurstück','Flurstuecksgrenze', None, True, 'flurstnr as Beschr',3,'Flurstuecksnummer']
        ] 
    return allshpList

def zipDownload(url,zipname):
    lok=EZUTempDir()
    size,status = DownLoadOverQT ( toUnicode(url), toUnicode(lok + zipname))
    return lok+zipname, size, status

























def DownloadLandListe (ansiDatName):
    qDatName=bytearray(ansiDatName, 'utf-8').decode("cp1252")
    unzipdir = EZUTempDir() + "/unzip/"
    datDatName = unzipdir + qDatName

    url="https://www.makobo.de/data/" + qDatName
    try:
        if not os.path.exists(unzipdir):
            os.makedirs(unzipdir) 
  
        size, status = DownLoadOverQT ( url,datDatName)    
        if not os.path.isfile(datDatName):
            addFehler (datDatName + ': download ist fehlgeschlagen (Status:' + status + ')') 
            return None
 

        fDatName  = fncUniDatOpen23(datDatName, "r",'ansi') 
        arr=[]
        for zeile in fDatName:
            zeile=zeile.rstrip() 
            arr.append (zeile)
        fDatName.close()
        return arr

    except:
        if fncDebugMode():
            raise
        errbox ('Download vom Makobo-Server fehlgeschlagen!\nBesteht eine Internetverbindung?')
        return False
        
def DownloadLand2Array (ansiDatName):

    qDatName=bytearray(ansiDatName, 'utf-8').decode("cp1252")
    unzipdir = EZUTempDir() + "/unzip/"
    datDatName = unzipdir + qDatName
    zipDatName = unzipdir + qDatName + ".zip"
    url="https://www.makobo.de/data/" + qDatName + ".zip"
    try:
        if not os.path.exists(unzipdir):
            os.makedirs(unzipdir) 
        if not ClearDir(unzipdir):
            addFehler (unzipdir + ': ' + "konnte nicht geleert werden")
            return False
        if os.getenv('COMPUTERNAME') == 'xxxx':
            shutil.copyfile('D:/Flurst4SNTH.zip/'+qDatName + ".zip",zipDatName)
        else:
            size, status = DownLoadOverQT ( url,zipDatName)
        
        if not os.path.isfile(zipDatName):
            addFehler (zipDatName + ': download ist fehlgeschlagen (Status:' + status + ')') 
            return False
        zip_ref = zipfile.ZipFile(zipDatName, 'r')
        zip_ref.extractall(unzipdir)
        zip_ref.close()
        if not os.path.isfile(datDatName):
            errbox (datDatName + ': UnZip ist fehlgeschlagen (Status:' + str(status) + ')')
            return False
            

        fDatName  = fncUniDatOpen23(datDatName, "r",'utf-8') 
        arr=[]
        for zeile in fDatName:
            zeile=zeile.rstrip() 
            if sys.version_info<(3,0,0):
                arr.append (''.join((chr(ord(c)^ord(k))) for c,k in zip(zeile.decode("hex"), cycle("makobo"))))
            else:
                arr.append (''.join((chr(ord(chr(c))^ord(k))) for c,k in zip(binascii.a2b_hex(zeile), cycle("makobo"))))
        fDatName.close()
        return arr

    except:
        if fncDebugMode():
            raise
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

            if shp[0][0:2] == '*_':
                NeuDat=os.path.split(FAktDat)[1]
                NeuDat=NeuDat[NeuDat.find('_')+1:]
                NeuDat=os.path.split(FAktDat)[0] + '/' + NeuDat
                shutil.move(FAktDat,NeuDat)
            Anz+=1
        if Anz == 0:
            if (ShpKern != 'INSPIRE_cpZoningS' and ShpKern != 'INSPIRE_cpParcelS'): 
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




    return must


def genDXF4Gemarkung (uiParent, unzipDir, shpList, dxfDatNam):

    import processing
    from processing.core.Processing import Processing
    uiParent.SetEinzelAktionText(tr("Generiere DXF Daten"))
    uiParent.SetEinzelAktionGesSchritte(len(shpList))
    

    korrDXFDatNam=(EZUTempDir() + str(uuid.uuid4()))    



    i=0;fertig=[]
    for sDat in shpList:
        uiParent.SetEinzelAktionAktSchritt(i)
        i=i+1
        Layer=sDat[ixZipName]
        if Layer[0:2]=='*_': Layer=Layer[2:]
        korrSHPDatNam= unzipDir + Layer + '.shp'
        if sDat[ixF2L]:
            opt = '-skipfailure -dialect sqlite -sql "SELECT \'' + sDat[ixLName] + '\' as Layer, ST_Boundary(geometry)  from \'' + Layer + '\'"'
        else:
            opt = '-skipfailure -dialect sqlite -sql "SELECT \'' + sDat[ixLName] + '\' as Layer, geometry from \'' + Layer + '\'"'
        if myqtVersion == 4:
            pAntw=processing.runalg('gdalogr:convertformat', korrSHPDatNam , 10, opt , korrDXFDatNam  + '_' + str(i) +'.dxf')
        else:
            pList={'INPUT':korrSHPDatNam,'OPTIONS':opt,'OUTPUT': korrDXFDatNam  + '_' + str(i) +'.dxf'}
            pAntw=processing.run('gdal:convertformat',pList)
        
        if pAntw is None:
            addFehler('gdalogr:convertformat -> '+opt)
        
        if len(sDat) > 6:

            opt = '-skipfailure -lco SEPARATOR=TAB -lco GEOMETRY=AS_XYZ -dialect sqlite -sql "SELECT ST_PointOnSurface(geometry), ' + sDat[ixLabel] + ' from \'' + Layer + '\'"'
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
            

            datError=False
            if not os.path.isfile(qDxfDat):
                errbox ('qDxfDat: Fehler bei Umsetzung "' + korrSHPDatNam + '"')
                addFehler('qDxfDat :Fehler bei Umsetzung "' + korrSHPDatNam + '"') 
                datError=True
            if not os.path.isfile(qCsvDat):
                errbox ('qCsvDat: Fehler bei Umsetzung "' + korrSHPDatNam + '"')
                addFehler('qCsvDat: Fehler bei Umsetzung "' + korrSHPDatNam + '"')  
                datError=True                
                
            if not datError:
                concatDXFBeschriftung(qDxfDat,qCsvDat,zDxfDat,sDat)
                fertig.append(zDxfDat)
        else:
            if not sDat[ixDXFFarbe] is None:

                qDxfDat=korrDXFDatNam  + '_' + str(i) +'.dxf'
                zDxfDat=korrDXFDatNam  + '_(korr)' + str(i) +'.dxf'
                changeDXFAttribute(qDxfDat,zDxfDat,sDat)
                fertig.append(zDxfDat)

    uiParent.SetEinzelAktionText(tr("Erzeuge DXF Datei"))
    uiParent.SetEinzelAktionAktSchritt(i)
    mergeDXFFiles (uiParent,EZUTempDir(),fertig, dxfDatNam, True)
    




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
    
    
def GemWorker(uiParent, lKenn, qgisRootName, listZIPDatNam, expPfad, bSHPSave, bDXFSave, bMergeFlur):    

    import processing
    from processing.core.Processing import Processing
    




    rNode=QgsProject.instance().layerTreeRoot()
    root = None
    for node in rNode.children(): 
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






    uiParent.FormRunning(True)
    uiParent.SetEinzelAktionText("")
    uiParent.SetDatAktionText(tr("process init - please wait"))

    Processing.initialize()




    i=0
    uiParent.SetDatAktionGesSchritte(len(listZIPDatNam))
    chkurl="https://www.makobo.de/links/GemList_SaxonyCadastralParcels.php?" + fncBrowserID() + "|" + fncPluginVersion() + ":"  
    
    StepCount4Datei = 2
    if  bSHPSave:
        StepCount4Datei = StepCount4Datei + 1
    if  bDXFSave:
        StepCount4Datei = StepCount4Datei + 3
    try:
        DownLoadOverQT(chkurl + str(myQGIS_VERSION_INT()) + ":" + lKenn + ':' + str(len(listZIPDatNam)).strip(),EZUTempDir()+'test.zip')
        
    except:
        pass
    dxfMerge=[]
    for daten in listZIPDatNam:


        datZeile=daten.split("\t")
        sLandKenn = (datZeile[0])
        bMitFlur = (datZeile[1] == 'True')
        datZeile=datZeile[2:]
        
        idxDownloadURL = 0;idxWeiter = 1;idxLokName = 2;idxLand = 3;idxLK = 4;idxGemeinde = 5;idxGemarkung = 6;idxFlur = 7

         

        AktLandkreis  = datZeile[idxLK]
        AktGemeinde   = datZeile[idxGemeinde]
        AktGemarkung  = datZeile[idxGemarkung]
        AktFlur = None
        if bMitFlur: AktFlur  = datZeile[idxFlur]
        
        url = datZeile[idxDownloadURL]


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
                

        uiParent.SetEinzelAktionAktSchritt(1)
        uiParent.SetEinzelAktionText(tr("Download ZIP-Archiv vom Landesserver"))
        
        if os.getenv('COMPUTERNAME') == 'xxxx':
            lokzip="d:/Flurst4SNTH.zip/" + sLandKenn + '/' + zip
        else:
            lokzip, size, status=zipDownload(url, zip)
        if (size == 0):
            addFehler ("Download der Geodaten von URL gescheitert:\n"+ url)
        else:


            

            uiParent.SetEinzelAktionAktSchritt(2)
            uiParent.SetEinzelAktionText(tr("Verarbeite ZIP-Archiv"))




            delUnzipIfUcan()
            unzipdir = EZUTempDir() + str(uuid.uuid4()) + ".unzip/"

            allShapeList=fncShapeDaten(sLandKenn)

            shpList = unzipShape4BL(allShapeList, unzipdir, lokzip, AktShapePfad, AktShapeName)
            if not shpList:
                continue

            for sDat in shpList:
                kenn=sDat[ixDatKuerz]
                qmlDat = os.path.dirname(__file__) + "/qml/" + sLandKenn + kenn +'.qml'
                shutil.copyfile(qmlDat, AktShapePfad + AktShapeName + kenn +'.qml')
                
                qpjDat = os.path.dirname(__file__) + "/qpj/" + sLandKenn   + '.qpj'
                shutil.copyfile(qpjDat, AktShapePfad + AktShapeName + kenn + '.qpj') 


            if bDXFSave:
                genDXF4Gemarkung (uiParent, unzipdir, shpList, expPfad + datZeile[idxLokName] + '.dxf')
            



            tPfad=[];tPfad.append(AktLandkreis);tPfad.append(AktGemeinde);tPfad.append(AktGemarkung)
            gemNode, Anz = NodeCreateByFullName (tPfad,root)
            if Anz > 0: gemNode.setExpanded(False) 



            if bMitFlur and AktFlur !='': 
                if bDXFSave and bMergeFlur:
                    dxfMerge.append(expPfad + datZeile[idxLokName] + '.dxf')
                tPfad.append(AktFlur)
                gemNode, Anz = NodeCreateByFullName (tPfad,root)
                if Anz > 0: gemNode.setExpanded(False) 
                
                

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
            shutil.move(block[1],block[0])
        else:
            arr=[]
            for i in range(0,len(block)):
                if i > 0:
                    arr.append (block[i])
            mergeDXFFiles(uiParent, EZUTempDir(), arr, block[0], bLoeschen)

            
def changeDXFAttribute(qDxfDat,zDxfDat,sDat):
    fqDxfDat  = fncUniDatOpen23(qDxfDat, "r",'cp1252') 
    fzDxfDat  = fncUniDatOpen23(zDxfDat, "w",'cp1252') 


    dxfArray=fqDxfDat.readlines()
    for aIdx in range(0,len(dxfArray)): 


        if dxfArray[aIdx].strip() == "HATCH":
            if dxfArray[aIdx-1].strip() == "0" and dxfArray[aIdx+1].strip() == "5":
                if dxfArray[aIdx+6].strip() != "AcDbEntity" and dxfArray[aIdx+4].strip() != "AcDbEntity":
                    addFehler ("Fehler DXF-Analyse Datei:\n" + qDxfDat + " Zeile " + str(aIdx+6) + "/" + str(aIdx+3) + " :  <> 'AcDbEntity'")
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
        
    fzDxfDat = fncUniDatOpen23(zDxfDat, "w",'cp1252')  
    csvArray = fncUniDatReadAll23(qCsvDat,'utf-8')  
    dxfArray = fncUniDatReadAll23(qDxfDat,'cp1252') 


    bStartFlENT = False
    h=0;z=0

    for aIdx in range(0,len(dxfArray)):

        if dxfArray[aIdx].rstrip() == "$HANDSEED" and dxfArray[aIdx - 1].strip() == "9" and dxfArray[aIdx + 1].strip() == "5":
            maxOldHandle = handleHex2Long(dxfArray[aIdx + 2])
            dxfArray[aIdx + 2] = handleLong2Hex(maxOldHandle + len(csvArray)-1) + '\n'


        if dxfArray[aIdx].rstrip() == "ENTITIES" and dxfArray[aIdx - 1].strip() == "2" and dxfArray[aIdx + 1].strip() == "0":
            bStartFlENT = True
        if dxfArray[aIdx].rstrip() == "ENDSEC" and dxfArray[aIdx - 1].strip() == "0" and dxfArray[aIdx + 1].strip() == "0"  and bStartFlENT:
            bStartFlENT = False


            handle = maxOldHandle ; z = 0

            for cIdx in range(0,len(csvArray)):
                if myqtVersion == 5:
                    xZeile = csvArray[cIdx].rstrip() 
                else:
                    xZeile = csvArray[cIdx].rstrip().decode("utf-8").encode('cp1252')
                z=z+1
                if z > 1 :
                    xZeile=xZeile.split(chr(9))





                    
                    fzDxfDat.write (dxf4Beschriftung(xZeile[0],xZeile[1],xZeile[3].replace('"',''), handleLong2Hex(handle),sDat[ixLHoe],sDat[ixBName]))
                    handle = handle + 1
                
        fzDxfDat.write (dxfArray[aIdx])
    fzDxfDat.close()
    return True    
    
def mergeDXFFiles(uiParent, Pfad, dxfFiles,zDatNam, bLoeschen):


    bFirst=True
    uiParent.SetEinzelAktionGesSchritte(len(dxfFiles)+1)      
    i=0
    for dxfDat in dxfFiles:
        uiParent.SetEinzelAktionAktSchritt(i)
        i=i+1

        if bFirst:

            handles = fncSplitOgrDXF(dxfDat, Pfad + "e.txt", -1, True, Pfad + "h.txt", Pfad + "f.txt")
            bFirst=False
        else:
            handles = fncSplitOgrDXF(dxfDat, Pfad + "e.txt", handles)




    uiParent.SetEinzelAktionAktSchritt(i)
    dxfArray=fncUniDatReadAll23(Pfad + "h.txt",'cp1252') 
    for aIdx in range(0,len(dxfArray)):
        if dxfArray[aIdx].rstrip() == "$HANDSEED" and dxfArray[aIdx - 1].strip() == "9" and dxfArray[aIdx + 1].strip() == "5":
            dxfArray[aIdx + 2] = handleLong2Hex(handles) + '\n'

    subUniDatWriteAll23(zDatNam, "w", dxfArray,'cp1252')
    subUniDatWriteAll23(zDatNam, "a", fncUniDatReadAll23 ( Pfad + "e.txt",'cp1252'),'cp1252')
    subUniDatWriteAll23(zDatNam, "a", fncUniDatReadAll23 ( Pfad + "f.txt",'cp1252'),'cp1252')
    
    if bLoeschen: 
        for dxfDat in dxfFiles:
            os.remove (dxfDat)

    os.remove (Pfad + "h.txt")
    os.remove (Pfad + "e.txt")
    os.remove (Pfad + "f.txt")

def fncSplitOgrDXF(quellDat, entDat, EntHandleStart = -1, bFirstDXF=False, headDat = None, footDat = None):






    varHandle=0 
    HndAktEnt = EntHandleStart

    dxfArray=fncUniDatReadAll23(quellDat,'cp1252')

    if bFirstDXF:
        if os.path.isfile(entDat): os.remove (entDat)
    if not footDat is None:
        if os.path.isfile(footDat): os.remove(footDat)
    if not headDat is None:
        if os.path.isfile(headDat): os.remove(headDat)

    
    



    for aIdx in range(0,len(dxfArray)):

        if dxfArray[aIdx].rstrip() == "$HANDSEED":
            if dxfArray[aIdx - 1].strip() == "9" and dxfArray[aIdx + 1].strip() == "5":
                varHandle = handleHex2Long(dxfArray[aIdx + 2])
                if HndAktEnt == -1: HndAktEnt = varHandle +1 
        

        if dxfArray[aIdx].rstrip() == "ENTITIES" and dxfArray[aIdx - 1].strip() == "2" and dxfArray[aIdx + 1].strip() == "0":
            idxEHeader=aIdx-1
            if not headDat is None:
                subUniDatWriteAll23(headDat, "a",dxfArray[0:idxEHeader],'cp1252')
            break
    



    for aIdx in range(idxEHeader,len(dxfArray)):
        if dxfArray[aIdx].strip() == "5" and dxfArray[aIdx - 2].strip() == "0":


            if len(dxfArray[aIdx - 1]) >= 4 and  not re.search("^[A-Z]*$",dxfArray[aIdx - 1]) is None:
                dxfArray[aIdx + 1] = handleLong2Hex(HndAktEnt) + '\n'
                HndAktEnt = HndAktEnt + 1
                        

        if dxfArray[aIdx].rstrip() == "ENDSEC" and dxfArray[aIdx - 1].strip() == "0" and dxfArray[aIdx + 1].strip() == "0":
            idxEEntities=aIdx-1
            if bFirstDXF:
                subUniDatWriteAll23(entDat, "w",'  2\nENTITIES\n','cp1252')
            subUniDatWriteAll23(entDat, "a",dxfArray[idxEHeader+2:idxEEntities],'cp1252')
            break            
    



    if not footDat is None:

        subUniDatWriteAll23(footDat, "w",dxfArray[idxEEntities: len(dxfArray) + 1],'cp1252')

    return HndAktEnt

    
