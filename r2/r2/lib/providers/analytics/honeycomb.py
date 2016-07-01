'''
honeycomb is a library to allow you to send events to Honeycomb from within
your python application.

Basic usage:
* initialize honeycomb with your Honeycomb writekey and dataset name
* create an event object and populate it with fields
* send the event object
* call honeycomb.close() when your program is finished

Sending on a closed or uninitialized honeycomb will throw a HoneycombSendError
exception.'''

import datetime
import json
import math
import Queue
import random
import requests
import threading

from pylons import app_globals as g

from r2.lib.providers.analytics import AnalyticsProvider
from r2.lib.providers.analytics import AnalyticsEvent
from r2.lib.providers.analytics import AnalyticsSendError


random.seed()


class HoneycombProvider(AnalyticsProvider):

    def __init__(self):
        '''initialize honeycomb and prepare it to send events to Honeycomb
        writekey: the authorization key for your team on Honeycomb
        dataset: the name of the default dataset to which to write
        sample_rate: the default sample rate
        num_workers: the number of threads to spin up to send events'''

        # hardcode some values, retrieve others from config
        num_workers = 10
        self.url = "https://api.hound.sh"
        self.writekey = g.secrets["honeycomb_writekey"]
        self.dataset = g.honeycomb_dataset
        self.sample_rate = math.ceil(g.honeycomb_sample_rate)
        if self.sample_rate <= 0:
            # want positive sample rate
            self.sample_rate = 1

        # use configured values to initialize the library
        self._xmit = Transmission(num_workers)

    def new_event(self):
        ev = HoneycombEvent(self._xmit, self.writekey, self.dataset,
                            self.sample_rate, self.url)
        return ev

    def close(self):
        '''wait for inflight events to be transmitted then shut down cleanly'''
        self._xmit.close()
        # we should error on post-close sends
        self._xmit = None


class HoneycombEvent(AnalyticsEvent):
    '''An Event is a collection of fields that will be sent to Honeycomb.'''

    def __init__(self, xmit, writekey, dataset, sample_rate, url):
        # populate the event's fields
        self.created_at = datetime.datetime.now()
        self._xmit = xmit
        self.writekey = writekey
        self.dataset = dataset
        self.url = url
        self.sample_rate = sample_rate
        self._data = {}

    def add_field(self, name, val):
        self._data[name] = val

    def send(self):
        '''send queues this event for transmission to Honeycomb.'''
        if self._xmit is None:
            # do this instead of a try below to error even when sampled
            raise AnalyticsSendError(
                "Tried to send on a closed or uninitialized honeycomb")
        # we keep 1/n events when samplerate is n
        if random.randint(1, self.sample_rate) != 1:
            return
        self._xmit.send(self)

    def __str__(self):
        return json.dumps(self._data)


class Transmission(object):

    def __init__(self, num_workers=10):
        self.num_workers = num_workers
        session = requests.Session()
        session.headers.update({"User-Agent": "honeycomb-reddit/1.0"})
        self.session = session

        # honeycomb adds events to the pending queue for us to send
        self.pending = Queue.Queue(maxsize=1000)

        self.threads = []
        for _ in range(self.num_workers):
            t = threading.Thread(target=self._sender)
            t.start()
            self.threads.append(t)

    def send(self, ev):
        '''send accepts an event and queues it to be sent'''
        try:
            self.pending.put_nowait(ev)
        except Queue.Full:
            # just drop the overflowed events
            pass

    def _sender(self):
        '''_sender is the control loop for each sending thread'''
        while True:
            ev = self.pending.get()
            if ev is None:
                break
            self._send(ev)

    def _send(self, ev):
        '''_send should only be called from sender and sends an individual
            event to Honeycomb'''
        req = requests.Request('POST', ev.url, data=str(ev))
        req.headers.update({
            "X-Event-Time": ev.created_at.isoformat("T"),
            "X-Honeycomb-Team": ev.writekey,
            "X-Honeycomb-Dataset": ev.dataset,
            "X-Honeycomb-SampleRate": ev.sample_rate})
        preq = self.session.prepare_request(req)
        self.session.send(preq)

    def close(self):
        '''call close to send all in-flight requests and shut down the
           senders nicely'''
        for _ in range(self.num_workers):
            self.pending.put(None)
        for t in self.threads:
            t.join()
