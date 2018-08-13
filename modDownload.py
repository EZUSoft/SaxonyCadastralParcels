# -*- coding: utf-8 -*-
"""
/***************************************************************************
 modDownload

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
# QGIS3:  funktioniert unter QGIS 3.x recht zuverlässig auch auf "eingeschränktem Rechner"
# - nutzt die Proxyeinstellungen von QGIS
# - funktioniert in QGIS selbst auch über HTTPS (es wird durch QGIS eiun Abfragefenster geöffnet)
# - bei extrem großen Dateien (z.B. 500MBYte) crasht es bei ReadAll()


# QGIS2:  funktioniert unter QGIS 2.x innerhalb von QGIS aktuell recht zuverlässig auch auf "eingeschränktem Rechner"
#         außerhalb hängt sich der Code auf "eingeschräktem Rechner" auf und bringt dann auch kein Ergebnis
#         Normalrechner funktioniert es 
    def WriteFile(LokFileName, content):
            # 1. Ziel löschen, wenn existent
            if path.exists(LokFileName):
                remove (LokFileName)
            out=open(LokFileName,'wb')
            out.write(content)
            out.close()

    def onfinish():
        WriteFile(LokFileName,reply.readAll());
        loop.quit()


    # 2. Download
    request = QNetworkRequest()
    request.setUrl(QUrl(dlURL))
    manager = QgsNetworkAccessManager.instance()
    
    reply = manager.get(request)
    reply.setParent(None)
    
    loop = QEventLoop()
    reply.finished.connect(onfinish)  
    loop.exec_() 
    
    # Wiederholung bei redirekt (13.08.18 Thüringen leitet an HTTPS weiter)
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
    



    
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    print ("========== QT" + str(myqtVersion) + " ===========")
    #http://geodownload.sachsen.de/inspire/cp_atom/sn_shape/sn_cp.zip
    #http://www.makobo.de/data/expTH.dat.zip    
    #http://geoportal5.geoportal-th.de/ALKIS/Shape/ALKIS_5506-001_shp.zip
    #print(DownLoadOverQT ("http://www.makobo.de/data/expTH.dat.zip","d:/tar/expTH_qt" + str(myqtVersion) + ".zip"))

    print(DownLoadOverQT ("http://geoportal5.geoportal-th.de/ALKIS/Shape/ALKIS_5506-001_shp.zip","d:/tar/ALKIS_5506-001_shp_qt" + str(myqtVersion) + ".zip"))

    #DownLoadOverQT ("http://geodownload.sachsen.de/inspire/cp_atom/sn_shape/sn_cp.zip","d:/tar/sn_cp_qt" + qtversion + ".zip")
    #print ("Fertig2")
    
