# -*- coding: utf-8 -*-
"""
/***************************************************************************
 clsQGISAction
  25.10.2016 V0.3
  - toUTF8(qry4pri.value(0)): lName auf alle Zugriffe erweitert
  31.08.2016 V0.3
  - Integration Shape-Export
  - Hinweis für Kreise für QGis.QGIS_VERSION_INT < 21200
  20.06.2016 V0.2
  - Einbindung der GIDDB Sachdaten
                                 A QGIS plugin
 CAIGOS-PostgreSQL/PostGIS in QGIS darstellen
                              -------------------
        begin                : 2016-04-18
        git sha              : $Format:%H$
        copyright            : (C) 2016 by EZUSoft
        email                : qgis (at) makobo.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 """
 
from qgis.utils import *
#from qgis.core import *
from PyQt4.QtCore import Qt
from PyQt4 import QtGui, uic
from PyQt4.QtCore import QSettings
from PyQt4.QtSql import QSqlDatabase, QSqlQuery, QSqlError


from clsDatenbank import *

from clsRenderingByQML import *
from fnc4all import *

class clsQGISAction():
    def AlleLayerLoeschen(self):
        # Löscht (im Moment) nur die Layer - nicht die Gruppen 
        LayerList = QgsMapLayerRegistry.instance().mapLayers()
        for layer in LayerList:
            QgsMapLayerRegistry.instance().removeMapLayer(layer)
 
    def GruppeLoeschenByName(self, NameOfGroup):
        # Löscht  die Gruppen 
        toc = iface.legendInterface()
        LegList = toc.groups()
        if NameOfGroup in LegList:
            groupIndex = LegList.index(NameOfGroup)
            toc.removeGroup(groupIndex)
    
    def getGroupIDByName(self, NameOfGroup):
        toc = iface.legendInterface()
        LegList = toc.groups()
        if NameOfGroup in LegList:
            return LegList.index(NameOfGroup)


    def LayerbyName (self,lName):
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.name() == lName:
                return lyr
                break        
        
    def ObjektAnzahlZeigen(self):
        root = QgsProject.instance().layerTreeRoot()
        for child in root.children():
            if isinstance(child, QgsLayerTreeLayer):
                child.setCustomProperty("showFeatureCount", True)
    

    def QGISBaum(self, db, User, rootname, qry4pri, qry, bGenDar, bPrjNeu, iDarGruppe, b3DDar, bDBTab, bSHPexp, bLeer, OutOfQGIS=False):
        if bSHPexp:
            s = QSettings( "EZUSoft", "CAIGOS-Konnektor" )
            txtCodePage = s.value( "txtCodePage", 0)
            txtZielPfad = s.value( "txtSHPDir", "" )
            
        # allgemeine Daten für Layereinbindung ermitteln
        clsRendXML = clsRenderingByQML()
        clsdb=pgDataBase()

        ConnInfo=clsdb.GetConnString()
        Epsg=clsdb.GetEPSG()

        newparent = True
        Fachschale = ""
        Thema = ""
        Gruppe = ""
        i=0
        
        # Progressbar intitialisieren
        GesAnz = qry4pri.size()
        if not OutOfQGIS:
            widget = iface.messageBar().createMessage("Daten werden geladen")
        prgBar = QtGui.QProgressBar()
        prgBar.setAlignment(Qt.AlignLeft)
        prgBar.setValue(0)
        prgBar.setMaximum(GesAnz)           
        widget.layout().addWidget(prgBar)
        iface.messageBar().pushWidget(widget, iface.messageBar().INFO)
        
        # Teil 1 =======================  Ebenen laden und attributieren  =============================
        if not OutOfQGIS:
            iface.mapCanvas().setRenderFlag( False )           
            # Projektname (-gruppe) in Root löschen
            rNode=QgsProject.instance().layerTreeRoot()
    
            for node in rNode.children():
                if str(type(node))  == "<class 'qgis._core.QgsLayerTreeGroup'>":
                    if node.name() == rootname:
                            rNode.removeChildNode(node)

            grpProjekt = iface.legendInterface().addGroup( rootname, False)
            iface.legendInterface().setGroupExpanded( grpProjekt, True )      

            #   0      1        2     
            # Ebene,layerid, layertyp
            while (qry4pri.next()):
                i=i+1
                #Progressbar weiterschalten
                try:
                    prgBar.setValue(i)
                    QCoreApplication.processEvents()
                except:
                    QtGui.QMessageBox.critical( None, "Abbruch","Vorgang durch Nutzereingriff beendet")
                    break
                
                GISDBTabName=None               
                if bDBTab and qry4pri.value(3):
                    clsdb1 = pgDataBase()
                    if clsdb1.CheckDBTabSpalte(qry4pri.value(3)):
                        GISDBTabName=qry4pri.value(3).lower()
                    else:
                        addFehler("Fehler Tabellenzugriff (" + qry4pri.value(3) + ") bei: " + lName )
                
                #VectorLayerPath (Art, ConnInfo, Epsg, LayerID, b3DDar , GISDbTab)

                vlp = clsdb.VectorLayerPath (qry4pri.value(2),ConnInfo,Epsg, qry4pri.value(1),b3DDar, GISDBTabName)
                if vlp:
                    # ================== 1. Schritt Layer einbinden =============================
                    #printlog (qry4pri.value(0)+ "|" + str(type(qry4pri.value(0))))
                    #printlog (vlp)
                    #errlog( qry4pri.value(0) + "\n" + vlp)
                    # QgsVectorFileWriter.writeAsVectorFormat(Layer,"hoppla.shp","utf-8",None,"ESRI Shapefile")
                    lName=toUTF8(qry4pri.value(0))
                    if lName <> qry4pri.value(0):
                        printlog (qry4pri.value(0) + ": UTF Korrektur vorm Erstellen notwendig")
                    Layer = iface.addVectorLayer(vlp, lName , "postgres")
                    if Layer:
                        if bLeer or Layer.featureCount() > 0:
                            if bSHPexp:
                                pShp=txtZielPfad + "/" + lName +".shp"
                                QgsVectorFileWriter.writeAsVectorFormat(Layer,pShp,txtCodePage,None,"ESRI Shapefile")
                                QgsMapLayerRegistry.instance().removeMapLayer( Layer.id() )
                                Layer = iface.addVectorLayer(pShp,lName , "ogr")
                        
                            Layer.setReadOnly()
                            iface.legendInterface().setLayerVisible(Layer, False) 

                            if bGenDar:
                            # ================== 2. Schritt Darstellung definieren  ================== 
                            #          Render(self, cgUser, qLayer, cgEbenenTyp, LayerID, bRolle, Group=0): 
                                if QGis.QGIS_VERSION_INT < 21200 and qry4pri.value(2) == 3:
                                    # Texte in Wien und Pisa:  ohne Rolle schreiben (nur erster Maßstab) Maßstab
                                    clsRendXML.Render(User, Layer, qry4pri.value(2), qry4pri.value(1),False,iDarGruppe)
                                else:                    
                                    # Neue Version über QML
                                    clsRendXML.Render(User, Layer, qry4pri.value(2), qry4pri.value(1),True,iDarGruppe)
                        else:
                            QgsMapLayerRegistry.instance().removeMapLayer( Layer.id() )
                    else:
                        if not (lName[-4:] == "(RL)" and QGis.QGIS_VERSION_INT < 21200):
                            addFehler("Fehler Layereinbindung bei: " + lName + "\n" + vlp)
                        else:
                            # Bei QGIS-Wien und leerem Layer (keine Referenzllinie) kommt es zum Fehler - welcher eigentlich ja keiner ist
                            debuglog (vlp + "|" + lName  + "|" + "postgres")
                else:
                    addFehler(u"Nicht unterstützt Typ " + str(qry4pri.value(2)) + ": " + lName)


        # print str(qry.size()) -> Absturz!!!???
        # Teil 2 =======================  Ebenen in die Struktur schieben  =============================
        widget = iface.messageBar().createMessage("Baum wird aufgebaut")
        prgBar = QtGui.QProgressBar()
        prgBar.setAlignment(Qt.AlignLeft)
        prgBar.setValue(0)
        prgBar.setMaximum(GesAnz)           
        widget.layout().addWidget(prgBar)
        iface.messageBar().pushWidget(widget, iface.messageBar().INFO)
        i=0
        
        #   0           1     2      3     4        5
        # Fachschale,Thema,Gruppe,Ebene,layerid, layertyp   
        while (qry.next()):
            i=i+1
            #Progressbar weiterschalten
            try:
                prgBar.setValue(i)
                QCoreApplication.processEvents()
            except:
                QtGui.QMessageBox.critical( None, "Abbruch","Vorgang durch Nutzereingriff beendet")
                break

            if qry.value(0) != Fachschale:
                newparent=True
                if not OutOfQGIS:
                    f = iface.legendInterface().addGroup( toUTF8(qry.value(0)), False,grpProjekt)
                    iface.legendInterface().setGroupExpanded( f, True )
                    iface.legendInterface().setGroupVisible( f, False )

            if newparent or qry.value(1) != Thema:
                newparent=True
                if not OutOfQGIS:
                    t = iface.legendInterface().addGroup( toUTF8(qry.value(1)), False,f)
                    iface.legendInterface().setGroupExpanded( t, False )
                    iface.legendInterface().setGroupVisible( t, False )
            
            if newparent or qry.value(2) != Gruppe:
                newparent=True
                if not OutOfQGIS:
                    g = iface.legendInterface().addGroup( toUTF8(qry.value(2)), False,t)
                    iface.legendInterface().setGroupExpanded( g, False )
                    iface.legendInterface().setGroupVisible( g, False )
            
            # Layer in Gruppen schieben 
            if not OutOfQGIS:
                # 1. Eine eventuelle Referenzlinie
                # Jetzt noch eine eventuelle Randlinie verschieben
                # das Verfahren über den "errechneten" Namen ist etwas dirty, 
                # aber die Randlinienen deshalb in die Layerliste zu übernehmen schein etwas überdimentioniert
                gu = None
                lName=toUTF8(qry.value(3))
                if lName <> qry.value(3):
                    printlog(qry.value(3) + ": UTF Korrektur vorm Verschieben notwendig")
                
                if qry.value(5) == 3: # Text
                    RLLayer = self.LayerbyName(lName + '(RL)')
                    if RLLayer:
                        if RLLayer.geometryType() == 1: # es ist eine Strecke 
                            gu = iface.legendInterface().addGroup( toUTF8(qry.value(3)), False,g)
                            iface.legendInterface().setGroupExpanded( gu, False )
                            iface.legendInterface().setGroupVisible( gu, False )
                            iface.legendInterface().moveLayer( RLLayer, gu )
                
                # self.ObjektAnzahlZeigen() -> kostet Zeit optional machen
 
                Layer = self.LayerbyName(lName)
                if Layer:
                    if gu:
                        # Textlayer mit Refrenzlinie
                        iface.legendInterface().moveLayer( Layer, gu )
                    else:
                        # Nomale Layer
                        iface.legendInterface().moveLayer( Layer, g )
                else:
                    printlog ("Layer wurde nicht verschoben: "  + qry.value(3)  )

                        
            Fachschale=qry.value(0)
            Thema=qry.value(1)
            Gruppe=qry.value(2)
            newparent=False
        
        # Anzeige wieder aktivieren, Progressbar rucksetzen
        if not OutOfQGIS:
            iface.mapCanvas().setRenderFlag( True )
            iface.messageBar().clearWidgets()
            iface.mapCanvas().refresh()
            iface.mapCanvas().zoomToSelected()
            # Reihenfolge laut LayerListe ab QGIS 2.12 
            try:
                iface.layerTreeCanvasBridge().setHasCustomLayerOrder(True)
            except:
                # in Wien und (Pisa) funktioniert das nicht
                addHinweis("\nBenutzerdefinierte Layserreihenfolge konnte nicht automatisch gesetzt werden!\nDiese muss in  dieser QGIS-Version manuell aktiviert werden.")
        if QGis.QGIS_VERSION_INT < 21200:
            addHinweis("Bis QGIS 2.12 ist nur eine eingeschränkte Textdarstellung möglich!\nAußerdem können keine Kreise dargestellt werden!")
        
        if len(getFehler()) > 0:
            errbox("\n\n".join(getFehler()))
        if len(getHinweis()) > 0:
            msgbox("\n\n".join(getHinweis()))        
                
if __name__ == "__main__":
    # zur zum lokalen testen 
    #app = QtGui.QApplication(sys.argv)
    #QgsApplication.initQgis()
    OutOfQGIS=True
    c=clsQGISAction()
    clsdb=pgDataBase()
    db=clsdb.OpenDatabase(clsdb.GetConnString())
 
    if  db :
        print clsdb.sqlStrukAlleLayer("'{B22183E0-3AEC-44ED-B0A8-60B2F02C6649}'")
        print clsdb.OpenRecordset(db,clsdb.sqlStrukAlleLayer("'{B22183E0-3AEC-44ED-B0A8-60B2F02C6649}'")) 
        qry = clsdb.OpenRecordset(db, clsdb.sqlStrukAlleLayer("'{B22183E0-3AEC-44ED-B0A8-60B2F02C6649}'")) 
        while (qry.next()):
            s=qry.value(0)
            printlog(s)
        
        #def QGISBaum(self, db, User, rootname, qry4pri, qry, bGenDar, bPrjNeu, OutOfQGIS=False)
        #c.QGISBaum(db,'000', clsdb.GetDBname(),qry,qry,True,True,True)
        

    else:
        QtGui.QMessageBox.critical( None, "Fehler beim Datenbankzu")
