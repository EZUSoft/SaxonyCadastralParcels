# -*- coding: utf-8 -*-
"""
/***************************************************************************
 clsDatenbank: Gemeinsame Basis für QGIS2 und QGIS3
  04.07.2017 V0.4
  - GISDB Tab jetzt auch an Punkten (Fehler im Select)
  - CheckVerbDaten umgebaut
  - CAIGOS 2016: VectorLayerPath kein setsrid mehr notwendig
  
  23.08.2016 V0.3
  - Layerreihenfolge nach Priorität zusätzlich nach Layertyp
  - sqlAttParam4IDandArt Reihenfolge der Teillinien (testweise) umgekehrt 
  
  09.08.2016 V0.3
  - optionale 3D Anbindung
  - Einbindung SQL für Kreis
  
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
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from qgis.core import *
from qgis.utils import os, sys
try:
    from PyQt5.QtCore import QSettings, Qt
    from PyQt5.QtSql import QSqlDatabase, QSqlQuery, QSqlError
    from PyQt5 import QtGui
    myqtVersion = 5
    QString = type("")

except:
    from PyQt4.QtCore import QSettings, Qt
    from PyQt4.QtSql import QSqlDatabase, QSqlQuery, QSqlError
    from PyQt4 import QtGui
    def QgsDataSourceUri():
        return QgsDataSourceURI()
    myqtVersion = 4



try:
    from fnc4all import *
except:
    from .fnc4all import *
    
import os.path
import tempfile
import sqlite3

"""
/***************************************************************************/
                    Teil1: Datenbankzugriffe
/***************************************************************************/
"""
class pgDatabaseNeu():
    def __init__( self, service, host, port, dbname, uid, pwd):
        self.Fehler = None
        self.conname=service+host+port+dbname
        self.QSqlDB = QSqlDatabase.addDatabase("QPSQL", self.conname )
        if service == "":
            self.QSqlDB.setHostName(host)
            self.QSqlDB.setPort(int(port))
        else:
            self.QSqlDB.setService(service)
        
        self.QSqlDB.setDatabaseName(dbname)
        self.QSqlDB.setUserName(uid)
        self.QSqlDB.setPassword(pwd)
    
    def Open(self):
        if self.QSqlDB.open():
            return self.QSqlDB
        else:
            err = (u"pgDatabaseNeu:"  + '\n' +
            "Text: " + self.QSqlDB.lastError().text() +  '\n' +
            "Type: " + str(self.QSqlDB.lastError().type()) +  '\n' +
            "Number: " + str(self.QSqlDB.lastError().number()) )
            self.Fehler =  (toUnicode(err))
            self.QSqlDB = None

    def getFehler(self):
        return self.Fehler
    
    def OpenRecordset (self, SQLString):
        # in Python 3 hängt rs scheinbar noch an der QSqlDatabase
        # weshalb nach zerstören der pgDatabaseNeu() Instanz  bzw. bei  QSqlDatabase.removeDatabase(self.conname)
        # beim Zugriff ein Absturz auftritt
        rs = QSqlQuery(self.QSqlDB)
        if rs.exec_( SQLString ):
            return rs
        else:
            err = (u"exec_( SQLString ):"  + "\n" +
            "Text: " + rs.lastError().text() +  "\n" +
            "Type: " + str(rs.lastError().type()) +  "\n" +
            "Number: " + str(rs.lastError().number()) +  "\n" +
            "SQL: " + SQLString)
            self.Fehler =  (toUnicode(err))            
 
    def __del__(self):
        if self.QSqlDB:
            del(self.QSqlDB)
            QSqlDatabase.removeDatabase(self.conname) 

class pgCurrentDB(pgDatabaseNeu):
    def __init__( self ):
        s = QSettings( "EZUSoft", "CAIGOS-Konnektor" )
        service = s.value( "service", "" )
        host    = s.value( "host", "localhost" )
        port    = s.value( "port", "5432" )
        dbname  = s.value( "dbname", "cgTestProjekt" )
        uid     = s.value( "uid", "caigos" )
        pwd     = s.value( "pwd", "*****" )
        pgDatabaseNeu.__init__( self, service, host, port, dbname, uid, pwd)
    def __del__(self):
        pgDatabaseNeu.__del__(self)

def pgCurrendLookUp (sqlStringMitEinemFeld, OffeneDB = None, FldNum = 0):  
    if OffeneDB:
        AktDB = OffeneDB
    else:
        AktDB = pgCurrentDB()
        if not AktDB.Open():
            del(AktDB)
            return None
            
    AktRS= AktDB.OpenRecordset (sqlStringMitEinemFeld)
    AktRS.next()
    Wert = AktRS.value(FldNum)
    del(AktRS)
    if not OffeneDB:
        del (AktDB)
    return Wert
        
"""
/***************************************************************************/
                    Teil1: SQL Codes
