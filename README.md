# lextrie

This package efficiently tags words in a text with labels based on 
a range of different predefined lexica, loaded using a simple
JSON-based plugin architecture. 

It comes with the [Bing sentiment analysis lexicon][bing] preloaded.

Currently, it uses a Trie written in vanilla Python. For faster
processing, a cython-based implementation is forthcoming.

[bing]: https://www.cs.uic.edu/~liub/FBS/sentiment-analysis.html
