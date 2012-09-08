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
# All portions of the code written by reddit are Copyright (c) 2006-2012 reddit
# Inc. All Rights Reserved.
###############################################################################

import time
from copy import deepcopy

from pylons import g, c

from r2.lib.utils import tup
from r2.lib.comment_tree import (moderator_messages,
                                 sr_conversation, 
                                 conversation,
                                 user_messages,
                                 subreddit_messages,
                                 )
from r2.lib.db.thing import Thing
from r2.lib.wrapped import Wrapped

# internal package imports should be fully qualified since __init__.py
# will not have imported everything yet.
from r2.models.builder import Builder
from r2.models._builder import _CommentBuilder, _MessageBuilder
from r2.models.account import Account
from r2.models.listing import Listing
from r2.models.subreddit import Subreddit
from r2.models.admintools import admintools, compute_votes, ip_span


__all__ = [
           #Constants
           #Classes
           "CommentBuilder",
           "IDBuilder",
           "ModeratorMessageBuilder",
           "MultiredditMessageBuilder",
           "QueryBuilder",
           "SearchBuilder",
           "SrMessageBuilder",
           "TopCommentBuilder",
           "UserMessageBuilder",
           #Exceptions
           #Functions
           ]


EXTRA_FACTOR = 1.5

class QueryBuilder(Builder):
    def __init__(self, query, wrap=Wrapped, keep_fn=None, skip=False, **kw):
        Builder.__init__(self, wrap=wrap, keep_fn=keep_fn)
        self.query = query
        self.skip = skip
        self.num = kw.get('num')
        self.start_count = kw.get('count', 0) or 0
        self.after = kw.get('after')
        self.reverse = kw.get('reverse')

        self.prewrap_fn = None
        if hasattr(query, 'prewrap_fn'):
            self.prewrap_fn = query.prewrap_fn
        #self.prewrap_fn = kw.get('prewrap_fn')

    def __repr__(self):
        return "<%s(%r)>" % (self.__class__.__name__, self.query)

    def item_iter(self, a):
        """Iterates over the items returned by get_items"""
        for i in a[0]:
            yield i

    def init_query(self):
        q = self.query

        if self.reverse:
            q._reverse()

        q._data = True
        self.orig_rules = deepcopy(q._rules)
        if self.after:
            q._after(self.after)

    def fetch_more(self, last_item, num_have):
        done = False
        q = self.query
        if self.num:
            num_need = self.num - num_have
            if num_need <= 0:
                #will cause the loop below to break
                return True, None
            else:
                #q = self.query
                #check last_item if we have a num because we may need to iterate
                if last_item:
                    q._rules = deepcopy(self.orig_rules)
                    q._after(last_item)
                    last_item = None
                q._limit = max(int(num_need * EXTRA_FACTOR), 1)
        else:
            done = True
        new_items = list(q)

        return done, new_items

    def get_items(self):
        self.init_query()

        num_have = 0
        done = False
        items = []
        count = self.start_count
        first_item = None
        last_item = None
        have_next = True

        #logloop
        self.loopcount = 0
        
        while not done:
            done, new_items = self.fetch_more(last_item, num_have)

            #log loop
            self.loopcount += 1
            if self.loopcount == 20:
                g.log.debug('BREAKING: %s' % self)
                done = True

            #no results, we're done
            if not new_items:
                break

            #if fewer results than we wanted, we're done
            elif self.num and len(new_items) < self.num - num_have:
                done = True
                have_next = False

            if not first_item and self.start_count > 0:
                first_item = new_items[0]

            if self.prewrap_fn:
                orig_items = {}
                new_items2 = []
                for i in new_items:
                    new = self.prewrap_fn(i)
                    orig_items[new._id] = i
                    new_items2.append(new)
                new_items = new_items2
            else:
                orig_items = dict((i._id, i) for i in new_items)

            if self.wrap:
                new_items = self.wrap_items(new_items)

            #skip and count
            while new_items and (not self.num or num_have < self.num):
                i = new_items.pop(0)

                if not (self.must_skip(i) or self.skip and not self.keep_item(i)):
                    items.append(i)
                    num_have += 1
                    count = count - 1 if self.reverse else count + 1
                    if self.wrap:
                        i.num = count
                last_item = i
        
            # get original version of last item
            if last_item and (self.prewrap_fn or self.wrap):
                last_item = orig_items[last_item._id]

        if self.reverse:
            items.reverse()
            last_item, first_item = first_item, have_next and last_item
            before_count = count
            after_count = self.start_count - 1
        else:
            last_item = have_next and last_item
            before_count = self.start_count + 1
            after_count = count

        #listing is expecting (things, prev, next, bcount, acount)
        return (items,
                first_item,
                last_item,
                before_count,
                after_count)

