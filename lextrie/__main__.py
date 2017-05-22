import os
import sys
import csv

from lextrie.util import LexTrie

def main():
    args = list(sys.argv)[1:]
    opts = [a for a in args if a.startswith('--')]
    args = [a for a in args if not a.startswith('--')]

    plugin_names = LexTrie.plugin_names()
    if opts:
        for op in opts:
            o = op.lstrip('--')
            if o in plugin_names:
                out_model = LexTrie.from_plugin(o)
                out_filename = '{}_count{{}}'.format(o)
            else:
                print('Option {} is not available'.format(op))
    elif 'lexicoder' in plugin_names:
        out_model = LexTrie.from_plugin('lexicoder')
        out_filename = 'lexicoder_count{}'
    elif plugin_names:
        out_model = LexTrie.from_plugin(plugin_names[0])
        out_filename = '{}_count{{}}'.format(plugin_names[0])
    else:
        sys.exit("No LexTrie plugins could be loaded. Please install one.")

    files = []
    for f in args:
        if not os.path.exists(f):
            print('Could not find file {}'.format(f))
        files.append(f)

    keys = ['FILENAME'] + sorted(out_model.lexicon.keys())
    lex_count = out_model.lex_count
    counts = []
    for f in files:
        with open(f) as infile:
            text = infile.read()
            count = lex_count(text)
        count['FILENAME'] = f
        counts.append(count)

    if files:
        version = 0
        tail = '.csv'
        while os.path.exists(out_filename.format(tail)):
            version += 1
            tail = '_{}.csv'.format(version)

        out_filename = out_filename.format(tail)
        with open(out_filename, 'w') as outfile:
            outcsv = csv.DictWriter(outfile, keys)
            outcsv.writeheader()
            outcsv.writerows(counts)

if __name__ == '__main__':
    if len(sys.argv) <= 1 or (len(sys.argv) == 2 and
                              sys.argv[1].startswith('--')):
        print('Read a list of files, count Lexicon instances, '
              'and generate a CSV.')
        print('Usage: python lextrie.py file_path [file_path ...]')
        print('Options: ')
        for pn in LexTrie.plugin_names():
            print('    --{}'.format(pn))
    else:
        main()
