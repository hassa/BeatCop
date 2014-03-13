BeatCop
=======

BeatCop ensures that a process runs on exactly one node in a cluster at a time. It was written for using celery beat in a worker cluster, but can be used for anything else. It uses Redis to co-ordinate.


Mechanism
=========

BeatCop uses an expiring Redis key as a lock, which it continually (and atomically) refreshes while the controlled process is running. If the monitored process exits, the node dies, drops off the network or loses connection to Redis, it stops updating the lock, causing it to expire and another BeatCop instance can then acquire the lock and launch a new process.

BeatCop also tries very hard to make sure that if anything goes wrong, the monitored process is stopped.

This process obviously relies on Redis connectivity. If Redis updates fail, BeatCop will stop the controlled process and exit, hoping that at least one other Node can still talk to Redis and spawn a new process. If all nodes lose Redis connectivity, this will obviously fail.


Installation
============

    # Make a virtualenv if you like first
    pip install -r requirements.txt
    ./beatcop.py /path/to/beatcop.ini
    
It is typically a good idea to run BeatCop in something that will restart it if it dies, such as [daemon-tools](http://cr.yp.to/daemontools.html) or the dreaded Upstart.


Configuration
=============

See sample `beatcop.ini`.