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

from r2.lib.export import export

__all__ = [
           #Constants Only, use @export for functions/classes
           ]


_reddit_controllers = {}
_plugin_controllers = {}


@export
def get_controller(name):
    name = name.lower() + 'controller'
    if name in _reddit_controllers:
        return _reddit_controllers[name]
    elif name in _plugin_controllers:
        return _plugin_controllers[name]
    else:
        raise KeyError(name)


@export
def add_controller(controller):
    name = controller.__name__.lower()
    assert name not in _plugin_controllers
    _plugin_controllers[name] = controller
    return controller


@export
def load_controllers():
    from r2.controllers.listingcontroller import ListingController
    from r2.controllers.listingcontroller import HotController
    from r2.controllers.listingcontroller import NewController
    from r2.controllers.listingcontroller import BrowseController
    from r2.controllers.listingcontroller import MessageController
    from r2.controllers.listingcontroller import RedditsController
    from r2.controllers.listingcontroller import ByIDController
    from r2.controllers.listingcontroller import RandomrisingController
    from r2.controllers.listingcontroller import UserController
    from r2.controllers.listingcontroller import CommentsController

    from r2.controllers.listingcontroller import MyredditsController

    from r2.controllers.feedback import FeedbackController
    from r2.controllers.front import FormsController
    from r2.controllers.front import FrontController
    from r2.controllers.health import HealthController
    from r2.controllers.buttons import ButtonsController
    from r2.controllers.captcha import CaptchaController
    from r2.controllers.embed import EmbedController
    from r2.controllers.error import ErrorController
    from r2.controllers.post import PostController
    from r2.controllers.toolbar import ToolbarController
    from r2.controllers.awards import AwardsController
    from r2.controllers.ads import AdsController
    from r2.controllers.usage import UsageController
    from r2.controllers.errorlog import ErrorlogController
    from r2.controllers.promotecontroller import PromoteController
    from r2.controllers.mediaembed import MediaembedController
    from r2.controllers.mediaembed import AdController
    
    from r2.controllers.wiki import WikiController
    from r2.controllers.wiki import WikiApiController

    from r2.controllers.querycontroller import QueryController

    from r2.controllers.api import ApiController
    from r2.controllers.api import ApiminimalController
    from r2.controllers.api_docs import ApidocsController
    from r2.controllers.apiv1 import APIv1Controller
    from r2.controllers.oauth2 import OAuth2FrontendController
    from r2.controllers.oauth2 import OAuth2AccessController
    from r2.controllers.redirect import RedirectController
    from r2.controllers.ipn import IpnController

    controllers = [(name.lower(), obj) for name, obj in locals().iteritems()]
    _reddit_controllers.update(controllers)
