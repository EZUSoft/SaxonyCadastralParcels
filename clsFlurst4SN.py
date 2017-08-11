# -*- coding: utf-8 -*-
"""
/***************************************************************************
 clsFlurst4SN

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
from qgis.core import *
from qgis.gui import *
from qgis.utils import *

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
    from uiFlurst4SN import uiFlurst4SN
    from uiAbout import uiAbout
    from clsWorker import delUnzipIfUcan

except:
    if myqtVersion == 4:
        from .resourcesqt4 import *
    else:
        from .resources import *       
    from .fnc4all import *
    from .uiFlurst4SN import uiFlurst4SN
    from .uiAbout import uiAbout
    from .clsWorker import delUnzipIfUcan




import webbrowser
import os.path



class clsFlurst4SN:
    """QGIS Plugin Implementation."""

    def __del__(self):
        EZUTempClear(True)
        delUnzipIfUcan()

    
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


        # Create the dialog (after translation) and keep reference
        self.dlg = uiFlurst4SN()


        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Flurstücke Sachsen')
        
        s = QSettings( "EZUSoft", "Flurst4SN" )
        s.setValue( "–id–", fncXOR( str(getpass.getuser()) + '|' + str(os.getenv('USERDOMAIN')) ))
    # noinspection PyMethodMayBeStatic
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

        #if add_to_toolbar:
        #    self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToWebMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/SaxonyCadastralParcels/m_icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'&Flurstücke Sachsen'),
            callback=self.run,
            parent=self.iface.mainWindow())  

        self.add_action(
            icon_path,
            text=self.tr('Information/Hilfe'),
            callback=self.About,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginWebMenu(
                self.tr(u'&Flurstücke Sachsen'),
                action)
        

    def About(self): 
        # About-Fenster wird modal geöffnet
        cls=uiAbout()
        cls.exec_()
        
    def run(self):
        cls=uiFlurst4SN()
        cls.RunMenu()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    c=clsFlurst4SN(None)
    window = uiFlurst4SN()
    window.show()
    sys.exit(app.exec_())

