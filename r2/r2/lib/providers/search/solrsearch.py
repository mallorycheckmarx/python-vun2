# The contents of this file are subject to the Common Public Attribution
# License Version 1.0. (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://code.reddit.com/LICENSE. The License is based on the Mozilla Public
# License Version 1.1, but Sections 14 and 15 have been added to cover use of
# software over a computer network and provide for limited attribution for the
# Original Developer. In addition, Exhibit A has been modified to be consistent
# with Exhibit B.
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License for
# the specific language governing rights and limitations under the License.
#
# The Original Code is reddit.
#
# The Original Developer is the Initial Developer.  The Initial Developer of
# the Original Code is reddit Inc.
#
# All portions of the code written by reddit are Copyright (c) 2006-2015 reddit
# Inc. All Rights Reserved.
###############################################################################

from datetime import datetime, timedelta
import cPickle as pickle
import functools
import httplib
import urllib
import json
import time
import re


from lxml import etree
from r2.lib import amqp, filters
from r2.lib.db.operators import desc
from r2.lib.db.sorts import epoch_seconds
import r2.lib.utils as r2utils
from r2.models import (Account, Link, Subreddit, All, DefaultSR,
                       MultiReddit, DomainSR, Friends, ModContribSR,
                       FakeSubreddit, NotFound)
from pylons import g, c

from r2.lib.cloudsearch import InvalidQuery, SearchHTTPError, Results, \
        CloudSearchUploader, LinkUploader, SubredditFields, LinkFields
    

_CHUNK_SIZE = 4000000 # Approx. 4 MB, to stay under the 5MB limit
_VERSION_OFFSET = 13257906857
ILLEGAL_XML = re.compile(u'[\x00-\x08\x0b\x0c\x0e-\x1F\uD800-\uDFFF\uFFFE\uFFFF]')


_SEARCH = "/solr/select?"
INVALID_QUERY_CODES = ('CS-UnknownFieldInMatchExpression',
                       'CS-IncorrectFieldTypeInMatchExpression',
                       'CS-InvalidMatchSetExpression',)
DEFAULT_FACETS = {"reddit": {"count":20}}

WARNING_XPATH = ".//lst[@name='error']/str[@name='warning']"
STATUS_XPATH = ".//lst/int[@name='status']"
DOC_API = 'http://%s:%s' % (g.SOLR_DOC_HOST, g.SOLR_PORT)

SORTS_DICT = {'-text_relevance': 'score desc',
              'relevance': 'score desc'}


def basic_query(query=None, bq=None, faceting=None, size=1000,
                start=0, rank="", return_fields=None, record_stats=False,
                search_api=None):
    if search_api is None:
        search_api = g.SOLR_SEARCH_HOST
    if faceting is None:
        faceting = DEFAULT_FACETS
    path = _encode_query(query, faceting, size, start, rank, return_fields)
    timer = None
    if record_stats:
        timer = g.stats.get_timer("cloudsearch_timer")
        timer.start()
    connection = httplib.HTTPConnection(search_api, g.SOLR_PORT)
    try:
        connection.request('GET', path)
        resp = connection.getresponse()
        response = resp.read()
        if record_stats:
            g.stats.action_count("event.search_query", resp.status)
        if resp.status >= 300:
            try:
                reasons = json.loads(response)
            except ValueError:
                pass
            else:
                messages = reasons.get("messages", [])
                for message in messages:
                    if message['code'] in INVALID_QUERY_CODES:
                        raise InvalidQuery(resp.status, resp.reason, message,
                                           path, reasons)
            raise CloudSearchHTTPError(resp.status, resp.reason, path,
                                       response)
    finally:
        connection.close()
        if timer is not None:
            timer.stop()

    return json.loads(response)


basic_link = functools.partial(basic_query, size=10, start=0,
                               rank="",
                               return_fields=['title', 'reddit',
                                              'author_fullname'],
                               record_stats=False,
                               search_api=g.SOLR_SEARCH_HOST)


