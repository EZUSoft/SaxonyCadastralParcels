# -*- coding: utf-8 -*-
"""
/***************************************************************************
 fnc4sqlite: Gemeinsame Basis für QGIS2 und QGIS3
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
import sqlite3 as sl
try:
    from fnc4all import *
except:
    from .fnc4all import *

def slOpenRecordset(dbName,sSQL):
    try:
        con = sl.connect(dbName)
        con.row_factory = sl.Row #the contents of table using the dictionary cursor

        cur = con.cursor()    
        cur.execute(sSQL)
        return cur.fetchall()

    except:
        subLZF ()

    finally:   
        if con:
            con.close()
if __name__ == "__main__":
    sSQL = ('SELECT DBPROJECT_PRJNAME AS prjName, DBCONNECT_SERVERNAME AS pgServer, DBCONNECT_DATABASENAME AS pgDatabase, DBCONNECT_USERNAME AS pgUserName, DBCONNECT_PASSWORD AS pgPasswd '
       'FROM DBPROJECT '
       'INNER JOIN DBCONNECT ON DBPROJECT.DBPROJECT_IDDBCONNECT = DBCONNECT.DBCONNECT_ID WHERE lower([DBCONNECT_PACTORTYPE])="postgresql";')
    dbName='X:\CAIGOS_HOME\CAIGOS_Server\dbdesign.cgbin'
    rs = slOpenRecordset(dbName,sSQL)
    if rs is None:
        print (getFehler())
    else:
        for row in rs:
            print (row["pgServer"])
        print ('hier')



