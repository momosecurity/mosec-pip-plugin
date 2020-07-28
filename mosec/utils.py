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