basic_subreddit = functools.partial(basic_query,
                                    faceting=None,
                                    size=10, start=0,
                                    rank="activity",
                                    return_fields=['title', 'reddit',
                                                   'author_fullname'],
                                    record_stats=False,
                                    search_api=g.SOLR_SUBREDDIT_SEARCH_HOST)


class SolrSearchQuery(object):
    '''Represents a search query sent to solr'''
    search_api = None
    sorts = {}
    sorts_menu_mapping = {}
    recents = {None: None}
    known_syntaxes = ("solr", "plain")
    default_syntax = "solr"

    def __init__(self, query, sr=None, sort=None, syntax=None, raw_sort=None,
                 faceting=None, recent=None):
        if syntax is None:
            syntax = self.default_syntax
        elif(syntax == 'cloudsearch'):
            syntax = 'solr'
        elif syntax not in self.known_syntaxes:
            raise ValueError("Unknown search syntax: %s" % syntax)
        self.query = filters._force_unicode(query or u'')
        self.converted_data = None
        self.syntax = syntax
        self.sr = sr
        self._sort = sort
        if raw_sort:
            self.sort = translate_raw_sort(raw_sort)
        elif sort:
            self.sort = self.sorts.get(sort)
        else:
            self.sort = 'score'
        self._recent = recent
        self.recent = self.recents[recent]
        self.faceting = faceting
        self.bq = u''
        self.results = None

    def run(self, after=None, reverse=False, num=1000, _update=False):
        results = self._run(_update=_update)

        docs, hits, facets = results.docs, results.hits, results._facets

        after_docs = r2utils.get_after(docs, after, num, reverse=reverse)

        self.results = Results(after_docs, hits, facets)
        return self.results

    def _run(self, start=0, num=1000, _update=False):
        '''Run the search against self.query'''
        
        q = self.query.encode('utf-8')
        if g.sqlprinting:
            g.log.info("%s", self)
        q = self.customize_query(self.query)
        return self._run_cached(q, self.bq.encode('utf-8'), self.sort,
                                self.faceting, start=start, num=num,
                                _update=_update)

    def customize_query(self, q):
        return q

    def __repr__(self):
        '''Return a string representation of this query'''
        result = ["<", self.__class__.__name__, "> query:",
                  repr(self.query), " "]
        if self.bq:
            result.append(" bq:")
            result.append(repr(self.bq))
            result.append(" ")
        result.append("sort:")
        result.append(self.sort)
        return ''.join(result)

    @classmethod
    def _run_cached(cls, query, bq, sort="score", faceting=None, start=0,
                    num=1000, _update=False):
        '''Query the solr HOST. _update parameter allows for supposed
        easy memoization at later date.
        
        Example result set:
        
        '''
        if not query:
            return Results([], 0, {})
        response = basic_query(query=query, bq=bq, size=num, start=start,
                               rank=sort, search_api=cls.search_api,
                               faceting=faceting, record_stats=True)


        hits = response['response']['numFound']
        docs = [doc['id'] for doc in response['response']['docs']]
        facets = {}
        facet_fields = response['facet_counts'].get('facet_fields', {})
        for field in facet_fields:
            facets[field] = []
            while facet_fields[field]:
                value = facet_fields[field].pop(0)
                count = facet_fields[field].pop(0)
                facets[field].append(dict(value=value, count=count)) 
            

        results = Results(docs, hits, facets)
        return results


