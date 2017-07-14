# -*- coding: utf-8 -*-
"""
/***************************************************************************
 uiExplorer: Gemeinsame Basis für QGIS2 und QGIS3
 09.09.2016 V0.3
  - Leere Ebenen optional einlesen
  - SHP Export integriert
  - optionale 3D Übergabe eingebaut
  
 17.06.2016 V0.2
  - Darstellungsgruppe eingebaut
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
    from PyQt5.QtCore import  QDir, Qt
    from PyQt5.QtWidgets import * 
except:
    from PyQt4 import QtGui, uic
    from PyQt4.QtCore import  QDir, Qt
    from PyQt4.QtGui  import * 

    
try:
    from fnc4all import *
except:
    from .fnc4all import *



FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'uiExplorer.ui'))


class uiExplorer(QDialog, FORM_CLASS):
    charsetList = ["System",
     "ascii",
     "big5",
     "big5hkscs",
     "cp037",
     "cp424",
     "cp437",
     "cp500",
     "cp720",
     "cp737",
     "cp775",
     "cp850",
     "cp852",
     "cp855",
     "cp856",
     "cp857",
     "cp858",
     "cp860",
     "cp861",
     "cp862",
     "cp863",
     "cp864",
     "cp865",
     "cp866",
     "cp869",
     "cp874",
     "cp875",
     "cp932",
     "cp949",
     "cp950",
     "cp1006",
     "cp1026",
     "cp1140",
     "cp1250",
     "cp1251",
     "cp1252",
     "cp1253",
     "cp1254",
     "cp1255",
     "cp1256",
     "cp1257",
     "cp1258",
     "euc_jp",
     "euc_jis_2004",
     "euc_jisx0213",
     "euc_kr",
     "gb2312",
     "gbk",
     "gb18030",
     "hz",
     "iso2022_jp",
     "iso2022_jp_1",
     "iso2022_jp_2",
     "iso2022_jp_2004",
     "iso2022_jp_3",
     "iso2022_jp_ext",
     "iso2022_kr",
     "latin_1",
     "iso8859_2",
     "iso8859_3",
     "iso8859_4",
     "iso8859_5",
     "iso8859_6",
     "iso8859_7",
     "iso8859_8",
     "iso8859_9",
     "iso8859_10",
     "iso8859_13",
     "iso8859_14",
     "iso8859_15",
     "iso8859_16",
     "johab",
     "koi8_r",
     "koi8_u",
     "mac_cyrillic",
     "mac_greek",
     "mac_iceland",
     "mac_latin2",
     "mac_roman",
     "mac_turkish",
     "ptcp154",
     "shift_jis",
     "shift_jis_2004",
     "shift_jisx0213",
     "System",
     "utf_32",
     "utf_32_be",
     "utf_32_le",
     "utf_16",
     "utf_16_be",
     "utf_16_le",
     "utf_7",
     "utf_8",
     "utf_8_sig"]
    def __init__(self, parent=None):
        """Constructor."""
        super(uiExplorer, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect

        self.setupUi(self)
        btn = self.button_box.button(QDialogButtonBox.Apply)
        btn.clicked.connect(self.Anwenden)
        self.browseZielPfad.clicked.connect(self.browseZielPfad_clicked) 
        self.chkSHPexp.clicked.connect(self.chkSHPexp_clicked)    
        self.setWindowTitle (fncCGFensterTitel())

        s = QSettings( "EZUSoft", "CAIGOS-Konnektor" )
        bGenDar = True  if s.value( "bGenDar", "Ja" )   == "Ja"   else False
        bPrjNeu = True  if s.value( "bPrjNeu", "Ja" )   == "Ja"   else False
        bLeer = False   if s.value( "bLeer", "Nein" )   == "Nein" else True
        bDBTab = False  if s.value( "bDBTab", "Nein" )  == "Nein" else True
        b3DDar = False  if s.value( "b3DDar", "Nein" )  == "Nein" else True
        bSHPexp = False if s.value( "bSHPexp", "Nein" ) == "Nein" else True
        iCodePage=s.value( "iCodePage", 0)
        # 25.10.16 Zeile war deaktiviert, warum!?
        self.txtZielPfad.setText(s.value( "txtSHPDir", "" ))
        
        self.cbCharSet.addItems(self.charsetList)
        self.cbCharSet.setCurrentIndex(int(iCodePage))
        
        iGruppe=s.value( "iDarGruppe", 0 )
        #errlog("gelesen"+str(iGruppe))
        self.chkDar.setChecked(bGenDar)
        self.chkGISDB.setChecked(bDBTab)
        self.chkLeer.setChecked(bLeer)
        self.chk3DDar.setChecked(b3DDar)
        self.chkLeer.setChecked(bLeer)
        
        self.chkSHPexp.setChecked(bSHPexp)
        self.chkSHPexp_clicked()
        
        if bPrjNeu:
            self.rBNeu.setChecked(True)
        else:
            self.rBHinz.setChecked(True)
        
        # Aktuell nur Neuaufbau unterstützt
        self.rBNeu.setChecked(True)
        self.grpBoxProjDat.setEnabled (False)
        
        # Gruppenauswahl
        for g in range(5): 
            self.cbGruppe.addItem("Gruppe-" + str(g))
        self.cbGruppe.setCurrentIndex(iGruppe)

    
    def chkSHPexp_clicked(self):
        bGenSHP=self.chkSHPexp.isChecked()   
        #self.txtZielPfad.setEnabled(bGenSHP)      
        self.browseZielPfad.setEnabled(bGenSHP) 
        self.cbCharSet.setEnabled(bGenSHP) 
        self.lbCharSet.setEnabled(bGenSHP) 
        if bGenSHP:
            self.txtZielPfad.setPlaceholderText(self.tr("Specify destination path")) 
        else:
            self.txtZielPfad.setPlaceholderText("") 
    
    
    def browseZielPfad_clicked(self):
        if self.txtZielPfad.text() == "":
            s = QSettings( "EZUSoft", "CAIGOS-Konnektor" )
            lastSHPDir = s.value("txtSHPDir", ".")
        else:
            lastSHPDir = self.txtZielPfad.text()
        
        if not os.path.exists(lastSHPDir):
            lastSHPDir=os.getcwd()    
        flags = QFileDialog.DontResolveSymlinks | QFileDialog.ShowDirsOnly
        shpDirName = QFileDialog.getExistingDirectory(self, u"Verzeichnis für Shape-Dateien wählen",lastSHPDir,flags)
        if shpDirName != "":
            if len( os.listdir( shpDirName ) ) > 0:
                reply = QMessageBox.question(None, u'Verzeichnis ist nicht leer',u"Namensgleiche Shape-Dateien werden überschrieben", QMessageBox.Yes |  QMessageBox.Cancel, QMessageBox.Cancel)
                if reply ==  QMessageBox.Yes:
                    self.txtZielPfad.setText(shpDirName)
            else:
                self.txtZielPfad.setText(shpDirName)
                
        #SHPDir, Dummy = os.path.split(shpDirName)
        #print "'" + SHPDir + "'" + "*"+"'" + Dummy + "'"
        #if shpDirName != "":
        #    s.setValue("lastSHPDir", shpDirName)

    
    def OptSpeichern(self):        
        s = QSettings( "EZUSoft", "CAIGOS-Konnektor" )
        s.setValue( "bGenDar", "Ja" if self.chkDar.isChecked() == True else "Nein")
        s.setValue( "bPrjNeu", "Ja" if self.rBNeu.isChecked() == True else "Nein")
        s.setValue( "iDarGruppe", self.cbGruppe.currentIndex())
        s.setValue( "bDBTab", "Ja" if self.chkGISDB.isChecked() == True else "Nein")
        s.setValue( "bLeer", "Ja" if self.chkLeer.isChecked() == True else "Nein")
        s.setValue( "b3DDar", "Ja" if self.chk3DDar.isChecked() == True else "Nein")
        s.setValue( "bSHPexp", "Ja" if self.chkSHPexp.isChecked() == True else "Nein")
        s.setValue( "iCodePage", self.cbCharSet.currentIndex())
        s.setValue( "txtCodePage", self.cbCharSet.currentText())
        s.setValue( "txtSHPDir", self.txtZielPfad.text())

    def Einlesen(self, rootname, qry):
        tw = self.twCaigosLayer
        tw.clear()
        # Fachschale, Thema, Gruppe, Ebene, layerid
        newparent = True
        Fachschale = ""
        Thema = ""
        Gruppe = ""
        p_item = QTreeWidgetItem(tw)
        p_item.setText(0, rootname)
        p_item.setCheckState(0,Qt.Unchecked)
        p_item.setExpanded(True)
        p_item.setFlags(p_item.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)

        while (qry.next()):
            if qry.value(0) != Fachschale:
                newparent=True
                f_item = QTreeWidgetItem(p_item)
                f_item.setText(0, qry.value(0))
                #f_item.setExpanded(True)
                f_item.setCheckState(0,Qt.Unchecked)
                f_item.setFlags(f_item.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)

            if newparent or qry.value(1) != Thema:
                newparent=True
                t_item = QTreeWidgetItem(f_item)
                t_item.setText(0, qry.value(1))
                t_item.setCheckState(0,Qt.Unchecked)
                t_item.setFlags(t_item.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
               
            if newparent or qry.value(2) != Gruppe:
                newparent=True
                g_item = QTreeWidgetItem(t_item)
                g_item.setText(0, qry.value(2))
                g_item.setCheckState(0,Qt.Unchecked)
                g_item.setFlags(g_item.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)  

            e_item = QTreeWidgetItem(g_item)
            e_item.setText(0, qry.value(3))
            e_item.setData(1,0,qry.value(4)) # Key in unsichtbare 2. Spalte
            e_item.setCheckState(0,Qt.Unchecked)
            e_item.setFlags(e_item.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)

            Fachschale=qry.value(0)
            Thema=qry.value(1)
            Gruppe=qry.value(2)
            newparent=False
    
    def Anwenden(self):
        # Check ob Import starten kann
        # 1. Test ob Ebenen gewählt
        view = self.twCaigosLayer
        Liste=[]
        it = QTreeWidgetItemIterator(view,QTreeWidgetItemIterator.Checked)
        while it.value():
            item = it.value()
            if item.text(1):
                Liste.append (item.text(1))    
            it += 1
        if len(Liste) == 0:
            msgbox("Es wurden keine Ebenen zur Darstellung  ausgewählt") 
            return
        # 2. Test ob alle Parameter gesetzt
        # 1. Codepage muss eigentlich nicht kontolliert werden
        # 2. Test ob ZielPfad vorhanden
        if self.chkSHPexp.isChecked():
            ZielPfad=self.txtZielPfad.text()                
            if ZielPfad == "":
                QMessageBox.critical(None, u"SHP-Zielpfad nicht gesetzt", u"Bitte Shape-Zielpfad wählen") 
                return
            if ZielPfad[:-1] != "/" and ZielPfad[:-1] != "\\":
                    ZielPfad=ZielPfad + "/"
            if not os.path.exists(ZielPfad):
                QMessageBox.critical(None, u"Shape Zielpfad nicht gefunden", ZielPfad)
                return
        super(uiExplorer, self).accept() # Fenster schließen
            
    # Die Zeilen mit ausgewaehlter Checkox ausgeben
    def Ausgeben(self):
        view = self.twCaigosLayer
        Liste=[]
        it = QTreeWidgetItemIterator(view,QTreeWidgetItemIterator.Checked)
        while it.value():
            item = it.value()
            if item.text(1):
                Liste.append (item.text(1))    
            it += 1

        self.OptSpeichern()
        # Achtung Shape-Parameter werden der Übersicht halber über die QSettings "übergeben"
        return Liste, self.chkDar.isChecked(),self.rBNeu.isChecked(), self.cbGruppe.currentIndex(),self.chk3DDar.isChecked(), self.chkGISDB.isChecked(),self.chkSHPexp.isChecked(), self.chkLeer.isChecked()
   

    def LayerErmitteln(self,rootname,qry):
        self.Einlesen (rootname,qry)

        result = self.exec_()
        if result==1:
             return self.Ausgeben()
        else:
            # es wurde Schließen gedrückt
            return None,None,None,None,None,None,None,None
            #QMessageBox.information( None,'','Abbruch') 

        
if __name__ == "__main__":
    from clsDatenbank import *
    app = QApplication(sys.argv)
    clsdb = pgDataBase()
    con=clsdb.GetConnString()
    db=clsdb.OpenDatabase(con) 
    rootname=clsdb.GetDBname()
    if db :
        qry = clsdb.OpenRecordset(db,clsdb.sqlStrukAlleLayer()) 
        cls = uiExplorer()

        guiListe = cls.LayerErmitteln(rootname, qry)
        print (guiListe)
        """
        if guiListe:
            str1 = "','".join(guiListe)
            str1 = "'" + str1 + "'"
            QMessageBox.information( None,u'Folgende Ebenen wurden gewählt',str1)
        """

    
