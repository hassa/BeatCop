#!/usr/bin/env python
## Python 2.7
"""Beatcop tries to ensure that a specified task runs on exactly one node in a cluster.
It does this by acquiring an expiring lock in Redis, which it then continually refreshes.
If the node stops refreshing its lock for any reason (like sudden death) another will acquire the lock and launch the specified process.

Beatcop is loosely based on the locking patterns described at http://redis.io/commands/set.
"""

import atexit
import ConfigParser
import logging
import os
import redis
import shlex
import signal
import socket
import subprocess
import sys
import time


class Lock(object):
    """Lock class using Redis expiry."""

    lua_refresh = """
        if redis.call("get", KEYS[1]) == ARGV[1]
        then
            return redis.call("pexpire", KEYS[1], ARGV[2])
        else
            return 0
        end
    """

    def __init__(self, redis_, name, timeout=None, sleep=0.1):
        self.redis = redis_
        self.name = name
        self.timeout = timeout
        self.sleep = sleep
        # Instead of putting any old rubbish into the Lock's value, use our IP address and PID
        self.value = "%s-%d" % (socket.gethostbyname(socket.gethostname()), os.getpid())
        self._refresh_script = self.redis.register_script(self.lua_refresh)

    def acquire(self):
        """Acquire lock. Blocks until acquired."""
        while True:
            # Try to set the lock
            if self.redis.set(self.name, self.value, px=self.timeout, nx=True):
                # It's ours until the timeout now
                return True
            # Lock is taken, try again in a bit
            time.sleep(self.sleep)

    def refresh(self):
        """Refresh an existing lock to prevent it from expiring.
        Uses a LUA (EVAL) script to ensure only a lock which we own is being overwritten.
        Returns True if refresh succeeded, False if not."""
        # Redis docs claim EVALs are atomic, and I'm inclined to believe it.
        return self._refresh_script(keys=[self.name], args=[self.value, self.timeout]) == 1

    def who(self):
        """Returns the owner (value) of the lock."""
        return self.redis.get(self.name)


class BeatCop(object):
    """Run a process on a single node by using a Redis lock."""

    def __init__(self, command, redis_host, redis_port=6379, lockname=None, timeout=1000, shell=False):
        self.command = command
        self.shell = shell
        self.timeout = timeout
        self.sleep = timeout / (1000.0 * 3)  # Convert to seconds and make sure we refresh at least 3 times per timeout period
        self.process = None
        self.redis = redis.Redis(host=redis_host, port=redis_port, db=0)
        self.lockname = lockname or ("beatcop:%s" % (self.command))
        self.lock = Lock(self.redis, self.lockname, timeout=self.timeout, sleep=self.sleep)

        atexit.register(self.crash)
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
        signal.signal(signal.SIGHUP, self.handle_signal)

    def run(self):
        """Run process if nobody else is, otherwise wait until we're needed. Never returns."""

        log.info("Waiting for lock, currently held by %s", self.lock.who())
        if self.lock.acquire():
            log.info("Lock acquired")
            # We got the lock, so we make sure the task is running and keep refreshing the lock - if we ever stop for any reason, for example because our host died, the lock will soon expire.
            while True:
                if self.process is None:  # Process not spawned yet
                    self.process = self.spawn(self.command)
                    log.info("Spawned PID %d", self.process.pid)
                child_status = self.process.poll()
                if child_status is not None:
                    # Oops, process died on us.
                    log.error("Child died with exit code %d", child_status)
                    sys.exit(2)
                # Everything okay, refresh lock and sleep
                if not self.lock.refresh():
                    log.error("Log refresh failed, bailing out")
                    self.cleanup()
                    sys.exit(66)
                time.sleep(self.sleep)

    def spawn(self, command):
        """Spawn process."""
        if self.shell:
            args = command
        else:
            args = shlex.split(command)
        return subprocess.Popen(args, shell=self.shell)

    def cleanup(self):
        """Clean up, making sure the task is stopped before we pack up and go home."""
        if self.process is None:  # Process wasn't running yet, so nothing to worry about
            return
        if self.process.poll() is None:
            log.info("Sending TERM to %d", self.process.pid)
            self.process.terminate()
            # Give process a second to terminate, if it didn't, kill it.
            start = time.clock()
            while time.clock() - start < 1.0:
                time.sleep(0.05)
                if self.process.poll() is not None:
                    break
            else:
                log.info("Sending KILL to %d", self.process.pid)
                self.process.kill()
        assert self.process.poll() is not None

    def handle_signal(self, sig, frame):
        """Handles signals, surprisingly."""
        if sig in [signal.SIGINT]:
            log.warning("Ctrl-C pressed, shutting down...")
        if sig in [signal.SIGTERM]:
            log.warning("SIGTERM received, shutting down...")
        self.cleanup()
        sys.exit(1)

    def crash(self):
        """Handles unexpected exit, for example because Redis connection failed."""
        log.error("Something went terribly wrong")
        self.cleanup()


if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO, format='%(asctime)s BeatCop: %(message)s', datefmt='%Y-%m-%d %H:%M:%S %Z')
    log = logging.getLogger()

    conf = ConfigParser.ConfigParser()
    conf.read('beatcop.ini')
    beatcop = BeatCop(
        conf.get('beatcop', 'command'),
        redis_host=conf.get('redis', 'host'),
        redis_port=conf.getint('redis', 'port'),
        lockname=conf.get('beatcop', 'lockname') if conf.has_option('beatcop', 'lockname') else None,
        timeout=conf.getint('beatcop', 'timeout'),
        shell=conf.getboolean('beatcop', 'shell'),
    )

    log.info("BeatCop starting on %s using lock '%s'", beatcop.lock.value, beatcop.lockname)
    beatcop.run()
