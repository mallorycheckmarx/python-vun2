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

import importlib
import os
import re
import sys

cwd = os.getcwd()
if os.path.split(cwd)[1] != "r2" or not os.path.isdir(os.path.join(cwd, "r2")):
   print "Must be run from reddit/r2 directory"
   sys.exit(1)


is_python = re.compile(".+\\.py$")
exclusions = [
              "r2.lib.c",
              "r2.tests",
              "r2.public",
              "r2.orig",
              "r2.templates",
              ]

def excluded_module(module):
    for ex in exclusions:
        if module.startswith(ex):
            return True
    return False

def module_name(package_heirarchy):
    return '.'.join(package_heirarchy)

def import_one(module):
    if not excluded_module(module):
        print "Importing %s" % module
        importlib.import_module(module)

def import_tree(path, curr_module):
    import_one(module_name(curr_module))

    for filename in os.listdir(path):
        curr_path = os.path.join(path, filename)
        if os.path.isdir(curr_path):
            import_tree(curr_path, curr_module + [filename])
        elif os.path.isfile(curr_path) and is_python.match(filename):
            if filename != "__init__.py":
                import_one(module_name(curr_module + [filename.split(".")[0]]))


import_tree(os.path.join(cwd, "r2"), ["r2"])
