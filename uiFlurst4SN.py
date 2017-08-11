# -*- coding: utf-8 -*-
"""
/***************************************************************************
 uiFlurst4SN

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

from qgis.utils import os, sys
from PyQt4.QtCore import QSettings, QSize, Qt
from PyQt4 import QtGui, uic
from PyQt4.QtGui import QMessageBox, QDialogButtonBox,QTreeWidgetItem,QTreeWidgetItemIterator
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from fnc4all import *
from clsWorker import GemWorker
import urllib

# Programm funktioniert auch ohne installierte gdal-Bibliothek, die Bibo wird nur zur Anzeige der Version genommen
try:
   import gdal
except:
   pass
 
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'uiFlurst4SN.ui'))
from PyQt4.QtCore import QObject, QEvent

    

class uiFlurst4SN(QtGui.QDialog, FORM_CLASS):
    bGlAbbruch = False

    def __init__(self, parent=None):
        """Constructor."""
        super(uiFlurst4SN, self).__init__(parent)
        
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.browseZielPfad.clicked.connect(self.browseZielPfad_clicked) 
        self.chkSHP.clicked.connect(self.chkSave_clicked)    
        self.chkDXF.clicked.connect(self.chkSave_clicked) 
        self.btnStart.clicked.connect(self.btnStart_clicked)          
        self.btnAbbruch.clicked.connect(self.btnAbbruch_clicked)  
        
        self.StartHeight = self.height()
        self.StartWidth  = self.width()
        
        self.SetzeVoreinstellungen()
        self.LadeGemarkungen()

        self.FormRunning(False)

    # noinspection PyMethodMayBeStatic
    def closeEvent(self, event):
        if not self.btnStart.isVisible():
            self.btnAbbruch_clicked()
            # event.ignore() ist zu riskannt, da bei Abstürzen das Fenster nicht mehr schließbar

    def isRunning(self):
        return not self.bGlAbbruch
        
    def LadeGemarkungen(self):
        gemdat=os.path.dirname(__file__) + "/GemSNAnsi.csv"
        fobj = open(gemdat, "r")
        tvLand      = QTreeWidgetItem(self.objTVGem)
        item        = QTreeWidgetItem()

        tvLand.setText(0, "Land Sachsen")
        tvLand.setFlags(tvLand.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
        tvLand.setExpanded(True)

        AktKreis=None
        AktGemeinde=None
        for Zeile in fobj:
            Zeile=Zeile.split(";")
            if Zeile[0] <> AktKreis:
                tvKreis = QTreeWidgetItem(tvLand)
                tvKreis.setText(0, Zeile[0].strip())
                tvKreis.setFlags(tvKreis.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
            AktKreis=Zeile[0].strip()
            
            if Zeile[2].strip() <> AktGemeinde:
                tvGemeinde = QTreeWidgetItem(tvKreis)
                tvGemeinde.setText(0, Zeile[2].strip())
                tvGemeinde.setFlags(tvKreis.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
            AktGemeinde=Zeile[2].strip()       
            
            tvGemark = QTreeWidgetItem(tvGemeinde)
            tvGemark.setFlags(tvGemark.flags() | Qt.ItemIsUserCheckable)
            tvGemark.setText(0, Zeile[4].strip() +' (' + Zeile[3].strip() + ')')
            tvGemark.setCheckState(0, Qt.Unchecked)  
            
            zip = Zeile[4].strip()
            zip = zip +' (' + Zeile[3].strip() + ').zip'
            
            zip = toUTF8(zip)
            zip = zip.replace("/","_")   
            tvGemark.setData(1,0,zip)
        fobj.close()

        
    def SetzeVoreinstellungen(self):
	    # Voreinstellungen setzen
        s = QSettings( "EZUSoft", "ADXF2Shape" )
        
        # letzte Anzeigegröße wiederherstellen
        SaveWidth  = int(s.value("SaveWidth", "0"))
        SaveHeight = int(s.value("SaveHeight", "0"))
        if SaveWidth > self.minimumWidth() and SaveHeight > self.minimumHeight():
            self.resize(SaveWidth,SaveHeight)
        
        
        bGenSHP = True if s.value( "bGenSHP", "Nein" ) == "Ja" else False
        self.chkSHP.setChecked(bGenSHP)
        bGenDXF = True if s.value( "bGenDXF", "Nein" ) == "Ja" else False
        self.chkDXF.setChecked(bGenDXF)
        
        self.chkSave_clicked()

        try:
            self.lbGDAL.setText(gdal.VersionInfo("GDAL_RELEASE_DATE"))
        except:
            self.lbGDAL.setText("-")
		

    def chkSave_clicked(self):
        bGenSHP=self.chkSHP.isChecked()
        bGenDXF=self.chkDXF.isChecked()
        self.lbSave.setEnabled(bGenSHP or bGenDXF)      
        self.txtZielPfad.setEnabled(bGenSHP or bGenDXF)      
        self.browseZielPfad.setEnabled(bGenSHP or bGenDXF) 
        if bGenSHP or bGenDXF:
            self.txtZielPfad.setPlaceholderText(self.tr("Specify destination path")) 
            self.lbSave.setText(self.tr(u"Output path"))
        else:
            self.txtZielPfad.setPlaceholderText("") 
            self.lbSave.setText("") 
    
   
    def browseZielPfad_clicked(self):
        s = QSettings( "EZUSoft", "ASHP2Shape" )
        lastSaveDir = s.value("lastSaveDir", ".")
        
        if not os.path.exists(lastSaveDir):
            lastSaveDir=os.getcwd()    
        flags = QtGui.QFileDialog.DontResolveSymlinks | QtGui.QFileDialog.ShowDirsOnly
        saveDirName = QtGui.QFileDialog.getExistingDirectory(self, "Open Directory",lastSaveDir,flags)
        saveDirName=saveDirName.replace("\\","/")
        self.txtZielPfad.setText(saveDirName)

        if saveDirName <> "":
            s.setValue("lastSaveDir", saveDirName)
    
    def OptSpeichern(self):        
        s = QSettings( "EZUSoft", "Flurst4SN" )
        s.setValue( "bGenSHP", "Ja" if self.chkSHP.isChecked() == True else "Nein")
        s.setValue( "bGenDXF", "Ja" if self.chkDXF.isChecked() == True else "Nein")
          
    
    def btnAbbruch_clicked(self):
        self.SetDatAktionText("... wird abgebrochen")
        self.SetEinzelAktionText("... wird abgebrochen")
        self.bGlAbbruch = True
    
    def btnStart_clicked(self):
        view = self.objTVGem
        Liste=[]
        it = QTreeWidgetItemIterator(view,QTreeWidgetItemIterator.Checked)
        while it.value():
            item = it.value()
            if item.text(1): 
                url = "http://geodownload.sachsen.de/inspire/cp_atom/gm_shape_25833/Gemarkung_"
                zip = item.text(1)
                url = url + urllib.quote(zip.encode("utf8"))
                Liste.append (url + chr(9) + zip) 
            it += 1
            
        if len(Liste) == 0:
            msgbox(u"Es wurden Gemarkungen ausgewählt") 
            return False
        

        # 2. Test ob ZielPfad vorhanden
        if self.chkSHP.isChecked() or self.chkDXF.isChecked():
            ZielPfad=self.txtZielPfad.text()
        else:
            ZielPfad=EZUTempDir()
            
        if ZielPfad == "":
            QMessageBox.critical(None, self.tr("Kein Zielverzeichnis gewählt"), self.tr("Bitte Verzeichnis auswählen")) 
            return
        if ZielPfad[:-1] <> "/" and ZielPfad[:-1] <> "\\":
                ZielPfad=ZielPfad + "/"
        if not os.path.exists(ZielPfad):
            QMessageBox.critical(None, self.tr("Verzeichnis nicht gefunden"), ZielPfad)
            return
            
        self.OptSpeichern()
        Antw = GemWorker (self, Liste, ZielPfad, self.chkSHP.isChecked(), self.chkDXF.isChecked())
        self.bGlAbbruch = False
        self.FormRunning(False) # nur sicherheitshalber, falls in GemWorker übersprungen/vergessen
        
    
        
    def SetEinzelAktionText(self,txt):
        QApplication.processEvents()
        self.lbAktion.setText(txt)
        self.repaint()   
    def SetEinzelAktionAktSchritt(self,akt):
        QApplication.processEvents()
        self.pgBar.setValue(akt)
        self.repaint()
        #QMessageBox.information(None, ("aktuell gesetzt"), str(akt))
    def SetEinzelAktionGesSchritte(self,ges):
        QApplication.processEvents()
        self.pgBar.setMaximum(ges)
        self.repaint()
        #QMessageBox.information(None, ("maximum gesetzt"), str(ges))
    
    def SetDatAktionText(self,txt):
        QApplication.processEvents()
        self.lbDatAktion.setText(txt)
        self.repaint()   
    def SetDatAktionAktSchritt(self,akt):
        QApplication.processEvents()
        self.pgDatBar.setValue(akt)
        self.repaint()
        #QMessageBox.information(None, ("aktuell gesetzt"), str(akt))
    def SetDatAktionGesSchritte(self,ges):
        QApplication.processEvents()
        self.pgDatBar.setMaximum(ges)
        self.repaint()
        #QMessageBox.information(None, ("maximum gesetzt"), str(ges))

    def FormRunning(self,bRun):
        def Anz(ctl):
            if bRun:
                ctl.hide()
            else:
                ctl.show()
        Anz(self.lbGDAL); Anz(self.lbDXF); Anz(self.lbSave)
 
        Anz(self.btnStart) 
        Anz(self.browseZielPfad)
        Anz(self.button_box.button(QDialogButtonBox.Close))
        Anz(self.objTVGem);Anz(self.txtZielPfad)
        Anz(self.chkSHP); Anz(self.chkDXF)


        if bRun:
            self.lbIcon.show()
            self.pgBar.show()
            self.lbAktion.show()
            self.pgBar.setValue(0) 
            self.AktSchritt = 0 
            self.pgDatBar.show()
            self.lbDatAktion.show()
            self.pgDatBar.setValue(0) 
            self.AktDatSchritt = 0 
            self.chkSave_clicked()
            self.btnAbbruch.show()
        else:
            self.lbIcon.hide()
            self.pgBar.hide()
            self.lbAktion.hide()
            self.pgDatBar.hide()
            self.lbDatAktion.hide()
            self.btnAbbruch.hide()

    def RunMenu(self):
        self.exec_()
        s = QSettings( "EZUSoft", "Flurst4SN" )
        s.setValue("SaveWidth", str(self.width()))
        s.setValue("SaveHeight", str(self.height()))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    #from uiFlurst4SN import uiFlurst4SN

    window = uiFlurst4SN()
    print window.isRunning()
    window.show()
    sys.exit(app.exec_())

