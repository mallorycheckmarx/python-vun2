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
# All portions of the code written by reddit are Copyright (c) 2006-2014 reddit
# Inc. All Rights Reserved.
###############################################################################

from account import *
from link import *
from vote import *
from report import *
from subreddit import DefaultSR, AllSR, Frontpage
from pylons import i18n, request, g
from pylons.i18n import _

from r2.lib.wrapped import Wrapped
from r2.lib import utils
from r2.lib.db import operators
from r2.lib.cache import sgm

from collections import namedtuple
from copy import deepcopy, copy

class Listing(object):
    # class used in Javascript to manage these objects
    _js_cls = "Listing"

    def __init__(self, builder, nextprev = True, next_link = True,
                 prev_link = True, **kw):
        self.builder = builder
        self.nextprev = nextprev
        self.next_link = True
        self.prev_link = True
        self.next = None
        self.prev = None
        self._max_num = 1

    @property
    def max_score(self):
        scores = [x.score for x in self.things if hasattr(x, 'score')]
        return max(scores) if scores else 0

    @property
    def max_num(self):
        return self._max_num

    def get_items(self, *a, **kw):
        """Wrapper around builder's get_items that caches the rendering."""
        from r2.lib.template_helpers import replace_render
        builder_items = self.builder.get_items(*a, **kw)
        for item in self.builder.item_iter(builder_items):
            # rewrite the render method
            if not hasattr(item, "render_replaced"):
                item.render = replace_render(self, item, item.render)
                item.render_replaced = True
        return builder_items

    def listing(self, next_suggestions=None):
        self.things, prev, next, bcount, acount = self.get_items()

        self.next_suggestions = next_suggestions
        self._max_num = max(acount, bcount)
        self.after = None
        self.before = None

        if self.nextprev and self.prev_link and prev and bcount > 1:
            p = request.GET.copy()
            p.update({'after':None, 'before':prev._fullname, 'count':bcount})
            self.before = prev._fullname
            self.prev = (request.path + utils.query_string(p))
            p_first = request.GET.copy()
            p_first.update({'after':None, 'before':None, 'count':None})
            self.first = (request.path + utils.query_string(p_first))
        if self.nextprev and self.next_link and next:
            p = request.GET.copy()
            p.update({'after':next._fullname, 'before':None, 'count':acount})
            self.after = next._fullname
            self.next = (request.path + utils.query_string(p))

        for count, thing in enumerate(self.things):
            thing.rowstyle = getattr(thing, 'rowstyle', "")
            thing.rowstyle += ' ' + ('even' if (count % 2) else 'odd')

        #TODO: need name for template -- must be better way
        return Wrapped(self)

    def __iter__(self):
        return iter(self.things)

class TableListing(Listing): pass

class ModActionListing(TableListing): pass

class WikiRevisionListing(TableListing): pass

class UserListing(TableListing):
    type = ''
    _class = ''
    title = ''
    form_title = ''
    destination = 'friend'
    has_add_form = True
    headers = None

    def __init__(self,
                 builder,
                 show_jump_to=False,
                 show_not_found=False,
                 jump_to_value=None,
                 addable=True, **kw):
        self.addable = addable
        self.show_not_found = show_not_found
        self.show_jump_to = show_jump_to
        self.jump_to_value = jump_to_value
        TableListing.__init__(self, builder, **kw)

    @property
    def container_name(self):
        return c.site._fullname

class FriendListing(UserListing):
    type = 'friend'

    @property
    def _class(self):
        return '' if not c.user.gold else 'gold-accent rounded'

    @property
    def headers(self):
        if c.user.gold:
            return (_('user'), '', _('note'), _('friendship'), '')

    @property
    def form_title(self):
        return _('add a friend')

    @property
    def container_name(self):
        return c.user._fullname


class EnemyListing(UserListing):
    type = 'enemy'
    has_add_form = False

    @property
    def title(self):
        return _('blocked users')

    @property
    def container_name(self):
        return c.user._fullname

class BannedListing(UserListing):
    type = 'banned'

    @property
    def form_title(self):
        return _("ban users")

    @property
    def title(self):
        return _("users banned from"
                 " /r/%(subreddit)s") % dict(subreddit=c.site.name)

