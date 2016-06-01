# -*- coding: utf-8 -*-
"""
/***************************************************************************
 uiExplorer
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
from PyQt4 import QtGui, uic
from PyQt4.QtCore import Qt
from PyQt4.QtCore import QSettings


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'uiExplorer.ui'))


class uiExplorer(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(uiExplorer, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        s = QSettings( "EZUSoft", "CAIGOS-Konnektor" )
        bGenDar = True if s.value( "bGenDar", "Ja" ) == "Ja" else False
        bPrjNeu = True if s.value( "bPrjNeu", "Ja" ) == "Ja" else False
        self.chkDar.setChecked(bPrjNeu)
        if bPrjNeu:
            self.rBNeu.setChecked(True)
        else:
            self.rBHinz.setChecked(True)
        # Aktuell nur Neuaufbau unterstützt
        self.rBNeu.setChecked(True)
        self.grpBoxProjDat.setEnabled (False)
    
    
    def OptSpeichern(self):        
        s = QSettings( "EZUSoft", "CAIGOS-Konnektor" )
        s.setValue( "bGenDar", "Ja" if self.chkDar.isChecked() == True else "Nein")
        s.setValue( "bPrjNeu", "Ja" if self.rBNeu.isChecked() == True else "Nein")

    def Einlesen(self, rootname, qry):
        tw = self.twCaigosLayer
        tw.clear()
        # Fachschale, Thema, Gruppe, Ebene, layerid
        newparent = True
        Fachschale = ""
        Thema = ""
        Gruppe = ""
        p_item = QtGui.QTreeWidgetItem(tw)
        p_item.setText(0, rootname)
        p_item.setCheckState(0,Qt.Unchecked)
        p_item.setExpanded(True)
        p_item.setFlags(p_item.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)

        while (qry.next()):
            if qry.value(0) != Fachschale:
                newparent=True
                f_item = QtGui.QTreeWidgetItem(p_item)
                f_item.setText(0, qry.value(0))
                #f_item.setExpanded(True)
                f_item.setCheckState(0,Qt.Unchecked)
                f_item.setFlags(f_item.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)

            if newparent or qry.value(1) != Thema:
                newparent=True
                t_item = QtGui.QTreeWidgetItem(f_item)
                t_item.setText(0, qry.value(1))
                t_item.setCheckState(0,Qt.Unchecked)
                t_item.setFlags(t_item.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
               
            if newparent or qry.value(2) != Gruppe:
                newparent=True
                g_item = QtGui.QTreeWidgetItem(t_item)
                g_item.setText(0, qry.value(2))
                g_item.setCheckState(0,Qt.Unchecked)
                g_item.setFlags(g_item.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)  

            e_item = QtGui.QTreeWidgetItem(g_item)
            e_item.setText(0, qry.value(3))
            e_item.setData(1,0,qry.value(4)) # Key in unsichtbare 2. Spalte
            e_item.setCheckState(0,Qt.Unchecked)
            e_item.setFlags(e_item.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)

            Fachschale=qry.value(0)
            Thema=qry.value(1)
            Gruppe=qry.value(2)
            newparent=False
    
    # Die Zeilen mit ausgewaehlter Checkox ausgeben
    def Ausgeben(self):
        view = self.twCaigosLayer
        Liste=[]
        it = QtGui.QTreeWidgetItemIterator(view,QtGui.QTreeWidgetItemIterator.Checked)
        while it.value():
            item = it.value()
            if item.text(1):
                Liste.append (item.text(1))    
            it += 1

        return Liste, self.chkDar.isChecked(),self.rBNeu.isChecked()
   

    def LayerErmitteln(self,rootname,qry):
        self.Einlesen (rootname,qry)

        result = self.exec_()
        if result==1:
            return self.Ausgeben()
        else:
            return None,None,None
            #QtGui.QMessageBox.information( None,'','Abbruch') 

        
if __name__ == "__main__":
    from clsDatenbank import *
    app = QtGui.QApplication(sys.argv)
    clsdb = pgDataBase()
    con=clsdb.GetConnString()
    db=clsdb.OpenDatabase(con) 
    rootname=clsdb.GetDBname()
    if db :
        qry = clsdb.OpenRecordset(db,clsdb.sqlStrukAlleLayer()) 
        cls = uiExplorer()
        guiListe = cls.LayerErmitteln(rootname, qry)
        if guiListe:
            str1 = "','".join(guiListe)
            str1 = "'" + str1 + "'"
            QtGui.QMessageBox.information( None,u'Folgende Ebenen wurden gewählt',str1)


    
