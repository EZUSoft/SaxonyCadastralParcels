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










from xml.dom import minidom
import urllib.request
import locale,datetime,uuid

try:
    from fnc4all import *

except:
    from .fnc4all import *


def fncProgKennung():
    return "CastralParcels" + str(myqtVersion)

def fncProgVersion():
    return "V " + fncPluginVersion()
    
def fncDebugMode(): 
    if (os.path.exists(os.path.dirname(__file__) + '/00-debug.txt')): 
        return True
    else:
        return False

def fncBrowserID():
    s = QSettings( "EZUSoft", fncProgKennung() )

    s.setValue( "-id-", (fncProgKennung() + str(uuid.uuid4())))
    return s.value( "–id–", "" ) 
    
def tr( message):
    return message  
    
def fncCGFensterTitel(intCG = None):
    s = QSettings( "EZUSoft", fncProgKennung() )
    sVersion = "-"
    if not intCG :
        intCG = int(s.value( "cgversion",-1))
    if intCG == 0:
        sVersion = "11.2"
    if intCG == 1:        
        sVersion = "2016"
    return u"Download und Konvertierung Inspire Flurstücke   (Programmversion " + fncProgVersion() + ")" 

def StandAusAtom(XMLDat):
    try:
        usock = urllib.request.urlopen(XMLDat)

        xmldoc = minidom.parse(usock)
        usock.close()

        Ebene1 = xmldoc.getElementsByTagName("feed")
        Ebene2 = Ebene1[0].getElementsByTagName("entry")
        Ebene3 = Ebene2[0].getElementsByTagName("updated")
        sDate=Ebene3[0].firstChild.data[0:10]

        locale.setlocale(locale.LC_ALL, 'de_DE')
        return (datetime.datetime.strptime(sDate,'%Y-%m-%d').strftime("%d. %B %Y"))
    except:
        return '#unbekannt#'
        
