# -*- coding: utf-8 -*-
"""
/***************************************************************************
 uiFlurst4BL
    V0.1.2
    - Anpassung 31.08.17: "." durch "_" bei Gemarkungen im Downloadname ersetzen
    V0.1.1
    - Anpassung 22.08.17: keine führende 0 bei Gemarkungen im Downloadname

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


from qgis.core import *
from qgis.gui import *
from qgis.utils import *
import urllib
try:
    from PyQt5 import QtCore, QtGui, QtWidgets
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *
    from PyQt5 import QtGui, uic
    myqtVersion = 5
except:
    from PyQt4.QtCore import *
    from PyQt4.QtGui import *
    from PyQt4 import QtGui, uic
    myqtVersion = 4

try:
    from fnc4all import *
    from fnc4SaxonyCadastralParcels import *
    from clsWorker import GemWorker,DownloadLand2Array
except:
    from .fnc4all import *
    from .fnc4SaxonyCadastralParcels import *
    from .clsWorker import GemWorker,DownloadLand2Array

# Programm funktioniert auch ohne installierte gdal-Bibliothek, die Bibo wird nur zur Anzeige der Version genommen
try:
   import gdal
except:
   pass
 
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'uiFlurst4BL.ui'))

    

class uiFlurst4BL(QDialog, FORM_CLASS):
    bGlAbbruch = False
    bGlMitFlur = False

    def __init__(self, parent=None):
        """Constructor."""
        super(uiFlurst4BL, self).__init__(parent)
        
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.setWindowTitle (fncCGFensterTitel())
        self.browseZielPfad.clicked.connect(self.browseZielPfad_clicked) 
        self.chkSHP.clicked.connect(self.chkSave_clicked)    
        self.chkDXF.clicked.connect(self.chkSave_clicked) 
        self.btnStart.clicked.connect(self.btnStart_clicked)          
        self.btnAbbruch.clicked.connect(self.btnAbbruch_clicked)  
        self.cbLand.currentIndexChanged.connect(self.signalLandWechsel) 
        self.StartHeight = self.height()
        self.StartWidth  = self.width()
        self.chkMergeFlur.setEnabled(False)
        self.SetzeLandName()
        self.FormRunning(False)

    # noinspection PyMethodMayBeStatic
    def closeEvent(self, event):
        if not self.btnStart.isVisible():
            self.btnAbbruch_clicked()
            # event.ignore() ist zu riskannt, da bei Abstürzen das Fenster nicht mehr schließbar

    def isRunning(self):
        return not self.bGlAbbruch
     
    def fncAktLandName(self):
        if self.glAktLandKenn == "SN": return "Land Sachsen"
        if self.glAktLandKenn == "TH": return u"Land Thüringen"
    def SetzeLandName(self, FolgeRuf=False):
        self.cbLand.clear()
        self.cbLand.addItem ("Land Sachsen")
        self.cbLand.addItem (u"Land Thüringen")
        self.cbLand.addItem (u"--- Bundesland auswählen ---")
        self.cbLand.setCurrentIndex(2)

    def signalLandWechsel(self):
        if self.cbLand.count() == 1 :
            self.btnStart.setEnabled (False)
            return # automatischer Erstaufruf        

        if self.cbLand.currentIndex() == 0: self.glAktLandKenn = "SN"; self.bGlMitFlur=False
        if self.cbLand.currentIndex() == 1: self.glAktLandKenn = "TH"; self.bGlMitFlur=True
        if self.cbLand.currentIndex() == 2: return
        
        
        if self.glAktLandKenn == "":
            self.btnStart.setEnabled (False)
        else:
            self.btnStart.setEnabled (True)
            self.FormRunning(True)
            self.LadeGemarkungen()
            self.FormRunning(False)
            if self.bGlMitFlur:
                self.chkMergeFlur.show()
            else:
                self.chkMergeFlur.hide()
        
        if self.cbLand.count() == 3 :
            self.cbLand.removeItem(2) # "Kommentar"-Zeile löschen



    def LadeGemarkungen(self):
        # 08.01.2018: Download der Liste vom makobo-Server "http://www.makobo.de/data/"
        bMitFlur=self.bGlMitFlur
        AktLandName=self.fncAktLandName()

        if AktLandName == None:
            errbox("Bundesland mit Kennung '" + self.glAktLandKenn + "' wird nicht unterstützt")
            return
        
        self.SetEinzelAktionText("");self.SetEinzelAktionGesSchritte(-1)
        self.SetDatAktionGesSchritte(3)

        idxDownloadURL = 0;idxWeiter = 1;idxLokName = 2;idxLand = 3;idxLK = 4;idxGemeinde = 5;idxGemarkung = 6;idxFlur = 7
        #http://geodownload.sachsen.de/inspire/cp_atom/gm_shape_25833/Gemarkung_Dittersdorf%20(2113).zip	-1	Dittersdorf (2113)	Sachsen	Erzgebirgskreis	Amtsberg	Dittersdorf (2113)
        
        self.SetDatAktionText("Download der Gemarkungsliste");self.SetDatAktionAktSchritt(1)
        arrGem=DownloadLand2Array("exp"+self.glAktLandKenn+".dat")
        if arrGem == False:
            return
        self.SetDatAktionText("Gemarkungsliste aufbauen");self.SetDatAktionAktSchritt(2)
        # treeview leeren
        tvLand  = QTreeWidgetItem(self.objTVGem)
        tvLand.takeChild(0)
        self.objTVGem.takeTopLevelItem(0)
        tvLand.takeChild(0)
        self.objTVGem.takeTopLevelItem(0)      
        
        # Treeview Neuaufbau
        self.objTVGem.addTopLevelItem(tvLand)
        tvLand.setText(0, AktLandName)
        #tvLand.setFlags(tvLand.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
        tvLand.setExpanded(True)
        
        AktKreis=None
        AktGemeinde=None
        AktGemarkung = None
        
        for gemDS in arrGem:
            Zeile=gemDS.split("\t")
            # <DownloadAdresse> <IstUmleitung> <LokalerName>
            #DownloadAdresse=Zeile[idxURL]
            istUmleitung = Zeile[idxWeiter] # noch nicht programmiert
            if Zeile[idxLK] != AktKreis:
                tvKreis = QTreeWidgetItem(tvLand)
                tvKreis.setText(0, Zeile[idxLK].strip())
                #tvKreis.setFlags(tvKreis.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
            AktKreis=Zeile[idxLK].strip()
            
            if Zeile[idxGemeinde].strip() != AktGemeinde:
                tvGemeinde = QTreeWidgetItem(tvKreis)
                tvGemeinde.setText(0, Zeile[idxGemeinde].strip())
                tvGemeinde.setFlags(tvKreis.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
            AktGemeinde=Zeile[idxGemeinde].strip()       
            
            
            # bMitFlur als Text übergeben
            if bMitFlur:
                param = "True\t" + gemDS
            else:
                param = "False\t" + gemDS
            param=self.glAktLandKenn + "\t" + param
            if bMitFlur and Zeile[idxFlur].strip() != '':
                if Zeile[idxGemarkung].strip() != AktGemarkung:
                    tvGemarkung = QTreeWidgetItem(tvGemeinde)
                    tvGemarkung.setText(0, Zeile[idxGemarkung].strip())
                    tvGemarkung.setFlags(tvGemeinde.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
                AktGemarkung=Zeile[idxGemarkung].strip() 
                tvFlur = QTreeWidgetItem(tvGemarkung)
                tvFlur.setFlags(tvFlur.flags() | Qt.ItemIsUserCheckable)
                tvFlur.setText(0, Zeile[idxFlur].strip()) # +' (' + Zeile[3].strip() + ')')
                tvFlur.setCheckState(0, Qt.Unchecked) 
                tvFlur.setData(1,0,param)
            else:
                tvGemark = QTreeWidgetItem(tvGemeinde)
                tvGemark.setFlags(tvGemark.flags() | Qt.ItemIsUserCheckable)
                tvGemark.setText(0, Zeile[idxGemarkung].strip()) # +' (' + Zeile[3].strip() + ')')
                tvGemark.setCheckState(0, Qt.Unchecked)  
                tvGemark.setData(1,0,param)
        return True

        
    def SetzeVoreinstellungen(self):
	    # Voreinstellungen setzen
        s = QSettings( "EZUSoft", fncProgKennung() )
        
        # letzte Anzeigegröße wiederherstellen
        # 14.02.18: Vermutlich beim Zurück auf eine ältere Version kommt es zu einem Fehler:
        #           unable to convert a QVariant back to a Python object
        #           --> Bei Fehler Settings löschen
        try:
            SaveWidth  = int(s.value("SaveWidth", "0"))
            SaveHeight = int(s.value("SaveHeight", "0"))
        except:
            QSettings( "EZUSoft", "ADXF2Shape" ).clear()
            SaveWidth  = 0
            SaveHeight = 0
        
        if SaveWidth > self.minimumWidth() and SaveHeight > self.minimumHeight():
            self.resize(SaveWidth,SaveHeight)
        
        
        bGenSHP = True if s.value( "bGenSHP", "Nein" ) == "Ja" else False
        self.chkSHP.setChecked(bGenSHP)
        bGenDXF = True if s.value( "bGenDXF", "Nein" ) == "Ja" else False
        self.chkDXF.setChecked(bGenDXF)
        self.chkMergeFlur.setEnabled(bGenDXF)
        
        self.chkSave_clicked()

        try:
            self.lbGDAL.setText(gdal.VersionInfo("GDAL_RELEASE_DATE"))
        except:
            self.lbGDAL.setText("-")
		

    def chkSave_clicked(self):
        bGenSHP=self.chkSHP.isChecked()
        bGenDXF=self.chkDXF.isChecked()
        self.chkMergeFlur.setEnabled(bGenDXF)
        self.lbSave.setEnabled(bGenSHP or bGenDXF)      
        self.txtZielPfad.setEnabled(bGenSHP or bGenDXF)      
        self.browseZielPfad.setEnabled(bGenSHP or bGenDXF) 
        if bGenSHP or bGenDXF:
            self.txtZielPfad.setPlaceholderText(u"Zielpfad noch nicht gewählt") 
            self.lbSave.setText(u"Zielpfad")
        else:
            self.txtZielPfad.setPlaceholderText("") 
            self.lbSave.setText("") 
    
   
    def browseZielPfad_clicked(self):
        s = QSettings( "EZUSoft", fncProgKennung() )
        lastSaveDir = s.value("lastSaveDir", ".")
        
        if not os.path.exists(lastSaveDir):
            lastSaveDir=os.getcwd()    
        if myqtVersion == 5:
            flags = QtWidgets.QFileDialog.DontResolveSymlinks | QtWidgets.QFileDialog.ShowDirsOnly
            saveDirName = QtWidgets.QFileDialog.getExistingDirectory(self, "Open Directory",lastSaveDir,flags)
        else:
            flags = QtGui.QFileDialog.DontResolveSymlinks | QtGui.QFileDialog.ShowDirsOnly
            saveDirName = QtGui.QFileDialog.getExistingDirectory(self, "Open Directory",lastSaveDir,flags)

        saveDirName=saveDirName.replace("\\","/")
        self.txtZielPfad.setText(saveDirName)

        if saveDirName != "":
            s.setValue("lastSaveDir", saveDirName)
    
    def OptSpeichern(self):        
        s = QSettings( "EZUSoft", fncProgKennung() )
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
                #url = "http://geodownload.sachsen.de/inspire/cp_atom/gm_shape_25833/Gemarkung_"
                #zip = item.text(1)
                #url = url + urllib.quote(zip.encode("utf8"))
                #Liste.append (url + chr(9) + zip) 
                Liste.append (item.text(1))
            it += 1
            
        if len(Liste) == 0:
            msgbox(u"Es wurden keine Gemarkungen ausgewählt") 
            return False

        if len(Liste) > 30:
            s="Es werden " + str(len(Liste)) + " Einzelshapes bearbeitet.\nDie wird einige Zeit in Anspruch nehmen."
            s=s+'\n\n' + "Soll der Import/die Konvertierung trotzdem gestartet werden?"
            antw=QMessageBox.question(None, u"Rückfrage", s, QMessageBox.Yes, QMessageBox.No)
            if antw != QtGui.QMessageBox.Yes:
                return False

        
        # 2. Test ob ZielPfad vorhanden
        if self.chkSHP.isChecked() or self.chkDXF.isChecked():
            ZielPfad=self.txtZielPfad.text()
        else:
            ZielPfad=EZUTempDir()
            
        if ZielPfad == "":
            QMessageBox.critical(None, u"Kein Zielverzeichnis gewählt",u"Bitte Verzeichnis auswählen") 
            return
        if ZielPfad[:-1] != "/" and ZielPfad[:-1] != "\\":
                ZielPfad=ZielPfad + "/"
        if not os.path.exists(ZielPfad):
            QMessageBox.critical(None, "Verzeichnis nicht gefunden", ZielPfad)
            return
            
        self.OptSpeichern()
        iface.mapCanvas().setRenderFlag( False )   # Kartenaktualisierung abschalten
        Antw = GemWorker (self,  self.fncAktLandName(), Liste, ZielPfad, self.chkSHP.isChecked(), self.chkDXF.isChecked(),self.chkMergeFlur.isChecked())
        iface.mapCanvas().setRenderFlag( True )   # Kartenaktualisierung einschalten
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
        if ges < 0 :
            self.pgBar.hide()
        else:    
            self.pgBar.show()
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
        if ges < 0 :
            self.pgDatBar.hide()
        else:    
            self.pgDatBar.show()
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
        Anz(self.lbGDAL); Anz(self.cbLand); Anz(self.lbSave)
 
        Anz(self.btnStart) 
        Anz(self.browseZielPfad)
        Anz(self.button_box.button(QDialogButtonBox.Close))
        Anz(self.objTVGem);Anz(self.txtZielPfad)
        Anz(self.chkSHP); Anz(self.chkDXF);Anz(self.chkMergeFlur)
        
        
        # Sondereinstellung
        if not bRun:
            if self.bGlMitFlur: self.chkMergeFlur.show()


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
        self.SetzeVoreinstellungen()

        self.exec_()
        s = QSettings( "EZUSoft", fncProgKennung() )
        s.setValue("SaveWidth", str(self.width()))
        s.setValue("SaveHeight", str(self.height()))
        
        if len(getFehler()) > 0:
            errbox("\n\n".join(getFehler()))
        if len(getHinweis()) > 0:
            msgbox(u"\n\n".join(getHinweis()))  
if __name__ == "__main__":
    app = QApplication(sys.argv)
    #from uiFlurst4BL import uiFlurst4BL

    window = uiFlurst4BL()
    print (window.isRunning())
    window.show()
    sys.exit(app.exec_())

