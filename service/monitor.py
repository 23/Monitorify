# TODO
# - Run benchmarks
# - Sign requests
# - Write results to Mongo DB

import pymongo, simplejson as json, time, urllib2, socket, sys, traceback
from threading import Timer

class MonitorService:
    """ Class for handling each monitoring service """

    def __init__(self, config, service):
        # Store config a properties
        self.config = config
        self.url = service['url']
        self.key = service['key']

        # Prepare object for saving check data
        self.info = {}
        self.tests = {}
        self.metrics = {}
        self.status = 'loading'

        # Explicitly define a timeout on the socket
        socket.setdefaulttimeout(self.config['monitoring']['checkTimeout'])

        # And start looping checks
        self.schedule()
        
    def schedule(self):
        Timer(self.config['monitoring']['checkInterval'], self.check).start()

    def check(self):
        # We will want to run this again soon
        self.schedule()

        try: 
            # Request the URL and get data
            req = urllib2.urlopen(self.url)
            raw = req.read()

            try: 
                # Parse JSON into a python dict
                data = json.loads(raw)
                try:
                    # Update information about the service
                    self.info = {'name':data['serviceName'], 'type':data['serviceType'], 'region':data['serviceRegion']}
                    # Remember metrics
                    self.metrics = data['metrics']
                    print "%s: Load is %s" % (self.info['name'], self.metrics['serverLoad'])
                    status = 'ok'

                    # Update tests
                    for test in data['tests']:
                        key = test['key']
                        if key in self.tests:
                            if self.tests[key].changed(test):
                                # The test exists, but has changed
                                # Stop the current test and overwrite with a new one
                                self.tests[key].stop()
                                self.tests[key] = MonitorTest(self.config, self, test)
                        else:
                            # The is a new test, set it up
                            self.tests[key] = MonitorTest(self.config, self, test)
                                
                except:
                    # The JSON document didn't meet our requirements
                    self.tests = []
                    self.metrics = {}
                    ###traceback.print_exc()
                    status = 'invalid_content'
            except:
                # The URL didn't return valid JSON
                self.tests = []
                self.metrics = {}
                status = 'invalid_json'
        except:
            # Couldn't access URL
            self.tests = []
            self.metrics = {}
            status = 'invalid_url'
            
        # If status on the endpoint has changed, let's notify
        if self.status is not status:
            print "%s changed from %s to %s" % (self.url, self.status, status)
            
        # Save status and return
        self.status = status
        sys.stdout.flush()



class MonitorTest:
    """ Class for tests """

    def __init__(self, config, service, test):
        # Store config a properties
        self.config = config
        self.service = service
        self.originalTest = test
        self.key = test['key']
        self.name = test['name']
        self.url = test['url']
        self.interval = test['interval']
        self.count = test['count']
        self.concurrency = test['concurrency']
        self.notifyOnError = test['notifyOnError']
        self.active = True
        print "%s: Initiate test %s" % (service.info['name'], self.name)

        # Explicitly define a timeout on the socket
        socket.setdefaulttimeout(self.config['monitoring']['testTimeout'])

        # And schedule the tests
        self.schedule()
        
    def stop(self):
        # This is simplistic, but it gives us a way to stop tests even with timers and callbacks
        self.active = False
        
    def schedule(self):
        if not self.active: return
        Timer(int(self.interval), self.run).start()

    def run(self):
        # Are we even still doing this thing?
        if not self.active: return

        # Already, let's schedule next test
        self.schedule()

        # Run the actual test
        print "%s: Run test %s (%s)" % (self.service.info['name'], self.name, self.key)

        # And return by flushing
        sys.stdout.flush()

    def changed(self, test):
        # Check if the passed in test setup is different from the one set up with this object?
        return False if self.originalTest==test else True
