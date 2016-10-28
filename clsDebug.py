# -*- coding: utf-8 -*-
from qgis.core import *
from qgis.gui import *
from qgis.utils import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *

# Initialize Qt resources from file resources.py
import resources

# Import der 3 Einzelmodule
from uiExplorer import uiExplorer
from uiAbout import uiAbout
from uiDBAnbindung import uiDBAnbindung
from clsDatenbank import *
import time
from clsQGISAction import clsQGISAction

import os.path
# import some modules used in the example
from qgis.core import *
from PyQt4 import QtCore, QtGui
import traceback
import time
from fnc4all import *
def OberRolle(qtyp,Name,Bedingung):
        # Erstellen der "Obergruppe"
        symbol = QgsSymbolV2.defaultSymbol(qtyp)
        renderer = QgsRuleBasedRendererV2(symbol)
        root_rule = renderer.rootRule()
        new_rule = root_rule.children()[0].clone()
        new_rule.setFilterExpression("defid = '{00000000-0000-0000-0000-000000000000}'")
        new_rule.setLabel("Name der AttDef")
        new_rule.setSymbol(None) # Kein Symbol bei "Oberrolle)
        root_rule.appendChild(new_rule)
        return root_rule, renderer,new_rule
        
def EineRolle(root_rule,Rollenname,Von, Bis):
        rule = root_rule.children()[0].clone()
        rule.setLabel(Rollenname)       
        rule.setScaleMinDenom(Von)
        rule.setScaleMaxDenom(Bis)
        return rule
        