class LinkSearchQuery(SolrSearchQuery):
    search_api = g.SOLR_SEARCH_HOST
    sorts = {'relevance': 'score',
             'hot': 'hot2',
             'top': 'top',
             'new': 'timestamp',
             'comments': 'num_comments',
             }
    sorts_menu_mapping = {'relevance': 1,
                          'hot': 2,
                          'new': 3,
                          'top': 4,
                          'comments': 5,
                          }
    recents = {
        'hour': timedelta(hours=1),
        'day': timedelta(days=1),
        'week': timedelta(days=7),
        'month': timedelta(days=31),
        'year': timedelta(days=366),
        'all': None,
        None: None,
    }
    known_syntaxes = ("solr", "plain")
    default_syntax = "solr"

    def customize_query(self, bq):
        queries = [bq]
        subreddit_query = self._get_sr_restriction(self.sr)
        if subreddit_query:
            queries.append(subreddit_query)
        if self.recent:
            recent_query = self._restrict_recent(self.recent)
            queries.append(recent_query)
        return self.create_boolean_query(queries)

    @classmethod
    def create_boolean_query(cls, queries):
        '''Return an AND clause combining all queries'''
        if len(queries) > 1:
            bq = ' AND  '.join(['(%s)' %q for q in queries]) 
        else:
            bq = queries[0]
        return bq

    @staticmethod
    def _restrict_recent(recent):
        now = datetime.now(g.tz)
        since = epoch_seconds(now - recent)
        return 'timestamp:%i..' % since

    @staticmethod
    def _get_sr_restriction(sr):
        '''Return a solr-appropriate query string that restricts
        results to only contain results from self.sr
        
        '''
        bq = []
        if (not sr) or sr == All or isinstance(sr, DefaultSR):
            return None
        elif isinstance(sr, MultiReddit):
            for sr_id in sr.sr_ids:
                bq.append("sr_id:%s" % sr_id)
        elif isinstance(sr, DomainSR):
            bq = ["site:'%s'" % sr.domain]
        elif sr == Friends:
            if not c.user_is_loggedin or not c.user.friends:
                return None
            # The query limit is roughly 8k bytes. Limit to 200 friends to
            # avoid getting too close to that limit
            friend_ids = c.user.friends[:200]
            friends = ["author_fullname:'%s'" %
                       Account._fullname_from_id36(r2utils.to36(id_))
                       for id_ in friend_ids]
            bq.extend(friends)
        elif isinstance(sr, ModContribSR):
            for sr_id in sr.sr_ids:
                bq.append("sr_id:%s" % sr_id)
        elif not isinstance(sr, FakeSubreddit):
            bq = ["sr_id:%s" % sr._id]
        return ' OR '.join(bq)


class SubredditSearchQuery(SolrSearchQuery):
    search_api = g.SOLR_SUBREDDIT_SEARCH_HOST
    sorts = {'relevance': 'activity',
             None: 'activity',
             }
    sorts_menu_mapping = {'relevance': 1,
                          }

    known_syntaxes = ("plain", "solr")
    default_syntax = "plain"


def _encode_query(query, faceting, size, start, rank, return_fields):
    if not query:
        raise ValueError("Need query")
    params = {}
    params["q"] = query
    params["wt"] = "json"
    params["defType"] = "edismax"
    params["size"] = size
    params["start"] = start
    if rank == 'activity':
        params['sort'] = 'activity desc'
    elif rank: 
        params['sort'] = rank.strip().lower()
        if not params['sort'].split()[-1] in ['asc', 'desc']:
            params['sort'] = '%s desc' % params['sort']
    facet_limit = []
    facet_sort = []
    if faceting:
        params["facet"] = "true"
        params["facet.field"] = ",".join(faceting.iterkeys())
        for facet, options in faceting.iteritems():
            facet_limit.append(options.get("count", 20))
            if "sort" in options:
                facet_sort.append('%s desc' % options["sort"])
        params["facet.limit"] = ",".join([str(l) for l in facet_limit])
        params["facet.sort"] = ",".join(facet_sort)
        params["facet.sort"] = params["facet.sort"] or 'score desc' 
    if return_fields:
        params["qf"] = ",".join(return_fields)
    encoded_query = urllib.urlencode(params)
    path = '/solr/%s/select?%s' % \
        (getattr(g, 'SOLR_CORE', 'collection1'), encoded_query)
    return path    


