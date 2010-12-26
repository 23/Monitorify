#!/usr/bin/python

"""
Service for 
Author: Steffen Tiedemann Christensen <steffen@23company.com>
"""

# Setup dependency search
import sys, os, simplejson as json
from threadpool import ThreadPool
sys.path.append('../lib')

# Load classes to play with
from monitor import *

# Load configuration
configFile = os.path.join(os.path.dirname(__file__), sys.argv[1] if len(sys.argv)>=2 else 'config.json')
config = json.load(open(configFile))

print "Loading services"
sys.stdout.flush()

# Set up worker threads for running multiple concurrent tests
config['worker_threads'] = ThreadPool(int(self.config['monitoring']['maxTestConcurrency']))

for service in config['services']:
    # Start monitoring service
    thread.start_new_thread(MonitorService, (config, service))





