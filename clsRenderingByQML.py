# -*- coding: utf-8 -*-
"""
/***************************************************************************
 clsRenderingByQML: Gemeinsame Basis für QGIS2 und QGIS3
  01.07.2017 V0.4
   - Erweiterung auf Caigos 2016 dadurch Umstellung von PRIV: auf "PUB:"
     Im 11.2 gibt es PRIV: und PUB: in CAIGOS 2016 nur noch PUB:. 
     Bisher wurden in 11.2 nur die PRIV: bearbeitet, das wird der Einfachkeit halber so beibehalten
     und für 2016 duch PUB ersetzt     
 
  05.10.2016 V0.3
  - Kreis jetzt auch mit attributierter Darstellung
  - Text-Referenzlinie mit Darstellung
  
  09.09.2016 V0.3
  - EinLinienPunktMarker: Start um halbe Signaturbreite verschieben, sonst steht's über
  - fnctxtCtoQ cArt 2 korrigiert
  - Abstand Liniensignaturen korrigiert (Interval setzen, auch wenn Abstand 0)
  
  08.08.2016 V0.3
  - Einbindung fnctxtCtoQ(cArt) für Kreis
  
  16.06.2016 V0.2
  - Generierung von Liniensignaturen
  - Generierung von Flächenfüllungen

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
import xml.etree.cElementTree as ET
import xml.dom.minidom as dom
import tempfile

from qgis.core import * 
try:
    from clsDatenbank import *
    from fnc4all import *
    from clsSig2SVG import *
except:
    from .clsDatenbank import *
    from .fnc4all import *
    from .clsSig2SVG import *
    
glTransparentsWert= 200

def fncAktRecToText(rsAtt):
    ds=""
    s=""
    for f in range(rsAtt.record().count()):
        if type(rsAtt.value(f)) == unicode:
            ds = ds + u"|" + rsAtt.value(f)
        else:
            ds = ds + u"|" + str(rsAtt.value(f))
    return ds
   
def fnctxtCtoQ(cArt):
    if cArt == 0:
        return 8
    if cArt == 1:
        return 5
    if cArt == 2:
        return 2
    if cArt == 3:
        return 7
    if cArt == 4:
        return 4
    if cArt == 5:
        return 1
    if cArt == 6:
        return 6
    if cArt == 7:
        return 3
    if cArt == 8:
        return 0

        
def fncStdAreaStyle(cgStyle):        
    """
0: Farbfüllung
1: Keine Füllung bzw. benutzerdefiniert
2: Horizontal
3: Vertikal
4: Diagonal1
5: Diagonal2
6: Kreuz
7: Diagonal Kreuz
    """
        
def fncStdLineStyle(cgStyle):
    """
    pentype	name	text
0	Voll-Linie	- durchgezogene Linie- abgerundete Ecken- 1/2 Geometriepunkt-Überstand
1	Strich-Linie	- gestrichelte Linie- abgerundete Ecken- 1/2 Geometriepunkt-Überstand
2	Punkt-Linie	- gepunktete Linie- abgerundete Ecken- 1/2 Geometriepunkt-Überstand
3	Strich-Punkt-Linie	- Strich-Punkt-Linie- abgerundete Ecken- 1/2 Geometriepunkt-Überstand
4	Strich-Punkt-Punkt-Linie	- Strich-Punkt-Punkt-Linie- abgerundete Ecken- 1/2 Geometriepunkt-Überstand
    """
    if cgStyle==0:
        return "solid"
    if cgStyle==1:
        return "dash"
    if cgStyle==2:
        return "dot"
    if cgStyle==3:
        return "dash dot"
    if cgStyle==4:
        return "dash dot dot"

def fncUserLineStyle(rsParam):
    """
