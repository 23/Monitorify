#!/usr/bin/python

"""
Frontend for Monitorify
Author: Steffen Tiedemann Christensen <steffen@23company.com>
"""

# Setup dependency search
import sys, os, simplejson as json
from pymongo import Connection

# Load configuration
configFile = os.path.join(os.path.dirname(__file__), sys.argv[1] if len(sys.argv)>=2 else 'config.json')
config = json.load(open(configFile))

# Build into a cherrypy config
cherrypy_conf = {
    'global': {
        'server.socket_host':config['server']['host'],
        'server.socket_port':config['server']['port'],
        'tools.sessions.on':True,
        'tools.encode.on':True,
        'tools.decode.on':True,
        'tools.gzip.on':True,
        'tools.staticdir.root':os.path.abspath(os.path.join(os.path.dirname(__file__))),
        },
    '/assets': {
        'tools.staticdir.on':True,
        'tools.staticdir.dir':'assets',
        }
    }

# Import controllers
import cherrypy, root
# Initialize the server quickly
cherrypy.quickstart(root.Controller(config), config=cherrypy_conf)

