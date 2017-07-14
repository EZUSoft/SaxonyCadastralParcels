# -*- coding: utf-8 -*-
"""
/***************************************************************************
 uiDBAnbindung: Gemeinsame Basis für QGIS2 und QGIS3
    01.07.2017 V0.4
        - Erweiterung auf Caigos 2016
        
    16.08.2016 V0.3
        - Dateidialog mit Vorauswahl der letzten/aktuellen Datei
        
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
try:
    from PyQt5 import QtGui, uic
    from PyQt5.QtCore import  QDir
    from PyQt5.QtWidgets import *
    myqtVersion = 5
except:
    from PyQt4 import QtGui, uic
    from PyQt4.QtCore import  QDir, QT_VERSION_STR
    from PyQt4.QtGui  import *
    myqtVersion = 4
    def QgsDataSourceUri():
        return QgsDataSourceURI()

try:
    from clsDatenbank import *
    from fnc4all import *
    from fnc4sqlite import *
except:
    from .clsDatenbank import *
    from .fnc4all import *
    from .fnc4sqlite import *


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'uiDBAnbindung.ui'))



class uiDBAnbindung(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super(uiDBAnbindung, self).__init__(parent)
        self.setupUi(self)

        s = QSettings( "EZUSoft", "CAIGOS-Konnektor" )
        self.cbVersion.setCurrentIndex(s.value( "cgversion", 0 ))
        self.cgVersionsWechsel()
        
        self.leSERVICE.setText( s.value( "service", "" ) )
        self.leHOST.setText( self.deftext (s.value( "host"), "localhost" ) )
        self.lePORT.setText( self.deftext (s.value( "port"), "5432") ) 
        self.leDBNAME.setText( s.value( "dbname", "" ) )
        self.leUID.setText( s.value( "uid", "" ))
        self.lePWD.setText( s.value( "pwd", "" ))
        self.leEPSG.setText( self.deftext(s.value( "epsg"), "25833" ) )
        self.leCGSignaturPfad.setText( s.value( "cgsignaturpfad", "") )
        self.leCGProjektName.setText( s.value( "cgprojektname", "") )
        
        self.bb.accepted.connect(self.Speichern) # OK-Buttom
        self.bb.rejected.connect(self.reject)    # Cancel Buttom
        self.btnTest.clicked.connect(self.CheckEingabe) # Daten testen Buttom
        self.btnDatAuswahl.clicked.connect(self.OpenDBIniOrAdmDB)
        self.chkManuel.clicked.connect(self.WechselEingabe)
        self.cbVersion.currentIndexChanged.connect(self.cgVersionsWechsel)
        self.cbProjektAusAdm.currentIndexChanged.connect(self.cgAdmProjektWechsel)
        

        
    def Projekte4AdmDBSetzen(self, dbName):
        prjList = [""]
        sSQL = ('SELECT DBPROJECT_PRJNAME AS prjName '
                'FROM DBPROJECT '
                'INNER JOIN DBCONNECT ON DBPROJECT.DBPROJECT_IDDBCONNECT = DBCONNECT.DBCONNECT_ID WHERE lower([DBCONNECT_PACTORTYPE])="postgresql";')
        if dbName == "":
            return False

        if not os.path.isfile (dbName):
            errbox("SQLite-Datei:\n" + dbName + "\nnicht gefunden")
            return False
        
        rs = slOpenRecordset(dbName,sSQL)
        if rs is None:
            if len(getFehler()) > 0:
                errbox("\n\n".join(getFehler()))
                resetFehler()
        else:
            for row in rs:
                prjList.append (row["prjName"])

        
        # Projektliste aus Datenbank bearbeiten
        self.cbProjektAusAdm.setEnabled(len(prjList) > 0)
        if len(prjList) > 0:            
            # Liste neu füllen
            self.cbProjektAusAdm.clear()
            self.cbProjektAusAdm.addItems(prjList)
        
        return True        
    
    def cgAdmProjektWechsel (self):
        prjName= self.cbProjektAusAdm.currentText()
        dbName = self.leAktDatName.text()
        if prjName == "":
            return False
        
        sSQL = ('SELECT DBPROJECT_PRJNAME AS prjName, DBCONNECT_SERVERNAME AS pgServer, DBCONNECT_DATABASENAME AS pgDatabase, DBCONNECT_USERNAME AS pgUserName, DBCONNECT_PASSWORD AS pgPasswd, DBPROJECT_REFSYSTEM AS txtEPSG '
                'FROM DBPROJECT '
                'INNER JOIN DBCONNECT ON DBPROJECT.DBPROJECT_IDDBCONNECT = DBCONNECT.DBCONNECT_ID '
                'WHERE DBPROJECT_PRJNAME=\'' + prjName + '\';')

        rs = slOpenRecordset(dbName,sSQL)
        if rs is None:
            if len(getFehler()) > 0:
                errbox("\n\n".join(getFehler()))
                resetFehler()   
                
        for row in rs:
            self.leCGProjektName.setText(prjName)
            self.leHOST.setText(row["pgServer"].split(":")[0])
            self.lePORT.setText(row["pgServer"].split(":")[1])
            self.leDBNAME.setText(row["pgDatabase"])
            self.leUID.setText(row["pgUserName"])
            self.lePWD.setText(row["pgPasswd"])
            self.leEPSG.setText(row["txtEPSG"])
            
    def cgVersionsWechsel(self):
        self.setWindowTitle (fncCGFensterTitel(self.cbVersion.currentIndex()))
        if self.cbVersion.currentIndex() == 0:
            self.lbProjektOrDB.setText(u"Ausgewählte database.ini")
            self.leAktDatName.setText("")
            self.leCGSignaturPfad.setText( QSettings( "EZUSoft", "CAIGOS-Konnektor" ).value( "cgsignaturpfad", "") ) # kann nicht ermittelt werden
            
        # Versuchen eine definierte Admin-Datenbank zu lesen und auszuwerten
        if self.cbVersion.currentIndex() == 1: 
            self.lbProjektOrDB.setText(u"Ausgewählte Administrationsdatenbank")  
            admDat = QSettings( "EZUSoft", "CAIGOS-Konnektor" ).value( "admindatei", "" )
            self.leAktDatName.setText( admDat) 
            self.leCGSignaturPfad.setText(os.path.dirname(admDat)+'/signaturen/')
            if self.leAktDatName.text() != "":
                if not os.path.isfile (self.leAktDatName.text()):
                    errbox("SQLite-Datei:\n" + self.leAktDatName.text() + "\nnicht gefunden")
                    self.leAktDatName.setText("")
                    self.leCGSignaturPfad.setText("")
                    QSettings( "EZUSoft", "CAIGOS-Konnektor" ).setValue( "admindatei", "" )
                    return False
            
            self.Projekte4AdmDBSetzen(self.leAktDatName.text())

         
        self.cbProjektAusAdm.setVisible(self.cbVersion.currentIndex() == 1)    
        self.lbProjektAusADM.setVisible(self.cbVersion.currentIndex() == 1)    
        self.leEPSG.setEnabled(self.cbVersion.currentIndex() == 0)
        
    def WechselEingabe(self):
        bFrei= self.chkManuel.isChecked()
        self.leSERVICE.setEnabled(bFrei)
        self.leHOST.setEnabled(bFrei)
        self.lePORT.setEnabled(bFrei)
        self.leDBNAME.setEnabled(bFrei)
        self.leUID.setEnabled(bFrei)
        self.lePWD.setEnabled(bFrei)
        self.leCGSignaturPfad.setEnabled(bFrei)
        self.leCGProjektName.setEnabled(bFrei) 
    
    def ConnAusDatabaseINI(self,IniDatNam):
        try:
            Fehler=""
            iDatNum = open(IniDatNam)
            z=0
            for iZeile in iDatNum:
                iZeile=iZeile.replace("\n","")
                if iZeile[:12] == "SERVER NAME=" :
                    v = iZeile[12:].split(":")
                    if len(v) != 2:
                        Fehler=Fehler + "\nFehler Servername:\n Erwartet: SERVER NAME=<rechner>:<port> \n Gelesen: " + iZeile[:12]
                    else:
                        self.leHOST.setText(v[0].strip())
                        self.lePORT.setText(v[1].strip())
                if iZeile[:14] == "DATABASE NAME=" :
                    self.leDBNAME.setText(iZeile[14:].strip())
                if iZeile[:10] == "USER NAME=" :
                    self.leUID.setText(iZeile[10:].strip())             
                if iZeile[:9] == "PASSWORD=" :
                    self.lePWD.setText(iZeile[9:].strip()) 
            self.leCGSignaturPfad.setText(os.path.dirname(IniDatNam)+'/signatur/')                    
            if Fehler:
                QMessageBox.critical( None, u"Es sind Fehler aufgetreten", Fehler )
        except: # catch *all* exceptions
            subLZF ()
    
    def ConnAusAdmDatei(self,AdmDatNam, prjName):
        try:
            Fehler=""
            iDatNum = open(IniDatNam)
            z=0
            for iZeile in iDatNum:
                iZeile=iZeile.replace("\n","")
                if iZeile[:12] == "SERVER NAME=" :
                    v = iZeile[12:].split(":")
                    if len(v) != 2:
                        Fehler=Fehler + "\nFehler Servername:\n Erwartet: SERVER NAME=<rechner>:<port> \n Gelesen: " + iZeile[:12]
                    else:
                        self.leHOST.setText(v[0].strip())
                        self.lePORT.setText(v[1].strip())
                if iZeile[:14] == "DATABASE NAME=" :
                    self.leDBNAME.setText(iZeile[14:].strip())
                if iZeile[:10] == "USER NAME=" :
                    self.leUID.setText(iZeile[10:].strip())             
                if iZeile[:9] == "PASSWORD=" :
                    self.lePWD.setText(iZeile[9:].strip()) 
            # wird schon bei der AdmAuswahl gesetzt
            # self.leCGSignaturPfad.setText(os.path.dirname(AdmDatNam)+'/signaturen/')          
            
            if Fehler:
                QMessageBox.critical( None, u"Es sind Fehler aufgetreten", Fehler )
        except: # catch *all* exceptions
            subLZF ()

    def ProjektAusPRJ(self,PrjDatNam):
        PrjName=""
        try:
            Fehler=""
            if PrjDatNam == "":
                Fehler = "Keine Projektdatei *.prj gefunden.\nEs wird der Datenbankname benutzt"
            else:
                iDatNum = open(PrjDatNam)
                PrjName =""
                for iZeile in iDatNum:
                    iZeile=iZeile.replace("\n","")
                    if iZeile[:12] == "ProjectName=" :
                        PrjName=iZeile[12:].strip()                               

                if PrjName == "":
                   Fehler="Projektname konnte nicht ermittelt werden.\nEs wird der Datenbankname benutzt"
            if Fehler:
                QMessageBox.critical( None, u"Es sind Fehler aufgetreten", Fehler )
        except: # catch *all* exceptions
            subLZF () 
        return PrjName
        
    def OpenDBIniOrAdmDB(self):
        try:
            if self.cbVersion.currentIndex() == 0:
                # Version für Caigos 11.2
                if self.leAktDatName.text().strip() == "":
                    vDat = QSettings( "EZUSoft", "CAIGOS-Konnektor" ).value( "dbinidatei", "" )
                else:
                    vDat = self.leAktDatName.text().strip()
                if vDat == "":
                    vDat="database.ini"
                if myqtVersion == 4:
                    iniDat = QFileDialog.getOpenFileName(None, 'database.ini im Projektordner des CAIGOS-SQL-Projektes', 
                             vDat , "database (*.ini)")
                else:
                    iniDat = QFileDialog.getOpenFileName(None, 'database.ini im Projektordner des CAIGOS-SQL-Projektes', 
                             vDat , "database (*.ini)")[0]

                if iniDat:
                    self.ConnAusDatabaseINI(iniDat)
                    
                    # Projektname ermitteln
                    prjDat=""
                    for f in os.listdir(os.path.dirname(iniDat)):
                        if f.lower().endswith(".prj"):
                             prjDat=os.path.dirname(iniDat) + "/" + f
                    PrjName=self.ProjektAusPRJ(prjDat)
                    if PrjName == "":
                       PrjName=self.leDBNAME.getText()
                    self.leCGProjektName.setText(fncKorrDateiName(PrjName))
                    self.leAktDatName.setText(iniDat)
                    
            if self.cbVersion.currentIndex() == 1:
                # Version für Caigos 2016
                admDat = QFileDialog.getOpenFileName(None, 'Administrationsdatenbank  im CAIGOS-Server Ordner', 
                             self.leAktDatName.text().strip() , "database (*.cgbin)")
                if admDat:
                    if self.Projekte4AdmDBSetzen (admDat):
                        self.leAktDatName.setText(admDat)
                        self.leCGSignaturPfad.setText(os.path.dirname(admDat)+'/signaturen/') 
                        #QSettings( "EZUSoft", "CAIGOS-Konnektor" ).setValue( "admindatei", self.leAktDatName.text().strip() )
        except Exception as e:
            subLZF ()
    
    def deftext(self,Wert,DefWert):
        # normales SetText mit Default funktioniert nicht, da nach erstem Aufruf mit Leerzeichen gefüllt wird
        if Wert == None:
            return DefWert        
        if Wert.strip() == "":
            return DefWert
        else:
            return Wert
    
    def DialogConnString(self):
        service = self.leSERVICE.text().strip()
        host = self.leHOST.text().strip()
        port = self.lePORT.text().strip()
        dbname = self.leDBNAME.text().strip()
        uid = self.leUID.text().strip()
        pwd = self.lePWD.text().strip()

        uri = QgsDataSourceUri()
        if service:
            uri.setConnection( service, dbname, uid, pwd )
        else:
            uri.setConnection( host, port, dbname, uid, pwd )

        return uri.connectionInfo()
        
    def EingabeSpeichern(self, error=True):
        s = QSettings( "EZUSoft", "CAIGOS-Konnektor" )
        s.setValue( "cgversion", self.cbVersion.currentIndex() )
        if self.cbVersion.currentIndex() == 0:
            s.setValue( "dbinidatei", self.leAktDatName.text().strip() )
        if self.cbVersion.currentIndex() == 1:
            s.setValue( "admindatei", self.leAktDatName.text().strip() )
  
        s.setValue( "service", self.leSERVICE.text().strip() )
        s.setValue( "host", self.leHOST.text().strip() )
        s.setValue( "port", self.lePORT.text().strip() )
        s.setValue( "dbname", self.leDBNAME.text().strip() )
        s.setValue( "uid", self.leUID.text().strip() )
        s.setValue( "pwd", self.lePWD.text().strip() )
        s.setValue( "epsg", self.leEPSG.text().strip() )
        s.setValue( "cgsignaturpfad", self.leCGSignaturPfad.text().strip() )
        s.setValue( "cgprojektname", fncKorrDateiName(self.leCGProjektName.text().strip()) )        
        #QMessageBox.information( None,'Datenbankzugriff','gespeichert')

    def CheckEingabe(self):
        connstr=self.DialogConnString()
        clsdb=pgDataBase()
        clsdb.CheckVerbDaten(self.leEPSG.text().strip(),self.leCGSignaturPfad.text().strip(),
                             fncKorrDateiName(self.leCGProjektName.text().strip()),connstr, False) 

    def Speichern(self):    
        self.EingabeSpeichern()
        QDialog.accept(self) # Fenster schließen


 
if __name__ == "__main__":
    uri = QgsDataSourceUri()
    app = QApplication(sys.argv)

    #uri=QgsDataSourceURI()
    cls=uiDBAnbindung()
    result=cls.exec_()
    """
    if result:
        clsdb=pgDataBase()
        clsdb.CheckVerbDaten(25833,"")
    """