astyle0	astyle1	astyle2	astyle3	astyle4	astyle5	astyle6	astyle7	astyle8	astyle9
    """
    s=""
    for i in range(10):
        s=s+";"+ str(fncfield(rsParam,"astyle"+str(i)))
    return s[1:]
    
def fncLongToRGB (Farbe):
    flist=[]
    flist.append (Farbe & 255)
    flist.append ((Farbe // 256) & 255)
    flist.append (Farbe // 65536)
    return flist

def fncLongTosRGB (Farbe,Transparent=False):
    s=str(Farbe & 255)
    s=s+","+str((Farbe // 256) & 255)
    s=s+","+str (Farbe // 65536) 
    if Transparent:
        s=s+","+ str(glTransparentsWert)
    return s
    
def fncfield (rs,FieldName):
    w= rs.value(rs.record().indexOf(FieldName)) 
    if not w is None:
        return w
    else:    
        errlog ("Fehler: " + FieldName)
    
def OberRolle(root_rule,qtyp,rName,Bedingung):
        # Erstellen der "Obergruppe"
        new_rule = root_rule.children()[0].clone()
        new_rule.setFilterExpression(Bedingung)
        new_rule.setLabel(rName)
        new_rule.setSymbol(None) # Kein Symbol bei "Oberrolle)
        root_rule.appendChild(new_rule)
        return new_rule
        
def EineRolle(root_rule,Rollenname,Von, Bis):
        rule = root_rule.children()[0].clone()
        rule.setLabel(Rollenname)       
        rule.setScaleMinDenom(Von)
        rule.setScaleMaxDenom(Bis)
        return rule

def Pfade4Signatur (clsdb,sigpath,signame):
    sigPfad=clsdb.GetCGSignaturPfad()
    svgPfad=clsdb.GetQSVGSignaturPfad() 
    
    if sigpath == "":
        if clsdb.GetCGVersion() == 0:
            sigpath="PRIV:"
            addHinweis("Kein Signaturverzeichnis : " + signame )
        else:
            addFehler("Kein Signaturverzeichnis : " + signame )
            
    cgPfad=sigpath.replace("PRIV:",sigPfad).replace("PUB:",sigPfad)
    qPfad=sigpath.replace("PRIV:",svgPfad).replace("PUB:",sigPfad)

    
    qDat= cgPfad + signame  + ".sig"
    qDat=qDat.replace("\\","/")
    zDat = qPfad + signame + ".svg"
    zDat=zDat.replace("\\","/")
    return  qPfad, qDat, zDat
    
def EinfacheBeschriftungZeichnen(clsdb, db, qLayer,AktDefName, Group):
        rsAtt=clsdb.OpenRecordset(db,clsdb.sqlAttParam4IDandArt(3, AktDefName, Group))
        symbol = QgsSymbolV2.defaultSymbol(QGis.Point)
        symbol.setSize( 0.0 )
        qLayer.setRendererV2( QgsSingleSymbolRendererV2( symbol ) )
        # Nur das erste Attribut wird umgesetzt
        if rsAtt.next():
            #printlog ("EinfacheBeschriftungZeichnen")
            # Textdarstellung über Punktlabel
            QgsPalLayerSettings().writeToLayer( qLayer )
            qLayer.setCustomProperty("labeling","pal")
            qLayer.setCustomProperty("labeling/dataDefined/Rotation","alpha")
            qLayer.setCustomProperty("labeling/displayAll","true")
            qLayer.setCustomProperty("labeling/enabled","true")
            qLayer.setCustomProperty("labeling/fieldName","pstext")
            qLayer.setCustomProperty("labeling/fontBold","True" if rsAtt.value(7) == "J" else "False") 
            qLayer.setCustomProperty("labeling/fontFamily",rsAtt.value(6)) 
            qLayer.setCustomProperty("labeling/fontItalic","True" if rsAtt.value(8) == "J" else "False")
            qLayer.setCustomProperty("labeling/fontUnderline","True" if rsAtt.value(9) == "J" else "False")
            qLayer.setCustomProperty("labeling/fontSize",rsAtt.value(5)) 
            qLayer.setCustomProperty("labeling/fontSizeInMapUnits","true")
            qLayer.setCustomProperty("labeling/obstacle","false")
            qLayer.setCustomProperty("labeling/placement","1")
            qLayer.setCustomProperty("labeling/placementFlags","0")
            qLayer.setCustomProperty("labeling/quadOffset", fnctxtCtoQ(rsAtt.value(11))) 
            qLayer.setCustomProperty("labeling/textColorA","255")
            
            color = fncLongToRGB(rsAtt.value(4)) #4
            qLayer.setCustomProperty("labeling/textColorR",color[0])
            qLayer.setCustomProperty("labeling/textColorG",color[1])
            qLayer.setCustomProperty("labeling/textColorB",color[2])

            qLayer.setCustomProperty("labeling/textTransp","0")
            qLayer.setCustomProperty("labeling/upsidedownLabels","2")
            qLayer.setCustomProperty("labeling/wrapChar",r"\n")  

def EinSchraffurPunktFuellung (eSym,db,clsdb,AttID,Win,sigPfad, svgPfad,Num, Group):
    rsParam=clsdb.OpenRecordset(db,clsdb.sqlAttParam4IDandArt(0, AttID , Group))
    rsParam.next()
    # ===================================       SVG erzeugen            ===================================================
    qPfad,qDat,zDat = Pfade4Signatur(clsdb,fncfield(rsParam,"sigpath"),fncfield(rsParam,"signame"))
    subMkPfad (qPfad, True)
    Sig2SVG (qDat,zDat)
    
    # ===============================================================================================================
    # Layerdaten schreiben
    qmap={'pass':'0','class':'SVGFill','locked':'0'}
    eLayer=ET.SubElement(eSym,"layer",qmap)    
    prop={}
    prop['angle']=str(Win)
    prop['svgFile']=zDat
    prop['width']=str(fncfield(rsParam,"wsizemm"))
    prop['pattern_width_unit']="MapUnit"
    for p in prop:
        ET.SubElement(eLayer, "prop",k=p,v=prop[p])
    
    # Dummylinie muss sein
    qmap={}   
    qmap['alpha']='1'
    qmap['clip_to_extent']='1'
    qmap['type']='line'
    eSym=ET.SubElement(eLayer,"symbol",qmap)   
    qmap={} 
    qmap={'pass':'0','class':'SimpleLine','locked':'0'}
    eLayer=ET.SubElement(eSym,"layer",qmap)    
    ET.SubElement(eLayer, "prop",k="line_width",v="0")    

    
    return eLayer   
    
def EinLinienPunktMarker (eSym,db,clsdb,AttID,qPosition, sUnit, Group, Abstand=None, Start=0, Offset = 0):
    #try:
        rsParam=clsdb.OpenRecordset(db,clsdb.sqlAttParam4IDandArt(0, AttID , Group))
        rsParam.next()

        # ===================================       SVG erzeugen            ===================================================
        qPfad,qDat,zDat = Pfade4Signatur(clsdb,fncfield(rsParam,"sigpath"),fncfield(rsParam,"signame"))
        
        subMkPfad (qPfad, True)
        Sig2SVG (qDat,zDat)
        
        # ===============================================================================================================
        # Layerdaten schreiben
        qmap={'pass':'0','class':'MarkerLine','locked':'0'}
        eLayer=ET.SubElement(eSym,"layer",qmap)    
        prop={}
        if not Abstand is None: # 22.08.16 is None, da bei =0 "gearbeitet" werden muss
            prop['interval']=str(Abstand+fncfield(rsParam,"wsizemm"))
            prop['interval_map_unit_scale']='0,0,0,0,0,0'
            prop['interval_unit']="MapUnit" # 22.08.16 caigos scheint bei Liniensignaturen immer Karteneinheiten zu nehmen
        else:
            #'lastvertex',"firstvertex","centralpoint"
            prop['placement']=qPosition
        
        # 22.08.16 caigos scheint bei Liniensignaturen immer Karteneinheiten zu nehmen
        # 05.10.16: # +fncfield(rsParam,"wsizemm")/2) hat sich als falsch erwiesen (getestet mit Zuordungspfeil)
        prop['offset_along_line']=str(Start) # +fncfield(rsParam,"wsizemm")/2) # 09.09.16 Start um halbe Signaturbreite verschieben, sonnst stehts über
        prop['offset_along_line_unit']="MapUnit"
        prop['offset']=str(Offset * -1)
        prop['offset_unit']="MapUnit"
        prop['offset_along_line_unit']="MapUnit"
        prop['offset_map_unit_scale']='0,0,0,0,0,0'


        prop['rotate']='1'    
        for p in prop:
            ET.SubElement(eLayer, "prop",k=p,v=prop[p])
        
        # jetzt das Symbol
        qmap={}   
        qmap['alpha']='1'
        qmap['clip_to_extent']='1'
        qmap['type']='marker'
        eSym=ET.SubElement(eLayer,"symbol",qmap)   
        qmap={} 
        qmap={'pass':'0','class':'SvgMarker','locked':'0'}
        eLayer=ET.SubElement(eSym,"layer",qmap)    
        prop={}
        prop['angle']='0' # str(Win)
        prop['color']='0,0,0,255'
        prop['horizontal_anchor_point']='1'
        prop['name']=zDat
        prop['offset']='0,0'
        prop['offset_map_unit_scale']='0,0,0,0,0,0'
        prop['offset_unit']= sUnit
        prop['outline_color']='255,255,255,255'
        prop['outline_width']='0'
        prop['outline_width_map_unit_scale']='0,0,0,0,0,0'
        prop['outline_width_unit']='MM'
        prop['scale_method']='diameter'
        prop['size']=str(fncfield(rsParam,"wsizemm"))
        prop['size_map_unit_scale']='0,0,0,0,0,0'
        prop['size_unit']=sUnit
        prop['vertical_anchor_point']='1'    
        for p in prop:
            ET.SubElement(eLayer, "prop",k=p,v=prop[p])    
        """
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        subLZF ("EinLinienPunktMarker (AttID=" + AttID + ")")
        return False
    
    return eLayer  
