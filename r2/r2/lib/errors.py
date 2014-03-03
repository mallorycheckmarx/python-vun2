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

from webob.exc import HTTPBadRequest, HTTPForbidden, status_map
from r2.lib.utils import Storage, tup
from pylons import request
from pylons.i18n import _
from copy import copy


error_list = dict((
        ('USER_REQUIRED', _("Please login to do that.")),
        ('HTTPS_REQUIRED', _("This page must be accessed using HTTPS.")),
        ('WRONG_DOMAIN', _("You can't do that on this domain.")),
        ('VERIFIED_USER_REQUIRED', _("You need to set a valid email address to do that.")),
        ('NO_URL', _('A url is required.')),
        ('BAD_URL', _('You should check that url.')),
        ('INVALID_SCHEME', _('URI scheme must be one of: %(schemes)s')),
        ('BAD_CAPTCHA', _('Care to try these again?')),
        ('BAD_USERNAME', _('Invalid username.')),
        ('USERNAME_TAKEN', _('That username is already taken.')),
        ('USERNAME_TAKEN_DEL', _('That username is taken by a deleted account.')),
        ('USER_BLOCKED', _("You can't send to a user that you have blocked.")),
        ('NO_THING_ID', _('id not specified.')),
        ('TOO_MANY_THING_IDS', _('You provided too many ids.')),
        ('NOT_AUTHOR', _("You can't do that.")),
        ('NOT_USER', _("You are not logged in as that user.")),
        ('LOGGED_IN', _("You are already logged in.")),
        ('DELETED_LINK', _('The link you are commenting on has been deleted.')),
        ('DELETED_COMMENT', _('That comment has been deleted.')),
        ('DELETED_THING', _('That element has been deleted.')),
        ('BAD_PASSWORD', _('That password is unacceptable.')),
        ('WRONG_PASSWORD', _('Invalid password.')),
        ('BAD_PASSWORD_MATCH', _('Passwords do not match.')),
        ('NO_NAME', _('Please enter a name.')),
        ('NO_EMAIL', _('Please enter an email address.')),
        ('NO_EMAIL_FOR_USER', _('No email address for that user.')),
        ('NO_VERIFIED_EMAIL', _('No verified email address for that user.')),
        ('NO_TO_ADDRESS', _('Send it to whom?')),
        ('NO_SUBJECT', _('Please enter a subject.')),
        ('USER_DOESNT_EXIST', _("That user doesn't exist.")),
        ('NO_USER', _('Please enter a username.')),
        ('INVALID_PREF', "That preference isn't valid."),
        ('BAD_NUMBER', _("That number isn't in the right range (%(range)s).")),
        ('BAD_STRING', _("You used a character here that we can't handle.")),
        ('BAD_BID', _("Your budget must be at least $%(min)d and no more than $%(max)d.")),
        ('ALREADY_SUB', _("That link has already been submitted.")),
        ('SUBREDDIT_EXISTS', _('That subreddit already exists.')),
        ('SUBREDDIT_NOEXIST', _('That subreddit doesn\'t exist.')),
        ('SUBREDDIT_NOTALLOWED', _("You aren't allowed to post there.")),
        ('SUBREDDIT_REQUIRED', _('You must specify a subreddit.')),
        ('BAD_SR_NAME', _('That name isn\'t going to work.')),
        ('RATELIMIT', _('You are doing that too much. Try again in %(time)s.')),
        ('QUOTA_FILLED', _("You've submitted too many links recently. Please try again in an hour.")),
        ('SUBREDDIT_RATELIMIT', _("You are doing that too much. Try again later.")),
        ('EXPIRED', _('Your session has expired.')),
        ('DRACONIAN', _('You must accept the terms first.')),
        ('BANNED_IP', "IP banned"),
        ('BAD_CNAME', "That domain isn't going to work."),
        ('USED_CNAME', "That domain is already in use."),
        ('INVALID_OPTION', _('That option is invalid.')),
        ('BAD_EMAILS', _('The following emails are invalid: %(emails)s.')),
        ('NO_EMAILS', _('Please enter at least one email address.')),
        ('TOO_MANY_EMAILS', _('Please only share to %(num)s emails at a time.')),
        ('OVERSOLD', _('That subreddit has already been oversold on %(start)s to %(end)s. Please pick another subreddit or date.')),
        ('OVERSOLD_DETAIL', _("We have insufficient inventory to fulfill your requested budget, target, and dates. Only %(available)s impressions available on %(target)s from %(start)s to %(end)s.")),
        ('BAD_DATE', _('Please provide a date in the form mm/dd/yyyy.')),
        ('BAD_DATE_RANGE', _('The dates need to be in order and not identical.')),
        ('DATE_RANGE_TOO_LARGE', _('You must choose a date range of less than %(days)s days.')),
        ('DATE_TOO_LATE', _('Please enter a date %(day)s or earlier.')),
        ('DATE_TOO_EARLY', _('Please enter a date %(day)s or later.')),
        ('BAD_ADDRESS', _('Address problem: %(message)s')),
        ('BAD_CARD', _('Card problem: %(message)s')),
        ('TOO_LONG', _("This is too long (max: %(max_length)s)")),
        ('NO_TEXT', _('We need something here.')),
        ('INVALID_CODE', _("We've never seen that code before.")),
        ('CLAIMED_CODE', _("That code has already been claimed -- perhaps by you?")),
        ('NO_SELFS', _("That subreddit doesn't allow text posts")),
        ('NO_LINKS', _("That subreddit only allows text posts")),
        ('TOO_OLD', _("That's a piece of history now; it's too late to reply to it")),
        ('BAD_CSS_NAME', _('Invalid CSS name.')),
        ('BAD_CSS', _('Invalid CSS.')),
        ('BAD_REVISION', _('Invalid revision ID.')),
        ('TOO_MUCH_FLAIR_CSS', _('Too many flair CSS classes.')),
        ('BAD_FLAIR_TARGET', _('Not a valid flair target.')),
        ('OAUTH2_INVALID_CLIENT', _('Invalid client id.')),
        ('OAUTH2_INVALID_REDIRECT_URI', _('Invalid redirect_uri parameter.')),
        ('OAUTH2_INVALID_SCOPE', _('Invalid scope requested.')),
        ('OAUTH2_INVALID_REFRESH_TOKEN', _('Invalid refresh token.')),
        ('OAUTH2_ACCESS_DENIED', _('Access denied by the user.')),
        ('CONFIRM', _("Please confirm the form.")),
        ('CONFLICT', _("Conflict error while saving.")),
        ('NO_API', _('Cannot perform this action via the API.')),
        ('DOMAIN_BANNED', _('%(domain)s is not allowed on reddit: %(reason)s')),
        ('NO_OTP_SECRET', _('You must enable two-factor authentication.')),
        ('BAD_IMAGE', _('There\'s a problem with the image.')),
        ('DEVELOPER_ALREADY_ADDED', _('Already added.')),
        ('TOO_MANY_DEVELOPERS', _('Too many developers.')),
        ('BAD_HASH', _("I don't believe you.")),
        ('ALREADY_MODERATOR', _('That user is already a moderator.')),
        ('NO_INVITE_FOUND', _('There is no pending invite for that subreddit.')),
        ('BID_LIVE', _('You cannot edit the budget of a live ad.')),
        ('TOO_MANY_CAMPAIGNS', _('You have too many campaigns for that promotion.')),
        ('BAD_JSONP_CALLBACK', _('That jsonp callback contains invalid characters.')),
        ('INVALID_PERMISSION_TYPE', _("Permissions don't apply to that type of user.")),
        ('INVALID_PERMISSIONS', _('Invalid permissions string.')),
        ('BAD_MULTI_PATH', _('Invalid multi path.')),
        ('BAD_MULTI_NAME', _('%(reason)s')),
        ('MULTI_NOT_FOUND', _('That multireddit doesn\'t exist.')),
        ('MULTI_EXISTS', _('That multireddit already exists.')),
        ('MULTI_CANNOT_EDIT', _('You can\'t change that multireddit.')),
        ('MULTI_TOO_MANY_SUBREDDITS', _('No more space for subreddits in that multireddit.')),
        ('MULTI_SPECIAL_SUBREDDIT', _("Can't add special subreddit %(path)s.")),
        ('JSON_PARSE_ERROR', _('Unable to parse JSON data.')),
        ('JSON_INVALID', _('Unexpected JSON structure.')),
        ('JSON_MISSING_KEY', _('JSON missing key: "%(key)s".')),
        ('NO_CHANGE_KIND', _("Can't change post type.")),
        ('INVALID_LOCATION', _("Invalid location.")),
        ('BANNED_FROM_SUBREDDIT', _('That user is banned from the subreddit.')),
    ))