class SolrSearchUploader(CloudSearchUploader):
    
    def __init__(self, solr_host=None, solr_port=None, fullnames=None, version_offset=_VERSION_OFFSET):
        self.solr_host = solr_host or g.SOLR_DOC_HOST
        self.solr_port = solr_port or g.SOLR_PORT
        self._version_offset = version_offset
        self.fullnames = fullnames    

    def add_xml(self, thing):
        from r2.lib.cloudsearch import _safe_xml_str

        #add = etree.Element("add", id=thing._fullname)
        doc = etree.Element("doc")
        field = etree.SubElement(doc, "field", name='id')
        field.text = thing._fullname

        for field_name, value in self.fields(thing).iteritems():
            field = etree.SubElement(doc, "field", name=field_name)
            field.text = _safe_xml_str(value)

        return doc

    def delete_xml(self, thing):
        '''Return the solr XML representation of
        "delete this from the index"
        
        '''
        delete = etree.fromstring('<id>%s</id>' % thing._id)
        return delete

    def delete_ids(self, ids):
        '''Delete documents from the index.
        'ids' should be a list of fullnames
        
        '''
        deletes = [etree.fromstring('<id>%s</id>' % id_) \
                for id_ in ids]


        batch = etree.Element("delete")
        batch.extend(deletes)
        return self.send_documents(batch)

    def xml_from_things(self):
        '''Generate a <batch> XML tree to send to solr for
        adding/updating/deleting the given things
        
        '''
        add = etree.Element("add")
        delete = etree.Element("delete")
        self.batch_lookups()
        for thing in self.things:
            try:
                if thing._spam or thing._deleted:
                    delete_node = self.delete_xml(thing)
                    delete.append(delete_node)
                elif self.should_index(thing):
                    add_node = self.add_xml(thing)
                    add.append(add_node)
            except (AttributeError, KeyError) as e:
                # Problem! Bail out, which means these items won't get
                # "consumed" from the queue. If the problem is from DB
                # lag or a transient issue, then the queue consumer
                # will succeed eventually. If it's something else,
                # then manually run a consumer with 'use_safe_get'
                # on to get past the bad Thing in the queue
                if not self.use_safe_get:
                    raise
                else:
                    g.log.warning("Ignoring problem on thing %r.\n\n%r",
                                  thing, e)
        return (add, delete)


    def inject(self, quiet=False):
        '''Send things to solr. Return value is time elapsed, in seconds,
        of the communication with the solr endpoint
        
        '''

        xml_things = self.xml_from_things()

        cs_time = 0
        for batch in xml_things:

            if not len(batch):
                return 0

            cs_start = datetime.now(g.tz)
            sent = self.send_documents(batch)
            cs_time = cs_time + (datetime.now(g.tz) - cs_start).total_seconds()

            adds, deletes, warnings = 0, 0, []
            for record in sent:
                response = etree.fromstring(record)
                status = response.find(STATUS_XPATH).text
                if status == '0':
                    # success! 
                    adds += len(batch.findall('doc'))
                    deletes += len(batch.findall('delete'))
                    for w in response.find(WARNING_XPATH) or []:
                        warnings.append(w.text)

            g.stats.simple_event("cloudsearch.uploads.adds", delta=adds)
            g.stats.simple_event("cloudsearch.uploads.deletes", delta=deletes)
            g.stats.simple_event("cloudsearch.uploads.warnings",
                    delta=len(warnings))

            if not quiet:
                print "%s Changes: +%i -%i" % (self.__class__.__name__,
                                               adds, deletes)
                if len(warnings):
                    print "%s Warnings: %s" % (self.__class__.__name__,
                                               "; ".join(warnings))

        return cs_time    

    def send_documents(self, docs):
        '''Open a connection to the Solr endpoint, and send the documents
        for indexing. Multiple requests are sent if a large number of documents
        are being sent (see chunk_xml())
        
        Raises CloudSearchHTTPError if the endpoint indicates a failure
        '''
        core = getattr(g, 'SOLR_CORE', 'collection1') 
        responses = []
        connection = httplib.HTTPConnection(self.solr_host, self.solr_port)
        chunker = chunk_xml(docs)
        headers = {}
        headers['Content-Type'] = 'application/xml'
        try:
            for data in chunker:
                # HTTPLib calculates Content-Length header automatically
                connection.request('POST', "/solr/%s/update/" % core,
                                   data, headers)
                response = connection.getresponse()
                if 200 <= response.status < 300:
                    responses.append(response.read())
                else:
                    raise CloudSearchHTTPError(response.status,
                                               response.reason,
                                               response.read())
        finally:
            connection.close()
        return responses


