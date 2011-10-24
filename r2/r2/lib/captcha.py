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
# The Original Code is Reddit.
#
# The Original Developer is the Initial Developer.  The Initial Developer of the
# Original Code is CondeNet, Inc.
#
# All portions of the code written by CondeNet are Copyright (c) 2006-2010
# CondeNet, Inc. All Rights Reserved.
################################################################################
from recaptcha.client import captcha

def get_captcha_html(public_key, use_ssl=False):
    return captcha.displayhtml(public_key, use_ssl=use_ssl)

def validate_captcha(challenge, response, ip, private_key):
    response = captcha.submit(challenge, response, private_key, ip)
    return response.is_valid and response.error_code == None

def bool_validate_captcha(captcha):
    if captcha != None:
        if not validate_captcha(captcha[0], captcha[1], captcha[2], captcha[3]):
            return False
    return True
