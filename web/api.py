import cherrypy

class Controller:
    """ API handler class """

    def __init__(self, config):
        # Open the configuration file
        self.config = config

    @cherrypy.expose
    def filters(self):
        return 'filters'

    @cherrypy.expose
    def data(self):
        return 'data'