class WikiBannedListing(BannedListing):
    type = 'wikibanned'

    @property
    def form_title(self):
        return _("ban wiki contibutors")

    @property
    def title(self):
        return _("wiki contibutors banned from"
                 " /r/%(subreddit)s") % dict(subreddit=c.site.name)

class ContributorListing(UserListing):
    type = 'contributor'

    @property
    def title(self):
        return _("approved submitters for"
                 " /r/%(subreddit)s") % dict(subreddit=c.site.name)

    @property
    def form_title(self):
        return _("add approved submitter")

class WikiMayContributeListing(ContributorListing):
    type = 'wikicontributor'

    @property
    def title(self):
        return _("approved wiki contributors"
                 " for /r/%(subreddit)s") % dict(subreddit=c.site.name)

    @property
    def form_title(self):
        return _("add approved wiki contributor")

class InvitedModListing(UserListing):
    type = 'moderator_invite'
    form_title = _('invite moderator')
    remove_self_title = _('you are a moderator of this subreddit. %(action)s')

    def sort_moderators(self, items):
        items = [(item, item.rel.get_permissions()) for item in items]
        for item, permissions in items:
            if permissions is None or permissions.is_superuser():
                yield item
        for item, permissions in items:
            if permissions is not None and not permissions.is_superuser():
                yield item

    def get_items(self, **kw):
        things, prev, next, bcount, acount = UserListing.get_items(self, **kw)
        things = list(self.sort_moderators(things))
        return things, prev, next, bcount, acount

    @property
    def title(self):
        return _("invited moderators for"
                 " %(subreddit)s") % dict(subreddit=c.site.name)

class ModListing(InvitedModListing):
    type = 'moderator'
    form_title = _('force add moderator')

    @property
    def has_add_form(self):
        return c.user_is_admin

    @property
    def can_remove_self(self):
        return c.user_is_loggedin and c.site.is_moderator(c.user)

    @property
    def has_invite(self):
        return c.user_is_loggedin and c.site.is_moderator_invite(c.user)

    @property
    def title(self):
        return _("moderators of /r/%(subreddit)s") % dict(subreddit=c.site.name)

class LinkListing(Listing):
    def __init__(self, *a, **kw):
        Listing.__init__(self, *a, **kw)

        self.show_nums = kw.get('show_nums', False)

class NestedListing(Listing):
    def __init__(self, *a, **kw):
        Listing.__init__(self, *a, **kw)

        self.num = kw.get('num', g.num_comments)
        self.parent_name = kw.get('parent_name')

    def listing(self):
        ##TODO use the local builder with the render cache. this may
        ##require separating the builder's get_items and tree-building
        ##functionality
        wrapped_items = self.get_items()

        self.things = wrapped_items

        #make into a tree thing
        return Wrapped(self)

SpotlightTuple = namedtuple('SpotlightTuple',
                            ['link', 'is_promo', 'campaign', 'weight'])

class SpotlightListing(Listing):
    # class used in Javascript to manage these objects
    _js_cls = "OrganicListing"

    def __init__(self, *a, **kw):
        self.nextprev   = False
        self.show_nums  = True
        self._parent_max_num   = kw.get('max_num', 0)
        self._parent_max_score = kw.get('max_score', 0)
        self.compress_display = c.user_is_loggedin and c.user.pref_compress
        self.interestbar = kw.get('interestbar')
        self.interestbar_prob = kw.get('interestbar_prob', 0.)
        self.show_promo = kw.get('show_promo', False)
        srnames = kw.get('srnames', [])
        self.srnames = '+'.join([srname if srname else Frontpage.name
                                 for srname in srnames])
        self.navigable = kw.get('navigable', True)
        self.things = kw.get('organic_links', [])
        self.show_placeholder = isinstance(c.site, (DefaultSR, AllSR))

    def get_items(self):
        from r2.lib.template_helpers import replace_render
        things = self.things
        for t in things:
            if not hasattr(t, "render_replaced"):
                t.render = replace_render(self, t, t.render)
                t.render_replaced = True
        return things, None, None, 0, 0

    def listing(self):
        res = Listing.listing(self)
        for t in res.things:
            t.num = ""
        return Wrapped(self)
