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

import hashlib

from pylons import g, c, request
from pylons.i18n import _

from r2.lib.emailer import opt_in, opt_out
from r2.lib.pages import BoringPage, LoginPage, OptOut, Over18
from r2.lib.utils import Storage, query_string, UrlParser

import r2.controllers.validator as validator
from r2.controllers.api import ApiController
from r2.controllers.validator import validate

__all__ = [
           #Constants Only, use @export for functions/classes
           ]


class PostController(ApiController):
    def api_wrapper(self, kw):
        return Storage(**kw)

    def set_options(self, all_langs, pref_lang, **kw):
        if c.errors.errors:
            print "fucker"
            return

        if all_langs == 'all':
            langs = 'all'
        elif all_langs == 'some':
            langs = []
            for lang in g.all_languages:
                if request.post.get('lang-' + lang):
                    langs.append(str(lang)) #unicode
            if langs:
                langs.sort()
                langs = tuple(langs)
            else:
                langs = 'all'

        for k, v in kw.iteritems():
            #startswith is important because kw has all sorts of
            #request info in it
            if k.startswith('pref_'):
                setattr(c.user, k, v)

        c.user.pref_content_langs = langs
        c.user.pref_lang = pref_lang
        c.user._commit()


    @validate(pref_lang=validator.VLang('lang'),
              all_langs=validator.VOneOf('all-langs', ('all', 'some'),
                                         default='all'))
    def POST_unlogged_options(self, all_langs, pref_lang):
        self.set_options( all_langs, pref_lang)
        return self.redirect(request.referer)

    @validate(validator.VUser(),
              validator.VModhash(),
              pref_frame=validator.VBoolean('frame'),
              pref_clickgadget=validator.VBoolean('clickgadget'),
              pref_organic=validator.VBoolean('organic'),
              pref_newwindow=validator.VBoolean('newwindow'),
              pref_public_votes=validator.VBoolean('public_votes'),
              pref_hide_from_robots=validator.VBoolean('hide_from_robots'),
              pref_hide_ups=validator.VBoolean('hide_ups'),
              pref_hide_downs=validator.VBoolean('hide_downs'),
              pref_over_18=validator.VBoolean('over_18'),
              pref_research=validator.VBoolean('research'),
              pref_numsites=validator.VInt('numsites', 1, 100),
              pref_lang=validator.VLang('lang'),
              pref_media=validator.VOneOf('media', ('on', 'off', 'subreddit')),
              pref_compress=validator.VBoolean('compress'),
              pref_min_link_score=validator.VInt('min_link_score', -100, 100),
              pref_min_comment_score=validator.VInt('min_comment_score',
                                                    -100, 100),
              pref_num_comments=validator.VInt('num_comments', 1,
                                               g.max_comments,
                                               default=g.num_comments),
              pref_show_stylesheets=validator.VBoolean('show_stylesheets'),
              pref_show_flair=validator.VBoolean('show_flair'),
              pref_show_link_flair=validator.VBoolean('show_link_flair'),
              pref_no_profanity=validator.VBoolean('no_profanity'),
              pref_label_nsfw=validator.VBoolean('label_nsfw'),
              pref_show_promote=validator.VBoolean('show_promote'),
              pref_mark_messages_read=validator.VBoolean("mark_messages_read"),
              pref_threaded_messages=validator.VBoolean("threaded_messages"),
              pref_collapse_read_messages=
                  validator.VBoolean("collapse_read_messages"),
              pref_private_feeds=validator.VBoolean("private_feeds"),
              pref_local_js=validator.VBoolean('local_js'),
              pref_show_adbox=validator.VBoolean("show_adbox"),
              pref_show_sponsors=validator.VBoolean("show_sponsors"),
              pref_show_sponsorships=validator.VBoolean("show_sponsorships"),
              pref_highlight_new_comments=
                  validator.VBoolean("highlight_new_comments"),
              all_langs=validator.VOneOf('all-langs', ('all', 'some'),
                                         default='all'))
    def POST_options(self, all_langs, pref_lang, **kw):
        #temporary. eventually we'll change pref_clickgadget to an
        #integer preference
        kw['pref_clickgadget'] = kw['pref_clickgadget'] and 5 or 0
        if c.user.pref_show_promote is None:
            kw['pref_show_promote'] = None
        elif not kw.get('pref_show_promote'):
            kw['pref_show_promote'] = False

        if not kw.get("pref_over_18") or not c.user.pref_over_18:
            kw['pref_no_profanity'] = True

        if kw.get("pref_no_profanity") or c.user.pref_no_profanity:
            kw['pref_label_nsfw'] = True

        if not c.user.gold:
            kw['pref_show_adbox'] = True
            kw['pref_show_sponsors'] = True
            kw['pref_show_sponsorships'] = True

        self.set_options(all_langs, pref_lang, **kw)
        u = UrlParser(c.site.path + "prefs")
        u.update_query(done = 'true')
        if c.cname:
            u.put_in_frame()
        return self.redirect(u.unparse())

    def GET_over18(self):
        return BoringPage(_("over 18?"),
                          content = Over18()).render()

    @validate(validator.VModhash(fatal=False),
              over18=validator.nop('over18'),
              dest=validator.VDestination(default = '/'))
    def POST_over18(self, over18, dest):
        if over18 == 'yes':
            if c.user_is_loggedin and not c.errors:
                c.user.pref_over_18 = True
                c.user._commit()
            else:
                ip_hash = hashlib.sha1(request.ip).hexdigest()
                domain = g.domain if not c.frameless_cname else None
                c.cookies.add('over18', ip_hash,
                              domain = domain)
            return self.redirect(dest)
        else:
            return self.redirect('/')


    @validate(msg_hash=validator.nop('x'))
    def POST_optout(self, msg_hash):
        email, sent = opt_out(msg_hash)
        if not email:
            return self.abort404()
        return BoringPage(_("opt out"),
                          content = OptOut(email = email, leave = True,
                                           sent = True,
                                           msg_hash = msg_hash)).render()

    @validate(msg_hash=validator.nop('x'))
    def POST_optin(self, msg_hash):
        email, sent = opt_in(msg_hash)
        if not email:
            return self.abort404()
        return BoringPage(_("welcome back"),
                          content = OptOut(email = email, leave = False,
                                           sent = True,
                                           msg_hash = msg_hash)).render()


    @validate(dest=validator.VDestination(default = "/"))
    def POST_login(self, dest, *a, **kw):
        ApiController._handle_login(self, *a, **kw)
        c.render_style = "html"
        c.response_content_type = ""

        if c.errors:
            return LoginPage(user_login = request.post.get('user'),
                             dest = dest).render()

        return self.redirect(dest)

    @validate(dest=validator.VDestination(default = "/"))
    def POST_reg(self, dest, *a, **kw):
        ApiController._handle_register(self, *a, **kw)
        c.render_style = "html"
        c.response_content_type = ""

        if c.errors:
            return LoginPage(user_reg = request.post.get('user'),
                             dest = dest).render()

        return self.redirect(dest)

    def GET_login(self, *a, **kw):
        return self.redirect('/login' + query_string(dict(dest="/")))

