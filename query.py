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

class SSE_Query(object):
	"""docstring for SSE_Query"""
	def __init__(self, indexer):
		super(SSE_Query, self).__init__()
		self.indexer = indexer
		self.indexer.load_default()
		
	def cosine_score(self, query, k=5):
		score = {}
		relatedDoc = []
		queryTermList = self.indexer.handle_query(query)
		for term in queryTermList:
			postingList = self.indexer.indexTable[term]
			for posting in postingList:
				doc = posting['doc']
				relatedDoc.append(doc)
				tf = posting['tf']
				weight = (1+math.log10(tf)) * self.indexer.idf[term]
				score[doc] += weight
		for doc in relatedDoc:
			score[doc] = score[doc] / self.indexer.doc_len[doc]
		return sorted(score.iteritems(), key=lambda d:d[1], reverse = True)[0:k]
