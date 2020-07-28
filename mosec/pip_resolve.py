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
import logging
import sys
import os
import argparse
import json
import ssl
import urllib.error
import urllib.request
from operator import attrgetter
from mosec import mosec_log_helper
from mosec import setup_file
from mosec import utils
from mosec.requirement_file_parser import get_requirements_list
from mosec.requirement_dist import ReqDist

try:
    import pkg_resources
except ImportError:
    # try using the version vendored by pip
    try:
        import pip._vendor.pkg_resources as pkg_resources
    except ImportError:
        raise ImportError(
            "Could not import pkg_resources; please install setuptools or pip.")

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict


log = mosec_log_helper.Logger(name="mosec")


def create_deps_tree(
        dist_tree,
        top_level_requirements,
        req_file_path,
        allow_missing=False,
        only_provenance=False
):
    """Create dist dependencies tree
    :param dict  dist_tree: the installed dists tree
    :param list  top_level_requirements: list of required dists
    :param str   req_file_path: path to the dependencies file (e.g. requirements.txt)
    :param bool  allow_missing: ignore uninstalled dependencies
    :param bool  only_provenance: only care provenance dependencies
    :rtype: dict
    """
    DEPENDENCIES = 'dependencies'
    VERSION = 'version'
    NAME = 'name'
    DIR_VERSION = '1.0.0'
    FROM = 'from'

    tree = OrderedDict(
        sorted(
            [(k, sorted(v, key=attrgetter('key'))) for k, v in dist_tree.items()]
            , key=lambda kv: kv[0].key
        )
    )
    nodes = tree.keys()
    key_tree = dict((k.key, v) for k, v in tree.items())

    top_level_req_lower_names = [p.name.lower() for p in top_level_requirements]
    top_level_req_dists = [p for p in nodes if p.key in top_level_req_lower_names]

    def _create_children_recursive(root_package, ancestors):
        root_name = root_package[NAME]
        if root_name.lower() not in key_tree:
            msg = 'Required packages missing: ' + root_name
            if allow_missing:
                log.error(msg)
                return
            else:
                sys.exit(msg)

        ancestors = ancestors.copy()
        ancestors.add(root_name.lower())
        children_dists = key_tree[root_name.lower()]
        for child_dist in children_dists:
            if child_dist.key in ancestors:
                continue

            child_node = _create_tree_node(child_dist, root_package)
            _create_children_recursive(child_node, ancestors)
            root_package[DEPENDENCIES][child_node[NAME]] = child_node
        return root_package

    def _create_root():
        name, version = None, None
        if os.path.basename(req_file_path) == 'setup.py':
            with open(req_file_path, "r") as setup_py_file:
                name, version = setup_file.parse_name_and_version(setup_py_file.read())

        root = {
            NAME: name or os.path.basename(os.path.dirname(os.path.abspath(req_file_path))),
            VERSION: version or DIR_VERSION,
            DEPENDENCIES: {}
        }
        root[FROM] = [root[NAME] + '@' + root[VERSION]]
        return root

    def _create_tree_node(dist_node, parent):
        version = dist_node.version
        if isinstance(version, tuple):
            version = '.'.join(map(str, version))
        return {
            NAME: dist_node.project_name,
            VERSION: version,
            FROM: parent[FROM] + [dist_node.project_name + '@' + version],
            DEPENDENCIES: {}
        }

    tree_root = _create_root()
    for dist in top_level_req_dists:
        tree_node = _create_tree_node(dist, tree_root)
        if only_provenance:
            tree_root[DEPENDENCIES][tree_node[NAME]] = tree_node
        else:
            tree_root[DEPENDENCIES][tree_node[NAME]] = _create_children_recursive(tree_node, set([]))
    return tree_root


