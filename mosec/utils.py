"""
Copyright 2017 Snyk Ltd.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import sys
import re
from importlib import import_module


def canonicalize_dist_name(name):
    # https://packaging.python.org/guides/distributing-packages-using-setuptools/#name
    name = name.lower().replace('-', '.').replace('_', '.')
    name = re.sub(r'\.+', '.', name)
    return name


def guess_version(pkg_key, default='?'):
    """Guess the version of a pkg when pip doesn't provide it
    :param str pkg_key: key of the package
    :param str default: default version to return if unable to find
    :returns: version
    :rtype: string
    """
    try:
        m = import_module(pkg_key)
    except ImportError:
        return default
    else:
        return getattr(m, '__version__', default)


def is_string(obj):
    """Check whether an object is a string"""
    if sys.version_info < (3,):
        # Python 2.x only
        return isinstance(obj, basestring)
    else:
        return isinstance(obj, str)
