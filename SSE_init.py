import os
import os.path
import re
import json
import io
import sys, locale
import math
import sys
import nltk
from indexer import SSE_Indexer

indexer = SSE_Indexer()
# index documents
indexer.index_files()
# indexer.append_index("./Reuters/17980.html")
indexer.compute_idf()
indexer.compute_doc_len()
# store index, idf, and doc_len
indexer.store_default()