def create_dependencies_tree_by_req_file(
        requirements_file,
        allow_missing=False,
        only_provenance=False
):
    """Create dist dependencies tree from file
    :param str   requirements_file: path to the dependencies file (e.g. requirements.txt)
    :param bool  allow_missing: ignore uninstalled dependencies
    :param bool  only_provenance: only care provenance dependencies
    :rtype: dict
    """

    # get all installed package distribution object list
    dists = list(pkg_resources.working_set)
    dists_dict = dict((p.key, p) for p in dists)
    dists_tree = dict((p, [ReqDist(r, dists_dict.get(r.key)) for r in p.requires()]) for p in dists_dict.values())

    required = get_requirements_list(requirements_file)
    installed = [utils.canonicalize_dist_name(d) for d in dists_dict]
    top_level_requirements = []
    missing_package_names = []
    for r in required:
        if utils.canonicalize_dist_name(r.name) not in installed:
            missing_package_names.append(r.name)
        else:
            top_level_requirements.append(r)
    if missing_package_names:
        msg = 'Required packages missing: ' + (', '.join(missing_package_names))
        if allow_missing:
            log.error(msg)
        else:
            sys.exit(msg)

    return create_deps_tree(
        dists_tree, top_level_requirements, requirements_file, allow_missing, only_provenance)


def render_response(response_json):

    def _print_single_vuln(vuln):
        log.error("✗ {} severity vulnerability ({} - {}) found on {}@{}".format(
            vuln.get('severity'),
            vuln.get('title', ''),
            vuln.get('cve', ''),
            vuln.get('packageName'),
            vuln.get('version'))
        )
        if vuln.get('from', None):
            from_arr = vuln.get('from')
            from_str = ""
            for _from in from_arr:
                from_str += _from + " > "
            from_str = from_str[:-3]
            print("- from: {}".format(from_str))
        if vuln.get('target_version', []):
            log.info("! Fix version {}".format(vuln.get('target_version')))
        print("")

    if response_json.get('ok', False):
        log.info("✓ Tested {} dependencies for known vulnerabilities, no vulnerable paths found."
                 .format(response_json.get('dependencyCount', 0)))
    elif response_json.get('vulnerabilities', None):
        vulns = response_json.get('vulnerabilities')
        for vuln in vulns:
            _print_single_vuln(vuln)

        log.warn("Tested {} dependencies for known vulnerabilities, found {} vulnerable paths."
                 .format(response_json.get('dependencyCount', 0), len(vulns)))


def run(args):
    deps_tree = create_dependencies_tree_by_req_file(
        args.requirements,
        allow_missing=args.allow_missing,
        only_provenance=args.only_provenance,
    )

    deps_tree['severityLevel'] = args.level
    deps_tree['type'] = 'pip'
    deps_tree['language'] = 'python'

    log.debug(json.dumps(deps_tree, indent=2))

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(
        method='POST',
        url=args.endpoint,
        headers={
            'Content-Type': 'application/json'
        },
        data=bytes(json.dumps(deps_tree).encode('utf-8'))
    )
    try:
        response = urllib.request.urlopen(req, timeout=15, context=ctx)
        response_json = json.loads(response.read().decode('utf-8'))
        render_response(response_json)

        if not response_json.get('ok', False):
            return 1
    except urllib.error.HTTPError as e:
        raise Exception("Network Error: {}".format(e))
    except json.JSONDecodeError as e:
        raise Exception("API return data format error.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("requirements",
                        help="依赖文件 (requirements.txt 或 Pipfile)")
    parser.add_argument("--endpoint",
                        action="store",
                        required=True,
                        help="上报API")
    parser.add_argument("--allow-missing",
                        action="store_true",
                        help="忽略未安装的依赖")
    parser.add_argument("--only-provenance",
                        action="store_true",
                        help="仅检查直接依赖")
    parser.add_argument("--level",
                        action="store",
                        default="High",
                        help="威胁等级 [High|Medium|Low]. default: High")
    parser.add_argument("--no-except",
                        action="store_true",
                        default=False,
                        help="发现漏洞不抛出异常")
    parser.add_argument("--debug",
                        action="store_true",
                        default=False)
    args = parser.parse_args()

    if args.debug:
        log.set_log_level(logging.DEBUG)

    status = run(args)
    if status == 1 and not args.no_except:
        raise BaseException("Found Vulnerable!")
