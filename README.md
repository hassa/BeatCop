BeatCop
=======

BeatCop is a simple cluster singleton manager. It ensures that a managed process runs on exactly one node in a cluster at a time, no more, no less (assuming there is at least one node left alive).

It was written for managing [Celery beat](http://celery.readthedocs.org/en/latest/userguide/periodic-tasks.html) in an autoscaling pool of Celery workers but was written as generic process manager and can therefore be used for pretty much anything. It uses (Redis)[http://redis.io/] to communicate.


Mechanism
=========

BeatCop uses an expiring Redis key ([SET EX NX](http://redis.io/commands/set)) as a lock, which it continually refreshes while the controlled process is running. If the BeatCop or the whole node dies for any reason, drops off the network or loses connection to Redis, the lock expires and a waiting BeatCop on another node will then acquire the lock and launch a new process.

The lock is acquired (via SET NX) and refreshed (via a short LUA script) atomically, so there should be no race conditions.

BeatCop also tries very hard to make sure that if anything goes wrong, the monitored process is stopped.


Prerequisites
=============

 * A server running Redis 2.6.12 or higher to which all nodes can connect.

Installation
============

    # Make a virtualenv if you like first
    pip install -r requirements.txt
    ./beatcop.py /path/to/beatcop.ini
    
It is typically a good idea to run BeatCop in something that will restart it if it dies, such as [daemon-tools](http://cr.yp.to/daemontools.html) or the dreaded Upstart.


Configuration
=============

See sample `beatcop.ini`.


Caveats
=======

BeatCop relies on Redis connectivity. If Redis updates fail, BeatCop will stop the controlled process and exit, hoping that at least one other node can still talk to Redis and spawn a new process. If all nodes lose Redis connectivity, this will obviously fail.

BeatCop does not currently work via [nutcracker (twemproxy)](https://github.com/twitter/twemproxy/blob/master/notes/redis.md#scripting).


License
=======

MIT - see [LICENSE](LICENSE) file.
