# -*- coding: utf-8 -*-
"""
/***************************************************************************
 clsCaigosConnector
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
from qgis.gui import *
from qgis.utils import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from fnc4all import *
# Initialize Qt resources from file resources.py
import resources

# Import der 3 Einzelmodule
from uiExplorer import uiExplorer
from uiAbout import uiAbout
from uiDBAnbindung import uiDBAnbindung

from clsDatenbank import *
from clsQGISAction import clsQGISAction

import webbrowser
import os
import getpass


if fncDebugMode():
    from clsDebug import clsDebug

class clsCaigosConnector:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        """
        # =====================================================================================================================
        # Übersetzung macht wenig Sinn, das CAIGOS selbst nur auf deutsch existiert und somit  keine fremdsprachigen Nutzer hat
        # =====================================================================================================================
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'clsCaigosConnector_{}.qm'.format(locale))
        print locale_path
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)
        """

        

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&CAIGOS Datenprovider')
        s = QSettings( "EZUSoft", "CAIGOS-Konnektor" )
        s.setValue( "–id–", fncXOR( getpass.getuser() + '|' + os.getenv('USERDOMAIN') ))



    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('clsCaigosConnector', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):


        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_menu:
            self.iface.addPluginToDatabaseMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/CaigosConnector/EZUSoftOT.png'
        
        self.add_action(
            icon_path,
            text=self.tr(u'CAIGOS PostGIS Layer einbinden'),
            callback=self.LayerEinlesen,
            parent=self.iface.mainWindow())
        self.add_action(
            icon_path,
            text=self.tr(u'CAIGOS PostGIS Datenbankverbindung anpassen'),
            callback=self.SetzeDBAnbindung,
            parent=self.iface.mainWindow())

        if fncDebugMode():
            self.add_action(
                icon_path,
                text=self.tr(u'Debug'),
                callback=self.modDebug,
                parent=self.iface.mainWindow())

        self.add_action(
            icon_path,
            text=self.tr(u'Onlinedokumentation'),
            callback=self.HilfeAnzeige,
            parent=self.iface.mainWindow())
        
        self.add_action(
            icon_path,
            text=self.tr(u'Über das Programm'),
            callback=self.About,
            parent=self.iface.mainWindow())
            
    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginDatabaseMenu(
                self.tr(u'&CAIGOS Datenprovider'),
                action)
         
        # -- keine Toolbar benötigt ---
        # self.iface.removeToolBarIcon(action)
        # remove the toolbar
        # del self.toolbar

    def modDebug(self): 
        # About-Fenster wird modal geöffnet
        c=clsDebug()
        c.debugplugin()
        
    def About(self): 
        # About-Fenster wird modal geöffnet
        cls=uiAbout()
        cls.exec_()
    
    def HilfeAnzeige(self): 
        # Link öffnen
        webbrowser.open_new_tab("http://www.makobo.de/links/Dokumentation_CaigosConnector.php?id=" + fncBrowserID())

    def LayerEinlesen(self):
        resetFehler()
        resetHinweis()
        User = '000'
        clsdb = pgDataBase()
        if clsdb.CheckVerbDaten(None,None,None,None, True):
            db=clsdb.CurrentDB()
        else:
             db=None  
        
        cls=uiExplorer()
        cls.OptSpeichern()
        if db :
            qry = clsdb.OpenRecordset(db, clsdb.sqlStrukAlleLayer()) 
            projekt=clsdb.GetCGProjektName()
            guiListe, bGenDar, bPrjNeu = cls.LayerErmitteln(projekt, qry)

            if guiListe:
                InStr = "','".join(guiListe)
                InStr = "'" + InStr + "'"
                # QtGui.QMessageBox.information( None,'Datenbankzugriff',InStr) 
                qry = clsdb.OpenRecordset(db, clsdb.sqlStrukAlleLayer(InStr))
                pri = clsdb.OpenRecordset(db, clsdb.sqlAlleLayerByPri(User,InStr))
                c = clsQGISAction()
                c.QGISBaum(db,User,projekt,pri,qry, bGenDar, bPrjNeu)
        else:          
            reply = QtGui.QMessageBox.question(None, 'Fehler beim Datenbankanbindung',"Soll der Dialog \n'CAIGOS PostGIS Datenbankverbindung anpassen'\naufgerufen werden", QtGui.QMessageBox.Yes |  QtGui.QMessageBox.No, QtGui.QMessageBox.No)
            if reply == QtGui.QMessageBox.Yes:
                self.SetzeDBAnbindung()

        
    
    def SetzeDBAnbindung(self):
        cls=uiDBAnbindung()
        cls.exec_()    
  
if __name__ == "__main__":
    c = clsCaigosConnector(QCoreApplication.instance())
    print c.tr(u'&CAIGOS Datenprovider')