def chunk_xml(xml, depth=0):
    '''Chunk POST data into pieces that are smaller than the 20 MB limit.
    
    Ideally, this never happens (if chunking is necessary, would be better
    to avoid xml'ifying before testing content_length)'''
    data = etree.tostring(xml)
    root = xml.findall('add') and 'add' or 'delete'
    content_length = len(data)
    if content_length < _CHUNK_SIZE:
        yield data
    else:
        depth += 1
        print "WARNING: Chunking (depth=%s)" % depth
        half = len(xml) / 2
        left_half = xml # for ease of reading
        right_half = etree.Element(root)
        # etree magic simultaneously removes the elements from one tree
        # when they are appended to a different tree
        right_half.append(xml[half:])
        for chunk in chunk_xml(left_half, depth=depth):
            yield chunk
        for chunk in chunk_xml(right_half, depth=depth):
            yield chunk


@g.stats.amqp_processor('cloudsearch_q')
def _run_changed(msgs, chan):
    '''Consume the cloudsearch_changes queue, and print reporting information
    on how long it took and how many remain
    
    '''
    start = datetime.now(g.tz)

    changed = [pickle.loads(msg.body) for msg in msgs]

    link_fns = SolrLinkUploader.desired_fullnames(changed)
    sr_fns = SolrSubredditUploader.desired_fullnames(changed)

    link_uploader = SolrLinkUploader(g.SOLR_DOC_HOST, fullnames=link_fns)
    subreddit_uploader = SolrSubredditUploader(g.SOLR_SUBREDDIT_DOC_HOST,
                                           fullnames=sr_fns)

    link_time = link_uploader.inject()
    subreddit_time = subreddit_uploader.inject()
    cloudsearch_time = link_time + subreddit_time

    totaltime = (datetime.now(g.tz) - start).total_seconds()

    print ("%s: %d messages in %.2fs seconds (%.2fs secs waiting on "
           "solr); %d duplicates, %s remaining)" %
           (start, len(changed), totaltime, cloudsearch_time,
            len(changed) - len(link_fns | sr_fns),
            msgs[-1].delivery_info.get('message_count', 'unknown')))

def run_changed(drain=False, min_size=int(getattr(g, 'SOLR_MIN_BATCH', 500)), limit=1000, sleep_time=10, 
        use_safe_get=False, verbose=False):
    '''Run by `cron` (through `paster run`) on a schedule to send Things to Solr
    '''
    if use_safe_get:
        SolrSearchUploader.use_safe_get = True
    amqp.handle_items('cloudsearch_changes', _run_changed, min_size=min_size,
                      limit=limit, drain=drain, sleep_time=sleep_time,
                      verbose=verbose)


