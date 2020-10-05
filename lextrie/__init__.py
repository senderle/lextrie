from lextrie.util import LexTrie
import os
import sys
import csv

def print_usage():
    print('Read a list of files, count Lexicon instances, '
          'and generate a CSV.')
    print('Usage: python lextrie.py file_path [file_path ...]')
    print('Options: ')
    for pn in LexTrie.plugin_names():
        print('    --{}'.format(pn))

def parse_args():
    parser = argparse.ArgumentParser(description='A lexicon-based word tagger.')
    subparsers = parser.add_subparsers(help='tag, install_plugin, disable_plugin, enable_plugin, copy_plugin')

    #sub-parsers
    tag_parser = subparsers.add_parser('tag', help='Tag one or more files.')
    group = scrape_parser.add_mutually_exclusive_group()
    group.add_argument('-s', '--search', action='store', help="search term to search for a tag to scrape")
    group.add_argument('-t', '--tag', action='store', help="the tag to be scraped")
    group.add_argument('-u', '--url', action='store', help="the full URL of first page to be scraped")
    scrape_parser.add_argument('-o', '--out', action='store', default=os.path.join('.','scraped-html'), help="target directory for scraped html files")
    scrape_parser.add_argument('-p', '--startpage', action='store', default=1, type=int, help="page on which to begin downloading (to resume a previous job)")
    scrape_parser.set_defaults(func=scrape)

    clean_parser = subparsers.add_parser('clean', help='takes a directory of html files and yields a new directory of text files')
    clean_parser.add_argument('input', action='store', help='directory of input html files to clean')
    clean_parser.add_argument('-o', '--output', action='store', default='plain-text', help='target directory for output txt files')
    clean_parser.set_defaults(func=convert_dir)

    meta_parser = subparsers.add_parser('getmeta', help='takes a directory of html files and yields a csv file containing metadata')
    meta_parser.add_argument('input', action='store', help='directory of input html files to process')
    meta_parser.add_argument('-o', '--output', action='store', default='fan-meta', help='filename for metadata csv file')
    meta_parser.set_defaults(func=collect_meta)

    validate_parser = subparsers.add_parser('validate', help='validate script markup')
    validate_parser.add_argument('script', action='store', help='filename for markup version of script')
    validate_parser.set_defaults(func=search.validate_cmd)

    # Search for reuse
    search_parser = subparsers.add_parser('search', help='compare fanworks with the original script')
    search_parser.add_argument('fan_works', action='store', help='directory of fanwork text files')
    search_parser.add_argument('script', action='store', help='filename for markup version of script')
    search_parser.add_argument('-n', '--num-works', default=-1, type=int, help="number of works to search (for subsampling)")
    search_parser.add_argument('-s', '--skip-works', default=0, type=int, help="number of works to skip (for subsampling)")
    search_parser.set_defaults(func=search.analyze)



def main():
    if len(sys.argv) <= 1 or (len(sys.argv) == 2 and
                              sys.argv[1].startswith('--')):
        print_usage()
    else:
        args = list(sys.argv)[1:]
        if args[0] in ['install_plugin', 'disable_plugin',
                       'enable_plugin', 'copy_plugin']:
            if len(args) == 1:
                print_usage()
            else:
                getattr(LexTrie, args[0])(*args[1:])
        else:
            main_args = [a for a in args if not a.startswith('--')]
            opts = [a for a in args if a.startswith('--')]
            default_cmd(main_args, opts)

def default_cmd(args, opts):
    plugin_names = LexTrie.plugin_names()
    if opts:
        for op in opts:
            o = op.lstrip('--')
            if o in plugin_names:
                out_model = LexTrie.from_plugin(o)
                out_filename = '{}_count{{}}'.format(o)
            else:
                print('Option {} is not available'.format(op))
    elif 'bing' in plugin_names:
        out_model = LexTrie.from_plugin('bing')
        out_filename = 'bing_count{}'
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
