# -*- coding: utf-8 -*-
"""
/***************************************************************************
 uiDBAnbindung
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
from qgis.core import *
from PyQt4 import QtGui, uic
from PyQt4.QtCore import QSettings

from clsDatenbank import *
from fnc4all import *


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'uiDBAnbindung.ui'))



class uiDBAnbindung(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):

        super(uiDBAnbindung, self).__init__(parent)
        self.setupUi(self)

        s = QSettings( "EZUSoft", "CAIGOS-Konnektor" )
        self.leSERVICE.setText( s.value( "service", "" ) )
        self.leHOST.setText( self.deftext (s.value( "host"), "localhost" ) )
        self.lePORT.setText( self.deftext (s.value( "port"), "5432") ) 
        self.leDBNAME.setText( s.value( "dbname", "" ) )
        self.leUID.setText( s.value( "uid", "" ))
        self.lePWD.setText( s.value( "pwd", "" ))
        self.leEPSG.setText( self.deftext(s.value( "epsg"), "25833" ) )
        self.leCGProjektPfad.setText( s.value( "cgprojektpfad", "") )
        self.leCGProjektName.setText( s.value( "cgprojektname", "") )
        
        self.bb.accepted.connect(self.Speichern) # OK-Buttom
        self.bb.rejected.connect(self.reject)    # Cancel Buttom
        self.btnTest.clicked.connect(self.CheckEingabe) # Daten testen Buttom
        self.btnProjekt.clicked.connect(self.OpenProjekt)
        self.chkManuel.clicked.connect(self.WechselEingabe)
    
    def WechselEingabe(self):
        bFrei= self.chkManuel.isChecked()
        self.leSERVICE.setEnabled(bFrei)
        self.leHOST.setEnabled(bFrei)
        self.lePORT.setEnabled(bFrei)
        self.leDBNAME.setEnabled(bFrei)
        self.leUID.setEnabled(bFrei)
        self.lePWD.setEnabled(bFrei)
        self.leCGProjektPfad.setEnabled(bFrei)
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
                    if len(v) <> 2:
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
            self.leCGProjektPfad.setText(os.path.dirname(IniDatNam))                    
            if Fehler:
                QtGui.QMessageBox.critical( None, u"Es sind Fehler aufgetreten", Fehler )
        except: # catch *all* exceptions
            e = sys.exc_info()[0]
            QtGui.QMessageBox.critical( None, u"Es ist ein Fehler aufgetreten",  str(e)) 

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
                QtGui.QMessageBox.critical( None, u"Es sind Fehler aufgetreten", Fehler )
        except: # catch *all* exceptions
            e = sys.exc_info()[0]
            QtGui.QMessageBox.critical( None, u"Es ist ein Fehler aufgetreten",  str(e)) 
        return PrjName
        
    def OpenProjekt(self):
        try:
            iniDat = QtGui.QFileDialog.getOpenFileName(None, 'database.ini im Projektordner des CAIGOS-SQL-Projektes', "database.ini", "database (*.ini)")
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
        except Exception as e:
            subLZF (e.message + ": " + e.__doc__,"uiDBAnbindung.OpenProjekt")
    
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

        uri = QgsDataSourceURI()
        if service:
            uri.setConnection( service, dbname, uid, pwd )
        else:
            uri.setConnection( host, port, dbname, uid, pwd )

        return uri.connectionInfo()
        
    def EingabeSpeichern(self, error=True):
        s = QSettings( "EZUSoft", "CAIGOS-Konnektor" )
        s.setValue( "service", self.leSERVICE.text().strip() )
        s.setValue( "host", self.leHOST.text().strip() )
        s.setValue( "port", self.lePORT.text().strip() )
        s.setValue( "dbname", self.leDBNAME.text().strip() )
        s.setValue( "uid", self.leUID.text().strip() )
        s.setValue( "pwd", self.lePWD.text().strip() )
        s.setValue( "epsg", self.leEPSG.text().strip() )
        s.setValue( "cgprojektpfad", self.leCGProjektPfad.text().strip() )
        s.setValue( "cgprojektname", fncKorrDateiName(self.leCGProjektName.text().strip()) )        
        #QtGui.QMessageBox.information( None,'Datenbankzugriff','gespeichert')

    def CheckEingabe(self):
        connstr=self.DialogConnString()
        clsdb=pgDataBase()
        clsdb.CheckVerbDaten(self.leEPSG.text().strip(),self.leCGProjektPfad.text().strip(),fncKorrDateiName(self.leCGProjektName.text().strip()),connstr) 
        
    def Speichern(self):    
        self.EingabeSpeichern()
        QtGui.QDialog.accept(self) # Fenster schließen


 
if __name__ == "__main__":
    # zur zum lokalen testen 
    from qgis.utils import *

    app = QApplication(sys.argv)
    cls=uiDBAnbindung()
    result=cls.exec_()
    """
    if result:
        clsdb=pgDataBase()
        clsdb.CheckVerbDaten(25833,"")
    """