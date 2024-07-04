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







try:
    from PyQt4.QtGui import QApplication
    from PyQt4.QtCore import QUrl, QEventLoop, QTimer
    from PyQt4.QtNetwork import QNetworkRequest
    from qgis.core import QgsNetworkAccessManager
    myqtVersion = 4

except:
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QUrl, QEventLoop, QTimer
    from PyQt5.QtNetwork import QNetworkRequest
    from qgis.core import QgsNetworkAccessManager
    myqtVersion = 5



from os import path, remove
    
def DownLoadOverQT (dlURL, LokFileName):









    def WriteFile(LokFileName, content):

            if path.exists(LokFileName):
                remove (LokFileName)
            out=open(LokFileName,'wb')
            out.write(content)
            out.close()

    def onfinish():
        WriteFile(LokFileName,reply.readAll());
        loop.quit()



    request = QNetworkRequest()
    request.setUrl(QUrl(dlURL))
    manager = QgsNetworkAccessManager.instance()
    reply = manager.get(request)
    reply.setParent(None)
    
    loop = QEventLoop()
    reply.finished.connect(onfinish)  
    loop.exec_() 
    

    status=reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
    if (status==301):
        redirectUrl = reply.attribute(request.RedirectionTargetAttribute)
        request = QNetworkRequest()



        request.setUrl(redirectUrl)
        manager = QgsNetworkAccessManager.instance()
        reply = manager.get(request)
        reply.setParent(None)
        
        loop = QEventLoop()
        reply.finished.connect(onfinish)  
        loop.exec_() 
    
    
    
    if path.exists(LokFileName):
        return path.getsize(LokFileName), reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
    else:
        return None, reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
    reply.deleteLater()
    



    
