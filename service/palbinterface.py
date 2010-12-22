#!/usr/bin/python

''' 
For some reason, PALB at http://pypi.python.org/pypi/palb/0.1.1
only has a command-line interface. This module hooks into palb.core
and extracts numbers in a meaningfull fashion.
'''

from palb.core import *, 
import simplejson as json, sys, socket

socket.setdefaulttimeout(20)

def check(url, n, c):
    pool = URLGetterPool(c)
    pool.start()
    producer = URLProducer(pool.url_queue, url, n=n)
    stats = ResultStats()
    producer.start()
    for _ in xrange(n):
        if not keep_processing: break
        stats.add(pool.result_queue.get())
    stats.stop()

    x = {'average_document_length':stats.avg_req_length, 'url':url, 'concurrency':c, 'total_requests':n, 'total_time':stats.total_wall_time, 'completed_requests':len(stats.results), 'failed_requests':stats.failed_requests, 'total_transfered':stats.total_req_length, 'requests_per_second':len(stats.results)/stats.total_wall_time, 'time_per_request':stats.avg_req_time*1000, 'time_per_request_across_concurrent':stats.avg_req_time*1000/c, 'transfer_rate':stats.total_req_length/stats.total_wall_time}
        
    connection_times = stats.connection_times()
    x['connection_times'] = {}
    if connection_times is not None:
        for name, data in zip(('connect', 'processing', 'waiting', 'total'), connection_times):
            x['connection_times'][name] = {}
            t_min, t_mean, t_sd, t_median, t_max = [v*1000 for v in data]
            t_min, t_mean, t_median, t_max = [round(v) for v in t_min, t_mean, t_median, t_max]
            x['connection_times'][name]['min'] = t_min
            x['connection_times'][name]['mean'] = t_mean
            x['connection_times'][name]['sd'] = t_sd
            x['connection_times'][name]['median'] = t_median
            x['connection_times'][name]['max'] = t_max

    x['time_distribution'] = {}
    for percent, seconds in stats.distribution():
        x['time_distribution'][percent] = seconds*1024

    print json.dumps(x)
    exit()

check(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))

