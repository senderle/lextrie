import sys
from lextrie import main, LexTrie

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