class IDBuilder(QueryBuilder):
    def thing_lookup(self, names):
        return Thing._by_fullname(names, data=True, return_dict=False,
                                  stale=self.stale)

    def init_query(self):
        names = list(tup(self.query))

        after = self.after._fullname if self.after else None

        self.names = self._get_after(names,
                                     after,
                                     self.reverse)

    @staticmethod
    def _get_after(l, after, reverse):
        names = list(l)

        if reverse:
            names.reverse()

        if after:
            try:
                i = names.index(after)
            except ValueError:
                names = ()
            else:
                names = names[i + 1:]

        return names

    def fetch_more(self, last_item, num_have):
        done = False
        names = self.names
        if self.num:
            num_need = self.num - num_have
            if num_need <= 0:
                return True, None
            else:
                if last_item:
                    last_item = None
                slice_size = max(int(num_need * EXTRA_FACTOR), 1)
        else:
            slice_size = len(names)
            done = True

        self.names, new_names = names[slice_size:], names[:slice_size]
        new_items = self.thing_lookup(new_names)
        return done, new_items


class FakeThing(object):
    def __init__(self, name):
        self._id = name

class SimpleBuilder(IDBuilder):
    def thing_lookup(self, names):
        return [FakeThing(name) for name in names]

    def init_query(self):
        names = list(tup(self.query))
        self.names = self._get_after(names, self.after, self.reverse)

    def get_items(self):
        items, prev, next, bcount, acount = IDBuilder.get_items(self)
        items = [i._id for i in items]
        if prev:
            prev = prev._id
        if next:
            next = next._id
        return (items, prev, next, bcount, acount)

class SearchBuilder(IDBuilder):
    def __init__(self, query, wrap=Wrapped, keep_fn=None, skip=False,
                 skip_deleted_authors=True, **kw):
        IDBuilder.__init__(self, query, wrap, keep_fn, skip, **kw)
        self.skip_deleted_authors = skip_deleted_authors
    def init_query(self):
        self.skip = True

        self.start_time = time.time()

        self.results = self.query.run()
        names = list(self.results.docs)
        self.total_num = self.results.hits

        after = self.after._fullname if self.after else None

        self.names = self._get_after(names,
                                     after,
                                     self.reverse)

    def keep_item(self,item):
        # doesn't use the default keep_item because we want to keep
        # things that were voted on, even if they've chosen to hide
        # them in normal listings
        # TODO: Consider a flag to disable this (and see listingcontroller.py)
        if item._spam or item._deleted:
            return False
        elif (self.skip_deleted_authors and
              getattr(item, "author", None) and item.author._deleted):
            return False
        else:
            return True

class CommentBuilder(_CommentBuilder):
    def item_iter(self, a):
        for i in a:
            yield i
            if hasattr(i, 'child'):
                for j in self.item_iter(i.child.things):
                    yield j

class MessageBuilder(_MessageBuilder):
    def item_iter(self, a):
        for i in a[0]:
            yield i
            if hasattr(i, 'child'):
                for j in i.child.things:
                    yield j

class ModeratorMessageBuilder(MessageBuilder):
    def __init__(self, user, **kw):
        self.user = user
        MessageBuilder.__init__(self, **kw)

    def get_tree(self):
        if self.parent:
            return conversation(self.user, self.parent)
        sr_ids = Subreddit.reverse_moderator_ids(self.user)
        return moderator_messages(sr_ids)

class MultiredditMessageBuilder(MessageBuilder):
    def __init__(self, user, **kw):
        self.user = user
        MessageBuilder.__init__(self, **kw)

    def get_tree(self):
        if self.parent:
            return conversation(self.user, self.parent)
        return moderator_messages(c.site.sr_ids)

class TopCommentBuilder(CommentBuilder):
    """A comment builder to fetch only the top-level, non-spam,
       non-deleted comments"""
    def __init__(self, link, sort, wrap = Wrapped):
        CommentBuilder.__init__(self, link, sort,
                                load_more = False,
                                continue_this_thread = False,
                                max_depth = 1, wrap = wrap)

    def get_items(self, num = 10):
        final = CommentBuilder.get_items(self, num = num)
        return [ cm for cm in final if not cm.deleted ]

class SrMessageBuilder(MessageBuilder):
    def __init__(self, sr, **kw):
        self.sr = sr
        MessageBuilder.__init__(self, **kw)

    def get_tree(self):
        if self.parent:
            return sr_conversation(self.sr, self.parent)
        return subreddit_messages(self.sr)

class UserMessageBuilder(MessageBuilder):
    def __init__(self, user, **kw):
        self.user = user
        MessageBuilder.__init__(self, **kw)

    def get_tree(self):
        if self.parent:
            return conversation(self.user, self.parent)
        return user_messages(self.user)

