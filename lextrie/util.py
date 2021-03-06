import re
import os
import pkg_resources
import shutil

from collections import defaultdict, Counter
from lextrie._lexica import plugins

_lexica_dir = pkg_resources.resource_filename('lextrie', '_lexica')

def load_lex(filename):
    with open(filename) as f:
        lines = f.readlines()

    lex_map = defaultdict(set)
    for l in lines:
        _n, stem, tag, _x = l.strip().split('\t')
        stem = stem.strip()

        # For simplicity we remove a few oddly formatted
        # entries that appear in certain dictionaries.
        stem_main = re.sub(r'[(][^)]*[)]', '', stem)
        if '(' in stem or ')' in stem:
            # ignore emoji
            continue
        lex_map[tag].add(stem_main)

    return {k: sorted(v) for k, v in lex_map.items()}

def make_trie(words, tags):
    root = {}
    for w, tag in zip(words, tags):
        node = root
        for c in w[:-1]:
            if c not in node:
                node[c] = {}
            node = node[c]

        last_c = w[-1]
        if last_c == '*':
            if '*' not in node:
                node['*'] = []
            node['*'].append(tag)
        else:
            if last_c not in node:
                node[last_c] = {}
            node = node[last_c]
            if '~' not in node:
                node['~'] = []
            node['~'].append(tag)

    return root

class LexTrie(object):
    _plugins = plugins._asdict()

    def __init__(self, lexicon):
        """
        Create a new LexTrie object from a lexicon in the tag_map
        format. Most of the time, users will want to use a pre-installed
        plugin; to create an instance of LexTrie based on a plugin, use
        the `from_plugin` method.
        """
        if isinstance(lexicon, str) and os.path.exists(lexicon):
            self.lexicon = load_lex(lexicon)
        else:
            self.lexicon = lexicon

        self._words_tags = [(stem, tag)
                            for tag, stems in self.lexicon.items()
                            for stem in stems]
        self.trie = make_trie(*zip(*self._words_tags))

    @classmethod
    def install_plugin(cls, plugin_path):
        """
        Copy a plugin into the plugin directory. If a plugin by the
        same name exists, raise a ValueError. If the user doesn't have the
        necessary permissions, this will fail, most likely with a
        PermissionError.
        """
        plugin_loc, plugin_name = os.path.split(plugin_path)
        if os.path.exists(os.path.join(_lexica_dir, plugin_name)):
            msg = ('Plugin {} already exists! '
                   'Use LexTrie.disable_plugin({}) to remove it.')
            raise ValueError(msg.format(plugin_name, plugin_name))
        else:
            shutil.copy(plugin_path, _lexica_dir)

    @classmethod
    def disable_plugin(cls, plugin_name):
        """
        Disable a plugin that has already been installed by
        appending '.disabled' to its filename. This does not delete the
        plugin. However, if the plugin being disabled has the same name
        as a plugin that was previously disabled, the previously
        disabled plugin will be deleted. If the user doesn't have the
        necessary permissions, this will fail, most likely with a
        PermissionError.
        """
        if not plugin_name.endswith('.json'):
            plugin_name = plugin_name + '.json'

        if not os.path.isfile(os.path.join(_lexica_dir, plugin_name)):
            msg = 'No plugin by the name {} exists.'
            raise ValueError(msg.format(plugin_name))
        else:
            moved_name = plugin_name + '.disabled'
            if os.path.isfile(os.path.join(_lexica_dir, moved_name)):
                os.remove(os.path.join(_lexica_dir, moved_name))
            shutil.move(os.path.join(_lexica_dir, plugin_name),
                        os.path.join(_lexica_dir, moved_name))

    @classmethod
    def enable_plugin(cls, plugin_name):
        """
        Re-enable a plugin that has previously been disabled
        by removing '.disabled' from its filename. If no plugin by
        the name has been removed, or if a plugin by the same name
        has already been reinstalled, raise a ValueError. If the user
        doesn't have the necessary permissions, this will fail, most
        likely with a PermissionError.
        """
        if not plugin_name.endswith('.json'):
            plugin_name = plugin_name + '.json'

        removed_plugin_name = plugin_name + '.disabled'
        if not os.path.isfile(os.path.join(_lexica_dir, removed_plugin_name)):
            msg = 'No plugin by the name {} has been disabled.'
            raise ValueError(msg.format(plugin_name))
        elif os.path.isfile(os.path.join(_lexica_dir, plugin_name)):
            msg = 'A plugin by the name {} has already been reinstalled.'
            raise ValueError(msg.format(plugin_name))
        else:
            shutil.move(os.path.join(_lexica_dir, removed_plugin_name),
                        os.path.join(_lexica_dir, plugin_name))

    @classmethod
    def copy_plugin(cls, plugin_name, out_path):
        """
        Copy the current version of the plugin to a specified output
        path. If no plugin by the name exists, or if a plugin by the
        same name exists at the specified output location, raise a
        ValueError. If the user doesn't have the necessary permissions,
        this will fail, most likely with a PermissionError.

        """
        if not plugin_name.endswith('.json'):
            plugin_name = plugin_name + '.json'

        if os.path.isdir(out_path):
            out_path = os.path.join(out_path, plugin_name)

        if not os.path.isfile(os.path.join(_lexica_dir, plugin_name)):
            msg = 'No plugin by the name {} exists.'
            raise ValueError(msg.format(plugin_name))
        elif os.path.exists(out_path):
            msg = 'A file by the name {} already exists.'
            raise ValueError(msg.format(out_path))
        else:
            shutil.copy(os.path.join(_lexica_dir, plugin_name),
                        out_path)

    @classmethod
    def from_plugin(cls, plugin_name):
        return cls(getattr(plugins, plugin_name))

    @classmethod
    def plugin_names(cls):
        return sorted(cls._plugins.keys())

    def get_lex_tags(self, word):
        """Return all the tags from the lexicon for a single word."""
        word = word + '~'
        root = self.trie
        for c in word:
            if c in root:
                root = root[c]
            elif '*' in root:
                return root['*']
            else:
                return []
        return root

    def lexify(self, text, key, window_size=500):
        words = text.lower().split()
        blocks = [words[n:n + window_size]
                  for n in range(0, len(words), window_size)]
        tags = [[tag for word in block
                 for tag in self.get_lex_tags(word) if tag == key]
                for block in blocks]

        return [len(tagblock) for tagblock in tags]

    def lextrans(self, text, join=True):
        words = text.lower().split()
        return ['|'.join(self.get_lex_tags(w)) for w in words]

    def lex_count(self, text):
        words = text.lower().split()
        return Counter(tag
                       for word in words
                       for tag in self.get_lex_tags(word))

def burrows_delta(A, B):
    return sum(abs(a - b) for a, b in zip(A, B))

def burrows_delta_l1(A, B):
    A_norm = sum(abs(a) for a in A)
    B_norm = sum(abs(b) for b in B)
    A = [a / A_norm for a in A]
    B = [b / B_norm for b in B]
    return burrows_delta(A, B)

def cosine_similarity(A, B):
    return (sum(a * b for a, b in zip(A, B)) /
            (sum(a * a for a in A) * sum(b * b for b in B)) ** 0.5
            )

def delta_max(A, B, tags=None):
    if tags is None:
        tags = range(len(A))
    return tags[max(range(len(A)), key=lambda i: abs(A[i] - B[i]))]

def delta_sort(A, B, tags=None):
    if tags is None:
        tags = range(len(A))
    return [tags[i] for i in
            sorted(range(len(A)), key=lambda i: abs(A[i] - B[i]))]
