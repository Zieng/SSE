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
		for d in self.indexer.doc_len:
			score[d] = 0
		# queryTermList = self.indexer.handle_query(query)
		queryTermList = self.indexer.tokenize(query)
		for term in queryTermList:
			postingList = self.indexer.indexTable.get(term,None)
			if postingList is None:
				continue
			for posting in postingList:
				doc = posting['doc']
				if doc not in relatedDoc:
					relatedDoc.append(doc)
				tf = posting['tf']
				weight = (1+math.log10(tf)) * self.indexer.idf_table[term]
				score[doc] += weight

		for doc in relatedDoc:
			score[doc] = score[doc] / self.indexer.doc_len[doc]

		return sorted(score.iteritems(), key=lambda d:d[1], reverse = True)[0:k]



# test
if __name__ == '__main__':
	SQ = SSE_Query( SSE_Indexer() )
	while True:
		query = raw_input("input a test query:")
		cos = SQ.cosine_score(query)
		print(cos)