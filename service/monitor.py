import pymongo, simplejson as json, time, urllib2, socket
from threading import Timer

class Monitor:
    """ Class for handling each monitoring service """

    def __init__(self, config, service):
        self.config = config
        self.url = service['url']
        self.key = service['key']
        self.schedule()

        self.info = {}
        self.tests = []
        self.metrics = {}
        self.status = 'loading'

        socket.setdefaulttimeout(self.config['monitoring']['checkTimeout'])
        
    def schedule(self):
        Timer(self.config['monitoring']['checkInterval'], self.check).start()

    def check(self):
        self.schedule()

        try: 
            req = urllib2.urlopen(self.url)
            raw = req.read()

            try: 
                data = json.loads(raw)
                try:
                    self.info = {'name':data['serviceName'], 'type':data['serviceType'], 'region':data['serviceRegion']}
                    self.tests = data['tests']
                    self.metrics = data['metrics']
                    print "%s: %s" % (self.info['name'], self.metrics)
                    status = 'ok'
                except:
                    self.tests = []
                    self.metrics = {}
                    status = 'invalid_content'
            except:
                self.tests = []
                self.metrics = {}
                status = 'invalid_json'
        except urllib2.URLError:
            self.tests = []
            self.metrics = {}
            status = 'invalid_url'
        except:
            self.tests = []
            self.metrics = {}
            status = 'unknown_error'
            
        if self.status is not status:
            print "%s changed from %s to %s" % (self.url, self.status, status)
            
        self.status = status
