# -*- coding: utf-8 -*-
"""
/***************************************************************************
 clsRenderingByQT
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

from qgis.core import * 
from clsDatenbank import *
from fnc4all import *
from clsSig2SVG import *
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
    flist.append ((Farbe / 256) & 255)
    flist.append (Farbe / 65536)
    return flist

def fncLongTosRGB (Farbe,Transparent=False):
    s=str(Farbe & 255)
    s=s+","+str((Farbe / 256) & 255)
    s=s+","+str (Farbe / 65536) 
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

def EineStreckeAttributieren (db,clsdb,qTyp, LinArt, AktAttID, Group, AttNum,symbol = None,fDist = None,fWin = None):
    rsParam=clsdb.OpenRecordset(db,clsdb.sqlAttParam4IDandArt(1, AktAttID, Group))
    """
                  #                      0                     1           2        3      4       5      6       7              8           9            10          11
            sSQL=("SELECT la_idfa AS st_attid, attrname AS st_attrname, la_linenr, used, color, sizemm, basemm, basecolor, linesigattr, linesigbegin,linesigofs, linesigofsline, "
                   #           12            13            14            15          16           17          18       19          20          21          22           23
                   "       lineoffset, sigbeginattr, sigmiddleattr, sigendattr, transparent, denyatpercent, penid, basepenid, sigbeginpos, sigendpos, sigmiddlepos, geocolor "
                   "            24
                   "         scrresize
    """
    if LinArt=="fill":
        bSchraff=True
        LinArt="line"
        lineMeta = QgsSymbolLayerV2Registry.instance().symbolLayerMetadata("LinePatternFill")
    else:    
        bSchraff=False
        lineMeta = QgsSymbolLayerV2Registry.instance().symbolLayerMetadata("SimpleLine")
        
    if symbol == None:    
        symbol = QgsSymbolV2.defaultSymbol(qTyp)
        symbol.deleteSymbolLayer(0)   
    
    
    if rsParam.size() == 0:
        if LinArt == "outline":
            # Keine Randlinie 
            debuglog( "\nEineStreckeAttributieren: " + str(AttNum) + ";" + LinArt + ";" + AktAttID + ";"+ str(Group) + " kein Attribut")
        else:
            errlog( "\nEineStreckeAttributieren: " + str(AttNum) + ";" + LinArt + ";" + AktAttID + ";"+ str(Group) + " kein Attribut")
    
    while rsParam.next(): 
        basemm=fncfield(rsParam,"basemm")
        penType=fncfield(rsParam,"pentype")
        if penType < 5:
            penArt=fncStdLineStyle(penType)
        else:
            penArt=fncUserLineStyle(rsParam)
            
        #Eine eventuelle Randlinie - Randlinie ist immer Volline
        unitArt='MapUnit' if fncfield(rsParam,"scrresize") == "J" else "MM"
        if basemm > 0:
            qmap={}    
            qmap[LinArt+"_color"]=fncLongTosRGB(fncfield(rsParam,"basecolor"),True if fncfield(rsParam,"transparent") == "J" else False)
            qmap[LinArt+"_width"]=str(fncfield(rsParam,"sizemm") + basemm * 2) 
            qmap[LinArt+"_width_unit"]=unitArt
            qmap["offset"]='0' 
            qmap["offset_unit"]='MapUnit'            
            qmap["line_style"]='solid'

            lineLayer = lineMeta.createSymbolLayer(qmap)
            symbol.appendSymbolLayer(lineLayer)
        # jetzt die normale Linie
        qmap={}
        if penType < 5:
            qmap["line_style"]=penArt
            qmap["use_custom_dash"]=str(0)
        else:
            qmap["customdash"]=penArt
            qmap["use_custom_dash"]=str(1)
        
        qmap[LinArt+"_color"]=fncLongTosRGB(fncfield(rsParam,"color"),True if fncfield(rsParam,"transparent") == "J" else False)
        qmap[LinArt+"_width"]=str(fncfield(rsParam,"sizemm"))
        qmap[LinArt+"_width_unit"]=unitArt
        qmap["offset"]=str(fncfield(rsParam,"lineoffset") * (-1 if LinArt=="outline" else 1))
        qmap["offset_unit"]='MapUnit'
        if bSchraff:
            qmap["distance"]=str(fDist)
            qmap["distance_unit"]="MapUnit"      
            qmap["outline_style"]='no' # hier kein Rand# 
            qmap["angle"]=str(fWin)
            #printlog (qmap)
        lineLayer = lineMeta.createSymbolLayer(qmap)
        if basemm > 0:
            lineLayer.setRenderingPass(1)
        symbol.appendSymbolLayer(lineLayer)
    return symbol
    
def EineFlaecheFuellstil (qTyp,rsParam) :
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
    cgArt=fncfield(rsParam,"brushstyle")
    AktSymbol = QgsSymbolV2.defaultSymbol(qTyp)
    AktSymbol.deleteSymbolLayer(0)   
    if cgArt==0: #Farbfüllung
        fillMeta = QgsSymbolLayerV2Registry.instance().symbolLayerMetadata("SimpleFill")
        qmap={}
        qmap["color"]=fncLongTosRGB(fncfield(rsParam,"brushcolor"),True if fncfield(rsParam,"transparent") == "J" else False)
        qmap["outline_style"]='no' # hier kein Rand       
        AktSymbol.appendSymbolLayer(fillMeta.createSymbolLayer(qmap))
    if cgArt==2: #Horizontal
        fillMeta = QgsSymbolLayerV2Registry.instance().symbolLayerMetadata("LinePatternFill")
        qmap={}
        qmap["color"]= fncLongTosRGB(fncfield(rsParam,"brushcolor"),True if fncfield(rsParam,"transparent") == "J" else False)
        qmap["distance"]="2.5"
        qmap["distance_unit"]="MM"      
        qmap["outline_style"]='no' # hier kein Rand# 
        qmap["angle"]="0"
        
        qmap["line_style"]="solid"
        qmap["line_width"]="0.1"
        qmap["line_width_unit"]="MM"
        AktSymbol.appendSymbolLayer(fillMeta.createSymbolLayer(qmap)) 
    if cgArt==3: # Vertikal
        fillMeta = QgsSymbolLayerV2Registry.instance().symbolLayerMetadata("LinePatternFill")
        qmap={}
        qmap["color"]= fncLongTosRGB(fncfield(rsParam,"brushcolor"),True if fncfield(rsParam,"transparent") == "J" else False)
        qmap["distance"]="2.5"
        qmap["distance_unit"]="MM"      
        qmap["outline_style"]='no' # hier kein Rand# 
        qmap["line_style"]="solid"
        qmap["angle"]="90"
        qmap["line_width"]="0.1"
        qmap["line_width_unit"]="MM"
        AktSymbol.appendSymbolLayer(fillMeta.createSymbolLayer(qmap))            
    if cgArt==4: #Diagonal1
        fillMeta = QgsSymbolLayerV2Registry.instance().symbolLayerMetadata("LinePatternFill")
        qmap={}
        qmap["color"]= fncLongTosRGB(fncfield(rsParam,"brushcolor"),True if fncfield(rsParam,"transparent") == "J" else False)
        qmap["distance"]="2.5"
        qmap["distance_unit"]="MM"      
        qmap["outline_style"]='no' # hier kein Rand# 
        qmap["line_style"]="solid"
        qmap["angle"]="135"
        qmap["line_width"]="0.1"
        qmap["line_width_unit"]="MM"
        AktSymbol.appendSymbolLayer(fillMeta.createSymbolLayer(qmap))         
    if cgArt==5: #Diagonal2
        fillMeta = QgsSymbolLayerV2Registry.instance().symbolLayerMetadata("LinePatternFill")
        qmap={}
        qmap["color"]= fncLongTosRGB(fncfield(rsParam,"brushcolor"),True if fncfield(rsParam,"transparent") == "J" else False)
        qmap["distance"]="2.5"
        qmap["distance_unit"]="MM"      
        qmap["outline_style"]='no' # hier kein Rand# 
        qmap["line_style"]="solid"
        qmap["angle"]="135"
        qmap["line_width"]="0.1"
        qmap["line_width_unit"]="MM"
        AktSymbol.appendSymbolLayer(fillMeta.createSymbolLayer(qmap))          
    if cgArt==6: #Kreuz
        fillMeta = QgsSymbolLayerV2Registry.instance().symbolLayerMetadata("LinePatternFill")
        qmap={}
        qmap["color"]= fncLongTosRGB(fncfield(rsParam,"brushcolor"),True if fncfield(rsParam,"transparent") == "J" else False)
        qmap["distance"]="2.5"
        qmap["distance_unit"]="MM"      
        qmap["outline_style"]='no' # hier kein Rand# 
        qmap["line_style"]="solid"
        qmap["angle"]="0"
        qmap["line_width"]="0.1"
        qmap["line_width_unit"]="MM"
        AktSymbol.appendSymbolLayer(fillMeta.createSymbolLayer(qmap))          
        qmap={}
        qmap["color"]= fncLongTosRGB(fncfield(rsParam,"brushcolor"),True if fncfield(rsParam,"transparent") == "J" else False)
        qmap["distance"]="2.5"
        qmap["distance_unit"]="MM"      
        qmap["outline_style"]='no' # hier kein Rand# 
        qmap["line_style"]="solid"
        qmap["angle"]="90"
        qmap["line_width"]="0.1"
        qmap["line_width_unit"]="MM"
        AktSymbol.appendSymbolLayer(fillMeta.createSymbolLayer(qmap)) 
    if cgArt==7: #diagonal Kreuz
        fillMeta = QgsSymbolLayerV2Registry.instance().symbolLayerMetadata("LinePatternFill")
        qmap={}
        qmap["color"]= fncLongTosRGB(fncfield(rsParam,"brushcolor"),True if fncfield(rsParam,"transparent") == "J" else False)
        qmap["distance"]="2.5"
        qmap["distance_unit"]="MM"      
        qmap["outline_style"]='no' # hier kein Rand# 
        qmap["line_style"]="solid"
        qmap["angle"]="45"
        qmap["line_width"]="0.1"
        qmap["line_width_unit"]="MM"
        AktSymbol.appendSymbolLayer(fillMeta.createSymbolLayer(qmap))          
        qmap={}
        qmap["color"]= fncLongTosRGB(fncfield(rsParam,"brushcolor"),True if fncfield(rsParam,"transparent") == "J" else False)
        qmap["distance"]="2.5"
        qmap["distance_unit"]="MM"      
        qmap["outline_style"]='no' # hier kein Rand# 
        qmap["line_style"]="solid"
        qmap["angle"]="135"
        qmap["line_width"]="0.1"
        qmap["line_width_unit"]="MM"
        AktSymbol.appendSymbolLayer(fillMeta.createSymbolLayer(qmap))     
        
    return  AktSymbol

def EinenPunktAttributieren (qTyp,rsParam,sigPfad, svgPfad ):
    symbol = QgsSymbolV2.defaultSymbol(qTyp)
    symbol.deleteSymbolLayer(0)   
    pktMeta = QgsSymbolLayerV2Registry.instance().symbolLayerMetadata("SvgMarker")
    
    # SVG erzeugen
    sigpath=fncfield(rsParam,"sigpath")
    if sigpath == "":
        sigpath="PRIV:"
    signame=fncfield(rsParam,"signame") 
    cgPfad=sigpath.replace("PRIV:",sigPfad)
    qPfad=sigpath.replace("PRIV:",svgPfad)
    subMkPfad (qPfad, True)

    qDat= cgPfad + signame  + ".sig"
    qDat=qDat.replace("\\","/").replace("//","/")
    zDat = qPfad + signame + ".svg"
    zDat=zDat.replace("\\","/").replace("//","/")

    Sig2SVG (qDat,zDat)
    
    unitArt='MapUnit' if fncfield(rsParam,"scrresize") == "J" else "MM"
    # jetzt die eigentliche Darstellung definieren
    qmap={}
    qmap['size']=str(fncfield(rsParam,"wsizemm"))
    qmap['size_unit']=unitArt
    qmap['name']=zDat
    
    #geht erst ab Essen
    #qmap['angle_dd_expression']="abs(360-alpha )"
    qmap['angle_expression']="abs(360-alpha )"
    pktLayer = pktMeta.createSymbolLayer(qmap)
    symbol.appendSymbolLayer(pktLayer)
    return symbol

def EinenTextAttributieren (qTyp,rsParam,AttNum ):
    # Alternativ layer_name.loadNamedStyle('path_to_qml_file')
    #rsParam=clsdb.OpenRecordset(db,clsdb.sqlAttParam4IDandArt(3, AktAttID, Group))
    #printlog(clsdb.sqlAttParam4IDandArt(3, AktAttID, Group))
    symbol = QgsSymbolV2.defaultSymbol(QGis.Point)
    symbol.deleteSymbolLayer(0)   
    txtMeta = QgsSymbolLayerV2Registry.instance().symbolLayerMetadata("SvgMarker")
    
    if rsParam.size() == 0:
        errlog( "\nEinenTextAttributieren: " +  str(AttNum) + ";" + "Text" + ";"+ AktAttID + ";"+ str(Group) + " kein Attribut")
    #while rsParam.next(): 
    unitArt='MapUnit' if fncfield(rsParam,"scrresize") == "J" else "MM"
    # jetzt die eigentliche Darstellung definieren
    qmap={}
    qmap['size']="3" # str(fncfield(rsParam,"wsizemm"))
    qmap['size_unit']=unitArt

    txtLayer = txtMeta.createSymbolLayer(qmap)
    symbol.appendSymbolLayer(txtLayer)
    return symbol    

class clsRenderingByQT():      
    def Render(self, cgUser, qLayer, cgEbenenTyp, LayerID, bRolle, Group=0): 
        clsdb = pgDataBase()
        db=clsdb.CurrentDB()
        
        # ===========================================================================================================================
        # Variante 1: Rollenbasierte Darstellung einer Ebene
        if bRolle and (cgEbenenTyp == 0 or cgEbenenTyp == 1 or cgEbenenTyp == 3 or cgEbenenTyp == 5 or cgEbenenTyp == 6): 
            rsAttDefs=clsdb.OpenRecordset(db,clsdb.sqlAttDef4Layer( cgEbenenTyp, LayerID))
            symbol = QgsSymbolV2.defaultSymbol(qLayer.geometryType())
            renderer = QgsRuleBasedRendererV2(symbol)
            root_rule = renderer.rootRule()
            
            # =========  Schleife über alle (Individual-)Attributdefinitionen einer Ebene ================
            while (rsAttDefs.next()): 
            
                if rsAttDefs.value(0) == "{00000000-0000-0000-0000-000000000000}":
                    AktDefID = clsdb.AttDefID4Layer(db, LayerID, cgUser)
                    AktDefName=clsdb.AttDefName4ID(db, AktDefID)
                else:
                    AktDefID = rsAttDefs.value(0)
                    AktDefName="IA:"+rsAttDefs.value(1)

                rsAtt=clsdb.OpenRecordset(db,clsdb.sqlAtt4Massstab(cgEbenenTyp, AktDefID, Group))
                debuglog (clsdb.sqlAtt4Massstab(cgEbenenTyp, AktDefID, Group))
                if rsAtt.size() == 0 :
                    #printlog (rsAttDefs.value(0)+"|"+rsAttDefs.value(1)+"|"+LayerID)
                    addHinweis( LayerID + "/" + rsAttDefs.value(1)+ "/"+AktDefName+"(" + str(cgEbenenTyp) + "): Keine Attributdefinition gefunden")
                    break
                # Oberrolle Schreiben
                new_rule = OberRolle(root_rule,qLayer.geometryType(),AktDefName,"defid = '" + rsAttDefs.value(0) +"'")
                
                # =========  Schleife über alle (5) möglichen Maßstabsattribute einer Definition ================
                while (rsAtt.next()): 
                    mMin=fncfield(rsAtt,"MMin")
                    rule= EineRolle(root_rule,str(fncfield(rsAtt,"AttNum")) + ":" + fncfield(rsAtt,"ATTname") ,1 if mMin==0 else mMin, fncfield(rsAtt,"MMax"))
                    
                    if cgEbenenTyp == 0:
                        #printlog (clsdb.sqlAtt4Massstab(cgEbenenTyp, AktDefID, Group))
                        qTyp=qLayer.geometryType()
                        symbol = EinenPunktAttributieren (qTyp,rsAtt,clsdb.GetCGProjektPfad() + "/signatur/",clsdb.GetQSVGProjektPfad())
                        
                        rule.setSymbol(symbol)
                        new_rule.appendChild(rule)     

                    if cgEbenenTyp == 1: # Strecke 
                        qTyp = qLayer.geometryType()
                        symbol = EineStreckeAttributieren (db,clsdb,qTyp, "line", fncfield(rsAtt,"ATTid"),Group,fncfield(rsAtt,"AttNum") )                     
                        rule.setSymbol(symbol)
                        new_rule.appendChild(rule)  

                    if cgEbenenTyp == 3: # Text
                        qTyp = qLayer.geometryType()
                        symbol = EinenTextAttributieren (qTyp,rsAtt,fncfield(rsAtt,"AttNum") )                     
                        rule.setSymbol(symbol)
                        new_rule.appendChild(rule)   
                    
                    if cgEbenenTyp == 5: # PolyLinie
                        qTyp = qLayer.geometryType()
                        symbol = EineStreckeAttributieren (db,clsdb,qTyp, "line", fncfield(rsAtt,"lineattr"),Group,fncfield(rsAtt,"AttNum") )                     
                        rule.setSymbol(symbol)
                        new_rule.appendChild(rule)   
                    
                    if cgEbenenTyp == 6: # Fläche
                        qTyp = qLayer.geometryType()
                        # 1. Füllung
                        if  fncfield(rsAtt,"brushstyle") <> 1:
                            symbol=EineFlaecheFuellstil (qTyp,rsAtt)
                        else:
                            symbol=None
                        
                        # 2. Randlinie
                        symbol = EineStreckeAttributieren (db,clsdb,qTyp, "outline", fncfield(rsAtt,"lineattr"),Group,fncfield(rsAtt,"AttNum"),symbol ) 

                        # 3. Fülleffekte
                        if fncfield(rsAtt,"fslineattr1") <> "{00000000-0000-0000-0000-000000000000}":
                            fDist=fncfield(rsAtt,"fsabstand1")
                            fWin=fncfield(rsAtt,"fsalpha")
                            symbol = EineStreckeAttributieren (db,clsdb,qTyp, "fill", fncfield(rsAtt,"fslineattr1"),Group,fncfield(rsAtt,"AttNum"),symbol,fDist,fWin ) 
                        
                        
                        rule.setSymbol(symbol)
                        new_rule.appendChild(rule) 
                  
            # delete the default rule
            root_rule.removeChildAt(0)
            # apply the renderer to the layer
            qLayer.setRendererV2(renderer)
        
        # ===========================================================================================================================
        # Variante 2: Notvariante Beschriftung ohne Rolle
        if not bRolle and (cgEbenenTyp ==3):  
            # Nur EbenenAttDef (und auch nur erstes Maßstabsattribut)
            AktDefID = clsdb.AttDefID4Layer(db, LayerID, cgUser)
            AktDefName=clsdb.AttDefName4ID(db, AktDefID)
            EinfacheBeschriftungZeichnen(clsdb, db, qLayer,AktDefID, Group)
    
if __name__ == "__main__":
    from qgis.utils import *
    app = QApplication(sys.argv)
    dummy=""