"""    

def EineSchraffurLinie (eSym,rsAtt,Num, Group):
    if fncfield(rsAtt,"fsalign") == 1:
        # Individualwinkel: Nur der Winkel aus den Geodaten gilt
        sWin= '"alphafs"' if Num ==1  else '"alphafs"+90'
    else:
        # nur der Winkel aus dem Attribut gilt
        sWin= str(fncfield(rsAtt,"fsalpha")) if Num ==1  else str(fncfield(rsAtt,"fsalpha")+90)
    qmap={'pass':'0','class':'LinePatternFill','locked':'0'}
    l1=ET.SubElement(eSym,"layer",qmap)                           
    prop={}
    prop['lineangle_expression']=sWin
    prop['color']='0,0,255,255'
    prop['distance']=str(fncfield(rsAtt,"fsabstand" + str(Num)))
    prop['distance_map_unit_scale']='0,0,0,0,0,0'
    prop['distance_unit']='MapUnit'
    prop['line_width']='0.26'
    prop['line_width_map_unit_scale']='0,0,0,0,0,0'
    prop['line_width_unit']='MM'
    prop['offset']='0'
    prop['offset_map_unit_scale']='0,0,0,0,0,0'
    prop['offset_unit']='MM'
    prop['outline_width_map_unit_scale']='0,0,0,0,0,0'
    prop['outline_width_unit']='MM'
    for p in prop:
        ET.SubElement(l1, "prop",k=p,v=prop[p]) 
    return ET.SubElement(l1, "symbol", {'alpha':'1','clip_to_extent':'1','type':'line'})                                                            

            

def EineStreckeXMLAttributieren (eSymbols, symNum,db,clsdb,qTyp, LinArt, AktAttID, Group, AttNum,eSym = None,fDist = None,fWin = None):
    # printlog ("Strecke  " + AktAttID + ": " + clsdb.sqlAttParam4IDandArt(1, AktAttID, Group))
    rsParam=clsdb.OpenRecordset(db,clsdb.sqlAttParam4IDandArt(1, AktAttID, Group))
    """
                  #                      0                     1           2        3      4       5      6       7              8           9            10          11
            sSQL=("SELECT la_idfa AS st_attid, attrname AS st_attrname, la_linenr, used, color, sizemm, basemm, basecolor, linesigattr, linesigbegin,linesigofs, linesigofsline, "
                   #           12            13            14            15          16           17          18       19          20          21          22           23
                   "       lineoffset, sigbeginattr, sigmiddleattr, sigendattr, transparent, denyatpercent, penid, basepenid, sigbeginpos, sigendpos, sigmiddlepos, geocolor "
                   "            24
                   "         scrresize
    """
    #printlog ("Strecke:" + AktAttID)
    if LinArt=="fill":
        bSchraff=True
        LinArt="line"
        #lineMeta = QgsSymbolLayerV2Registry.instance().symbolLayerMetadata("LinePatternFill")
    else:    
        bSchraff=False
        #lineMeta = QgsSymbolLayerV2Registry.instance().symbolLayerMetadata("SimpleLine")
        
    #if symbol == None:    
    #    symbol = QgsSymbolV2.defaultSymbol(qTyp)
    #    symbol.deleteSymbolLayer(0)   
    
    
    if rsParam.size() == 0:
        if LinArt == "outline":
            # Keine Randlinie 
            debuglog( "\nEineStreckeAttributieren: " + str(AttNum) + ";" + LinArt + ";" + AktAttID + ";"+ str(Group) + " kein Attribut")
        else:
            errlog( "\nEineStreckeAttributieren: " + str(AttNum) + ";" + LinArt + ";" + AktAttID + ";"+ str(Group) + " kein Attribut")
    
    # ===============================================================================================================
    # 1. <symbol
    if eSym == None:
        qmap={}   
        qmap['alpha']='1'
        qmap['clip_to_extent']='1'
        qmap['type']='line'
        qmap['name']=str(symNum)
        eSym=ET.SubElement(eSymbols,"symbol",qmap)

    
    while rsParam.next(): 
    # ===============================================================================================================
    # 3. layer Haupt und Teillinien   
        basemm=fncfield(rsParam,"basemm")
        penType=fncfield(rsParam,"pentype")
        if penType < 5:
            penArt=fncStdLineStyle(penType)
        else:
            penArt=fncUserLineStyle(rsParam)
            
        unitArt='MapUnit' if fncfield(rsParam,"scrresize") == "J" else "MM"
        
        if basemm > 0:
            #Eine eventuelle Randlinie - Randlinie ist immer Volline
            qmap={'pass':'0','class':'SimpleLine','locked':'0'}
            eLayer=ET.SubElement(eSym,"layer",qmap)
            prop={}
            prop['capstyle']='square'
            prop['customdash']='5;2'
            prop['customdash_map_unit_scale']='0,0'
            prop['customdash_unit']='MM'
            prop['draw_inside_polygon']='0'
            prop['joinstyle']='bevel'
            prop[LinArt+'_color']=fncLongTosRGB(fncfield(rsParam,"basecolor"),True if fncfield(rsParam,"transparent") == "J" else False)
            prop[LinArt+'_style']='solid'
            prop[LinArt+'_width']=str(fncfield(rsParam,"sizemm") + basemm * 2) 
            prop[LinArt+'_width_unit']=unitArt
            prop['offset']='0'
            prop['offset_map_unit_scale']='0,0'
            prop['offset_unit']='MapUnit'
            prop['use_custom_dash']='0'
            prop['width_map_unit_scale']='0,0'
            for p in prop:
                ET.SubElement(eLayer, "prop",k=p,v=prop[p])
            #lineLayer = lineMeta.createSymbolLayer(qmap)
            #symbol.appendSymbolLayer(lineLayer)
        
        # jetzt die normale Linie
        qmap={'pass':'1' if basemm > 0 else '0','class':'SimpleLine','locked':'0'}
        eLayer=ET.SubElement(eSym,"layer",qmap)
        prop={}
        if penType < 5:
            prop["line_style"]=penArt
            prop["use_custom_dash"]=str(0)
        else:
            prop["customdash"]=penArt
            prop["use_custom_dash"]=str(1)

        prop['capstyle']='square'

        prop['customdash_map_unit_scale']='0,0,0,0,0,0'
        prop['customdash_unit']='MM'
        prop['draw_inside_polygon']='0'
        prop['joinstyle']='bevel'
        prop[LinArt+"_color"]=fncLongTosRGB(fncfield(rsParam,"color"),True if fncfield(rsParam,"transparent") == "J" else False)

        prop[LinArt+'_width']=str(fncfield(rsParam,"sizemm"))
        prop[LinArt+'_width_unit']=unitArt
        prop["offset"]=str(fncfield(rsParam,"lineoffset") * (-1 if LinArt=="outline" else 1))
        prop['offset_map_unit_scale']='0,0,0,0,0,0'
        prop['offset_unit']='MapUnit'

        prop['width_map_unit_scale']='0,0,0,0,0,0'
         
        
        if bSchraff:
            prop["distance"]=str(fDist)
            prop["distance_unit"]="MapUnit"      
            prop["outline_style"]='no' # hier kein Rand# 
            prop["angle"]=str(fWin)

        #lineLayer = lineMeta.createSymbolLayer(qmap)
        for p in prop:
            ET.SubElement(eLayer, "prop",k=p,v=prop[p])
            
        # ===============================================================================================================
        # Liniensymbole am Ende schreiben
        # Eventuelle Liniensigaturen
        sUnit='MapUnit' if fncfield(rsParam,"scrresize") == "J" else "MM"
        if fncfield(rsParam,"sigbeginattr") != "{00000000-0000-0000-0000-000000000000}":    
            EinLinienPunktMarker (eSym,db,clsdb,fncfield(rsParam,"sigbeginattr") ,'firstvertex',sUnit, Group)
        if fncfield(rsParam,"sigendattr") != "{00000000-0000-0000-0000-000000000000}":    
            EinLinienPunktMarker (eSym,db,clsdb,fncfield(rsParam,"sigendattr") ,'lastvertex',sUnit, Group)
        if fncfield(rsParam,"sigmiddleattr") != "{00000000-0000-0000-0000-000000000000}":    
            EinLinienPunktMarker (eSym,db,clsdb,fncfield(rsParam,"sigmiddleattr") ,'centralpoint',sUnit, Group)
        if fncfield(rsParam,"linesigattr") != "{00000000-0000-0000-0000-000000000000}":    
            EinLinienPunktMarker (eSym,db,clsdb,fncfield(rsParam,"linesigattr") ,'egal',sUnit, Group,fncfield(rsParam,"linesigofs"),fncfield(rsParam,"linesigbegin"),fncfield(rsParam,"linesigofsline"))
               
    return eSymbols
        
def EineFlaecheXMLFuellstil (eSymbols, symNum,qTyp,rsParam) :
    """
0: Farbfüllung
1: Keine Füllung bzw. benutzerdefiniert
2: Horizontal
3: Vertikal
4: Diagonal1
5: Diagonal2
6: Kreuz
7: Diagonal Kreuz
    """
    def EineLineMitWinkel(Winkel,AktColor,eSym):
            #printlog (str(Winkel)+ "|" + AktColor)
            eLayer=ET.SubElement(eSym,"layer",{'pass':'0','class':'LinePatternFill','locked':'0'})
            prop={}
            prop['angle']=str(Winkel)
            prop['color']=AktColor
            prop['distance']='2.5'
            prop['distance_map_unit_scale']='0,0,0,0,0,0'
            prop['distance_unit']='MM'
            prop['line_width']='0.1'
            prop['line_width_map_unit_scale']='0,0,0,0,0,0'
            prop['line_width_unit']='MM'
            prop['offset']='0'
            prop['offset_map_unit_scale']='0,0,0,0,0,0'
            prop['offset_unit']='MM'
            prop['outline_width_map_unit_scale']='0,0,0,0,0,0'
            prop['outline_width_unit']='MM'
            for p in prop:
                ET.SubElement(eLayer, "prop",k=p,v=prop[p])
            # Untersymbol
            eUSym=ET.SubElement(eLayer,"symbol",{'alpha':'1','clip_to_extent':'1','type':'line'})
            uLayer=ET.SubElement(eUSym,"layer",{'pass':'0','class':'SimpleLine','locked':'0'})
            prop={}
            prop['capstyle']='square'
            prop['customdash']='5;2'
            prop['customdash_map_unit_scale']='0,0,0,0,0,0'
            prop['customdash_unit']='MM'
            prop['draw_inside_polygon']='0'
            prop['joinstyle']='bevel'
            prop['line_color']=AktColor
            prop['line_style']='solid'
            prop['line_width']='0.1'
            prop['line_width_unit']='MM'
            prop['offset']='0'
            prop['offset_map_unit_scale']='0,0,0,0,0,0'
            prop['offset_unit']='MM'
            prop['use_custom_dash']='0'
            prop['width_map_unit_scale']='0,0,0,0,0,0'
            for p in prop:
                ET.SubElement(uLayer, "prop",k=p,v=prop[p])
            return eLayer
            
            
    cgArt=fncfield(rsParam,"brushstyle")
    #printlog ("Hier"+str(cgArt))
    qmap={}   
    qmap['alpha']='1'
    qmap['clip_to_extent']='1'
    qmap['type']='fill'
    qmap['name']=str(symNum)
    eSym=ET.SubElement(eSymbols,"symbol",qmap)
    #AktSymbol = QgsSymbolV2.defaultSymbol(qTyp)
    #AktSymbol.deleteSymbolLayer(0)   
    if cgArt==0: #Farbfüllung
        #fillMeta = QgsSymbolLayerV2Registry.instance().symbolLayerMetadata("SimpleFill")
        eLayer=ET.SubElement(eSym,"layer",{'pass':'0','class':'SimpleFill','locked':'0'})        
        prop={}
        prop['border_width_map_unit_scale']='0,0,0,0,0,0'
        prop['color']=fncLongTosRGB(fncfield(rsParam,"brushcolor"),True if fncfield(rsParam,"transparent") == "J" else False)
        prop['joinstyle']='bevel'
        prop['offset']='0,0'
        prop['offset_map_unit_scale']='0,0,0,0,0,0'
        prop['offset_unit']='MM'
        prop['outline_color']='0,0,0,255'
        prop['outline_style']='no'
        prop['outline_width']='0.26'
        prop['outline_width_unit']='MM'
        prop['style']='solid'
        for p in prop:
            ET.SubElement(eLayer, "prop",k=p,v=prop[p])
    if cgArt==1: # keine Füllung
        dummy = ""
    if cgArt==2: #Horizontal
        eLayer=EineLineMitWinkel(0, fncLongTosRGB(fncfield(rsParam,"brushcolor"),True if fncfield(rsParam,"transparent") == "J" else False),eSym)       
    if cgArt==3: # Vertikal
        eLayer=EineLineMitWinkel(90,fncLongTosRGB(fncfield(rsParam,"brushcolor"),True if fncfield(rsParam,"transparent") == "J" else False), eSym)           
    if cgArt==4: #Diagonal1
        eLayer=EineLineMitWinkel(135,fncLongTosRGB(fncfield(rsParam,"brushcolor"),True if fncfield(rsParam,"transparent") == "J" else False), eSym)        
    if cgArt==5: #Diagonal2
        eLayer=EineLineMitWinkel(45,fncLongTosRGB(fncfield(rsParam,"brushcolor"),True if fncfield(rsParam,"transparent") == "J" else False), eSym)          
    if cgArt==6: #Kreuz
        eLayer=EineLineMitWinkel(0,fncLongTosRGB(fncfield(rsParam,"brushcolor"),True if fncfield(rsParam,"transparent") == "J" else False), eSym)          
        eLayer=EineLineMitWinkel(90,fncLongTosRGB(fncfield(rsParam,"brushcolor"),True if fncfield(rsParam,"transparent") == "J" else False), eSym)          
    if cgArt==7: #diagonal Kreuz
        eLayer=EineLineMitWinkel(45,fncLongTosRGB(fncfield(rsParam,"brushcolor"),True if fncfield(rsParam,"transparent") == "J" else False), eSym)          
        eLayer=EineLineMitWinkel(135,fncLongTosRGB(fncfield(rsParam,"brushcolor"),True if fncfield(rsParam,"transparent") == "J" else False), eSym)            
        
    return  eSym

def EinenPunktXMLAttributieren (eSymbols, symNum,  rsParam, clsdb ) :
    # ===================================       SVG erzeugen            ===================================================
    qPfad,qDat,zDat = Pfade4Signatur(clsdb,fncfield(rsParam,"sigpath"),fncfield(rsParam,"signame"))
    subMkPfad (qPfad, True)
    Sig2SVG (qDat,zDat)
    
    # ===================================   Darstellung definieren    ===================================================        
    unitArt='MapUnit' if fncfield(rsParam,"scrresize") == "J" else "MM"
    
    # ===============================================================================================================
    # 1. <symbol
    qmap={}   
    qmap['alpha']='1'
    qmap['clip_to_extent']='1'
    qmap['type']='marker'
    qmap['name']=str(symNum)
    eSym=ET.SubElement(eSymbols,"symbol",qmap)
    
    # ===============================================================================================================
    # 2. <layer
    qmap={'pass':'0','class':'SvgMarker','locked':'0'}
    eLayer=ET.SubElement(eSym,"layer",qmap)
    
    prop={}
    prop['angle']='0'
    prop['angle_dd_active']='1'
    prop['angle_dd_expression']='abs(360-alpha )' # für Essen
    prop['angle_expression']='abs(360-alpha )'    # für Wien
    prop['angle_dd_field']=''
    prop['angle_dd_useexpr']='1'
    prop['color']='0,0,0,255'
    prop['horizontal_anchor_point']='1'
    prop['name']=zDat
    prop['offset']='0,0'
    prop['offset_map_unit_scale']='0,0,0,0,0,0'
    prop['offset_unit']=unitArt
    prop['outline_color']='0,0,0,255'
    prop['outline_width']='0.2'
    prop['outline_width_map_unit_scale']='0,0,0,0,0,0'
    prop['outline_width_unit']='MM'
    prop['scale_method']='diameter'
    prop['size']=str(fncfield(rsParam,"wsizemm"))
    prop['size_map_unit_scale']='0,0,0,0,0,0'
    prop['size_unit']=unitArt
    prop['vertical_anchor_point']='1'
    for p in prop:
        ET.SubElement(eLayer, "prop",k=p,v=prop[p])
     
    qmap={}
    qmap['size']=str(fncfield(rsParam,"wsizemm"))
    qmap['size_unit']=unitArt
    qmap['name']=zDat

    ET.SubElement(eSym,"layer",qmap)
    
    return eSymbols    

def EinenTextXMLAttributieren (eSettings,rsParam):
    # ===============================================================================================================
    # 1. <text-style
    qmap={}   
    qmap['fontItalic']= "1" if fncfield(rsParam,"italic") == "J" else '0'
    qmap['fontFamily']=fncfield(rsParam,"fontname")
    qmap['fontLetterSpacing']='0'
    qmap['fontUnderline']='0'
    qmap['fontSizeMapUnitMaxScale']='0'
    qmap['fontWeight']='50'
    qmap['fontStrikeout']='0'
    qmap['textTransp']='0'
    qmap['previewBkgrdColor']='#ffffff'
    qmap['fontCapitals']='0'
    qmap["textColor"]= fncLongTosRGB(fncfield(rsParam,"color"))
    qmap['fontSizeMapUnitMinScale']='0'
    qmap['fontSizeInMapUnits']='1' if fncfield(rsParam,"scrresize") == "J" else '0'
    qmap['isExpression']='1'
    qmap['blendMode']='0'
    # Ein "MM" gibt es bei Beschriftung nicht, deshalb in Punkte * 2
    qmap['fontSize']=str(fncfield(rsParam,"sizemm") * ( 1 if fncfield(rsParam,"scrresize") == "J" else 2 ))
    qmap['fieldName']="replace(replace(\"pstext\",'\\\\u','')  ,'\\\\c','')"   
    s='Normal'
    if fncfield(rsParam,"bold")=="J":
        s="Bold"
    if fncfield(rsParam,"italic")=="J":
        s="Italic"  
    if fncfield(rsParam,"bold")=="J" and fncfield(rsParam,"italic")=="J":
        s="Bold Italic"     
    qmap['namedStyle']=s
    qmap['fontWordSpacing']='0'    
    ET.SubElement(eSettings,"text-style",qmap)


    # ===============================================================================================================
    # 2. <text-format
    qmap={} 
    qmap['placeDirectionSymbol']='0'
    qmap['multilineAlign']='0'
    qmap['rightDirectionSymbol']='>'
    qmap['multilineHeight']='1'
    qmap['plussign']='0'
    qmap['addDirectionSymbol']='0'
    qmap['leftDirectionSymbol']='&lt;'
    qmap['formatNumbers']='0'
    qmap['decimals']='0'
    qmap['wrapChar']='\\n'
    qmap['reverseDirectionSymbol']='0'
    ET.SubElement(eSettings,"text-format",qmap)
    
    # ===============================================================================================================
    # 3. <placement
    qmap={'repeatDistanceUnit':'1','placement':'0','maxCurvedCharAngleIn':'20','repeatDistance':'0','distMapUnitMaxScale':'0','labelOffsetMapUnitMaxScale':'0','distInMapUnits':'0',
          'labelOffsetInMapUnits':'1','xOffset':'0','predefinedPositionOrder':'TR,TL,BR,BL,R,L,TSR,BSR','preserveRotation':'1','centroidWhole':'0','priority':'0',
          'repeatDistanceMapUnitMaxScale':'0','yOffset':'0','offsetType':'0','placementFlags':'0','repeatDistanceMapUnitMinScale':'0','centroidInside':'0','dist':'0','angleOffset':'0',
          'maxCurvedCharAngleOut':'-20','fitInPolygonOnly':'0','quadOffset':'4','distMapUnitMinScale':'0','labelOffsetMapUnitMinScale':'0'}
    ET.SubElement(eSettings,"placement",qmap)
    
    # ===============================================================================================================
    # 4. <rendering
    qmap={'fontMinPixelSize':'3','scaleMax':'0','fontMaxPixelSize':'10000','scaleMin':'0','upsidedownLabels':'2','limitNumLabels':'0','obstacle':'0','obstacleFactor':'1',
          'scaleVisibility':'0','fontLimitPixelSize':'0','mergeLines':'0','obstacleType':'0','labelPerPart':'0','zIndex':'0','maxNumLabels':'2000','displayAll':'1','minFeatureSize':'0'}
    ET.SubElement(eSettings,"rendering",qmap)
    
    # ===============================================================================================================
    # 5. <data-defined>
    eD=ET.SubElement(eSettings,"data-defined")
    
    qmap={} #Rotation aus Geometriedaten
    qmap['expr']=''
    qmap['field']='alpha'
    qmap['active']='true'
    qmap['useExpr']='false'
    ET.SubElement(eD,"Rotation",qmap)
        
    qmap={} #Textaufhängung aus Attributtabelle
    qmap['expr']= str(fnctxtCtoQ(fncfield(rsParam,"textalign")))
    qmap['field']=''
    qmap['active']='true'
    qmap['useExpr']='true'
    ET.SubElement(eD,"OffsetQuad",qmap)

    qmap={} #Unterstreichung aus Geometriedaten
    qmap['expr']= ("case %swhen strpos(\"pstext\",'\\\\\\\\u') then True%selse False %send") % ( chr(13)+chr(10),chr(13)+chr(10),chr(13)+chr(10))
    #            "case &amp;#xd;&amp;#xa;when strpos(&amp;quot;pstext&amp;quot;,'/\u') then True&amp;#xd;&amp;#xa;else False &amp;#xd;&amp;#xa;end"
    qmap['field']=''
    qmap['active']='true'
    qmap['useExpr']='true'
    ET.SubElement(eD,"Underline",qmap)    

    qmap={} #Zentrierung aus Geometriedaten
    qmap['expr']= ("case %s when strpos(\"pstext\",'\\\\\\\\c') then 'Center' %s else 'Left' %s end") % ( chr(13)+chr(10),chr(13)+chr(10),chr(13)+chr(10))
    qmap['field']=''
    qmap['active']='true'
    qmap['useExpr']='true'
    ET.SubElement(eD,"MultiLineAlignment",qmap)  

    # ===============================================================================================================
    # 5. <background>
    # V1 Weder Rand noch Füllung: Hintergrund deaktivieren -> shapeDraw=0
    # V2 Füllung und kein Rand: Randbreite auf 0 ->
    # V3 keine Füllung aber Rand: keine Möglichkeit gefunden -> Füllung auf weiß setzen
    bAktiv=(fncfield(rsParam,"freestyle") == "J" or fncfield(rsParam,"frametext") == "J")
    if bAktiv and fncfield(rsParam,"freestyle") == "N":
        bkColor='0'
    else:    
        bkColor = fncLongTosRGB(fncfield(rsParam,"bkcolor"))
    if bAktiv and fncfield(rsParam,"frametext") == "N":
        wRand='0'
    else:    
        wRand=str(fncfield(rsParam,"framewidthmm"))      
        
    qmap={}
    qmap['shapeSizeUnits']='1'
    qmap['shapeType']='0'
    qmap['shapeOffsetMapUnitMinScale']='0'
    qmap['shapeSizeMapUnitMinScale']='0'
    qmap['shapeSVGFile']=''
    qmap['shapeOffsetX']='0'
    qmap['shapeOffsetY']='0'
    qmap['shapeBlendMode']='0'
    qmap['shapeBorderWidthMapUnitMaxScale']='0'
    qmap['shapeFillColor']=bkColor
    qmap['shapeTransparency']='0'
    qmap['shapeSizeType']='0'
    qmap['shapeJoinStyle']='64'
    qmap['shapeDraw']='1' if bAktiv else '0'
    qmap['shapeSizeMapUnitMaxScale']='0'
    qmap['shapeBorderWidthUnits']='2' # Karteneinheiten
    qmap['shapeSizeX']='0'
    qmap['shapeSizeY']='0'
    qmap['shapeRadiiX']='0'
    qmap['shapeOffsetMapUnitMaxScale']='0'
    qmap['shapeOffsetUnits']='1'
    qmap['shapeRadiiY']='0'
    qmap['shapeRotation']='0'
    qmap['shapeBorderWidth']=wRand
    qmap['shapeRadiiMapUnitMinScale']='0'
    qmap['shapeRadiiMapUnitMaxScale']='0'
    qmap['shapeBorderColor']=fncLongTosRGB(fncfield(rsParam,"framecolor"))
    qmap['shapeRotationType']='0'
    qmap['shapeRadiiUnits']='1'
    qmap['shapeBorderWidthMapUnitMinScale']='0'
    ET.SubElement(eSettings,"background",qmap)

    return eSettings    

class clsRenderingByQML():      
    def Render(self, cgUser, qLayer, cgEbenenTyp, LayerID, bRolle, Group): 
        # bRolle = False bei QGIS < Pisa und Text
        symNum=0
        clsdb = pgDataBase()
        db=clsdb.CurrentDB()
        eRoot = ET.Element("qgis")
        if bRolle and (cgEbenenTyp == 3):
            eLabeling = ET.SubElement(eRoot,"labeling",{'type':'rule-based'}) 
            eRenderer = ET.SubElement(eRoot,"renderer-v2",{'forceraster':'0','symbollevels':'0','type':'singleSymbol','enableorderby':'0'})
        else:
            eRenderer = ET.SubElement(eRoot,"renderer-v2",{'symbollevels':'0', 'type':'RuleRenderer'})
        #if clsdb.NeedLine4TextLayer(db,LayerID, cgUser):
        #    printlog ("Zuordnungspfeil 4" + LayerID)
        
        
        # ===========================================================================================================================
        # Variante 1: Rollenbasierte Darstellung einer Ebene
        if bRolle : # and (cgEbenenTyp == 0 or cgEbenenTyp == 1 or cgEbenenTyp == 3 or cgEbenenTyp == 5 or cgEbenenTyp == 6): 
            rsAttDefs=clsdb.OpenRecordset(db,clsdb.sqlAllAttDef4Layer( cgEbenenTyp, LayerID))
            if cgEbenenTyp == 3:
                eRules = ET.SubElement(eLabeling,"rules")
            else:
                eRules = ET.SubElement(eRenderer,"rules")

            eSymbols= ET.SubElement(eRenderer,"symbols")
            
            # =========  Schleife über alle (Individual-)Attributdefinitionen einer Ebene ================
            while (rsAttDefs.next()):   
                if rsAttDefs.value(0) == "{00000000-0000-0000-0000-000000000000}":
                    AktDefID = clsdb.AttDefID4Layer(db, LayerID, cgUser)
                    AktDefName=clsdb.AttDefName4ID(db, AktDefID)
                else:
                    AktDefID = rsAttDefs.value(0)
                    AktDefName="IA:"+rsAttDefs.value(1)

                rsAtt=clsdb.OpenRecordset(db,clsdb.sqlAtt4Massstab(cgEbenenTyp, AktDefID, Group))
                #printlog ('Hier:' + str(cgEbenenTyp) + "|" + AktDefID + "|" +clsdb.sqlAtt4Massstab(cgEbenenTyp, AktDefID, Group))
                if rsAtt.size() == 0 :
                    #printlog (rsAttDefs.value(0)+"|"+rsAttDefs.value(1)+"|"+LayerID)
                    addHinweis( LayerID + "/" + rsAttDefs.value(1)+ "/"+AktDefName+"(" + str(cgEbenenTyp) + "): Keine Attributdefinition gefunden")
                    break
                
                # Oberrolle Schreiben
                qmap={}
                qmap["filter"]= "defid = '" + rsAttDefs.value(0) +"'"
                if cgEbenenTyp == 3:
                    qmap["description"] = AktDefName
                else:
                    qmap["label"] = AktDefName
                eORule = ET.SubElement(eRules,"rule",qmap)

                
                # =========  Schleife über alle (5) möglichen Maßstabsattribute einer Definition ================
                while (rsAtt.next()): 
                    symNum=symNum + 1
                    mMin=fncfield(rsAtt,"MMin")
                    qmap={}
                    qmap["scalemindenom"]= str(1 if mMin==0 else mMin)
                    qmap["scalemaxdenom"] = str(fncfield(rsAtt,"MMax"))
                    if cgEbenenTyp == 3:
                        qmap["description"] = str(fncfield(rsAtt,"AttNum")) + ":" + fncfield(rsAtt,"ATTname")
                        #if fncfield(rsAtt,"lineattr") != "{00000000-0000-0000-0000-000000000000}":
                        #    printlog (fncfield(rsAtt,"lineattr"))
                    else:
                        qmap["label"] = str(fncfield(rsAtt,"AttNum")) + ":" + fncfield(rsAtt,"ATTname")

                    qmap["symbol"] = str(symNum)
                    AktRule=ET.SubElement(eORule,"rule",qmap)
                    
                    if cgEbenenTyp == 0:
                        qTyp=qLayer.geometryType()
                        #                                      (eSymbols, symNum,  rsParam, sigPfad, svgPfad )
                        EinenPunktXMLAttributieren (eSymbols, symNum,  rsAtt,clsdb)
    

                    if cgEbenenTyp == 1: # Strecke 
                        qTyp = qLayer.geometryType()
                        EineStreckeXMLAttributieren (eSymbols, symNum,  db,clsdb,qTyp, "line", fncfield(rsAtt,"ATTid"),Group,fncfield(rsAtt,"AttNum") )                     
                        #rule.setSymbol(symbol)
                        #new_rule.appendChild(rule)  


                    if cgEbenenTyp == 3: # Text
                        # Einfaches Symbol (um Textaufhängung zu sehen -> Größe setzen)
                        s1  = ET.SubElement(eSymbols, "symbol", {'alpha':'1','clip_to_extent':'1','type':'marker','name':'0'})
                        l1 =  ET.SubElement(s1,       "layer" , {'locked': '0', 'class': 'SimpleMarker', 'pass': '0'})
                        props={'size': '0.0', 'size_unit': 'MM'}
                        for p in props:
                            ET.SubElement(l1, "prop",k=p,v=props[p])
                        
                        # Jetzt der Text
                        eSettings=ET.SubElement(AktRule,"settings")
                        eSettings = EinenTextXMLAttributieren (eSettings,rsAtt )                      
 
                    if cgEbenenTyp == 31: # Referenzlinie
                        qTyp = qLayer.geometryType()
                        EineStreckeXMLAttributieren (eSymbols, symNum, db,clsdb,qTyp, "line", fncfield(rsAtt,"lineattr"),Group,fncfield(rsAtt,"AttNum") )                     
 
                    if cgEbenenTyp == 5: # PolyLinie
                        qTyp = qLayer.geometryType()
                        EineStreckeXMLAttributieren (eSymbols, symNum, db,clsdb,qTyp, "line", fncfield(rsAtt,"lineattr"),Group,fncfield(rsAtt,"AttNum") )                     
                        #rule.setSymbol(symbol)
                        #new_rule.appendChild(rule)   
                    
                    if cgEbenenTyp == 2 or cgEbenenTyp == 6: # Kreis und Fläche
                        qTyp = qLayer.geometryType()
                        # 1. Füllung
                        # printlog ( fncfield(rsAtt,"ATTname")+"|"+str(fncfield(rsAtt,"AttNum")))
                        eSym=EineFlaecheXMLFuellstil (eSymbols, symNum,qTyp,rsAtt)
                        
                         
                        # 3. Fülleffekte
                        # 3.1. Schraffurlinie
                        # Im Gegensatz zum Drehwinkel an Punkten, schein hier der Winkel in die gleiche Richtung
                        # wie im QGIS zu laufen   
                        # eine 2. Linie ist zur ersten 90 ° versetzt und wird nur gezeichnet, wenn eine erste Linie definiert
                        if fncfield(rsAtt,"fslineattr1") != "{00000000-0000-0000-0000-000000000000}":
                            s1=EineSchraffurLinie (eSym,rsAtt,1, Group)
                            EineStreckeXMLAttributieren (None, 0,  db,clsdb,qTyp, "line",fncfield(rsAtt,"fslineattr1"),Group,0,s1 )
                            if fncfield(rsAtt,"fslineattr2") != "{00000000-0000-0000-0000-000000000000}":
                                s1=EineSchraffurLinie (eSym,rsAtt,2, Group) 
                                EineStreckeXMLAttributieren (None, 0,  db,clsdb,qTyp, "line",fncfield(rsAtt,"fslineattr2"),Group,0,s1 )

                        # 3.2. Signaturfüllung
                        #      funktioniert nicht 100%, da der Abstand zwischen den einzelnen Signaturen (woffsetmm, hoffsetmm) nicht einstellbar ist
                        if fncfield(rsAtt,"pointattr1") != "{00000000-0000-0000-0000-000000000000}":
                            #  EinSchraffurPunktFuellung (eSym,db,clsdb,   AttID, sWin,                      sigPfad,                                svgPfad,                  Num, Group)
                            sWin=abs(360-fncfield(rsAtt,"alpha1"))
                            l1=EinSchraffurPunktFuellung (eSym,db,clsdb,fncfield(rsAtt,"pointattr1"),sWin,clsdb.GetCGSignaturPfad(),clsdb.GetQSVGSignaturPfad(),1, Group)
                            if fncfield(rsAtt,"pointattr2") != "{00000000-0000-0000-0000-000000000000}":
                                sWin=abs(360-fncfield(rsAtt,"alpha2"))
                                l1=EinSchraffurPunktFuellung (eSym,db,clsdb,fncfield(rsAtt,"pointattr2"),sWin,GetCGSignaturPfad(),clsdb.GetQSVGSignaturPfad(),1, Group)
                        
                        # 4. Randlinie
                        EineStreckeXMLAttributieren (None, symNum, db,clsdb,qTyp, "outline", fncfield(rsAtt,"lineattr"),Group,fncfield(rsAtt,"AttNum"),eSym) 

                        
                        #rule.setSymbol(symbol)
                        #new_rule.appendChild(rule) 
                  
            # delete the default rule
            #root_rule.removeChildAt(0)
            # apply the renderer to the layer
            #qLayer.setRendererV2(renderer)
        
        else:
            # ===========================================================================================================================
            # Variante 2: Notvariante Beschriftung ohne Rolle
            #if not bRolle and (cgEbenenTyp ==3):  
            # Nur EbenenAttDef (und auch nur erstes Maßstabsattribut)
            AktDefID = clsdb.AttDefID4Layer(db, LayerID, cgUser)
            AktDefName=clsdb.AttDefName4ID(db, AktDefID)
            EinfacheBeschriftungZeichnen(clsdb, db, qLayer,AktDefID, Group)
            #errlog(Fehler)

        tree = ET.ElementTree(eRoot)
        if fncDebugMode():
            tempName="d:/tar/mytest1.qml"
        else:
            tempName=tempfile.gettempdir() + "/{D5E6A1F8-392F-4241-A0BD-5CED09CFABC7}.qml"
        f = open(tempName, "w")
        
        sXML=dom.parseString(
                    ET.tostring(
                      tree.getroot(),
                      'utf-8')).toprettyxml(indent="    ")
        if myqtVersion == 4:
            f.write(sXML.encode('utf8'))
        else:
            f.write(sXML)
        f.close()
        
        qLayer.loadNamedStyle(tempName)
        if not fncDebugMode():
            os.remove(tempName)

    
if __name__ == "__main__":
    from qgis.utils import *
    app = QApplication(sys.argv)
    print (myqtVersion)
