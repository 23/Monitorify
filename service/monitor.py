# TODO
# - Write results to Mongo DB

import calcsize, memsize
import pymongo, simplejson as json, time, urllib2, socket, sys, traceback, sha, re, palbinterface, random
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
        self.time = int(time.time())
        self.status = 'loading'
        self.clear()

        # Explicitly define a timeout on the socket
        socket.setdefaulttimeout(self.config['monitoring']['checkTimeout'])

        # And start looping checks
        self.schedule()
        
    def save(self):
        return True

    def schedule(self):
        # We'll add a little variability to avoid tests running exactly the same time
        Timer(self.config['monitoring']['checkInterval']*(0.9+(random.random()/5.0)), self.check).start()

    def sign(self, url):
        timestamp = int(time.time())
        url = url + ('&' if re.search("\?", url) else '?') + "timestamp=" + str(timestamp)
        h = sha.new(self.key)
        h.update(url + str(timestamp))
        url = url + "&signature=" + h.hexdigest()
        return url

    def clear(self):
        self.data = {'metrics':{}, 'tests':{}}

    def check(self):
        # We will want to run this again soon
        self.schedule()

        try: 
            # Request the URL and get data
            raw = ''
            req = urllib2.urlopen(self.sign(self.url))
            raw = req.read()
            del req

            try: 
                # Parse JSON into a python dict
                data = json.loads(raw)
                try:
                    # Update information about the service
                    self.time = int(time.time())
                    self.info = {'name':data['serviceName'], 'type':data['serviceType'], 'region':data['serviceRegion']}
                    # Remember metrics
                    self.data['metrics'] = data['metrics']
                    print "%s: Load is %s" % (self.info['name'], self.data['metrics']['serverLoad'])
                    status = 'ok'

                    # Update tests
                    for test in data['tests']:
                        key = test['key']
                        if key in self.tests:
                            if self.tests[key].changed(test):
                                # The test exists, but has changed
                                # Stop the current test and overwrite with a new one
                                self.tests[key].stop()
                                del self.tests[key]
                                self.tests[key] = MonitorTest(self.config, self, test)
                        else:
                            # The is a new test, set it up
                            x = 1
                            self.tests[key] = MonitorTest(self.config, self, test)
                                
                except:
                    # The JSON document didn't meet our requirements
                    self.tests = []
                    self.clear()
                    traceback.print_exc()
                    status = 'invalid_content'
            except:
                # The URL didn't return valid JSON
                self.tests = []
                self.clear()
                status = 'invalid_json'
        except:
            # Couldn't access URL
            self.tests = []
            self.clear()
            status = 'invalid_url'
            
        # If status on the endpoint has changed, let's notify
        if self.status is not status:
            print "%s changed from %s to %s" % (self.url, self.status, status)

        #print "size self=%s, tests=%s" % (calcsize.asizeof(self), calcsize.asizeof(self.tests))
        print "memory memory=%s, resident=%s, stacksize=%s" % (memsize.memory(), memsize.resident(), memsize.stacksize())
            
        # Save status and return
        self.status = status
        self.save()
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
        self.interval = int(test['interval'])
        self.count = int(test['count'])
        self.concurrency = int(test['concurrency'])
        self.notifyOnError = test['notifyOnError']
        self.active = True

        # We don't want unemployed threads
        if (self.concurrency>self.count): self.concurrency=self.count

        # We shouldn't run test more often than generic checks
        if (self.interval<self.config['monitoring']['checkInterval']): self.interval = self.config['monitoring']['checkInterval']

        print "%s: Initiated test %s (i=%s, n=%s, c=%s)" % (self.service.info['name'], self.name, self.interval, self.count, self.concurrency)

        # Explicitly define a timeout on the socket
        socket.setdefaulttimeout(self.config['monitoring']['testTimeout'])

        self.schedule()
        
    def stop(self):
        # This is simplistic, but it gives us a way to stop tests even with timers and callbacks
        self.active = False
        
    def schedule(self):
        if not self.active: return
        # We'll add a little variability to avoid tests running exactly the same time
        Timer(int(self.interval*(0.9+(random.random()/5.0))), self.run).start()

    def run(self):
        # Are we even still doing this thing?
        if not self.active: return

        # Already, let's schedule next test
        self.schedule()

        try:
            # Run the test, please
            result = palbinterface.check(self.url, self.count, self.concurrency)
            
            # Print information about the succesful test
            print "%s: %s/%s requests succeced in %.3f seconds" % (self.service.info['name'], result['completed_requests'], result['total_requests'], result['total_time'])
        
            # Is this considered an error?
            result['error'] = True if float(self.config['monitoring']['errorWarnRatio'])*result['total_requests']>=result['completed_requests'] else False

        except:
            # Tetsts failed badly
            print "%s: Test failed totally and completely" % (self.service.info['name'], )
            results = {'url':self.url, 'concurrency':self.concurrency, 'total_requests':1, 'error':True}

        # Store tests as a metric
        self.service.data['tests'][self.key] = result
        self.service.save()
        sys.stdout.flush()

    def changed(self, test):
        # Check if the passed in test setup is different from the one set up with this object?
        return False if self.originalTest==test else True
