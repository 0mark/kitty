#!/usr/bin/env python
# vim:fileencoding=utf-8
# License: GPL v3 Copyright: 2018, Kovid Goyal <kovid at kovidgoyal.net>

import os
import re
from collections import namedtuple

from .rgb import to_color as as_color
from .utils import log_error

key_pat = re.compile(r'([a-zA-Z][a-zA-Z0-9_-]*)\s+(.+)$')


def to_color(x):
    return as_color(x, validate=True)


def positive_int(x):
    return max(0, int(x))


def positive_float(x):
    return max(0, float(x))


def unit_float(x):
    return max(0, min(float(x), 1))


def to_bool(x):
    return x.lower() in 'y yes true'.split()


def parse_line(line, type_map, special_handling, ans, all_keys, base_path_for_includes):
    line = line.strip()
    if not line or line.startswith('#'):
        return
    m = key_pat.match(line)
    if m is not None:
        key, val = m.groups()
        if special_handling(key, val, ans):
            return
        if key == 'include':
            val = val.strip()
            if not os.path.isabs(val):
                val = os.path.join(base_path_for_includes, val)
            try:
                with open(val, encoding='utf-8', errors='replace') as include:
                    _parse(include, type_map, special_handling, ans, all_keys)
            except FileNotFoundError:
                log_error('Could not find included config file: {}, ignoring'.format(val))
            except EnvironmentError:
                log_error('Could not read from included config file: {}, ignoring'.format(val))
            return
        if all_keys is not None and key not in all_keys:
            log_error('Ignoring unknown config key: {}'.format(key))
            return
        tm = type_map.get(key)
        if tm is not None:
            val = tm(val)
        ans[key] = val


def _parse(lines, type_map, special_handling, ans, all_keys):
    name = getattr(lines, 'name', None)
    if name:
        base_path_for_includes = os.path.dirname(os.path.abspath(name))
    else:
        from .constants import config_dir
        base_path_for_includes = config_dir
    for line in lines:
        parse_line(line, type_map, special_handling, ans, all_keys, base_path_for_includes)


def parse_config_base(
    lines, defaults, type_map, special_handling, ans, check_keys=True
):
    all_keys = defaults._asdict() if check_keys else None
    _parse(lines, type_map, special_handling, ans, all_keys)


def init_config(defaults_path, parse_config):
    with open(defaults_path, encoding='utf-8', errors='replace') as f:
        defaults = parse_config(f, check_keys=False)
    Options = namedtuple('Defaults', ','.join(defaults.keys()))
    defaults = Options(**defaults)
    return Options, defaults