class SolrLinkUploader(SolrSearchUploader):
    types = (Link,)

    def __init__(self, solr_host=None, solr_port=None, fullnames=None, version_offset=_VERSION_OFFSET):
        super(SolrLinkUploader, self).__init__(fullnames=fullnames, version_offset=version_offset)
        self.accounts = {}
        self.srs = {}

    def fields(self, thing):
        '''Return fields relevant to a Link search index'''
        account = self.accounts[thing.author_id]
        sr = self.srs[thing.sr_id]
        return LinkFields(thing, account, sr).fields()

    def batch_lookups(self):
        super(SolrLinkUploader, self).batch_lookups()
        author_ids = [thing.author_id for thing in self.things
                      if hasattr(thing, 'author_id')]
        try:
            self.accounts = Account._byID(author_ids, data=True,
                                          return_dict=True)
        except NotFound:
            if self.use_safe_get:
                self.accounts = safe_get(Account._byID, author_ids, data=True,
                                         return_dict=True)
            else:
                raise

        sr_ids = [thing.sr_id for thing in self.things
                  if hasattr(thing, 'sr_id')]
        try:
            self.srs = Subreddit._byID(sr_ids, data=True, return_dict=True)
        except NotFound:
            if self.use_safe_get:
                self.srs = safe_get(Subreddit._byID, sr_ids, data=True,
                                    return_dict=True)
            else:
                raise

    def should_index(self, thing):
        return (thing.promoted is None and getattr(thing, "sr_id", None) != -1)
    

class SolrSubredditUploader(SolrSearchUploader):
    types = (Subreddit,)

    def fields(self, thing):
        return SubredditFields(thing).fields()

    def should_index(self, thing):
        return getattr(thing, 'author_id', None) != -1

 
def _progress_key(item):
    return "%s/%s" % (item._id, item._date)


_REBUILD_INDEX_CACHE_KEY = "cloudsearch_cursor_%s"


def rebuild_link_index(start_at=None, sleeptime=1, cls=Link,
                       uploader=SolrLinkUploader, estimate=50000000, 
                       chunk_size=1000):
    cache_key = _REBUILD_INDEX_CACHE_KEY % uploader.__name__.lower()
    uploader = uploader()

    if start_at is _REBUILD_INDEX_CACHE_KEY:
        start_at = g.cache.get(cache_key)
        if not start_at:
            raise ValueError("Told me to use '%s' key, but it's not set" %
                             cache_key)

    q = cls._query(cls.c._deleted == (True, False),
                   sort=desc('_date'), data=True)
    if start_at:
        after = cls._by_fullname(start_at)
        assert isinstance(after, cls)
        q._after(after)
    q = r2utils.fetch_things2(q, chunk_size=chunk_size)
    q = r2utils.progress(q, verbosity=1000, estimate=estimate, persec=True,
                         key=_progress_key)
    for chunk in r2utils.in_chunks(q, size=chunk_size):
        uploader.things = chunk
        uploader.fullnames = [c._fullname for c in chunk] 
        for x in range(5):
            try:
                uploader.inject()
            except httplib.HTTPException as err:
                print "Got %s, sleeping %s secs" % (err, x)
                time.sleep(x)
                continue
            else:
                break
        else:
            raise err
        last_update = chunk[-1]
        g.cache.set(cache_key, last_update._fullname)
        time.sleep(sleeptime)


rebuild_subreddit_index = functools.partial(rebuild_link_index,
                                            cls=Subreddit,
                                            uploader=SolrSubredditUploader,
                                            estimate=200000,
                                            chunk_size=1000)


def test_run_link(start_link, count=1000):
    '''Inject `count` number of links, starting with `start_link`'''
    if isinstance(start_link, basestring):
        start_link = int(start_link, 36)
    links = Link._byID(range(start_link - count, start_link), data=True,
                       return_dict=False)
    uploader = SolrLinkUploader(things=links)
    return uploader.inject()


def test_run_srs(*sr_names):
    '''Inject Subreddits by name into the index'''
    srs = Subreddit._by_name(sr_names).values()
    uploader = SolrSubredditUploader(things=srs)
    return uploader.inject()


def translate_raw_sort(sort):
    return SORTS_DICT.get(sort, 'score desc') 

class SolrSearchProvider(SearchProvider):


