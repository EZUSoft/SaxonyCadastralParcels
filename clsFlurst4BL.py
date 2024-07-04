# -*- coding: utf-8 -*-
"""
/***************************************************************************
 A QGIS plugin
SaxonyCadastralParcels: Download Flurstuecke Sachsen und Thueringen, Darstellung in QGIS und Konvertierung nach DXF
        copyright            : (C) 2020 by EZUSoft
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
import uuid

try:
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
    from PyQt5.QtWidgets import *
    myqtVersion = 5
except:
    from PyQt4.QtCore import *
    from PyQt4.QtGui import *
    myqtVersion = 4
    
try:
    if myqtVersion == 4:
        from resourcesqt4 import *
    else:
        from resources import *
    
    from fnc4all import *
    from fnc4SaxonyCadastralParcels import *
    from uiFlurst4BL import uiFlurst4BL
    from uiAbout import uiAbout
    from clsWorker import delUnzipIfUcan

except:
    if myqtVersion == 4:
        from .resourcesqt4 import *
    else:
        from .resources import *       
    from .fnc4all import *
    from .fnc4SaxonyCadastralParcels import *
    from .uiFlurst4BL import uiFlurst4BL
    from .uiAbout import uiAbout
    from .clsWorker import delUnzipIfUcan




import webbrowser
import os.path



class clsFlurst4BL:


    def __del__(self):
        EZUTempClear(True)
        delUnzipIfUcan()

    
    def __init__(self, iface):







       

        self.iface = iface

        self.plugin_dir = os.path.dirname(__file__)








        self.actions = []
        self.menu = self.tr(u'&Inspire Flurstücke')
        
        s = QSettings( "EZUSoft", fncProgKennung() )

        s.setValue( "–id–", fncXOR( str(getpass.getuser()) + '|' + str(os.getenv('USERDOMAIN')) ))



    def tr(self, message):
        return  message


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
            self.iface.addPluginToWebMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):


        icon_path = ':/plugins/SaxonyCadastralParcels/m_icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Flurstücke &Sachsen/Thüringen'),
            callback=self.runMenue,
            parent=self.iface.mainWindow())  

        self.add_action(
            icon_path,
            text=self.tr('Information/Hilfe'),
            callback=self.About,
            parent=self.iface.mainWindow())


    def unload(self):

        for action in self.actions:
            self.iface.removePluginWebMenu(
                self.tr(u'&Inspire Flurstücke'),
                action)
 
    def About(self): 

        cls=uiAbout()
        cls.exec_()
        
    def runMenue(self):
        cls=uiFlurst4BL()
        cls.RunMenu()
        
