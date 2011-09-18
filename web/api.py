import simplejson as json, cherrypy, pymongo
from pymongo import json_util

class Controller:
    """ API handler class """

    def __init__(self, config, db):
        # Open the configuration file
        self.config = config
        self.db = db

    @cherrypy.expose
    def filters(self):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return json.dumps(self.db.filters.find_one(), default=json_util.default)

    @cherrypy.expose
    def data(self, type=None, region=None, name=None, from_date=None, to_date=None):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        list = []
        for row in self.db.checks.find().limit(200):
            list.append(json.dumps(row, default=json_util.default))
        return "[%s]" % ', '.join(list)
