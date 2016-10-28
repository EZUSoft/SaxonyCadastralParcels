# -*- coding: utf-8 -*-
"""
/***************************************************************************
 uiToolsPolygonDirection
                                 A QGIS plugin
 CAIGOS-Servicetools
                              -------------------
        begin                : 2016-0823
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
from fnc4all import *

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'uiToolsPolygonDirection.ui'))


class uiToolsPolygonDirection(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(uiToolsPolygonDirection, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        btn = self.button_box.button(QtGui.QDialogButtonBox.Apply)
        btn.clicked.connect(self.attWechseln)
        self.tvCaigosAtt.doubleClicked.connect(self.tv_dblClick)
 
    def tv_dblClick(self,index):
        item = self.tvCaigosAtt.itemFromIndex(self.tvCaigosAtt.selectedIndexes()[0])
        clsdb = pgDataBase()
        con=clsdb.GetConnString()
        db=clsdb.OpenDatabase(con) 
        if db :
            cls = uiToolsPolygonDirection()
            s=""
            printlog (cls.sqlEbene4AttID(item.text(1)))
            qry = clsdb.OpenRecordset(db,cls.sqlEbene4AttID(item.text(1)),True) 
            while qry.next():
                if qry.value(0) is None:
                    Ebenen = "--keine---"
                else:    
                    Ebene=qry.value(0)
                s = s + "\n---------------\nEbene: " + Ebene + "\nAD: " + qry.value(1) 
                
        msgbox(s[3:],True) 
        
    def attEinlesen(self):
        clsdb = pgDataBase()
        con=clsdb.GetConnString()
        db=clsdb.OpenDatabase(con) 
        rootname=clsdb.GetDBname()
        if db :
            cls = uiToolsPolygonDirection()
            qry = clsdb.OpenRecordset(db,cls.sql4AttList()) 
    
            tw = self.tvCaigosAtt
            tw.clear()
            newparent = True
            p_item = QtGui.QTreeWidgetItem(tw)
            p_item.setText(0, rootname)

            p_item.setExpanded(True)
            p_item.setFlags(p_item.flags()  )

            i_item = QtGui.QTreeWidgetItem(p_item)
            i_item.setText(0, u"Darstellung nach innen")
            i_item.setExpanded(True)
            i_item.setFlags(p_item.flags()  )
            a_item = QtGui.QTreeWidgetItem(p_item)
            a_item.setText(0, u"Darstellung nach außen")
            a_item.setExpanded(True)
            a_item.setFlags(p_item.flags()  )
            b_item = QtGui.QTreeWidgetItem(p_item)
            b_item.setText(0, u"Darstellung beidseitig")
            b_item.setExpanded(True)
            b_item.setFlags(p_item.flags()  )
            
            #attid;st_attrname;min_linesigofsline;max_linesigofsline;min_lineoffset;max_lineoffset
            while (qry.next()):
                # positive Werte sind Außen, negative Innen
                bInnen=False
                bAussen=False
                Art=""
                if qry.value(2) <  0 or qry.value(3) <  0 or qry.value(4) <  0 or qry.value(5) <  0:
                    bInnen=True
                if qry.value(2) >  0 or qry.value(3) >  0 or qry.value(4) >  0 or qry.value(5) >  0:
                    bAussen=True
                
                if qry.value(2) <>  0 or qry.value(3) <>  0:
                    Art="Signatur"
                if qry.value(4) <>  0 or qry.value(5) <>  0: 
                    if Art=="":
                        Art = "Linie"
                    else:
                        Art = Art + " und Linie"
                
                if bInnen:
                    item = i_item
                if bAussen:
                    item = a_item
                if bInnen and bAussen:
                    item = b_item
                    
                item=QtGui.QTreeWidgetItem(item)
                item.setText(0, qry.value(1) + " (" + Art+ ")")
                item.setData(1,0,qry.value(0)) # Key in unsichtbare 2. Spalte
                item.setCheckState(0,Qt.Unchecked)
                item.setFlags(item.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)

     
    # Die Zeilen mit ausgewaehlter Checkox ausgeben
    def attWechseln(self):
        view = self.tvCaigosAtt
        Liste=[]
        it = QtGui.QTreeWidgetItemIterator(view,QtGui.QTreeWidgetItemIterator.Checked)
        while it.value():
            item = it.value()
            if item.text(1):
                Liste.append (item.text(1))    
            it += 1
        if len(Liste) == 0:
            msgbox(u"Es wurden keine Änderungen ausgewählt - Attributtabelle wird neu gelesen") 
            self.attEinlesen ()

        else:
            reply = QtGui.QMessageBox.question(self, u'Datenbank wird geändert',
            str(len(Liste)) + " Richtungsattribute tauschen", QtGui.QMessageBox.Yes,QtGui.QMessageBox.Cancel)       
            if reply == QtGui.QMessageBox.Yes:
                # jetzt per SQL umschreiben
                self.dbSchreiben(Liste)
                self.attEinlesen ()
    
    def dbSchreiben(self,Liste):
        clsdb = pgDataBase()
        con=clsdb.GetConnString()
        db=clsdb.OpenDatabase(con)
        if db:
            # Alle Elemente der Liste durchlaufen
            for id in Liste:
                sSQL="UPDATE  lineatttable  set linesigofsline = linesigofsline::numeric * -1,lineoffset = lineoffset::numeric * -1 "
                sSQL=sSQL + "WHERE  used='J' AND la_idfa='" + id + "' AND ( linesigofsline <> 0 OR  lineoffset <> 0)"
                feh = clsdb.Execute(db,sSQL)
                if feh <> "":
                    errbox (feh)
                    return
            msgbox ("""Hinweis: Die Änderungen werden erst nach einem Neustart von CAIGOS sichtbar\n
                     Bei unsymetrischen Symbolen muss das Symbol noch manuell angepasst werden""")
            
    def Start(self):
            self.attEinlesen ()
            self.exec_()

    
    def sql4AttList (self):
        sSQL = """SELECT  l.la_idfa AS attid,
	        f.attrname AS st_attrname,
	        min(l.linesigofsline),max(l.linesigofsline),
	        min(l.lineoffset),max(l.lineoffset)
	        --l.lineoffset
                    FROM (frameatttable as f
                          INNER JOIN lineatttable as l ON f.fa_id = l.la_idfa)
                    WHERE used='J'
                      AND l.la_idfa IN
                        (SELECT lineattr
                         FROM polyatttable)
                      AND (l.linesigofsline <> 0
                           OR l.lineoffset <> 0)
                    GROUP by l.la_idfa, f.attrname
                    ORDER BY f.attrname"""
        return sSQL
    
    def sqlEbene4AttID (self,AttID):
        # 29.08.16 RIGHT JOIN damit auch AD ohne Ebene angezeigt
        sSQL = """select distinct layername as ebene, defname as attribdef from (
            SELECT  l.layername , p.defid FROM prptable as p INNER JOIN lyrtable as l ON  p.layerid = l.layerid) as Layer 
            RIGHT JOIN

            --- alle 5 Screenattribute
            (
            SELECT distinct d.defname,d.defid AS fl_ADid,f.attrname AS st_ATTname,p.lineattr AS st_ATTid
            FROM frameatttable as f INNER JOIN (deftable as d INNER JOIN polyatttable  as p ON d.scrattrname1 = p.poa_idfa) ON f.fa_id = p.poa_idfa
            UNION
            SELECT distinct d.defname,d.defid AS fl_ADid,f.attrname AS st_ATTname,p.lineattr AS st_ATTid
            FROM frameatttable as f INNER JOIN (deftable as d INNER JOIN polyatttable  as p ON d.scrattrname2 = p.poa_idfa) ON f.fa_id = p.poa_idfa
            UNION
            SELECT distinct d.defname,d.defid AS fl_ADid,f.attrname AS st_ATTname,p.lineattr AS st_ATTid
            FROM frameatttable as f INNER JOIN (deftable as d INNER JOIN polyatttable  as p ON d.scrattrname3 = p.poa_idfa) ON f.fa_id = p.poa_idfa
            UNION
            SELECT distinct d.defname,d.defid AS fl_ADid,f.attrname AS st_ATTname,p.lineattr AS st_ATTid
            FROM frameatttable as f INNER JOIN (deftable as d INNER JOIN polyatttable  as p ON d.scrattrname4 = p.poa_idfa) ON f.fa_id = p.poa_idfa
            UNION
            SELECT distinct d.defname,d.defid AS fl_ADid,f.attrname AS st_ATTname,p.lineattr AS st_ATTid
            FROM frameatttable as f INNER JOIN (deftable as d INNER JOIN polyatttable  as p ON d.scrattrname5 = p.poa_idfa) ON f.fa_id = p.poa_idfa

            --- alle 5 Screenattribute
            UNION
            SELECT distinct d.defname,d.defid AS fl_ADid,f.attrname AS st_ATTname,p.lineattr AS st_ATTid
            FROM frameatttable as f INNER JOIN (deftable as d INNER JOIN polyatttable  as p ON d.prtattrname1 = p.poa_idfa) ON f.fa_id = p.poa_idfa
            UNION
            SELECT distinct d.defname,d.defid AS fl_ADid,f.attrname AS st_ATTname,p.lineattr AS st_ATTid
            FROM frameatttable as f INNER JOIN (deftable as d INNER JOIN polyatttable  as p ON d.prtattrname2 = p.poa_idfa) ON f.fa_id = p.poa_idfa
            UNION
            SELECT distinct d.defname,d.defid AS fl_ADid,f.attrname AS st_ATTname,p.lineattr AS st_ATTid
            FROM frameatttable as f INNER JOIN (deftable as d INNER JOIN polyatttable  as p ON d.prtattrname3 = p.poa_idfa) ON f.fa_id = p.poa_idfa
            UNION
            SELECT distinct d.defname,d.defid AS fl_ADid,f.attrname AS st_ATTname,p.lineattr AS st_ATTid
            FROM frameatttable as f INNER JOIN (deftable as d INNER JOIN polyatttable  as p ON d.prtattrname4 = p.poa_idfa) ON f.fa_id = p.poa_idfa
            UNION
            SELECT distinct d.defname AS AD,d.defid AS fl_ADid,f.attrname AS st_ATTname,p.lineattr AS st_ATTid
            FROM frameatttable as f INNER JOIN (deftable as d INNER JOIN polyatttable  as p ON d.prtattrname5 = p.poa_idfa) ON f.fa_id = p.poa_idfa) as FlAtt
            on FlAtt.fl_ADid = Layer.defid
            where st_attid = '""" + AttID + "'"
        return sSQL
        
if __name__ == "__main__":
    from clsDatenbank import *
    app = QtGui.QApplication(sys.argv)

    cls = uiToolsPolygonDirection()
    #print cls.sql4AttList()
    #qry = clsdb.OpenRecordset(db,cls.sql4AttList()) 
    cls.Start()

    """
    if guiListe:
        str1 = "','".join(guiListe)
        str1 = "'" + str1 + "'"
        QtGui.QMessageBox.information( None,u'Folgende Ebenen wurden gewählt',str1)
    """

    