errors = Storage([(e, e) for e in error_list.keys()])


def add_error_codes(new_codes):
    """Add error codes to the error enumeration.

    It is assumed that the incoming messages are marked for translation but not
    yet translated, so they can be declared before pylons.i18n is ready.

    """
    for code, message in new_codes.iteritems():
        error_list[code] = _(message)
        errors[code] = code


class RedditError(Exception):
    name = None
    fields = None
    code = None

    def __init__(self, name=None, msg_params=None, fields=None, code=None):
        Exception.__init__(self)

        if name is not None:
            self.name = name

        self.i18n_message = error_list.get(self.name)
        self.msg_params = msg_params or {}

        if fields is not None:
            # list of fields in the original form that caused the error
            self.fields = tup(fields)

        if code is not None:
            self.code = code

    @property
    def message(self):
        return _(self.i18n_message) % self.msg_params

    def __iter__(self):
        yield ('name', self.name)
        yield ('message', _(self.message))

    def __repr__(self):
        return '<RedditError: %s>' % self.name

    def __str__(self):
        return repr(self)


class ErrorSet(object):
    def __init__(self):
        self.errors = {}

    def __contains__(self, pair):
        """Expects an (error_name, field_name) tuple and checks to
        see if it's in the errors list."""
        return self.errors.has_key(pair)

    def get(self, name, default=None):
        return self.errors.get(name, default)

    def __getitem__(self, name):
        return self.errors[name]

    def __repr__(self):
        return "<ErrorSet %s>" % list(self)

    def __iter__(self):
        for x in self.errors:
            yield x

    def __len__(self):
        return len(self.errors)

    def add(self, error_name, msg_params=None, field=None, code=None):
        for field_name in tup(field):
            e = RedditError(error_name, msg_params, fields=field_name,
                            code=code)
            self.add_error(e)

    def add_error(self, error):
        for field_name in tup(error.fields):
            self.errors[(error.name, field_name)] = error

    def remove(self, pair):
        """Expects an (error_name, field_name) tuple and removes it
        from the errors list."""
        if self.errors.has_key(pair):
            del self.errors[pair]


class ForbiddenError(HTTPForbidden):
    def __init__(self, error_name):
        HTTPForbidden.__init__(self)
        self.explanation = error_list[error_name]


class BadRequestError(HTTPBadRequest):
    def __init__(self, error_name):
        HTTPBadRequest.__init__(self)
        self.error_data = {
            'reason': error_name,
            'explanation': error_list[error_name],
        }


def reddit_http_error(code=400, error_name='UNKNOWN_ERROR', **data):
    exc = status_map[code]()

    data['reason'] = exc.explanation = error_name
    if 'explanation' not in data and error_name in error_list:
        data['explanation'] = exc.explanation = error_list[error_name]

    # omit 'fields' json attribute if it is empty
    if 'fields' in data and not data['fields']:
        del data['fields']

    exc.error_data = data
    return exc


class UserRequiredException(RedditError):
    name = errors.USER_REQUIRED
    code = 403


class VerifiedUserRequiredException(RedditError):
    name = errors.VERIFIED_USER_REQUIRED
    code = 403


class MessageError(Exception): pass
