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
# All portions of the code written by reddit are Copyright (c) 2006-2013 reddit
# Inc. All Rights Reserved.
###############################################################################

from __future__ import with_statement

from r2.models import *
from r2.models.wiki import ImagesByWikiPage
from r2.lib.utils import sanitize_url, strip_www, randstr
from r2.lib.strings import string_dict
from r2.lib.pages.things import wrap_links

from pylons import g, c
from pylons.i18n import _
from mako import filters

import os
import tempfile

from r2.lib.media import upload_media

import re
from urlparse import urlparse

import tinycss
from tinycss import tokenizer
from tinycss.css21 import Stylesheet

msgs = string_dict['css_validator_messages']

class ValidationReport(object):
    def __init__(self, original_text=''):
        self.errors        = []
        self.original_text = original_text.split('\n') if original_text else ''

    def __str__(self):
        "only for debugging"
        return "Report:\n" + '\n'.join(['\t' + str(x) for x in self.errors])

    def append(self,error):
        if hasattr(error,'line'):
            error.offending_line = self.original_text[error.line-1]
        self.errors.append(error)

class ValidationError(Exception):
    def __init__(self, message, obj=None):
        self.message = message
        if hasattr(obj, 'line'):
            self.line = obj.line

    def __cmp__(self, other):
        return cmp(getattr(self, 'line', 0), getattr(other, 'line', 0))

    def __repr__(self):
        return "ValidationError%s: [%s] (%s)" % (self.line, self.message)


# substitutable urls will be css-valid labels surrounded by "%%"
custom_img_urls = re.compile(r'%%([a-zA-Z0-9\-]+)%%')
def valid_url(rule, report, generate_https_urls):
    """Validate a URL in the stylesheet.

    The only valid URLs for use in a stylesheet are the custom image format
    (%%example%%) which this function will translate to actual URLs.

    """
    url = rule.value

    m = custom_img_urls.match(url)
    if m:
        name = m.group(1)

        # this relies on localcache to not be doing a lot of lookups
        images = ImagesByWikiPage.get_images(c.site, "config/stylesheet")

        if name in images:
            if not generate_https_urls:
                url = images[name]
            else:
                url = g.media_provider.convert_to_https(images[name])
            rule._as_css = 'url(%s)' % url
        else:
            # unknown image label -> error
            report.append(ValidationError(msgs['broken_url']
                                          % dict(brokenurl = rule.as_css()),
                                          rule))
    else:
        report.append(ValidationError(msgs["custom_images_only"], rule))

class CSSParser(tinycss.CSSPage3Parser):
    def parse_stylesheet(self, css_unicode):
        flat = tokenizer.tokenize_flat(css_unicode)
        tokens = tokenizer.regroup(flat)
        rules, errors = self.parse_rules(tokens, context='stylesheet')
        return Stylesheet(rules, errors, None), flat

only_whitespace = re.compile('\A\s*\Z')
def validate_css(string, generate_https_urls):
    if not string or only_whitespace.match(string):
        return ('',ValidationReport())

    report = ValidationReport(string)

    # avoid a very expensive parse
    max_size_kb = 100;
    if len(string) > max_size_kb * 1024:
        report.append(ValidationError((msgs['too_big']
                                       % dict (max_size = max_size_kb))))
        return ('', report)

    parser = tinycss.make_parser(CSSParser)

    parsed, flat = parser.parse_stylesheet(string)

    for error in parsed.errors:
        report.append(ValidationError(error.reason, error))

    # Iterate over top level rules to find import declarations
    for rule in parsed.rules:
        if rule.at_keyword == '@import':
            report.append(ValidationError(_('@import is not allowed'), rule))

    # Iterate over flat unparsed css tokens to find URIs
    for rule in flat:
        if rule.type == 'URI':
            valid_url(rule, report, generate_https_urls)

    stylesheet = ''.join(r.as_css() for r in flat) if not report.errors else ''
    return stylesheet, report

def find_preview_comments(sr):
    from r2.lib.db.queries import get_sr_comments, get_all_comments

    comments = get_sr_comments(sr)
    comments = list(comments)
    if not comments:
        comments = get_all_comments()
        comments = list(comments)

    return Thing._by_fullname(comments[:25], data=True, return_dict=False)

def find_preview_links(sr):
    from r2.lib.normalized_hot import normalized_hot

    # try to find a link to use, otherwise give up and return
    links = normalized_hot([sr._id])
    if not links:
        links = normalized_hot(Subreddit.default_subreddits())

    if links:
        links = links[:25]
        links = Link._by_fullname(links, data=True, return_dict=False)

    return links

def rendered_link(links, media, compress, stickied=False):
    with c.user.safe_set_attr:
        c.user.pref_compress = compress
        c.user.pref_media    = media
    links = wrap_links(links, show_nums = True, num = 1)
    for wrapped in links:
        wrapped.stickied = stickied
    delattr(c.user, 'pref_compress')
    delattr(c.user, 'pref_media') 
    return links.render(style = "html")

def rendered_comment(comments):
    return wrap_links(comments, num = 1).render(style = "html")

class BadImage(Exception):
    def __init__(self, error = None):
        self.error = error

def save_sr_image(sr, data, suffix = '.png'):
    try:
        return upload_media(data, file_type = suffix)
    except Exception as e:
        raise BadImage(e)

