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

from pylons import c

from r2.lib.db.thing import Thing
from r2.lib.export import export
from r2.lib.strings import Score
from r2.lib.utils import tup
from r2.lib.wrapped import Wrapped
from r2.models import (#Classes
                       IDBuilder,
                       LinkListing,
                       Link,
                       PromotedLink,
                       #Functions
                       make_wrapper,
                       )
__all__ = [
           #Constants Only, use @export for functions/classes
           ]


# formerly ListingController.builder_wrapper
@export
def default_thing_wrapper(**params):
    def _default_thing_wrapper(thing):
        w = Wrapped(thing)
        style = params.get('style', c.render_style)
        if isinstance(thing, Link):
            if thing.promoted is not None:
                w.render_class = PromotedLink
                w.rowstyle = 'promoted link'
            elif style == 'htmllite':
                w.score_fmt = Score.points
        return w
    params['parent_wrapper'] = _default_thing_wrapper
    return make_wrapper(**params)


@export
def wrap_links(links, wrapper=default_thing_wrapper(),
               listing_cls=LinkListing, 
               num=None, show_nums=False, nextprev=False,
               num_margin=None, mid_margin=None, **kw):
    links = tup(links)
    if not all(isinstance(x, str) for x in links):
        links = [x._fullname for x in links]
    b = IDBuilder(links, num=num, wrap=wrapper, **kw)
    l = listing_cls(b, nextprev=nextprev, show_nums=show_nums)
    if num_margin is not None:
        l.num_margin = num_margin
    if mid_margin is not None:
        l.mid_margin = mid_margin
    return l.listing()


