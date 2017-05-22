import json
import os
from collections import namedtuple

from pkg_resources import resource_string, resource_listdir

_lex_files = [r for r in resource_listdir('lextrie._lexica', '')
              if r.endswith('.json')]
_lex_plugins = [json.loads(resource_string('lextrie._lexica', _lf))['tag_map']
                for _lf in _lex_files]
_lex_names = [os.path.splitext(_lf)[0] for _lf in _lex_files]

_PluginTuple = namedtuple('PluginTuple', _lex_names)

plugins = _PluginTuple(*_lex_plugins)

del _lex_files, _lex_plugins, _lex_names, _PluginTuple
