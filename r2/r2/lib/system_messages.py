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

from pylons import request
from pylons.i18n import _, N_

from r2.models import Account, Message
from r2.lib.db import queries
from r2.lib.utils import blockquote_text


user_added_messages = {
    "moderator": {
        "pm": {
            "subject": N_("you are a moderator"),
            "msg": N_("you have been added as a moderator to [%(title)s](%(url)s)."),
        },
    },
    "moderator_invite": {
        "pm": {
            "subject": N_("invitation to moderate %(url)s"),
            "msg": N_("**gadzooks! you are invited to become a moderator of [%(title)s](%(url)s)!**\n\n"
                      "*to accept*, visit the [moderators page for %(url)s](%(url)s/about/moderators) and click \"accept\".\n\n"
                      "*otherwise,* if you did not expect to receive this, you can simply ignore this invitation or report it."),
        },
        "modmail": {
            "subject": N_("moderator invited"),
            "msg": N_("%(user)s has been invited by %(author)s to moderate %(url)s."),
        },
    },
    "accept_moderator_invite": {
        "modmail": {
            "subject": N_("moderator added"),
            "msg": N_("%(user)s has accepted an invitation to become moderator of %(url)s."),
        },
    },
    "contributor": {
        "pm": {
            "subject": N_("you are an approved submitter"),
            "msg": N_("you have been added as an approved submitter to [%(title)s](%(url)s)."),
        },
    },
    "wikicontributor": {
        "pm": {
            "subject": N_("you are a wiki contributor"),
            "msg": N_("you have been added as a contributor to [%(title)s](%(url)s)."),
        },
    },
    "traffic": {
        "pm": {
            "subject": N_("you can view traffic on a promoted link"),
            "msg": N_('you have been added to the list of users able to see [traffic for the sponsored link "%(title)s"](%(traffic_url)s).'),
        },
    },
}


def notify_user_added(rel_type, author, user, target):
    msgs = user_added_messages.get(rel_type)
    if not msgs:
        return

    url = target.path.rstrip("/")
    title = "%s: %s" % (url, target.title)
    if rel_type == "wikicontributor":
        title = "%s's wiki" % url
        url += "/wiki"
    d = {
        "url": url,
        "title": title,
        "author": "/u/" + author.name,
        "user": "/u/" + user.name,
    }

    if "pm" in msgs and author != user:
        subject = msgs["pm"]["subject"] % d
        msg = msgs["pm"]["msg"] % d

        if rel_type in ("moderator_invite", "contributor", "wikicontributor"):
            # send the message from the subreddit
            item, inbox_rel = Message._new(author, user, subject, msg, request.ip,
                                           sr=target, from_sr=True)
        else:
            item, inbox_rel = Message._new(author, user, subject, msg, request.ip)

        queries.new_message(item, inbox_rel, update_modmail=False)

    if "modmail" in msgs:
        subject = msgs["modmail"]["subject"] % d
        msg = msgs["modmail"]["msg"] % d

        if rel_type == "moderator_invite":
            modmail_author = Account.system_user()
        else:
            modmail_author = author

        item, inbox_rel = Message._new(modmail_author, target, subject, msg,
                                       request.ip, sr=target)
        queries.new_message(item, inbox_rel)


def send_ban_message(subreddit, mod, user, note=None,
                     days=None, new=True, wiki=False):
    location = "/r/" + subreddit.name
    ban_type = "subreddit"
    if wiki:
        location += "'s wiki"
        ban_type += "'s wiki"
    if days:
        subject = "you've been temporarily banned from %(location)s"
        message = ("you have been temporarily banned from posting to "
            "%(location)s. this ban will last for %(duration)s days.")
    else:
        subject = "you've been banned from %(location)s"
        message = "you have been banned from posting to %(location)s."

    if not new:
        subject = "Your ban from %(location)s has changed"

    subject %= {"location": location}
    message %= {"location": location, "duration": days}

    if note:
        message += "\n\n" + 'note from the moderators:'
        message += "\n\n" + blockquote_text(note)

    message += "\n\n" + ("you can contact the moderators regarding your ban "
        "by replying to this message. **warning**: using other accounts to "
        "circumvent a %(ban_type)s ban is considered a violation of reddit's "
        "[site rules](/rules) and can result in being banned from reddit "
        "entirely." % {"ban_type": ban_type})

    item, inbox_rel = Message._new(mod, user, subject, message, request.ip,
        sr=subreddit, from_sr=True)
    queries.new_message(item, inbox_rel, update_modmail=False)


def send_mod_permission_message(subreddit, changer, mod, oldperms,
                                newperms=None, demod=False):
    data = {
        'srname': "/r/" + subreddit.name,
        'changername': "/u/" + changer.name,
    }
    if demod:
        subject = "you've been demodded from %(srname)s" % data
        message = "you have been demodded from %(srname)s by %(changername)s" % data
        send_from_sr = ('mail', True) in oldperms.iteritems() or oldperms.is_superuser()
    else:
        assert newperms
        oldnegative = [perm for perm, status in oldperms.iteritems() if not status]
        newnegative = [perm for perm, status in newperms.iteritems() if not status]
        oldpositive = [perm for perm, status in oldperms.iteritems() if status]
        newpositive = [perm for perm, status in newperms.iteritems() if status]

        netnegative = [perm for perm in newnegative if perm not in oldnegative]
        netpositive = [perm for perm in newpositive if perm not in oldpositive]

        if oldperms.is_superuser():
            # only can get demoted from here :(
            netnegative = newnegative
            netpositive = []

        # mod used to have mail perms, but now doesn't.
        # might want to be discussed with the rest of the mods
        send_from_sr = 'mail' in netnegative

        subject = "your permissions on %(srname)s have changed" % data
        message = ("%(changername)s has changed your moderator permissions on "
            "%(srname)s. here's a summary of the change in your permissions:\n"
            "\n---" % data)

        if newperms.is_superuser():
            message += '\n\n**you now have full permissions:**\n\n'
            for perm in newperms.info.keys():
                message += ("* %(permission)s: %(description)s\n\n" %
                    dict(permission=newperms.info[perm]['title'],
                         description=newperms.info[perm]['description']))
        else:
            if netnegative != []:
                message += '\n\n**you have lost the following permissions:**\n\n'
                for perm in netnegative:
                    message += ("* %(permission)s: %(description)s\n\n" %
                        dict(permission=newperms.info[perm]['title'],
                             description=newperms.info[perm]['description']))
            if netpositive != []:
                message += '\n\n**you have gained the following permissions:**\n\n'
                for perm in netpositive:
                    message += ("* %(permission)s: %(description)s\n\n" %
                        dict(permission=newperms.info[perm]['title'],
                             description=newperms.info[perm]['description']))

    sr = subreddit if send_from_sr else None
    item, inbox_rel = Message._new(changer, mod, subject, message, request.ip,
                                   sr=sr, from_sr=send_from_sr)
    queries.new_message(item, inbox_rel, update_modmail=send_from_sr)