/***************************************************************************/
"""

        
def sqlAtt4Massstab4All( Art, AktDef=None):
    # Art 31 (Referenzpfeil) wird hier auf Text(abfrage) zurückgesetzt
    # Attribute nach Maßstab - Grunddaten für alle Geometriearten gleich
    sFilt = "" if AktDef == None else " deftable.defid='" + AktDef + "' AND "
    sSQL=""
    for i in range(5):
        if i>0:
            sSQL=sSQL + "\nUNION ALL\n"
        sSQL = sSQL + (
"SELECT  %i AS AttNum, deftable.defid AS ADid, defname AS ADname,fa_id AS ATTid, attrname AS ATTname, scrscale%i AS MMin, scrscale%i AS mMax, scrresize "
"FROM deftable INNER JOIN frameatttable ON deftable.scrattrname%i = frameatttable.fa_id where " + sFilt + " attrtype=%i"
) % (i+1,i+1,i+2,i+1,3 if Art==31 else Art)

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

        uri = QgsDataSourceUri()
        
        if service == "":
            uri.setConnection( host, port, dbname, uid, pwd )
        else:
            uri.setConnection(service, dbname, uid, pwd )
        return uri.connectionInfo()
    
    def GetCGVersion(self):
        s = QSettings( "EZUSoft", "CAIGOS-Konnektor" )
        try:
            return int(s.value( "cgversion"))
        except:
            return None
    
    def GetEPSG(self):
        s = QSettings( "EZUSoft", "CAIGOS-Konnektor" )
        try:
            return int(s.value( "epsg"))
        except:
            return None
    
    def GetQSVGSignaturPfad(self):
        return tempfile.gettempdir() + "/{D5E6A1F8-392F-4241-A0BD-5CED09CFABC7}/" + 'projekt_svg' + '/' + self.GetCGProjektName() + '/'
        #return os.path.dirname(__file__) + "/" + 'projekt_svg' + '/' + self.GetCGProjektName() + '/'       
        
    
    def GetCGSignaturPfad(self):
        s = QSettings( "EZUSoft", "CAIGOS-Konnektor" )
        return s.value("cgsignaturpfad","nicht festgelegt")
    
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
            err = ("OpenDatabase:"  + "\n" +
            "Text: " + db.lastError().text() +  "\n" +
            "Type: " + str(db.lastError().type()) +  "\n" +
            "Number: " + str(db.lastError().number()) )
            addFehler(err)
   
    def CloseDatabase(self,db):
        db.close()
        # QSqlDatabasePrivate::removeDatabase: connection 'cgProjekt' is still in use, all queries will cease to work.
        # kein Weg gefunden die  Warnung anzuschalten
        QSqlDatabase.removeDatabase( "cgProjekt" )

    def CheckDBTabSpalte(self,GISDBTabName):
        db=self.CurrentDB()
        sDB=GISDBTabName.lower()
        sSQL=("SELECT True FROM pg_attribute WHERE attrelid = (SELECT oid FROM pg_class WHERE relname = '%s') AND attname = '%s_objid'")%(sDB,sDB)
        #rs = self.OpenRecordset(db,sSQL)
        #db.close()
        #return True
        return (self.OpenRecordset(db,sSQL).size()==1) 
    
    def CheckVerbDaten(self,EPSG=None, CGSignaturPfad=None,CGProjektName=None,conninfo=None, NurFehler=False):
        Meldung =""
        Fehler=""
        Warnung = ""
        if not EPSG:
            EPSG = self.GetEPSG()  
        if not CGSignaturPfad:
            CGSignaturPfad = self.GetCGSignaturPfad()    
        if not CGProjektName:
            CGProjektName = self.GetCGProjektName()      
        if not conninfo:
            conninfo = self.GetConnString()
        
        QApplication.setOverrideCursor(Qt.WaitCursor)
        if self.OpenDatabase(conninfo):
            Meldung= u"Datenbankverbindung erfolgreich"
        else:
            Fehler=u"Datenbankverbindung schlug fehl:\n" + "\n".join(getFehler())
            resetFehler()           
        QApplication.restoreOverrideCursor()
        
        if EPSG == None or EPSG == "" or EPSG == 0 or EPSG == "0":
            Fehler=Fehler + "\n" if Fehler else ""
            Fehler=Fehler+"EPSG-Code nicht definiert"
        
        if CGProjektName == "":
            Fehler=Fehler + "\n" if Fehler else ""
            Fehler=Fehler+"Kein Projektname festgelegt"
    
        if CGSignaturPfad == "":
            Warnung=Warnung + "\n" if Warnung else ""
            Warnung=Warnung+u"CAIGOS Signaturverzeichnis nicht festgelegt\n  ->Es können keinen SVG-Symbole generiert werden"            
        else:
            sigPfad = CGSignaturPfad             
            if os.path.exists(sigPfad):
                Meldung = Meldung + "\n" if Meldung else ""
                Meldung = Meldung + "CAIGOS Signaturverzeichnis gefunden"
            else:
                Warnung = Warnung + "\n" if Warnung else ""
                Warnung = Warnung + sigPfad + u"\nCAIGOS Signaturverzeichnis nicht gefunden\n  ->Es können keinen SVG-Symbole generiert werden"            
        
        if Fehler:
            QMessageBox.critical( None, u"Es sind Fehler aufgetreten", Fehler )
            return False
        else:  
            if not NurFehler:
               QMessageBox.information( None,u'Folgende Tests waren erfolgreich:',Meldung)
            if Warnung:
               QMessageBox.information( None,u'Konfigurationsproblem',Warnung)
            return True             

    def OpenRecordset(self,db,sqlString,ShowErr = False):
        qry = QSqlQuery(db)
        if not qry.exec_( sqlString ):
            err = ("OpenRecordset:"  + "\n" +
            "Text: " + qry.lastError().text() +  "\n" +
            "Type: " + str(qry.lastError().type()) +  "\n" +
            "Number: " + str(qry.lastError().number()) +  "\n" +
            "SQL: " + sqlString)
            if ShowErr:
                errbox(err)
            else:
                addFehler (err)
        return qry

    def Execute(self,db,sqlString):
        err = ""
        qry = QSqlQuery(db)
        if not qry.exec_( sqlString ):
            err = ("OpenRecordset:"  + "\n" +
            "Text: " + qry.lastError().text() +  "\n" +
            "Type: " + str(qry.lastError().type()) +  "\n" +
            "Number: " + str(qry.lastError().number()) +  "\n" +
            "SQL: " + sqlString)
        return err 
        
    def GeoTabName4Art (self,Art):
        table=None
        if Art == 0: # Point      
            table="pointssqlspatial"
        if Art == 1: # Line
            table="linessqlspatial"
        if Art == 2: # Kreis
            table="arcssqlspatial"
        if Art == 3: # Text
            table="textssqlspatial"
        if Art == 31: # Referenzlinie
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
            sSQL="select * from (" + sSQL +") as dummy inner join (select * from arcatttable where arcatttable.aa_ag=" + str(Group) + ") as arc ON dummy.ATTid = arc.aa_idfa  inner join polyatttable  ON arc.polyattr = polyatttable.poa_idfa where polyatttable.poa_ag=" + str(Group) + " order by attnum"  
            sSQL = sSQL
        if Art == 3 or Art == 31: # Text bzz Referenzlinie
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
            sSQL=("select * from  pointatttable  where pointatttable.pta_idfa = '%s' and  pointatttable.pta_ag=%d") % (AktAttID, Group)

        if Art == 1 or Art == 5: # Strecke, Polylinie
                  #                      0                     1           2        3      4       5      6       7              8           9            10          11
            sSQL=("SELECT la_idfa AS st_attid, attrname AS st_attrname, la_linenr, used, color, sizemm, basemm, basecolor, linesigattr, linesigbegin,linesigofs, linesigofsline, "
                   #           12            13            14            15          16           17          18       19          20          21          22           23
                  "       lineoffset, sigbeginattr, sigmiddleattr, sigendattr, transparent, denyatpercent, penid, basepenid, sigbeginpos, sigendpos, sigmiddlepos, geocolor, "
                   #           24
                  "       scrresize, pentable.* "
                  "FROM (frameatttable INNER JOIN lineatttable ON frameatttable.fa_id = lineatttable.la_idfa) "
                  "INNER JOIN pentable ON lineatttable.penid =pentable.id "
                  "WHERE la_idfa='%s' AND used='J' AND la_ag=%i order by la_linenr DESC") %(AktAttID, Group) # 22.08.16 Reihenfolge (testweise) umgedreht, damit Symbolde der Baseline zuletzt

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
            sSQL=None       
        return sSQL

    def sqlGisDBShortFieldName (self,TabName):
        clsdb=pgDataBase()
        db = clsdb.CurrentDB()
        rs = clsdb.OpenRecordset(db,"select column_name from information_schema.columns where table_name='" + TabName + "'")
        clsdb.CloseDatabase
        s = "select "
        while (rs.next()) :
            if rs.value(0).replace(TabName + '_','') == 'objid':
                s = s + rs.value(0) + " as objidgistab," # objid wäre sonnst doppelter Name in Abfrage, da Spalte objid auch in GeoTab
            else:
                s = s + rs.value(0) + " as " + rs.value(0).replace(TabName + '_','') + ","
        # letztes , weg
        s = s[:-1]
        s=  s + " FROM " + TabName  
        
        return s

    
    def VectorLayerPath (self, Art, ConnInfo, Epsg, LayerID, b3DDar , GISDbTab, cgVersion, bShape):
        bDeltaTexte = True # evtl. später mal optional 
        uri = None
        geoTabName=self.GeoTabName4Art(Art)
        if LayerID:
            where="layerid='%s'" % (LayerID)
        else:
            where =""
        
        if b3DDar:
            ken3D="Z"
        else:    
            ken3D=""
            
        if GISDbTab:
            if bShape:
                # Tabellennamen aus Spalte kürzen, da Shape nur 10 Zeichen
                sql4GISDB = self.sqlGisDBShortFieldName(GISDbTab).replace("\\","")
                sqlZusatz = (' left join (%s) as gtab on %s.objid = gtab.objidgistab') % (sql4GISDB,geoTabName)
            else:
                sqlZusatz = (' left join %s  on %s.objid = %s.%s_objid') % (GISDbTab,geoTabName,GISDbTab,GISDbTab)

        else:
            sqlZusatz=""
        
        if myQGIS_VERSION_INT() < 21200: # ab Lyon
            # Unterabfrage definieren - macht das Ganze aber ziemlich langsam und ist bei Essen nicht mehr notwendig
            IndexGen1="(SELECT row_number() over () AS _uid_,* FROM "
            IndexGen2=" as dummy)"
            Key="_uid_"
        else:
            IndexGen1 =''
            IndexGen2 =''
            Key="objid"
        
        #08.08.16:
        # table='%s' --> table=\"%s\": sicherheitshalber für alle, obwohl es nur beim Kreis Probleme gab
        
        # in CAIGOS 2016 steht der EPSG-Code jetzt korrekt in PostGIS
        # der neue Code ist irgendwie schlecht aus dem alten ableitbar --> 2 komplett verschiedene Varianten 
        if cgVersion == 0: # alte Variante mit EPSG-Einabu
            if Art == 0: # Point      
                table=("%s(select *, st_setsrid(st_translate(shape, deltar, deltah),%d) as sid_shape from %s %s)%s") % (IndexGen1,Epsg,geoTabName,sqlZusatz,IndexGen2)
                uri=("%s key='%s' srid=%s type=Point%s table=\"%s\" (sid_shape) sql=%s") % (ConnInfo, Key, Epsg, ken3D, table, where)        
            if Art == 1: # Line
                table=("%s(select *,st_setsrid(shape,%d) as sid_shape from %s %s)%s") % (IndexGen1,Epsg,geoTabName,sqlZusatz,IndexGen2)
                uri=("%s key='%s' srid=%d type=LineString%s table=\"%s\" (sid_shape) sql=%s") % (ConnInfo, Key, Epsg, ken3D, table, where)
            if Art == 2: # Kreis
                # 05.10.16: Kreis als Fläche
                #table= ("%s(select *,st_setsrid(shape,%d) as sid_shape from %s %s)%s") % (IndexGen1,Epsg,geoTabName,sqlZusatz,IndexGen2)
                #uri=("%s key='%s' srid=%d type=CircularString table='%s' (sid_shape) sql=%s") % (ConnInfo, Key, Epsg, table, where)
                table=("%s(select *,st_setsrid('CurvePolygon(' || array_to_string( array_append( array_append((string_to_array(ST_AsText(shape),','))[1:3], substring((string_to_array(ST_AsText(shape),','))[5], 1,length((string_to_array(ST_AsText(shape),','))[5])-1)),(string_to_array( substring(ST_AsText(shape),19),','))[1]),',') || '))',%d) as sid_shape from %s %s)%s") % (IndexGen1,Epsg,geoTabName,sqlZusatz,IndexGen2)
                if myQGIS_VERSION_INT()  < 21200:
                    uri=None
                else:
                    uri=("%s key='%s' srid=%d type=CurvePolygon%s table=\"%s\" (sid_shape) sql=%s") % (ConnInfo, Key, Epsg, ken3D, table, where)

            if Art == 3: # Text
                sShape = "st_translate(shape, deltar, deltah)" if bDeltaTexte else "shape"
                table=("%s(select *,st_setsrid(" + sShape  + " ,%d) as sid_shape from %s %s)%s") % (IndexGen1,Epsg,geoTabName,sqlZusatz,IndexGen2)
                uri=("%s key='%s' srid=%d type=Point%s table=\"%s\" (sid_shape) sql=%s") % (ConnInfo, Key, Epsg, ken3D, table, where)
            if Art == 31: # Textreferenzpfeil
                # 1. Punkt steht in "shape" 
                # 2. Punkt "st_translate(shape, deltar, deltah)"           
                sShape = "st_makeline(shape, st_translate(shape, deltar, deltah))"
                table=("%s(select *,st_setsrid(" + sShape  + " ,%d) as sid_shape from %s %s WHERE isdelta = 'J' and (deltar * deltah) != 0)%s") % (IndexGen1,Epsg,geoTabName,sqlZusatz,IndexGen2)
                uri=("%s key='%s' srid=%d type=LineString%s table=\"%s\" (sid_shape) sql=%s") % (ConnInfo, Key, Epsg, ken3D, table, where)
            if Art == 4: # Bemaßung
                uri = None
            if Art == 5: # Polylinie
                table=("%s(select *,st_setsrid(shape,%d) as sid_shape from %s %s)%s") % (IndexGen1,Epsg,geoTabName,sqlZusatz,IndexGen2)
                uri=("%s key='%s' srid=%d type=LineString%s table=\"%s\" (sid_shape) sql=%s") % (ConnInfo, Key, Epsg, ken3D, table, where)     
            if Art == 6: # Fläche
                table=("%s(select *,st_setsrid(shape,%d) as sid_shape from %s %s)%s") % (IndexGen1,Epsg,geoTabName,sqlZusatz,IndexGen2)
                uri=("%s key='%s' srid=%d type=MultiPolygon%s table=\"%s\"(sid_shape) sql=%s") % (ConnInfo, Key, Epsg, ken3D, table, where)
        else:
            if Art == 0: # Point      
                table=("%s(select *, st_translate(shape, deltar, deltah) as geom from %s %s)%s") % (IndexGen1,geoTabName,sqlZusatz,IndexGen2)
                uri=("%s key='%s' srid=%s type=Point%s table=\"%s\" (geom) sql=%s") % (ConnInfo, Key, Epsg, ken3D, table, where)        
            if Art == 1: # Line
                table=("%s(select *,shape as geom from %s %s)%s") % (IndexGen1,geoTabName,sqlZusatz,IndexGen2)
                uri=("%s key='%s' srid=%d type=LineString%s table=\"%s\" (geom) sql=%s") % (ConnInfo, Key, Epsg, ken3D, table, where)
            if Art == 2: # Kreis
                table=("%s(select *,st_setsrid('CurvePolygon(' || array_to_string( array_append( array_append((string_to_array(ST_AsText(shape),','))[1:3], substring((string_to_array(ST_AsText(shape),','))[5], 1,length((string_to_array(ST_AsText(shape),','))[5])-1)),(string_to_array( substring(ST_AsText(shape),19),','))[1]),',') || '))',%d) as geom from %s %s)%s") % (IndexGen1,Epsg,geoTabName,sqlZusatz,IndexGen2)
                if myQGIS_VERSION_INT()  < 21200:
                    uri=None
                else:
                    uri=("%s key='%s' srid=%d type=CurvePolygon%s table=\"%s\" (geom) sql=%s") % (ConnInfo, Key, Epsg, ken3D, table, where)
            if Art == 3: # Text
                sShape = "st_translate(shape, deltar, deltah)" if bDeltaTexte else "shape"
                table=("%s(select *," + sShape  + " as geom from %s %s)%s") % (IndexGen1,geoTabName,sqlZusatz,IndexGen2)
                uri=("%s key='%s' srid=%d type=Point%s table=\"%s\" (geom) sql=%s") % (ConnInfo, Key, Epsg, ken3D, table, where)
            if Art == 31: # Textreferenzpfeil
                # 1. Punkt steht in "shape" 
                # 2. Punkt "st_translate(shape, deltar, deltah)"           
                sShape = "st_makeline(shape, st_translate(shape, deltar, deltah))"
                table=("%s(select *," + sShape  + " as geom from %s %s WHERE isdelta = 'J' and (deltar * deltah) != 0)%s") % (IndexGen1,geoTabName,sqlZusatz,IndexGen2)
                uri=("%s key='%s' srid=%d type=LineString%s table=\"%s\" (geom) sql=%s") % (ConnInfo, Key, Epsg, ken3D, table, where)
            if Art == 4: # Bemaßung
                uri = None
            if Art == 5: # Polylinie
                table=("%s(select *,shape as geom from %s %s)%s") % (IndexGen1,geoTabName,sqlZusatz,IndexGen2)
                uri=("%s key='%s' srid=%d type=LineString%s table=\"%s\" (geom) sql=%s") % (ConnInfo, Key, Epsg, ken3D, table, where)     
            if Art == 6: # Fläche
                table=("%s(select *,shape as geom from %s %s)%s") % (IndexGen1,geoTabName,sqlZusatz,IndexGen2)
                uri=("%s key='%s' srid=%d type=MultiPolygon%s table=\"%s\"(geom) sql=%s") % (ConnInfo, Key, Epsg, ken3D, table, where)
        return uri
    """    
    def sqlLayerIsEmpty(self, Art, LayerID):
        geoTabName=self.GeoTabName4Art(Art)
        sSQL = "SELECT count(*) FROM " + geoTabName + " where layerid='" + LayerID + "'"
        db1 = pgCurrentDB()
        db1.Open()
        rs1 = db1.OpenRecordset (sSQL)
        rs1.next() # erster (und letzer) Datensatz
        if rs1.value(0) > 0:
            Wert = True
        else:    
            Wert = False
        del (rs1)
        del (db1)
        return Wert
    """    
    def sqlStruk4Layer(self, LayerID):
        sSQL = (u"SELECT dbname  as Fachschale, entityname as Thema, groupname as Gruppe, layername as layer, layerid, layertyp "
                    "FROM (enttable INNER JOIN grptable ON enttable.entityid = grptable.entityid) "
                    "INNER JOIN lyrtable ON (grptable.groupid = lyrtable.groupid) AND (enttable.entityid = lyrtable.entityid) "
                    "WHERE layerid='%s'") % (LayerID)
        db1 = pgCurrentDB()
        db1.Open()
        rs1 = db1.OpenRecordset (sSQL)
        rs1.next() # erster (und letzer) Datensatz
        ausg = rs1.value(0),rs1.value(1),rs1.value(2),rs1.value(3)
        del (rs1)
        del (db1)
        return ausg

    def sqlStrukAlleLayer(self,LayerList = None, Richtung=''):
        sSQL=""
        if LayerList:
            sSQL = "WHERE layerid In ("
            sSQL = sSQL + LayerList
            sSQL = sSQL + ")"
        # Alphabetische Reihenfolge für Explorerbaum, dabei Layername DESC, da Einfügereihenfolge über moveLayer umgekeht
        sSQL = (u"SELECT dbname  as Fachschale, entityname as Thema, groupname as Gruppe, layername as layer, layerid, layertyp "
                    "FROM (enttable INNER JOIN grptable ON enttable.entityid = grptable.entityid) "
                    "INNER JOIN lyrtable ON (grptable.groupid = lyrtable.groupid) AND (enttable.entityid = lyrtable.entityid) "
                    "%s order by dbname,entityname,groupname,layername %s") % (sSQL, Richtung)
        return sSQL

    def sqlAlleLayerByPriAndGISDB(self,UserNum = '000', LayerList = None):
        sSQL=""
        if LayerList:
            if len(LayerList.split(",")) == 1:
                sSQL =   "AND lyrtable.layerid = " + LayerList     
            else:
                sSQL = "AND lyrtable.layerid In ("
                sSQL = sSQL + LayerList
                sSQL = sSQL + ")"
        # Ebenen nach Prioritäten sortiert
        sSQL = (u"SELECT layername, lyrtable.layerid, lyrtable.layertyp, dbname, priority "
                    "FROM prptable INNER JOIN lyrtable ON prptable.layerid = lyrtable.layerid LEFT JOIN frametbltable on lyrtable.tblid = frametbltable.ft_id "
                    "WHERE usernr='%s' %s "
                    "UNION ALL "
                    ""
                    "select DISTINCT  layername,T1.layerid, layertyp,  dbname, priority from  ( "
                    "SELECT layername || '(RL)' as layername, lyrtable.layerid, 31 as layertyp, ''::text as  dbname, priority FROM prptable INNER JOIN lyrtable ON prptable.layerid = lyrtable.layerid "
                    "LEFT JOIN frametbltable on lyrtable.tblid = frametbltable.ft_id WHERE usernr='%s' AND lyrtable.layertyp=3 %s "
                    " \n") % (UserNum,sSQL,UserNum, sSQL) # 23.08.16 zusätzlich nach Layertyp (damit bei gleicher Pri Punkte über Flächen liegen)
        
        sSQL = sSQL + ") as T1 inner join "
        sSQL = sSQL + "(SELECT layerid FROM  ( SELECT * FROM (" + self.sqlAtt4Massstab ( 3,None, UserNum) + ") AS dummy "
        sSQL = sSQL + ("INNER JOIN textatttable ON dummy.ATTid = textatttable.ta_idfa "
                "WHERE textatttable.ta_ag=0 and textatttable.lineattr != '{00000000-0000-0000-0000-000000000000}' ORDER BY attnum\n")
                
        sSQL = sSQL + (") AS t1 "
        "INNER JOIN "
        "  (SELECT DISTINCT textssqlspatial.defid, layerid "
        "   FROM textssqlspatial "
        "   LEFT JOIN deftable ON textssqlspatial.defid =deftable.defid "
        "   WHERE  textssqlspatial.defid != '{00000000-0000-0000-0000-000000000000}' "
        "   UNION ALL SELECT defid, layerid "
        "   FROM prptable "
        "   WHERE usernr='000') AS t2 ON t1.adid = t2.defid) as T2 on T1.layerid = T2.layerid "
        "   ORDER BY priority DESC,layertyp ")
        return sSQL
    
    def sqlAllAttDef4Layer(self, Art, LayerID):
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
        Wert = rs.value(0)
        del(rs)
        return Wert
    
    def AttDefName4ID (self,db,DefID):
        # Name der Attributdefinition aus der DefID ermitteln
        sqlString=("SELECT defname FROM  deftable WHERE defid ='%s'") % (DefID)
        rs = self.OpenRecordset(db,sqlString)
        rs.next() # erster (und letzer) Datensatz
        Wert = rs.value(0)
        del(rs)
        return Wert

    def NeedLine4TextLayer(self,db,LayerID, cgUser):  
        sqlString= self.sqlAtt4Massstab ( 3,None, cgUser)
        sqlString = "select count(*) from (" + sqlString + ") as t1 inner join ("
        sqlString = sqlString + ("SELECT DISTINCT textssqlspatial.defid FROM textssqlspatial LEFT JOIN deftable ON textssqlspatial.defid =deftable.defid where layerid='%s' and textssqlspatial.defid != '{00000000-0000-0000-0000-000000000000}' union all select defid from prptable where layerid='%s' and usernr='%s'")%(LayerID,LayerID,cgUser)
        sqlString = sqlString + ") as t2 on t1.adid = t2.defid"

        rs = self.OpenRecordset(db,sqlString)
        rs.next() # erster (und letzer) Datensatz
        Wert=rs.value(0) != 0
        del(rs)
        return Wert
                   
if __name__ == "__main__":
    #cls = pgDataBase()
    #print (cls.sqlLayerIsEmpty(3,'xx'))
    """
    print (cls.sqlStruk4Layer('{72EA7AC0-C293-4F1B-871B-DDC30113E76B}'))
    db = pgDatabaseNeu("","pl309","5432", "tkTempProjekt","caigos","*****")
    if not db.Open():
        print ('-----------------')
        print (db.getFehler())
        print ('-----------------')
    else:
        rs = db. OpenRecordset ("select * from lyrtable")
        if rs:
            rs.next()
            print (rs.value(0))
        else:
            print ('-----------------')
            print (db.getFehler())
            print ('-----------------') 

    db1 = pgCurrentDB()
    if db1.Open():
        rs = db1. OpenRecordset ("select * from lyrtable")
        rs.next()
        print ("CurrentDB"+rs.value(0))
    del (db1)
    del (db)

    # zur zum lokalen testen
    #from qgis.core import QgsDataSourceUri
    #uri = QgsDataSourceUri()
    #app = QApplication(sys.argv)
    #print (str(myQGIS_VERSION_INT()))
    #clsdb=pgDatabaseNeu()
    #db = clsdb.CurrentDB()
    #print (clsdb.sqlStruk4Layer(db,'{72EA7AC0-C293-4F1B-871B-DDC30113E76B}'))
    

    #rs = clsdb.OpenRecordset(db,"select column_name from information_schema.columns where table_name='d4ustdok_abs'")
    #clsdb.CloseDatabase
    #s = ""
    #while (rs.next()):
    #    s = s + rs.value(0) + " as " + rs.value(0).replace('d4ustdok_abs_','') + ","
    #print s    
    #print clsdb.sqlGisDBShortFieldName('d4ustdok_qs')
    #print clsdb.sqlAtt4Massstab ( 31, '{C96A820A-6309-4068-9051-187E025ED271}', '000')
    #print clsdb.VectorLayerPath( 31, "ConnInfo",25833, "{3B2187AD-3F62-479A-B33F-004E51B81F45}",False , False)
    #print clsdb.sqlAllAttDef4Layer( 3, "{3B2187AD-3F62-479A-B33F-004E51B81F45}")
    #print clsdb.AttDefID4Layer(db, "{3B2187AD-3F62-479A-B33F-004E51B81F45}", 0)
    #print clsdb.NeedLine4TextLayer(None,"{3B2187AD-3F62-479A-B33F-004E51B81F45}",'000') 
    #print clsdb.sqlAlleLayerByPriAndGISDB('000')
    #print clsdb.NeedLine4TextLayer(None,'LayerID', 'cgUser')

    
    from uiToolsPolygonDirection import *
    cls = uiToolsPolygonDirection()
    sSQL=cls.sqlEbene4AttID("{4626E491-62BF-4874-A3D0-897EB4D7D507}")
    
    if not qry.exec_(sSQL ):
            err = ("OpenRecordset:"  + "\n" +
            "Text: " + qry.lastError().text() +  "\n" +
            "Type: " + str(qry.lastError().type()) +  "\n" +
            "Number: " + str(qry.lastError().number()) +  "\n" +
            "SQL: " + "sqlString")
            errbox ("Fehler: " + err)

    qry = clsdb.OpenRecordset(db,sSQL,True)

    #print clsdb.CheckDBTabSpalte ("xx")
    #print clsdb.CheckDBTabSpalte ("d4uadress")
    #print clsdb.CheckDBTabSpalte ("xx")
    #clsdb.CheckVerbDaten(None,None,None,None, False)
    #db = clsdb.CurrentDB()
    #print clsdb.sqlAttParam4IDandArt(1, "{CFAC4A38-A2EE-4419-AE29-D0A0BACAC3B5}", 0)
    #print clsdb.sqlAtt4Massstab(5, "{AA27D166-0453-4D7F-9640-4619C8DBA257}", 0)
    #print clsdb.sqlAtt4Massstab(6, "{9B9D21A1-A8D0-4EEF-883D-7B7AC6DA03E5}", 0)
    if db:
        #def VectorLayerPath (self, Art, ConnInfo, Epsg, LayerID):
        #print clsdb.VectorLayerPath(2,clsdb.GetConnString(),25833,"{88855ADA-E854-4025-85EC-2C6805B597DB}")
        
        #print clsdb.sqlAttParam4IDandArt(6, "{CFAC4A38-A2EE-4419-AE29-D0A0BACAC3B5}", 0)
        #print clsdb.sqlAtt4Massstab(0,"{FE5E17AD-2C4D-423E-A705-7393C57914D8}",0)
        #print sqlAtt4Massstab4All(0,"AktDef")
        #print clsdb.sqlAttParam4IDandArt( 1, "{70F5BC71-93C3-4282-A0F4-2EE198EE51E0}", Group = 0)
        #rs=clsdb.OpenRecordset(db,clsdb.sqlAttParam4IDandArt( 1, "{70F5BC71-93C3-4282-A0F4-2EE198EE51E0}", Group = 0))

        clsdb.CloseDatabase(db)
    else:
        print "Fehler"
    #clsdb.Check(
    """

