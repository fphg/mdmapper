#!/usr/bin/env python
# encoding: utf-8

import shapefile, urllib2
from owslib.csw import CatalogueServiceWeb

# catalog URL
cswUrl = "http://geobretagne.fr/geonetwork/srv/fre/csw"
# bbox filter
bbox = [-4.8,47.3,-0.9,49]
#~ proxy = "http://127.0.0.1:8888"
proxy = ""

if bool(proxy):
    proxyHandler = urllib2.ProxyHandler({"http" : proxy})
    opener = urllib2.build_opener(proxyHandler)
    urllib2.install_opener(opener)

csw = CatalogueServiceWeb(cswUrl)
csw.getrecords(qtype="dataset", keywords=[], esn="full", maxrecords=1000, bbox=bbox)

shp = shapefile.Writer(shapefile.POLYGON)
shp.autoBalance = 1
shp.field('id')
shp.field('title')
shp.field('layerurl')
shp.field('layername')
shp.field('layertitle')
shp.field('subjects')

layercount = 0

# owslib can access these fields :
#'abstract', 'accessrights', 'alternative', 'bbox', 'contributor',
#'coverage', 'created', 'creator', 'date', 'format', 'identifier',
#'identifiers', 'ispartof', 'issued', 'language', 'license', 'modified',
# 'publisher', 'references', 'relation', 'rights', 'rightsholder', 'source',
#'spatial', 'subjects', 'temporal', 'title', 'type', 'uris', 'xml'


def cleanAttr(s):
    """
    Converts string to unicode string
    """
    return s.encode('utf-8') if bool(s) else ''

for mdId in csw.records:
    rec = csw.records[mdId]

    title = cleanAttr(rec.title)
    abstract = cleanAttr(rec.abstract)
    date = cleanAttr(rec.date)
    identifier = cleanAttr(rec.identifier)
    source = cleanAttr(rec.source)
    subjects = rec.subjects

    xmin, ymin = float(rec.bbox.minx), float(rec.bbox.miny)
    xmax, ymax = float(rec.bbox.maxx), float(rec.bbox.maxy)
    shp.poly(parts=[[
        [xmin,ymin,xmax,ymin],
        [xmax,ymin,xmax,ymax],
        [xmax,ymax,xmin,ymax],
        [xmin,ymax,xmin,ymin],
        [xmin,ymin,xmax,ymin]
    ]], shapeType=shapefile.POLYGON)

    uris = rec.uris
    for uri in rec.uris:
        if uri['protocol']:
            if uri['protocol'][:7].upper() == 'OGC:WMS':
                layername = cleanAttr(uri['name']) if uri['name'] else 'misconfigured layer name'
                layerurl = cleanAttr(uri['url']) if uri['url'] else 'misconfigured layer url'
                layertitle = cleanAttr(uri['description']) if uri['description'] else 'misconfigured layer title'
                shp.record(mdId, title, layerurl, layername, layertitle, subjects)
                layercount = layercount + 1

print "layers %s"%layercount
print "md %s"%len(csw.records)

shp.save("metadata.shp")

