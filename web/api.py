import simplejson as json, cherrypy

class Controller:
    """ API handler class """

    def __init__(self, config, db):
        # Open the configuration file
        self.config = config
        self.db = db

    @cherrypy.expose
    def filters(self):
        row = self.db.filters.find_one()
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return json.dumps({
                'regions':row['regions'],
                'types':row['types'],
                'names':row['names'],
                'min_time':row['min_time']
                })

    @cherrypy.expose
    def data(self):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return 'data'
