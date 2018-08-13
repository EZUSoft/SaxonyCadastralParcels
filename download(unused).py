# funktioniert innerhalb von QGIS 2 und 3
try:
    from PyQt4.QtCore import QUrl, QEventLoop
    from PyQt4.QtNetwork import QNetworkRequest
    from qgis.core import QgsNetworkAccessManager
    qtversion="4"
except:
    from PyQt5.QtCore import QUrl, QEventLoop
    from PyQt5.QtNetwork import QNetworkRequest
    from qgis.core import QgsNetworkAccessManager
    qtversion="5"
#http://geodownload.sachsen.de/inspire/cp_atom/sn_shape/sn_cp.zip
#http://www.makobo.de/data/expTH.dat.zip
url = QUrl("http://www.makobo.de/data/expTH.dat.zip")

def WriteFile(LokFileName, content):
        out=open(LokFileName,'wb')
        out.write(content)
        out.close()


request = QNetworkRequest()
request.setUrl(url)
manager = QgsNetworkAccessManager.instance()
replyObject = manager.get(request)
loop = QEventLoop()

def onfinish(  ):
    print("Qt Return Code:",replyObject.attribute(QNetworkRequest.HttpStatusCodeAttribute))
    WriteFile("d:/tar/qt" + qtversion + ".zip",replyObject.readAll());
    loop.quit()

replyObject.finished.connect( onfinish )
loop.exec_()
print ("Fertig")