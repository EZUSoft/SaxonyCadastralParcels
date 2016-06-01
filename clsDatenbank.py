# -*- coding: utf-8 -*-
"""
/***************************************************************************
 clsDatenbank
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

from qgis.core import *
from PyQt4.QtCore import QSettings
from PyQt4.QtSql import QSqlDatabase, QSqlQuery, QSqlError
from PyQt4 import QtGui
import os.path
from fnc4all import *
import tempfile

def sqlAtt4Massstab4All( Art, AktDef):
        # Attribute nach Maßstab - Grunddaten für alle Geometriearten gleich
        sSQL=""
        for i in range(5):
            if i>0:
                sSQL=sSQL + "\nUNION ALL\n"
            sSQL = sSQL + (
"SELECT  %i AS AttNum, deftable.defid AS ADid, defname AS ADname,fa_id AS ATTid, attrname AS ATTname, scrscale%i AS MMin, scrscale%i AS mMax, scrresize "
"FROM deftable INNER JOIN frameatttable ON deftable.scrattrname%i = frameatttable.fa_id where deftable.defid='%s' AND attrtype=%i"
) % (i+1,i+1,i+2,i+1,AktDef,Art)
   
        return sSQL

        
class pgDataBase():
    db=None    
    def GetConnString(self):
        s = QSettings( "EZUSoft", "CAIGOS-Konnektor" )
        service = s.value( "service", "" )
        host    = s.value( "host", "" )
        port    = s.value( "port", "5432" )
        dbname  = s.value( "dbname", "" )
        uid     = s.value( "uid", "" )
        pwd     = s.value( "pwd", "" )

        uri = QgsDataSourceURI()
        
        if service == "":
            uri.setConnection( host, port, dbname, uid, pwd )
        else:
            uri.setConnection(service, dbname, uid, pwd )
        return uri.connectionInfo()
    
    def GetEPSG(self):
        s = QSettings( "EZUSoft", "CAIGOS-Konnektor" )
        try:
            return int(s.value( "epsg"))
        except:
            return None
    
    def GetQSVGProjektPfad(self):
        return tempfile.gettempdir() + "/{D5E6A1F8-392F-4241-A0BD-5CED09CFABC7}/" + 'projekt_svg' + '/' + self.GetCGProjektName() + '/'
        #return os.path.dirname(__file__) + "/" + 'projekt_svg' + '/' + self.GetCGProjektName() + '/'
        
    def GetCGProjektPfad(self):
        s = QSettings( "EZUSoft", "CAIGOS-Konnektor" )
        return s.value("cgprojektpfad","nicht festgelegt")
    
    def GetCGProjektName(self):
        s = QSettings( "EZUSoft", "CAIGOS-Konnektor" )
        return s.value( "cgprojektname")  
    
    def GetDBname(self):
        s = QSettings( "EZUSoft", "CAIGOS-Konnektor" )
        return s.value( "dbname")
    
    def CurrentDB(self):
        if self.db:
            return self.db
        else:
            conninfo0 = self.GetConnString()
            self.db = self.OpenDatabase(conninfo0)
            return self.db
    
    def OpenDatabase(self,conninfo0):     
        QSqlDatabase.removeDatabase( "cgProjekt" )
        db = QSqlDatabase.addDatabase( "QPSQL", "cgProjekt" )
        db.setConnectOptions( conninfo0 )

        if db.open():
            return (db)
        else:
            addFehler( db.lastError().text())
   
    def CloseDatabase(self,db):
        db.close()
        # QSqlDatabasePrivate::removeDatabase: connection 'cgProjekt' is still in use, all queries will cease to work.
        # kein Weg gefunden die  Warnung anzuschalten
        QSqlDatabase.removeDatabase( "cgProjekt" )

    
    def CheckVerbDaten(self,EPSG=None,CGProjektPfad=None,CGProjektName=None,conninfo=None, NurFehler=False):
        Meldung =""
        Fehler=""
        Warnung = ""
        if not EPSG:
            EPSG = self.GetEPSG()
        if not CGProjektPfad:
            CGProjektPfad = self.GetCGProjektPfad()    
        if not CGProjektName:
            CGProjektName = self.GetCGProjektName()      
        if not conninfo:
            conninfo = self.GetConnString()
        
        if self.OpenDatabase(conninfo):
            Meldung= u"Datenbankverbindung erfolgreich"
            #QtGui.QMessageBox.information( None,'Datenbankzugriff',u"Datenbankverbindung erfolgreich.")
        else:
            Fehler=u"Datenbankverbindung schlug fehl:\n" + "\n".join(getFehler())
            resetFehler()
            #QtGui.QMessageBox.critical( None, "Fehler beim Datenbankzugriff", u"Datenbankverbindung schlug fehl." )

        if EPSG == None or EPSG == 0 or EPSG == "0":
            Fehler=Fehler + "\n" if Fehler else ""
            Fehler=Fehler+"EPSG-Code nicht definiert"
        
        if CGProjektName == "":
            Fehler=Fehler + "\n" if Fehler else ""
            Fehler=Fehler+"Kein Projektname festgelegt"
    
        if CGProjektPfad == "":
            Warnung=Warnung + "\n" if Warnung else ""
            Warnung=Warnung+u"CAIGOS Projektverzeichnis nicht festgelegt\n  ->Es können keinen SVG-Symbole generiert werden"            
        else:
            sigPfad = CGProjektPfad + "/signatur"
            if os.path.exists(sigPfad):
                Meldung = Meldung + "\n" if Meldung else ""
                Meldung = Meldung + "CAIGOS Signaturverzeichnis gefunden"
            else:
                Warnung = Warnung + "\n" if Warnung else ""
                Warnung = Warnung + sigPfad + u"\nCAIGOS Signaturverzeichnis nicht gefunden\n  ->Es können keinen SVG-Symbole generiert werden"            
        
        if Fehler:
            QtGui.QMessageBox.critical( None, u"Es sind Fehler aufgetreten", Fehler )
            return False
        else:  
            if not NurFehler:
                QtGui.QMessageBox.information( None,u'Folgende Tests waren erfolgreich:',Meldung)
            if Warnung:
                QtGui.QMessageBox.information( None,u'Konfigurationsproblem',Warnung)
            return True    
            
    def OpenRecordset(self,db,sqlString):
        qry = QSqlQuery(db)
        if not qry.exec_( sqlString ):
            err = ("OpenRecordset:"  + "\n" +
            "Text: " + qry.lastError().text() +  "\n" +
            "Type: " + str(qry.lastError().type()) +  "\n" +
            "Number: " + str(qry.lastError().number()))
            errlog (err)
        return qry
        
    def GeoTabName4Art (self,Art):
        table=None
        if Art == 0: # Point      
            table="pointssqlspatial"
        if Art == 1: # Line
            table="linessqlspatial"
        if Art == 2: # Kreis
            table = None
        if Art == 3: # Text
            table="textssqlspatial"
        if Art == 4: # Bemaßung
            table = None
        if Art == 5: # Polylinie
            table="segssqlspatial"
        if Art == 6: # Fläche
            table="polyssqlspatial"    
        return table
    
    def sqlAtt4Massstab (self, Art, AktDef, Group):
        sSQL=sqlAtt4Massstab4All(Art,AktDef)      
        if Art == 0: # Point      
            sSQL="select * from (" + sSQL +") as dummy inner join pointatttable ON dummy.ATTid = pointatttable.pta_idfa where pointatttable.pta_ag=" + str(Group)  + " order by attnum"  
        if Art == 1: # Line
            sSQL=sSQL
        if Art == 2: # Kreis
            sSQL = sSQL
        if Art == 3: # Text
           sSQL="select * from (" + sSQL +") as dummy inner join textatttable ON dummy.ATTid = textatttable.ta_idfa where textatttable.ta_ag=" + str(Group)  + " order by attnum"  
        if Art == 4: # Bemaßung
            sSQL = sSQL
        if Art == 5: # Polylinie
            sSQL="select * from (" + sSQL +") as dummy inner join segatttable  ON dummy.ATTid = segatttable.sa_idfa where segatttable.sa_ag=" + str(Group)  + " order by attnum"  
        if Art == 6: # Fläche
            sSQL="select * from (" + sSQL +") as dummy inner join polyatttable  ON dummy.ATTid = polyatttable.poa_idfa where polyatttable.poa_ag=" + str(Group) + " order by attnum"  
        return sSQL   

    def sqlAttParam4IDandArt(self, Art, AktAttID, Group):
        sSQL=None
        if Art == 0: # Point      
                  #                      0                     1           2        3      4       5      6       7              8           9            10          11
            sSQL=("SELECT la_idfa AS st_attid, attrname AS st_attrname, la_linenr, used, color, sizemm, basemm, basecolor, linesigattr, linesigbegin,linesigofs, linesigofsline, "
                   #           12            13            14            15          16           17          18       19          20          21          22           23
                  "       lineoffset, sigbeginattr, sigmiddleattr, sigendattr, transparent, denyatpercent, penid, basepenid, sigbeginpos, sigendpos, sigmiddlepos, geocolor, "
                   #           24
                  "       scrresize "
                  "FROM frameatttable INNER JOIN lineatttable ON frameatttable.fa_id = lineatttable.la_idfa "
                  "WHERE la_idfa='%s' AND used='J' AND la_ag=%i order by la_linenr") %(AktAttID, Group)
        if Art == 1 or Art == 5: # Strecke, Polylinie
                  #                      0                     1           2        3      4       5      6       7              8           9            10          11
            sSQL=("SELECT la_idfa AS st_attid, attrname AS st_attrname, la_linenr, used, color, sizemm, basemm, basecolor, linesigattr, linesigbegin,linesigofs, linesigofsline, "
                   #           12            13            14            15          16           17          18       19          20          21          22           23
                  "       lineoffset, sigbeginattr, sigmiddleattr, sigendattr, transparent, denyatpercent, penid, basepenid, sigbeginpos, sigendpos, sigmiddlepos, geocolor, "
                   #           24
                  "       scrresize, pentable.* "
                  "FROM (frameatttable INNER JOIN lineatttable ON frameatttable.fa_id = lineatttable.la_idfa) "
                  "INNER JOIN pentable ON lineatttable.penid =pentable.id "
                  "WHERE la_idfa='%s' AND used='J' AND la_ag=%i order by la_linenr") %(AktAttID, Group)

        if Art == 2: # Kreis
            sSQL = None
        if Art == 3: # Text
            # nur noch für alte Version Rendering Wien 
                  #          0        1       2         3        4       5        6       7      8
            sSQL=("SELECT defname, defid , attrname, lineattr, color, sizemm, fontname, bold, italic, "
                  #             9         10          11        12         13             14         15        16       17       18        19       20
                  "         underline, freestyle, textalign, frametext, framecolor, framewidthmm, bkcolor, lineattr, tabpos1, tabpos2, usememo, blattnord, "
                  #             21          22             23               24            25       26
                  "         oneline, charframetext, charframecolor, charframewidthmm, quality, ofsalign "
                  "  FROM (textatttable INNER JOIN deftable ON textatttable.ta_idfa = deftable.scrattrname1) "
                  "        INNER JOIN frameatttable ON textatttable.ta_idfa = frameatttable.fa_id "
                  "  WHERE defid='%s' AND textatttable.ta_ag=%i;") % (AktAttID,Group)
            #sSQL=None # unused
        if Art == 4: # Bemaßung
            sSQL = None

        if Art == 6: # Fläche
            sSQL=""       
        return sSQL

    
    def VectorLayerPath (self, Art, ConnInfo, Epsg, LayerID):
        uri = None
        if LayerID:
            where="layerid='%s'" % (LayerID)
        else:
            where =""
            
        if QGis.QGIS_VERSION_INT < 21200: # ab Lyon
            # Unterabfrage definieren - macht das Ganze aber ziemlich langsam und ist bei Essen nicht mehr notwendig
            IndexGen1="(SELECT row_number() over () AS _uid_,* FROM "
            IndexGen2=" as dummy)"
            Key="_uid_"
        else:
            IndexGen1 =""
            IndexGen2 =""
            Key="objid"

            
        if Art == 0: # Point      
            table=("%s(select objid,layerid,povchanged,georestr,dokucount,defid,objpri,objclass,alpha,isdelta,deltar,deltah,sigwidth,sigheight, "
                           "st_setsrid(st_translate(shape, deltar, deltah),%d) as sid_shape from pointssqlspatial)%s") % (IndexGen1,Epsg,IndexGen2)
            uri=("%s key='%s' srid=%s type=Point table='%s' (sid_shape) sql=%s") % (ConnInfo, Key, Epsg, table, where)
        if Art == 1: # Line
            table=("%s(select *,st_setsrid(shape,%d) as sid_shape from linessqlspatial)%s") % (IndexGen1,Epsg,IndexGen2)
            uri=("%s key='%s' srid=%d type=LineString table='%s' (sid_shape) sql=%s") % (ConnInfo, Key, Epsg, table, where)
        if Art == 2: # Kreis
            uri = None
        if Art == 3: # Text
            table=("%s(select *,st_setsrid(shape,%d) as sid_shape from textssqlspatial)%s") % (IndexGen1,Epsg,IndexGen2)
            uri=("%s key='%s' srid=%d type=Point table='%s' (sid_shape) sql=%s") % (ConnInfo, Key, Epsg, table, where)

        if Art == 4: # Bemaßung
            uri = None
        if Art == 5: # Polylinie
            table=("%s(select *,st_setsrid(shape,%d) as sid_shape from segssqlspatial)%s") % (IndexGen1,Epsg,IndexGen2)
            uri=("%s key='%s' srid=%d type=LineString table='%s' (sid_shape) sql=%s") % (ConnInfo, Key, Epsg, table, where)
        if Art == 6: # Fläche
            table=("%s(select *,st_setsrid(shape,%d) as sid_shape from polyssqlspatial)%s") % (IndexGen1,Epsg,IndexGen2)
            uri=("%s key='%s' srid=%d type=MultiPolygon table='%s' (sid_shape) sql=%s") % (ConnInfo, Key, Epsg, table, where)
        
        return uri
        
        
    def sqlStrukAlleLayer(self,LayerList = None):
        sSQL=""
        if LayerList:
            sSQL = "WHERE layerid In ("
            sSQL = sSQL + LayerList
            sSQL = sSQL + ")"
        # Alphabetische Reihenfolge für Explorerbaum, dabei Layername DESC, da Einfügereihenfolge über moveLayer umgekeht
        sSQL = (u"SELECT dbname  as Fachschale, entityname as Thema, groupname as Gruppe, layername as layer, layerid, layertyp "
                    "FROM (enttable INNER JOIN grptable ON enttable.entityid = grptable.entityid) "
                    "INNER JOIN lyrtable ON (grptable.groupid = lyrtable.groupid) AND (enttable.entityid = lyrtable.entityid) "
                    "%s order by dbname,entityname,groupname,layername DESC") % (sSQL)
        return sSQL

    def sqlAlleLayerByPri(self,UserNum = '000', LayerList = None):
        sSQL=""
        if LayerList:
            if len(LayerList.split(",")) == 1:
                sSQL =   "AND lyrtable.layerid = " + LayerList     
            else:
                sSQL = "AND lyrtable.layerid In ("
                sSQL = sSQL + LayerList
                sSQL = sSQL + ")"
        # Ebenen nach Prioritäten sortiert
        sSQL = (u"SELECT layername, lyrtable.layerid, layertyp "
                    "FROM prptable INNER JOIN lyrtable ON prptable.layerid = lyrtable.layerid "
                    "WHERE usernr='%s' %s "
                    "ORDER BY priority DESC") % (UserNum,sSQL)
        return sSQL
    
    def sqlAttDef4Layer(self, Art, LayerID):
        # verwendete Objekt-Attributdefinitionen aus der Geometrietabelle holen
        TabName=self.GeoTabName4Art(Art)
        if TabName:
            return (u"SELECT DISTINCT %s.defid, COALESCE(defname, '        ') as sortdefname FROM %s LEFT JOIN deftable ON %s.defid =deftable.defid where layerid='%s' order by sortdefname") % (TabName,TabName,TabName,LayerID)
        else:
            return None
    
    def AttDefID4Layer(self, db, LayerID, cgUser):
        # Attributdefinitionen der Ebene auslesen
        sqlString=("select defid from prptable where layerid='%s' and usernr='%s'") %(LayerID, cgUser)
        rs = self.OpenRecordset(db,sqlString)
        rs.next() # erster (und letzer) Datensatz
        return rs.value(0)
    
    def AttDefName4ID (self,db,DefID):
        # Name der Attributdefinition aus der DefID ermitteln
        sqlString=("SELECT defname FROM  deftable WHERE defid ='%s'") % (DefID)
        rs = self.OpenRecordset(db,sqlString)
        rs.next() # erster (und letzer) Datensatz
        return rs.value(0)

                   
if __name__ == "__main__":
    # zur zum lokalen testen
    app = QtGui.QApplication([])
    clsdb=pgDataBase()
    clsdb.CheckVerbDaten(None,None,None,None, False)
    db = clsdb.CurrentDB()
    if db:
        #print clsdb.sqlAttParam4IDandArt(6, "{CFAC4A38-A2EE-4419-AE29-D0A0BACAC3B5}", 0)
        #print clsdb.sqlAtt4Massstab(0,"{FE5E17AD-2C4D-423E-A705-7393C57914D8}",0)
        print clsdb.sqlAttParam4IDandArt( 1, "{70F5BC71-93C3-4282-A0F4-2EE198EE51E0}", Group = 0)
        #rs=clsdb.OpenRecordset(db,clsdb.sqlAttParam4IDandArt( 1, "{70F5BC71-93C3-4282-A0F4-2EE198EE51E0}", Group = 0))

        clsdb.CloseDatabase(db)
    else:
        print "Fehler"
    #clsdb.Check(


