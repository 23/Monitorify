import cherrypy

class Controller:
    """ Primary handler class """

    def __init__(self, config):
        # Open the configuration file
        self.config = config

    @cherrypy.expose
    def index(self):
        return 'Visual Analytics 2.0 Frontend Server'