class clsDebug():
    def ParamOfLayerByName (self, Layername):
        Layer = None
        for l in QgsMapLayerRegistry.instance().mapLayers().values():
            if l.name() == Layername:
                Layer = l
                break
        if Layer:
            label = QgsPalLayerSettings()
            print label.fieldName
            label.readFromLayer(Layer)
            print label.fieldName
        else:
            print "Layer: '", Layername, "'existiert nicht"

    def LayerLoeschen(self):
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

            
    def ObjektAnzahlZeigen(self):
        root = QgsProject.instance().layerTreeRoot()
        for child in root.children():
            if isinstance(child, QgsLayerTreeLayer):
                child.setCustomProperty("showFeatureCount", True)
    
    def PunktMitDelta4Wien(self,ConnInfo,layerid, Ebene, OutOfQGIS=False):
        # if OutOfQGIS or QGis.QGIS_VERSION == '2.8.1-Wien':
        table="(SELECT row_number() over () AS _uid_,* FROM (select objid,layerid,povchanged,georestr,dokucount,defid,objpri,objclass,alpha,isdelta,deltar,deltah,sigwidth,sigheight, st_setsrid(st_translate(shape, deltar, deltah),25833) as shape from pointssqlspatial) as dummy)"
        
        where="layerid='%s'" % (layerid) 
        id = "_uid_"  
        epsg=25833            
        uri=("%s key='%s' srid=%s type=Point table='%s' (shape) sql=%s") % (ConnInfo, id, epsg, table, where)

        if not OutOfQGIS:
            LayerName =iface.addVectorLayer(uri, Ebene , "postgres")
            LayerName.setReadOnly()
        else:
            print uri

    def PunktMitDelta4Essen(self,ConnInfo,layerid, Ebene,OutOfQGIS=False):
        # if OutOfQGIS or QGis.QGIS_VERSION == '2.14.1-Essen':
        table=("(select objid,layerid,povchanged,georestr,dokucount,defid,objpri,objclass,alpha,isdelta,deltar,deltah,sigwidth,sigheight, "
                   "st_setsrid(st_translate(shape, deltar, deltah),25833) as shape from pointssqlspatial)")
        
        where="layerid='%s'" % (layerid) 
        id = "objid"  
        epsg=25833            
        uri=("%s key='%s' srid=%s type=Point table='%s' (shape) sql=%s") % (ConnInfo, id, epsg, table, where)

        if not OutOfQGIS:
            LayerName = iface.addVectorLayer(uri, Ebene , "postgres")
            LayerName.setReadOnly()
        else:
            print uri

    def Flaeche4Essen(self,ConnInfo,layerid, Ebene,OutOfQGIS=False):
        # if OutOfQGIS or QGis.QGIS_VERSION == '2.14.1-Essen':
        table=("(select *,st_setsrid(shape,25833) as sid_shape from polyssqlspatial)")
        
        where="layerid='%s'" % (layerid) 
        id = "objid"  
        epsg=25833            
        uri=("%s key='%s' srid=%s type=MultiPolygon table='%s' (sid_shape) sql=%s") % (ConnInfo, id, epsg, table, where)

        if not OutOfQGIS:
            LayerName = iface.addVectorLayer(uri, Ebene , "postgres")
            if LayerName:
                LayerName.setReadOnly()
            else:
                print "Fehler: " + uri + " " + Ebene
        else:
            print uri
        return LayerName
    def Flaeche4Wien(self,ConnInfo,layerid, Ebene,OutOfQGIS=False):
        # if OutOfQGIS or QGis.QGIS_VERSION == '2.14.1-Essen':
        table=("polyssqlspatial")
        
        where="layerid='%s'" % (layerid) 
        id = "objid"  
        # Übergabe EPSG funktioniert nicht, wenn nicht gleichzeitig das Shape-Feld korrigiert wird
        # deshalb bleibt im Moment nur die Übergabe von 0 und eine manuelle Einstellung
        epsg=0            
        uri=("%s key='%s' srid=%s type=MultiPolygon table=%s (shape) sql=%s") % (ConnInfo, id, epsg, table, where)

        if not OutOfQGIS:
            LayerName = iface.addVectorLayer(uri, Ebene , "postgres")
            if LayerName:
                LayerName.setReadOnly()
            else:
                print "Fehler: " + uri + " " + Ebene
        else:
            print uri
    
    def PunktMitMitLabelV1(self):
        # if OutOfQGIS or QGis.QGIS_VERSION == '2.8.1-Wien':
        #table="(SELECT row_number() over () AS _uid_,* FROM (select objid,layerid,povchanged,georestr,dokucount,defid,objpri,objclass,alpha,isdelta,deltar,deltah,sigwidth,sigheight, st_setsrid(st_translate(shape, deltar, deltah),25833) as shape from pointssqlspatial) as dummy)"
        clsdb=pgDataBase()
        ConnInfo=clsdb.GetConnString()
        vlp = clsdb.VectorLayerPath (3,ConnInfo,25833, None)
        layer = iface.addVectorLayer(vlp,"MeineTexteV1" , "postgres")
        
        # self.setScale( layer, d['label'] )
        geom="point"
        sym = QgsSymbolV2.defaultSymbol( QGis.Point if geom=="point" else QGis.Line )
        if  geom=="point":
            sym.setSize( 0.0 )
        else:
            sym.changeSymbolLayer( 0, QgsSimpleLineSymbolLayerV2( Qt.black, 0.0, Qt.NoPen ) )
        layer.setRendererV2( QgsSingleSymbolRendererV2( sym ) )
        #self.iface.legendInterface().refreshLayerSymbology( layer )
        #self.iface.legendInterface().moveLayer( layer, thisGroup )

        lyr = QgsPalLayerSettings()
        lyr.fieldName = "pstext"
        lyr.isExpression = False
        lyr.enabled = True
        lyr.fontSizeInMapUnits = True
        lyr.textFont.setPointSizeF( 2.5 )
       
        lyr.textFont.setFamily( "Courier" )
        lyr.bufferSizeInMapUnits = True
        lyr.bufferSize = 0.25
        lyr.displayAll = True
        lyr.upsidedownLabels = QgsPalLayerSettings.ShowAll
        lyr.scaleVisibility = True
        lyr.scaleVisibility = True
        print "MultiLineAlignment: " + str(lyr.MultiLineAlignment)

        print str(lyr.Bold)
        lyr.MultiLineWrapChar = "r"


        
        if geom == "point":
            lyr.placement = QgsPalLayerSettings.AroundPoint
        else:
            lyr.placement = QgsPalLayerSettings.Curved
            lyr.placementFlags = QgsPalLayerSettings.AboveLine

        lyr.setDataDefinedProperty( QgsPalLayerSettings.Size, True, False, "", "tsize" )
        lyr.setDataDefinedProperty( QgsPalLayerSettings.Family, True, False, "", "family" )
        lyr.setDataDefinedProperty( QgsPalLayerSettings.Italic, True, False, "", "italic" )
        lyr.setDataDefinedProperty( QgsPalLayerSettings.Bold, True, False, "", "bold" )
        lyr.setDataDefinedProperty( QgsPalLayerSettings.Hali, True, False, "", "halign" )
        lyr.setDataDefinedProperty( QgsPalLayerSettings.Vali, True, False, "", "valign" )
        lyr.setDataDefinedProperty( QgsPalLayerSettings.Color, True, True, "1234", "1234" )
        lyr.setDataDefinedProperty( QgsPalLayerSettings.FontLetterSpacing, True, False, "", "fontsperrung" )
        lyr.setDataDefinedProperty( QgsPalLayerSettings.MultiLineAlignment  , True, True, "Center", "" )
        lyr.setDataDefinedProperty( QgsPalLayerSettings.MultiLineWrapChar  , True, True, r"'\\n'", "" )
        #lyr.setDataDefinedProperty(QgsPalLayerSettings.Bold, True, True, '1', '')
        #lyr.setDataDefinedProperty(QgsPalLayerSettings.Italic, True, True, '1', '')
        

        if geom == "point":
            lyr.setDataDefinedProperty( QgsPalLayerSettings.PositionX, True, False, "", "tx" )
            lyr.setDataDefinedProperty( QgsPalLayerSettings.PositionY, True, False, "", "ty" )
            lyr.setDataDefinedProperty( QgsPalLayerSettings.Rotation, True, False, "", "tangle" )
        lyr.writeToLayer( layer )
        iface.legendInterface().refreshLayerSymbology( layer )
   
    def PunktMitMitLabelV2(self):
        # if OutOfQGIS or QGis.QGIS_VERSION == '2.8.1-Wien':
        #table="(SELECT row_number() over () AS _uid_,* FROM (select objid,layerid,povchanged,georestr,dokucount,defid,objpri,objclass,alpha,isdelta,deltar,deltah,sigwidth,sigheight, st_setsrid(st_translate(shape, deltar, deltah),25833) as shape from pointssqlspatial) as dummy)"
        clsdb=pgDataBase()
        ConnInfo=clsdb.GetConnString()
        vlp = clsdb.VectorLayerPath (3,ConnInfo,25833, None)
        qLayer = iface.addVectorLayer(vlp,"MeineTexteV2" , "postgres")
        
        symbol = QgsSymbolV2.defaultSymbol(QGis.Point)
        symbol.setSize( 0.0 )
        qLayer.setRendererV2( QgsSingleSymbolRendererV2( symbol ) )

        QgsPalLayerSettings().writeToLayer( qLayer )
        qLayer.setCustomProperty("labeling","pal")
        qLayer.setCustomProperty("labeling/dataDefined/Rotation","alpha")
        qLayer.setCustomProperty("labeling/displayAll","true")
        qLayer.setCustomProperty("labeling/enabled","true")
        qLayer.setCustomProperty("labeling/fieldName","pstext")
        qLayer.setCustomProperty("labeling/fontBold","False")
        qLayer.setCustomProperty("labeling/fontFamily","Arial")
        qLayer.setCustomProperty("labeling/fontItalic","False")
        qLayer.setCustomProperty("labeling/fontSize","2")
        qLayer.setCustomProperty("labeling/fontSizeInMapUnits","true")
        qLayer.setCustomProperty("labeling/obstacle","false")
        qLayer.setCustomProperty("labeling/placement","1")
        qLayer.setCustomProperty("labeling/placementFlags","0")
        qLayer.setCustomProperty("labeling/quadOffset","1")
        qLayer.setCustomProperty("labeling/textColorA","255")
        qLayer.setCustomProperty("labeling/textColorB","000")
        qLayer.setCustomProperty("labeling/textColorG","000")
        qLayer.setCustomProperty("labeling/textColorR","255")
        qLayer.setCustomProperty("labeling/textTransp","0")
        qLayer.setCustomProperty("labeling/upsidedownLabels","2")
        qLayer.setCustomProperty("labeling/wrapChar",r"\n")  
    


    def EineLinieByRuleV1(self):
        clsdb=pgDataBase()
        ConnInfo=clsdb.GetConnString()
        vlp = clsdb.VectorLayerPath (1,ConnInfo,25833, None)
        layer = iface.addVectorLayer(vlp,"DieLinienPerRule" , "postgres")
        
        # Erstellen der "Obergruppe"
        root_rule, renderer, new_rule = OberRolle(layer.geometryType(),"attrname","defid = ''")
        lineMeta = QgsSymbolLayerV2Registry.instance().symbolLayerMetadata("SimpleLine")
    
        rule= EineRolle(root_rule,"Rollenname",10, 100)
        symbol = QgsSymbolV2.defaultSymbol(layer.geometryType())
        symbol.deleteSymbolLayer(0)    
         
        road_rules = (
            ('Major road', '"type" LIKE \'major\'', 'orange', None),
            ('Minor road', '"type" LIKE \'minor\'', 'black', (0.0, 2500.0,)),
            ('Residential road', '"type" LIKE \'residential\'', 'grey', (100.0, 1000.0,)),
        )       

        
        # erste teillinie
        qmap={}
        qmap['offset']="-1.23"
        qmap["offset_unit"]='MapUnit'
        lineLayer = lineMeta.createSymbolLayer(qmap)
        symbol.appendSymbolLayer(lineLayer)
        
        # zweite Teilinie
        qmap['offset']="1.23"
        qmap["offset_unit"]='MapUnit'
        lineLayer = lineMeta.createSymbolLayer(qmap)
        symbol.appendSymbolLayer(lineLayer)
        
        rule.setSymbol(symbol)
        new_rule.appendChild(rule)

        # =========================================================
        # 2. Maßstab
        rule = root_rule.children()[0].clone()
        rule.setLabel(u"zwiter Maßstab")       
        rule.setScaleMinDenom(100)
        rule.setScaleMaxDenom(1000)
        #rule.setFilterExpression(expression)
        symbol = QgsSymbolV2.defaultSymbol(layer.geometryType()) 
        symbol.deleteSymbolLayer(0)
        
        # erste teillinie
        qmap={}
        qmap['offset']="-1.23"
        qmap["offset_unit"]='MapUnit'
        qmap["color"]='red'
        lineLayer = lineMeta.createSymbolLayer(qmap)
        symbol.appendSymbolLayer(lineLayer)
        
        # zweite Teilinie
        qmap['offset']="1.23"
        qmap["offset_unit"]='MapUnit'
        qmap["color"]='red'
        lineLayer = lineMeta.createSymbolLayer(qmap)
        symbol.appendSymbolLayer(lineLayer)
        
        rule.setSymbol(symbol)
        new_rule.appendChild(rule)

        # delete the default rule
        root_rule.removeChildAt(0)

        # apply the renderer to the layer
        layer.setRendererV2(renderer)

    def EineLinieByCategoryV2(self):
        clsdb=pgDataBase()
        ConnInfo=clsdb.GetConnString()
        vlp = clsdb.VectorLayerPath (1,ConnInfo,25833, None)
        layer = iface.addVectorLayer(vlp,"DieLinienPerKategorie" , "postgres")       
        
        r = QgsCategorizedSymbolRendererV2( "defid" )
        r.deleteAllCategories()
        
        
        registry = QgsSymbolLayerV2Registry.instance()
        lineMeta = registry.symbolLayerMetadata("SimpleLine")
        symbol = QgsSymbolV2.defaultSymbol(layer.geometryType())
        symbol.deleteSymbolLayer(0)
        
        # Line layer
        qmap={}
        qmap['offset']="-1.23"
        qmap["offset_unit"]='MapUnit'
        lineLayer = lineMeta.createSymbolLayer(qmap)
        symbol.appendSymbolLayer(lineLayer)
        lineLayer = lineMeta.createSymbolLayer({'offset': '1.0'})
        lineLayer.setColor(QtGui.QColor("red"))
        symbol.appendSymbolLayer(lineLayer)
        
        sym = symbol
        #sym.setColor(QtGui.QColor("red"))
        r.addCategory( QgsRendererCategoryV2( "AktDefID1", sym, "Attributname1" ) )
        
        
        sym = QgsSymbolV2.defaultSymbol( QGis.Line )
        sym.setColor(QtGui.QColor("blue"))
        r.addCategory( QgsRendererCategoryV2( "AktDefID2", sym, "Attributname2" ) )

        layer.setRendererV2( r)

        
        
    # AddLayerByID    
    def debugplugin(self,OutOfQGIS=False):
        #self.ParamOfLayerByName("MeineTexte")
        self.LayerLoeschen()
        #self.PunktMitMitLabelV1()
        #self.PunktMitMitLabelV2()
        #self.EineLinieByRuleV1()
        #self.EineLinieByCategoryV2()
        #self.ObjektAnzahlZeigen()
        #print QtGui.QFileDialog.getOpenFileName(None, 'database.ini im Projektordner des CAIGOS-Projektes', 'database.ini')
        
        # =============================================================================
        # 1. Layer laden
        qLayer= iface.addVectorLayer("d:/tar/flaechen.shp", u"MeinFlächenLayer", "ogr")
        
        # =============================================================================
        # 2. Rendern by XML
        """
        fillSymbol = QgsSymbolV2.defaultSymbol(qLayer.geometryType())
        renderer = QgsRuleBasedRendererV2(fillSymbol)
        root_rule = renderer.rootRule()
        
        # "Oberrolle" normalerweise mit Filter
        new_rule = root_rule.children()[0].clone()
        new_rule.setLabel("Oberrolle")
        new_rule.setSymbol(None) # Kein Symbol bei "Oberrolle)
        root_rule.appendChild(new_rule)

        # 1. zugehörige Unterrolle
        rule = root_rule.children()[0].clone()
        rule.setLabel("Rolle1")       
        rule.setScaleMinDenom(1)
        rule.setScaleMaxDenom(1000)
        
        fillSymbol = QgsSymbolV2.defaultSymbol(qLayer.geometryType())
        fillSymbol.deleteSymbolLayer(0)   
        rule.setSymbol(fillSymbol)
        new_rule.appendChild(rule)  

        # 1. Füllung definiereni
        qmap={}
        qmap["color"]= "12345" # fncLongTosRGB(fncfield(rsParam,"brushcolor"),True if fncfield(rsParam,"transparent") == "J" else False)
        qmap["distance"]="2.5"
        qmap["angle"]="45"
        qmap["distance_unit"]="MM"      
        qmap["outline_style"]='no' # hier kein Rand# 
        qmap["line_color"]="34567"
        qmap["line_width"]="1.15"
        qmap["line_width_unit"]="MM"
        qmap["line_style"]="solid"
        Meta=QgsSymbolLayerV2Registry.instance().symbolLayerMetadata("LinePatternFill")        
        fillSymbol.appendSymbolLayer(Meta.createSymbolLayer(qmap))
        
        
        qmap={'line_color': '10,110,220', 'line_width': '1.234', 'distance_unit': 'MapUnit', 'angle': '45.0', 
              'offset_unit': 'MapUnit', 'distance': '5.0', 'outline_style': 'no', 'use_custom_dash': '1', 'offset': '0.0', 
              'customdash': '4.0;3.0;2.0;1.0;0.0;0.0;0.0;0.0;0.0;0.0', 'line_width_unit': 'MM'}
        Meta=QgsSymbolLayerV2Registry.instance().symbolLayerMetadata("LinePatternFill")        
        fillSymbol.appendSymbolLayer(Meta.createSymbolLayer(qmap))     

        
        
        
        
        lineMeta = QgsSymbolLayerV2Registry.instance().symbolLayerMetadata("SimpleLine")
        qmap={}
        qmap["line_color"]="12345"
        qmap["line_width"]="4.3"
        qmap["line_width_unit"]="MM"

        lineLayer = lineMeta.createSymbolLayer(qmap)
        fillSymbol.appendSymbolLayer(lineLayer)
        
    
        root_rule.removeChildAt(0)
        qLayer.setRendererV2(renderer)
        """
