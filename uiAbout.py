# -*- coding: utf-8 -*-
"""
/***************************************************************************
 uiAbout

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
from qgis.utils import os, sys

try:
    from PyQt5          import  uic, QtWidgets
    from PyQt5.QtCore   import  QDir
    from PyQt5.QtWidgets import QDialog
except:
    from PyQt4          import QtGui, uic
    from PyQt4.QtCore   import  QDir
    from PyQt4.QtGui    import QDialog

try:
    from fnc4all import *
    from fnc4SaxonyCadastralParcels import *
except:
    from .fnc4all import *
    from .fnc4SaxonyCadastralParcels import *


d = os.path.dirname(__file__)
QDir.addSearchPath( "SaxonyCadastralParcels", d )
uiAboutBase = uic.loadUiType( os.path.join( d, 'uiAbout.ui' ) )[0]

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'uiAbout.ui'))
   

class uiAbout(QDialog, FORM_CLASS):  
    def __init__(self, parent=None):
        """Constructor."""
        super(uiAbout, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        s=self.lblLink.text()
        s=s.replace("$$Homepage$$","http://www.makobo.de/links/Home_SaxonyCadastralParcels.php?id=" + fncBrowserID())
        s=s.replace("$$Daten$$","http://www.makobo.de/links/Daten_SaxonyCadastralParcels.php?id=" + fncBrowserID())
        s=s.replace("$$Forum$$","http://www.makobo.de/links/Forum_SaxonyCadastralParcels.php?id=" + fncBrowserID())
        s=s.replace("$$Doku$$","http://www.makobo.de/links/Dokumentation_SaxonyCadastralParcels.php?id=" + fncBrowserID())
        self.lblLink.setText(s)
  
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = uiAbout()
    window.show()
    sys.exit(app.exec_())

