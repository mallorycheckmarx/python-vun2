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

from pycassa.system_manager import ASCII_TYPE

from r2.lib.db import tdb_cassandra
from r2.lib.memoize import memoize

__all__ = [
           #Constants
           #Classes
           "AccountsActiveBySR",
           #Exceptions
           #Functions
           ]


#NOTE: this file exists to contain classes that might create a circular
#dependency between account.py and subreddit.py

class AccountsActiveBySR(tdb_cassandra.View):
    _use_db = True
    _connection_pool = 'main'
    _ttl = 15*60

    _extra_schema_creation_args = dict(key_validation_class=ASCII_TYPE)

    _read_consistency_level  = tdb_cassandra.CL.ONE
    _write_consistency_level = tdb_cassandra.CL.ANY

    @classmethod
    def touch(cls, account, sr):
        cls._set_values(sr._id36,
                        {account._id36: ''})

    @classmethod
    def get_count(cls, sr, cached=True):
        return cls.get_count_cached(sr._id36, _update=not cached)

    @classmethod
    @memoize('accounts_active', time=60)
    def get_count_cached(cls, sr_id):
        return cls._cf.get_count(sr_id)
