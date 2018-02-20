# -*- coding: utf-8 -*-
"""
/***************************************************************************
 __init__

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
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load clsFlurst4BL class from file clsFlurst4BL.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .clsFlurst4BL import clsFlurst4BL
    return clsFlurst4BL(iface)
