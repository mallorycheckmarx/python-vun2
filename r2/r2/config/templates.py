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

import r2.lib.jsontemplates as jtmpl
from r2.lib.manager import tp_manager

tpm = tp_manager.tp_manager()

def api(type, cls):
    tpm.add_handler(type, 'api', cls())
    tpm.add_handler(type, 'api-html', cls())
    tpm.add_handler(type, 'api-compact', cls())

# blanket fallback rule
api('templated', jtmpl.NullJsonTemplate)

# class specific overrides
api('link',          jtmpl.LinkJsonTemplate)
api('promotedlink',  jtmpl.PromotedLinkJsonTemplate)
api('comment',       jtmpl.CommentJsonTemplate)
api('message',       jtmpl.MessageJsonTemplate)
api('subreddit',     jtmpl.SubredditJsonTemplate)
api('morerecursion', jtmpl.MoreCommentJsonTemplate)
api('morechildren',  jtmpl.MoreCommentJsonTemplate)
api('reddit',        jtmpl.RedditJsonTemplate)
api('panestack',     jtmpl.PanestackJsonTemplate)
api('listing',       jtmpl.ListingJsonTemplate)
api('modlist',       jtmpl.UserListJsonTemplate)
api('userlist',      jtmpl.UserListJsonTemplate)
api('contributorlist', jtmpl.UserListJsonTemplate)
api('bannedlist',    jtmpl.UserListJsonTemplate)
api('friendlist',    jtmpl.UserListJsonTemplate)
api('usertableitem', jtmpl.UserTableItemJsonTemplate)
api('account',       jtmpl.AccountJsonTemplate)

api('organiclisting',       jtmpl.OrganicListingJsonTemplate)
api('subreddittraffic', jtmpl.TrafficJsonTemplate)
api('takedownpane', jtmpl.TakedownJsonTemplate)

api('wikibasepage', jtmpl.WikiJsonTemplate)
api('wikipagerevisions', jtmpl.WikiJsonTemplate)
api('wikiview', jtmpl.WikiViewJsonTemplate)
api('wikirevision', jtmpl.WikiRevisionJsonTemplate)

api('flairlist', jtmpl.FlairListJsonTemplate)
api('flaircsv', jtmpl.FlairCsvJsonTemplate)

api('subredditstylesheet', jtmpl.StylesheetTemplate)
api('createsubreddit', jtmpl.SubredditSettingsTemplate)

tpm.add_handler('usertableitem', 'api-html', jtmpl.UserItemHTMLJsonTemplate())