class mytest(QObject):
        showProgress = pyqtSignal(int,int)
        showStatusMessage = pyqtSignal(str)


        def progress(self,i,m,s):
                self.showStatusMessage.emit( u"%s/%s" % (alkisplugin.themen[i]['name'],m) )
                self.showProgress.emit( i*5+s, len(alkisplugin.themen)*5 )
                QCoreApplication.processEvents()

        def iregndwas(self):
            self.showProgress.connect( self.iface.mainWindow().showProgress )
            self.showStatusMessage.connect( self.iface.mainWindow().showStatusMessage )


        
            self.progress(iThema, u"Flächen", 0)        #self.ObjektAnzahlZeigen()

if __name__ == "__main__":
    # zur zum lokalen testen 
    app = QtGui.QApplication(sys.argv)
    #QgsApplication.initQgis()

    #QtGui.QMessageBox.question(None, 'Message',"Are you sure to quit?", QtGui.QMessageBox.Yes |  QtGui.QMessageBox.No, QtGui.QMessageBox.No)
    
    #OutOfQGIS=True
    #printlog ("printlog:ÄÖÜ",4)
    #c=clsDebug()
    #c.debugplugin(True)

    clsdb=pgDataBase()
    db=clsdb.CurrentDB()
    u=(u'select * from deftable')
    #s=('select * from "tabÄÖÜ"').decode("utf-8")
    #print s
    #print u
    #print type(str1),str1,str1.encode("utf-8")
    #print s
    #print u
    if  db :
        q=clsdb.OpenRecordset(db,u)
        rec = q.record()
        anz=rec.count()
        ds=""
        q.next()
        for f in range(q.record().count()):
            ds = ds + u"|" + str(q.value(f))
        print ds
        #q.next()
        #nameCol = rec.indexOf("name") # index of the field "name"
        #while q.next():
        #    print q.value(nameCol) # output all names
 
    else:
        QtGui.QMessageBox.critical( None, "Fehler beim Datenbankzu")

