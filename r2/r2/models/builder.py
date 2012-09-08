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

from pylons import g, c
from pylons.i18n import _

from r2.lib.db import tdb_cassandra
from r2.lib.filters import _force_unicode
from r2.lib.wrapped import Wrapped

#internal package imports should be fully qualified to allow
#__init__.py to ignore dependency ordering
from r2.models.account import Account
from r2.models.listing import Listing
from r2.models.subreddit import Subreddit
from r2.models.admintools import admintools, compute_votes, ip_span


__all__ = [
           #Constants
           "MAX_RECURSION",
           #Classes
           "Builder",
           #Exceptions
           #Functions
           "empty_listing",
           "make_wrapper",
           ]

MAX_RECURSION = 10

class Builder(object):
    def __init__(self, wrap=Wrapped, keep_fn=None, stale=True):
        self.stale = stale
        self.wrap = wrap
        self.keep_fn = keep_fn

    def keep_item(self, item):
        if self.keep_fn:
            return self.keep_fn(item)
        else:
            return item.keep_item(item)

    def wrap_items(self, items):
        from r2.lib.db import queries
        from r2.lib.template_helpers import add_attr
        user = c.user if c.user_is_loggedin else None

        #get authors
        #TODO pull the author stuff into add_props for links and
        #comments and messages?

        aids = set(l.author_id for l in items if hasattr(l, 'author_id')
                   and l.author_id is not None)

        authors = {}
        cup_infos = {}
        email_attrses = {}
        friend_rels = None
        if aids:
            authors = Account._byID(aids, data=True, stale=self.stale) if aids else {}
            cup_infos = Account.cup_info_multi(aids)
            if c.user_is_admin:
                email_attrses = admintools.email_attrs(aids, return_dict=True)
            if user and user.gold:
                friend_rels = user.friend_rels()

        subreddits = Subreddit.load_subreddits(items, stale=self.stale)

        if not user:
            can_ban_set = set()
        else:
            can_ban_set = set(id for (id,sr) in subreddits.iteritems()
                              if sr.can_ban(user))

        #get likes/dislikes
        try:
            likes = queries.get_likes(user, items)
        except tdb_cassandra.TRANSIENT_EXCEPTIONS as e:
            g.log.warning("Cassandra vote lookup failed: %r", e)
            likes = {}
        uid = user._id if user else None

        types = {}
        wrapped = []
        count = 0

        modlink = {}
        modlabel = {}
        for s in subreddits.values():
            modlink[s._id] = '/r/%s/about/moderators' % s.name
            modlabel[s._id] = (_('moderator of /r/%(reddit)s, speaking officially') %
                        dict(reddit = s.name) )


        for item in items:
            w = self.wrap(item)
            wrapped.append(w)
            # add for caching (plus it should be bad form to use _
            # variables in templates)
            w.fullname = item._fullname
            types.setdefault(w.render_class, []).append(w)

            #TODO pull the author stuff into add_props for links and
            #comments and messages?
            w.author = None
            w.friend = False

            # List of tuples (see add_attr() for details)
            w.attribs = []

            w.distinguished = None
            if hasattr(item, "distinguished"):
                if item.distinguished == 'yes':
                    w.distinguished = 'moderator'
                elif item.distinguished in ('admin', 'special'):
                    w.distinguished = item.distinguished

            try:
                w.author = authors.get(item.author_id)
                if user and item.author_id in user.friends:
                    # deprecated old way:
                    w.friend = True

                    # new way:
                    label = None
                    if friend_rels:
                        rel = friend_rels[item.author_id]
                        note = getattr(rel, "note", None)
                        if note:
                            label = u"%s (%s)" % (_("friend"), 
                                                  _force_unicode(note))
                    add_attr(w.attribs, 'F', label)

            except AttributeError:
                pass

            if (w.distinguished == 'admin' and w.author):
                add_attr(w.attribs, 'A')

            if w.distinguished == 'moderator':
                add_attr(w.attribs, 'M', label=modlabel[item.sr_id],
                         link=modlink[item.sr_id])
            
            if w.distinguished == 'special':
                args = w.author.special_distinguish()
                args.pop('name')
                if not args.get('kind'):
                    args['kind'] = 'special'
                add_attr(w.attribs, **args)

            if False and w.author and c.user_is_admin:
                for attr in email_attrses[w.author._id]:
                    add_attr(w.attribs, attr[2], label=attr[1])

            if w.author and w.author._id in cup_infos and not c.profilepage:
                cup_info = cup_infos[w.author._id]
                label = _(cup_info["label_template"]) % \
                        {'user':w.author.name}
                add_attr(w.attribs, 'trophy:' + cup_info["img_url"],
                         label=label,
                         link = "/user/%s" % w.author.name)

            if hasattr(item, "sr_id") and item.sr_id is not None:
                w.subreddit = subreddits[item.sr_id]

            w.likes = likes.get((user, item))

            # update vote tallies
            compute_votes(w, item)

            w.score = w.upvotes - w.downvotes

            if w.likes:
                base_score = w.score - 1
            elif w.likes is None:
                base_score = w.score
            else:
                base_score = w.score + 1

            # store the set of available scores based on the vote
            # for ease of i18n when there is a label
            w.voting_score = [(base_score + x - 1) for x in range(3)]

            w.deleted = item._deleted

            w.link_notes = []

            if c.user_is_admin:
                if item._deleted:
                    w.link_notes.append("deleted link")
                if getattr(item, "verdict", None):
                    if not item.verdict.endswith("-approved"):
                        w.link_notes.append(w.verdict)

            w.rowstyle = getattr(w, 'rowstyle', "")
            w.rowstyle += ' ' + ('even' if (count % 2) else 'odd')

            count += 1

            if c.user_is_admin and getattr(item, 'ip', None):
                w.ip_span = ip_span(item.ip)
            else:
                w.ip_span = ""

            # if the user can ban things on a given subreddit, or an
            # admin, then allow them to see that the item is spam, and
            # add the other spam-related display attributes
            w.show_reports = False
            w.show_spam    = False
            w.can_ban      = False
            w.reveal_trial_info = False
            w.use_big_modbuttons = False

            if (c.user_is_admin
                or (user
                    and hasattr(item,'sr_id')
                    and item.sr_id in can_ban_set)):
                if getattr(item, "promoted", None) is None:
                    w.can_ban = True

                ban_info = getattr(item, 'ban_info', {})
                w.unbanner = ban_info.get('unbanner')

                if item._spam:
                    w.show_spam = True
                    w.moderator_banned = ban_info.get('moderator_banned', False)
                    w.autobanned = ban_info.get('auto', False)
                    w.banner = ban_info.get('banner')
                    if ban_info.get('note', None) and w.banner:
                        w.banner += ' (%s)' % ban_info['note']
                    w.use_big_modbuttons = True
                    if getattr(w, "author", None) and w.author._spam:
                        w.show_spam = "author"

                elif getattr(item, 'reported', 0) > 0:
                    w.show_reports = True
                    w.use_big_modbuttons = True


        # recache the user object: it may be None if user is not logged in,
        # whereas now we are happy to have the UnloggedUser object
        user = c.user
        for cls in types.keys():
            cls.add_props(user, types[cls])

        return wrapped

    def get_items(self):
        raise NotImplementedError

    def item_iter(self, *a):
        """Iterates over the items returned by get_items"""
        raise NotImplementedError

    def must_skip(self, item):
        """whether or not to skip any item regardless of whether the builder
        was contructed with skip=true"""
        user = c.user if c.user_is_loggedin else None
        if hasattr(item, "promoted") and item.promoted is not None:
            return False
        if hasattr(item, 'subreddit') and not item.subreddit.can_view(user):
            return True
        if hasattr(item, 'can_view_slow') and not item.can_view_slow():
            return True


def empty_listing(*things):
    parent_name = None
    for t in things:
        try:
            parent_name = t.parent_name
            break
        except AttributeError:
            continue
    l = Listing(None, None, parent_name = parent_name)
    l.things = list(things)
    return Wrapped(l)

def make_wrapper(parent_wrapper = Wrapped, **params):
    def wrapper_fn(thing):
        w = parent_wrapper(thing)
        for k, v in params.iteritems():
            setattr(w, k, v)
        return w
    return wrapper_fn
