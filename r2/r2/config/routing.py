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

"""
Setup your Routes options here
"""
import admin_routes
from routes import Mapper
from pylons import config

def make_map():
    mapper = Mapper()
    connect = mapper.connect

    for plugin in config['r2.plugins']:
        plugin.add_routes(connect)

    connect('/admin/', controller='awards')

    connect('/login', controller='forms', action='login')
    connect('/register', controller='forms', action='register')
    connect('/logout', controller='forms', action='logout')
    connect('/verify', controller='forms', action='verify')
    connect('/adminon', controller='forms', action='adminon')
    connect('/adminoff', controller='forms', action='adminoff')
    connect('/submit', controller='front', action='submit')
    connect('/validuser', controller='forms', action='validuser')

    connect('/over18', controller='post', action='over18')

    connect('/search', controller='front', action='search')

    connect('/rules', controller='front', action='rules')
    connect('/sup', controller='front', action='sup')
    connect('/traffic', controller='front', action='site_traffic')
    connect('/traffic/languages/:langcode', controller='front', action='lang_traffic', langcode='')
    connect('/traffic/adverts/:code', controller='front', action='advert_traffic', code='')
    connect('/account-activity', controller='front', action='account_activity')

    connect('/about/message/:where', controller='message', action='listing')
    connect('/about/log', controller='front', action='moderationlog')
    connect('/about', controller='front', action='about')
    connect('/about/:location', controller='front', action='editreddit',
       location='about')

    connect('/reddits/create', controller='front', action='newreddit')
    connect('/reddits/search', controller='front', action='search_reddits')
    connect('/reddits/login', controller='forms', action='login')
    connect('/reddits/:where', controller='reddits', action='listing',
       where='popular', requirements=dict(where="popular|new|banned"))

    connect('/reddits/mine/:where', controller='myreddits', action='listing',
       where='subscriber',
       requirements=dict(where='subscriber|contributor|moderator'))

    connect('/buttons', controller='buttons', action='button_demo_page')

    #/button.js and buttonlite.js - the embeds
    connect('/button', controller='buttons', action='button_embed')
    connect('/buttonlite', controller='buttons', action='button_lite')

    connect('/widget', controller='buttons', action='widget_demo_page')
    connect('/bookmarklets', controller='buttons', action='bookmarklets')

    connect('/awards', controller='front', action='awards')

    connect('/i18n', controller='redirect', action='redirect',
            dest='http://www.reddit.com/r/i18n')
    connect('/feedback', controller='feedback', action='feedback')
    connect('/ad_inq', controller='feedback', action='ad_inq')

    connect('/admin/usage', controller='usage')

    # Used for editing ads
    connect('/admin/ads', controller='ads')
    connect('/admin/ads/:adcn/:action', controller='ads',
            requirements=dict(action="assign|srs"))

    connect('/admin/awards', controller='awards')
    connect('/admin/awards/:awardcn/:action', controller='awards',
            requirements=dict(action="give|winners"))

    connect('/admin/errors', controller='errorlog')

    connect('/user/:username/about', controller='user', action='about',
       where='overview')
    connect('/user/:username/:where', controller='user', action='listing',
       where='overview')
    connect('/u/:username', controller='redirect', action='user_redirect')

    # preserve timereddit URLs from 4/1/2012
    connect('/t/:timereddit', controller='redirect',
            action='timereddit_redirect')
    connect('/t/:timereddit/*rest', controller='redirect',
            action='timereddit_redirect')

    connect('/prefs/:location', controller='forms', action='prefs',
            location='options')

    connect('/depmod', controller='forms', action='depmod')

    connect('/info/0:article/*rest', controller='front',
            action='oldinfo', dest='comments', type='ancient')
    connect('/info/:article/:dest/:comment', controller='front',
            action='oldinfo', type='old', dest='comments', comment=None)

    connect('/related/:article/:title', controller='front',
            action='related', title=None)
    connect('/details/:article/:title', controller='front',
            action='details', title=None)
    connect('/traffic/:article/:title', controller='front',
            action='traffic', title=None)
    connect('/comments/:article/:title/:comment', controller='front',
            action='comments', title=None, comment=None)
    connect('/duplicates/:article/:title', controller='front',
            action='duplicates', title=None)

    connect('/mail/optout', controller='forms', action='optout')
    connect('/mail/optin', controller='forms', action='optin')
    connect('/stylesheet', controller='front', action='stylesheet')
    connect('/frame', controller='front', action='frame')
    connect('/framebuster/:blah', controller='front', action='framebuster')
    connect('/framebuster/:what/:blah',
            controller='front', action='framebuster')

    connect('/promoted/edit_promo/:link',
            controller='promote', action='edit_promo')
    connect('/promoted/pay/:link/:indx',
            controller='promote', action='pay')
    connect('/promoted/graph',
            controller='promote', action='graph')
    connect('/promoted/:action', controller='promote',
            requirements=dict(action="edit_promo|new_promo|roadblock"))
    connect('/promoted/:sort', controller='promote', action="listing")
    connect('/promoted/', controller='promoted', action="listing", sort="")

    connect('/health', controller='health', action='health')

    connect('/', controller='hot', action='listing')

    listing_controllers = "hot|new|randomrising|comments"

    connect('/:controller', action='listing',
            requirements=dict(controller=listing_controllers))
    connect('/saved', controller='user', action='saved_redirect')

    connect('/by_id/:names', controller='byId', action='listing')

    connect('/:sort', controller='browse', sort='top', action='listing',
            requirements=dict(sort='top|controversial'))

    connect('/message/compose', controller='message', action='compose')
    connect('/message/messages/:mid', controller='message', action='listing',
            where="messages")
    connect('/message/:where', controller='message', action='listing')
    connect('/message/moderator/:subwhere', controller='message',
            action='listing', where='moderator')

    connect('/thanks', controller='forms', action="thanks", secret='')
    connect('/thanks/:secret', controller='forms', action="thanks")

    connect('/gold', controller='forms', action="gold")

    connect('/password', controller='forms', action="password")
    connect('/:action', controller='front',
            requirements=dict(action="random|framebuster|selfserviceoatmeal"))
    connect('/:action', controller='embed',
            requirements=dict(action="help|blog|faq"))
    connect('/help/*anything', controller='embed', action='help')

    connect('/goto', controller='toolbar', action='goto')
    connect('/tb/:id', controller='toolbar', action='tb')
    connect('/toolbar/:action', controller='toolbar',
            requirements=dict(action="toolbar|inner|login"))
    connect('/toolbar/comments/:id', controller='toolbar', action='comments')

    connect('/c/:comment_id', controller='front', action='comment_by_id')

    connect('/s/*rest', controller='toolbar', action='s')
    # additional toolbar-related rules just above the catchall

    connect('/d/:what', controller='api', action='bookmarklet')

    connect('/resetpassword/:key', controller='forms', action='resetpassword')
    connect('/verification/:key', controller='forms', action='verify_email')
    connect('/resetpassword', controller='forms', action='resetpassword')

    connect('/post/:action/:url_user', controller='post',
            requirements=dict(action="login|reg"))
    connect('/post/:action', controller='post',
            requirements=dict(action="options|over18|unlogged_options|optout"
                              "|optin|login|reg"))

    connect('/api', controller='redirect', action='redirect', dest='/dev/api')
    connect('/api/distinguish/:how', controller='api', action="distinguish")
    # wherever this is, google has to agree.
    connect('/api/gcheckout', controller='ipn', action='gcheckout')
    connect('/api/spendcreddits', controller='ipn', action="spendcreddits")
    connect('/api/ipn/:secret', controller='ipn', action='ipn')
    connect('/ipn/:secret', controller='ipn', action='ipn')
    connect('/api/:action/:url_user', controller='api',
            requirements=dict(action="login|register"))
    connect('/api/gadget/click/:ids', controller='api', action='gadget',
       type='click')
    connect('/api/gadget/:type', controller='api', action='gadget')
    connect('/api/:action', controller='promote',
       requirements=dict(action=("promote|unpromote|edit_promo|link_thumb|"
                                 "freebie|promote_note|update_pay|refund|"
                                 "traffic_viewer|rm_traffic_viewer|"
                                 "edit_campaign|delete_campaign|meta_promo|"
                                 "add_roadblock|rm_roadblock")))
    connect('/api/:action', controller='apiminimal',
            requirements=dict(action="new_captcha"))
    connect('/api/:action', controller='api')

    connect("/api/v1/:action", controller="oauth2frontend",
            requirements=dict(action="authorize"))
    connect("/api/v1/:action", controller="oauth2access",
            requirements=dict(action="access_token"))
    connect("/api/v1/:action", controller="apiv1")

    connect('/dev', controller='redirect', action='redirect', dest='/dev/api')
    connect('/dev/api', controller='apidocs', action='docs')

    connect("/button_info", controller="api", action="info", limit=1)

    connect('/captcha/:iden', controller='captcha', action='captchaimg')

    connect('/mediaembed/:link', controller="mediaembed", action="mediaembed")

    connect('/doquery', controller='query', action='doquery')

    connect('/store', controller='redirect', action='redirect',
       dest='http://store.reddit.com/index.html')

    connect('/code', controller='redirect', action='redirect',
            dest='http://github.com/reddit/')

    connect('/socialite', controller='redirect', action='redirect',
            dest='https://addons.mozilla.org/firefox/addon/socialite/')

    connect('/mobile', controller='redirect', action='redirect',
            dest='http://m.reddit.com/')

    connect('/authorize_embed', controller='front', action='authorize_embed')

    # Used for showing ads
    connect("/ads/", controller="ad", action="ad")
    connect("/ads/r/:reddit_name/:keyword", controller="ad", action="ad",
            keyword=None)
    connect("/ads/:codename", controller="ad", action="ad_by_codename")

    connect("/try", controller="forms", action="try_compact")

    # This route handles displaying the error page and
    # graphics used in the 404/500
    # error pages. It should likely stay at the top
    # to ensure that the error page is
    # displayed properly.
    connect('/error/document/:id', controller='error', action="document")

    # these should be near the buttom, because they should only kick
    # in if everything else fails. It's the attempted catch-all
    # reddit.com/http://... and reddit.com/34fr, but these redirect to
    # the less-guessy versions at /s/ and /tb/
    connect('/:linkoid', controller='toolbar', action='linkoid',
            requirements=dict(linkoid='[0-9a-z]{1,6}'))
    connect('/:urloid', controller='toolbar', action='urloid',
            requirements=dict(urloid=r'(\w+\.\w{2,}|https?).*'))

    connect("/*url", controller='front', action='catchall')

    return mapper
