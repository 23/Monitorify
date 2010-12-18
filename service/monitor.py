# TODO
# - Write results to Mongo DB
# - Warn about errors
# - Require HTTP 200 in tests, otherwise fail 'em

import pymongo, simplejson as json, time, urllib2, socket, sys, traceback, sha, re, threading
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
        self.metrics = {'custom':{}, 'tests':{}}
        self.time = int(time.time())
        self.status = 'loading'

        # Explicitly define a timeout on the socket
        socket.setdefaulttimeout(self.config['monitoring']['checkTimeout'])

        # And start looping checks
        self.schedule()
        
    def save(self):
        return True

    def schedule(self):
        Timer(self.config['monitoring']['checkInterval'], self.check).start()

    def sign(self, url):
        timestamp = int(time.time())
        url = url + ('&' if re.search("\?", url) else '?') + "timestamp=" + str(timestamp)
        h = sha.new(self.key)
        h.update(url + str(timestamp))
        url = url + "&signature=" + h.hexdigest()
        return url

    def check(self):
        # We will want to run this again soon
        self.schedule()

        try: 
            # Request the URL and get data
            req = urllib2.urlopen(self.sign(self.url))
            raw = req.read()

            try: 
                # Parse JSON into a python dict
                data = json.loads(raw)
                try:
                    # Update information about the service
                    self.time = int(time.time())
                    self.info = {'name':data['serviceName'], 'type':data['serviceType'], 'region':data['serviceRegion']}
                    # Remember metrics
                    self.metrics['custom'] = data['metrics']
                    print "%s: Load is %s" % (self.info['name'], self.metrics['custom']['serverLoad'])
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
                    self.metrics = {'custom':{}, 'tests':{}}
                    traceback.print_exc()
                    status = 'invalid_content'
            except:
                # The URL didn't return valid JSON
                self.tests = []
                self.metrics = {'custom':{}, 'tests':{}}
                status = 'invalid_json'
        except:
            # Couldn't access URL
            self.tests = []
            self.metrics = {'custom':{}, 'tests':{}}
            status = 'invalid_url'
            
        # If status on the endpoint has changed, let's notify
        if self.status is not status:
            print "%s changed from %s to %s" % (self.url, self.status, status)
            
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
        if (self.concurrency>self.count):
            self.concurrency=self.count

        print "%s: Initiated test %s (i=%s, n=%s, c=%s)" % (service.info['name'], self.name, self.interval, self.count, self.concurrency)

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

    def worker(self, url):
        # Run tests and tests and tests
        while(self.outstandingRequests>0):
            # Begin connection
            try:
                begin = time.time()
                req = urllib2.urlopen(url)
                # Save time and size for req
                self.resultsSize.append(len(req.read()))
                self.resultsTime.append(time.time()-begin)
            except:
                # Record an error
                self.resultsErrors = self.resultsErrors

            # Incr total count of tests
            self.outstandingRequests = self.outstandingRequests-1


    def run(self):
        # Are we even still doing this thing?
        if not self.active: return

        # Already, let's schedule next test
        self.schedule()

        # Reset some counters
        self.outstandingRequests = self.count
        self.resultsSize = []
        self.resultsTime = []
        self.resultsErrors = 0
        # Start threads for each concurrent connection we want to run in tests
        signed_url = self.service.sign(self.url)
        for i in xrange(self.concurrency):
            threading.Thread(target=self.worker, args=(signed_url, )).start()
        # ... and keep 'em running until we're done
        while(self.outstandingRequests>0):
            time.sleep(.1)

        if len(self.resultsSize)>0:
            # Print information about the succesful test
            print "%s: %s: Total requests: %s" % (self.service.name, self.key, len(self.resultsSize))
            print "%s: %s: Total bytes: %s" % (self.service.name, self.key, sum(self.resultsSize))
            print "%s: %s: Num errors: %s" % (self.service.name, self.key, self.resultsErrors)
            print "%s: %s: Avg bytes: %s" % (self.service.name, self.key, sum(self.resultsSize)/len(self.resultsSize))
            print "%s: %s: Avg time: %s" % (self.service.name, self.key, sum(self.resultsTime)/len(self.resultsTime))

            # Is this considered an error?
            error = True if float(self.config['monitoring']['errorWarnRatio'])*len(self.resultsSize)>=self else False

            # Store tests as a metric
            self.service.metrics['tests'][self.key] = {'totalRequests':len(self.resultsSize), 'totalBytes':sum(self.resultsSize), 'numErrors':self.resultsErrors, 'avgBytes':(sum(self.resultsSize)/len(self.resultsSize)), 'avgTime':(sum(self.resultsTime)/len(self.resultsTime)), 'error':error}
        else:
            # Nothing useful from the request
            self.service.metrics['tests'][self.key] = {'totalRequests':0, 'totalBytes':0, 'numErrors':self.count, 'avgBytes':0, 'avgTime':0, 'error':True}

        self.service.save()
        sys.stdout.flush()

    def changed(self, test):
        # Check if the passed in test setup is different from the one set up with this object?
        return False if self.originalTest==test else True
