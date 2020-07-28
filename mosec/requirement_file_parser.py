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
import re
import sys
import os
from operator import le, lt, gt, ge, eq, ne
from mosec import pipfile
from mosec import requirements
from mosec import setup_file
from pkg_resources._vendor.packaging.version import parse as version_parser

PYTHON_MARKER_REGEX = re.compile(r'python_version\s*(?P<operator>==|<=|=>|>|<)\s*[\'"](?P<python_version>.+?)[\'"]')
SYSTEM_MARKER_REGEX = re.compile(r'sys_platform\s*==\s*[\'"](.+)[\'"]')


def satisfies_python_version(parsed_operator, py_version_str):
    operator_func = {
        ">": gt,
        "==": eq,
        "<": lt,
        "<=": le,
        ">=": ge,
        '!=': ne,
    }[parsed_operator]
    system_py_version = version_parser("{}.{}.{}".format(sys.version_info[0], sys.version_info[1], sys.version_info[2]))
    required_py_version = version_parser(py_version_str)
    return operator_func(system_py_version, required_py_version)


def get_markers_text(requirement):
    if isinstance(requirement, pipfile.PipfileRequirement):
        return requirement.markers
    return requirement.line


def matches_python_version(requirement):
    """Filter out requirements that should not be installed
    in this Python version.
    See: https://www.python.org/dev/peps/pep-0508/#environment-markers
    """
    markers_text = get_markers_text(requirement)
    if not (markers_text and re.match(".*;.*python_version", markers_text)):
        return True

    cond_text = markers_text.split(";", 1)[1]

    # Gloss over the 'and' case and return true on the first matching python version

    for sub_exp in re.split("\s*(?:and|or)\s*", cond_text):
        match = PYTHON_MARKER_REGEX.search(sub_exp)

        if match:
            match_dict = match.groupdict()

            if len(match_dict) == 2 and satisfies_python_version(
                    match_dict['operator'],
                    match_dict['python_version']
            ):
                return True

    return False


def matches_environment(requirement):
    """Filter out requirements that should not be installed
    in this environment. Only sys_platform is inspected right now.
    This should be expanded to include other environment markers.
    See: https://www.python.org/dev/peps/pep-0508/#environment-markers
    """
    sys_platform = sys.platform.lower()
    markers_text = get_markers_text(requirement)
    if markers_text and 'sys_platform' in markers_text:
        match = SYSTEM_MARKER_REGEX.findall(markers_text)
        if len(match) > 0:
            return match[0].lower() == sys_platform
    return True


def is_testable(requirement):
    return not requirement.editable and requirement.vcs is None


def get_requirements_list(requirements_file_path):
    if os.path.basename(requirements_file_path) == 'Pipfile':
        with open(requirements_file_path, 'r', encoding='utf-8') as f:
            requirements_data = f.read()
        parsed_reqs = pipfile.parse(requirements_data)
        req_list = list(parsed_reqs.get('packages', []))
    elif os.path.basename(requirements_file_path) == 'setup.py':
        with open(requirements_file_path, 'r') as f:
            setup_py_file_content = f.read()
        requirements_data = setup_file.parse_requirements(setup_py_file_content)
        req_list = list(requirements.parse(requirements_data))
    else:
        # assume this is a requirements.txt formatted file
        # Note: requirements.txt files are unicode and can be in any encoding.
        with open(requirements_file_path, 'r') as f:
            req_list = list(requirements.parse(f))

    req_list = filter(matches_environment, req_list)
    req_list = filter(is_testable, req_list)
    req_list = filter(matches_python_version, req_list)
    req_list = [r for r in req_list if r.name]
    return req_list
