#!/usr/bin/env python
# encoding: utf-8

import shapefile, urllib2, argparse, logging
from owslib.csw import CatalogueServiceWeb
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

# default parameters
default = {
    'csw': 'http://sdi.georchestra.org/geonetwork/srv/eng/csw',
    'extent': '-180,-90,180,90',
    'maxrecords': 500,
    'output': 'metadata.shp',
    'debug': 'WARNING'
}


def cleanAttr(s):
    """
    Converts string to unicode string
    """
    return s.encode('utf-8') if bool(s) else ''

##
## arguments retrieval
##

parser = argparse.ArgumentParser(description="""geOrchestra metadata mapper.
Queries a CSW service, retrieves dataset bboxes,
produces a georeferenced table of the datasets.""")

parser.add_argument('csw',
    type=str,
    default=default['csw'] ,
    help='the CSW service URL, default '+default['csw'])

# shapefile name
parser.add_argument('-o', '--output',
    type=str,
    nargs='?',
    default=default['output'],
    help='shapefile file path, default "%s"'%default['output'],
    metavar='filepath')

# optional extent restriction
parser.add_argument('-e', '--extent',
    type=str,
    nargs='?',
    default=default['extent'],
    help='results are contained in WGS84 extent, default "%s"'%default['extent'],
    metavar='xmin,ymin,xmax,ymax')

# optional max records
parser.add_argument('-m', '--maxrecords',
    type=int,
    nargs='?',
    default=500,
    help='retrieves no more than MAXRECORDS metadatas, default %s'%default['maxrecords'],
    metavar='maxrecords')

# optional http proxy
parser.add_argument('--http_proxy', type=str,
    default=None,
    nargs='?',
    help='http proxy host and port, example http://proxy:3128')



args = parser.parse_args()

# optional proxy handler for urllib2 and owslib
if bool(args.http_proxy):
    logging.debug('using proxy %s'%args.http_proxy)
    proxyHandler = urllib2.ProxyHandler({"http" : args.http_proxy})
    opener = urllib2.build_opener(proxyHandler)
    urllib2.install_opener(opener)

# csw connection
bbox = [float(x) for x in args.extent.split(',')]
logging.debug('connecting to %s'%args.csw)
csw = CatalogueServiceWeb(args.csw)
logging.info('retrieving %s datasets, bbox=%s'%(args.maxrecords, bbox))
csw.getrecords(qtype="dataset", keywords=[], esn="full", maxrecords=args.maxrecords, bbox=bbox)
logging.info('retrieved %s records'%len(csw.records))
if len(csw.records)>=args.maxrecords:
    logging.warn('maxrecords reached')


# shapefile preparation
shp = shapefile.Writer(shapefile.POLYGON)
shp.autoBalance = 1
shp.field('id')
shp.field('title')
shp.field('layerurl')
shp.field('layername')
shp.field('layertitle')
shp.field('subjects')

layercount = 0

for mdId in csw.records:
    logging.debug('reading %s'%mdId)
    # owslib can access these fields :
    #'abstract', 'accessrights', 'alternative', 'bbox', 'contributor',
    #'coverage', 'created', 'creator', 'date', 'format', 'identifier',
    #'identifiers', 'ispartof', 'issued', 'language', 'license', 'modified',
    # 'publisher', 'references', 'relation', 'rights', 'rightsholder', 'source',
    #'spatial', 'subjects', 'temporal', 'title', 'type', 'uris', 'xml'
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
                logging.debug('WMS layer found: %s'%layername)
                layercount = layercount + 1

logging.info('metadatas found: %s'%len(csw.records))
logging.info('layers found: %s'%layercount)
logging.info('saving results in: %s'%args.output)
shp.save(args.output)

