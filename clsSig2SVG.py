# -*- coding: utf-8 -*-
"""
/***************************************************************************
 clsSig2SVG
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
import os.path
from fnc4all import *
import re

def subMkPfad (VerzNam, Rekursiv=False):
    try:
        if Rekursiv:
            Pfad = ""
            v=VerzNam.replace("\\","/")
            v=v.replace("//","/")
            for p in  v.split("/"):
                Pfad = Pfad  + p + "/"
                if not os.path.exists(Pfad):
                    os.makedirs(Pfad)
        else:
            if not os.path.exists(VerzNam):
                os.makedirs(VerzNam) 
        return True
    except:
        return False

    
def Sig2SVG (qDat, zDat, Fill=False):
    #!!! Achtung: QGIS cache die SVG-s, deshalb ist bei Änderungen an den Signaturen
    #             bzw. an der Programmierung eine Neustart erforderlich !!!   
    if not os.path.isfile(qDat): 
        addFehler("CAIGOS Signatur '" + qDat + "'nicht gefunden")
        return False
    try:
        bLW = None
        def korr(w0,w1): 
            # Linienbreite anpassen
            # Parameter LINEWIDTH on/off
            #   on: am Bildschirm keine Strichbreite, am Drucker aber schon

            #return str(float(w0)/50 * float(w1))
            if bLW:
                return str(1.8 * float(w1))
            else:
                #1000-er -> 10 ; 100 ->  1
                # es gibt scheinbar keinen perfekte Lösung:
                # - bei GP müsste der Wert 1000/100 *2 = 20 sein
                # - bei Verkehrszeichenflächen darf er nur 2 statt 20 sein.
                # Es wird jetzt doch pauschal mit 2 gearbeitet. GP sollten entweder auf Kreisring oder auf LINEWIDTH=On um gestellt werden
                return "2" # str(float(w0)/100 *2)
            
        def neg(w, h):
            if w.find("/") <> -1:
                v = w.split("/")
                d = float(v[1])
                v[1] = str(h - d)
                return "/".join(v)
            else:
                return str(h-float(w))

        
        iDatNum = open(qDat)
        oDatNum = open(zDat,"w")
        z=0
        sTrenn = "@"
        for iZeile in iDatNum:
            iZeile=iZeile.replace("\n","")
            if iZeile[:10] == "TOKENCHAR " : 
                sTrenn = iZeile.split()[1]
            if iZeile[:6] == "WIDTH " : 
                w = float(iZeile.split()[1])
            if iZeile[:7] == "HEIGHT " :
                h = float(iZeile.split()[1])
                oDatNum.write("<svg width='" + str(w) + "' height='" + str(h) + "' xmlns='http://www.w3.org/2000/svg'>\n")
            if iZeile[:10] == "LINEWIDTH " : 
                bLW = True if iZeile.split()[1] == "on" else False

            # Reihenfolge des Schreibens entspricht der Priotität in der Darstellung
            # 1. Flächen
            if iZeile[:5] == "POLY " :
                v = iZeile.split()
                oZeile = "<polygon points='"
                for i in range(10,len(v)):
                    oZeile = oZeile + neg(v[i], h).replace( "/", ",") + " "

                oDatNum.write(oZeile.strip() + "'\n")
                oDatNum.write("style='fill-opacity: " + str(abs(1 - int(v[6]))) + ";fill:rgb(" + v[7] + "," + v[8] + "," + v[9] + ");stroke-width:" + korr(w,v[1]) + ";stroke:rgb(" + v[3] + "," + v[4] + "," + v[5] + ")'\n")
                oDatNum.write(" />\n")
            
            # 2. Kreise        
            if iZeile[:4] == "ARC " :
                v = iZeile.split()
                Fuell=v[6]
                oDatNum.write("<circle cx='" + v[10] + "' cy='" + neg(v[11], h) + "' r='" + v[12] + "'\n")
                oDatNum.write("style='fill-opacity: " + str(abs(1 - int(v[6]))) + ";fill:rgb(" + v[7] + "," + v[8] + "," + v[9] + ");stroke-width:" + korr(w,v[1]) + ";stroke:rgb(" + v[3] + "," + v[4] + "," + v[5] + ")'\n")
                oDatNum.write("/>\n")
            
            # 3. Polylinien
            if iZeile[:5] == "LINE " :
                v = iZeile.split()
                oDatNum.write("<line x1='" + v[6] + "' y1='" + neg(v[7], h) + "' x2='" + v[8] + "' y2='" + neg(v[9], h) + "'\n")
                oDatNum.write("style='stroke-linecap:round;stroke-width:" + korr(w,v[1]) + ";stroke:rgb(" + v[3] + "," + v[4] + "," + v[5] + ")'\n")
                oDatNum.write(" />\n")
            
            #4. Strecken
            if iZeile[:4] == "SEG " :
                v = iZeile.split()
                oZeile = "<polyline points='"
                for i in range(10,len(v)):
                    oZeile = oZeile + neg(v[i], h).replace( "/", ",") + " "
                oDatNum.write(oZeile.strip() + "'\n")
                oDatNum.write("style='stroke-linecap:round;fill:none;stroke-width:" + korr(w,v[1]) + ";stroke:rgb(" + v[3] + "," + v[4] + "," + v[5] + ")'\n")
                oDatNum.write(" />\n")
            
            #5. Texte
            if iZeile[:5] == "TEXT " :
                #  0    1     2  3 4 5    6       7    8   9 10   11     12 13  14  15
                #TEXT ¤Arial¤200¤0¤0¤0¤500.000¤200.000¤J¤text¤N¤429.402¤255¤255¤255¤0.0
                # Trenner kann "¤" oder "@" sein

                #v = re.split("\xA4|@",iZeile)
                v=iZeile.split(sTrenn)
                fY= str(float(v[7]) - float( v[2]) * 0.9)           
                oDatNum.write("<text x='" + v[6] + "' y='" + neg(fY, h)  + "'\n")
                oDatNum.write(("style='font-size:%spx;font-family:%s;fill:rgb(%s,%s,%s)'") % (v[2],v[1],v[3],v[4],v[5])) #" + ";fill:rgb(" + v[7] + "," + v[8] + "," + v[9] + ");stroke-width:" + korr(w,v[1]) + ";stroke:rgb(" + v[3] + "," + v[4] + "," + v[5] + ")'\n")
                oDatNum.write(">"+v[9]+"</text>\n")
                

        oDatNum.write("</svg>")
        iDatNum.close()
        oDatNum.close()

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        subLZF (qDat,exc_type, fname, exc_tb.tb_lineno,qDat)

    
if __name__ == "__main__":



    # =========================================================================
    # Werte aus Tabelle


        resetFehler()
        #qDat=u"X:/caigos/CAIGOS_Projekte150109/RisZwickau/signatur/Stadtplan/STPL_Kindertagesstätten.sig"
        qDat=u"X:/caigos/CAIGOS_Projekte150109/Straßendokumentation/signatur/Verkehrszeichen/66-StraDok-V1008-32.sig"
        zDat = r"d:\tar\MeinePunktsignaturDatei.svg"
        #printlog (qDat.replace("/","\\"))
        #printlog (zDat.replace("/","\\"))
        Sig2SVG (qDat,zDat)
        print getFehler()
