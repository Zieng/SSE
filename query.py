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
		self.keyword=re.compile("AND|OR")

	@staticmethod
	def AND_operation(score1, score2):
		result_score={}
		for i in score1.keys():
			if i in score2.keys():
				result_score[i]=min(score1[i],score2[i])
		return result_score

	@staticmethod
	def OR_operation(score1, score2):
		result_score=score1
		for i in score2.keys():
			if i in result_score.keys():
				result_score[i]=max(result_score[i],score2[i])
			else:
				result_score[i]=score2[i]
		return result_score

	@staticmethod
	def build_dict(score_list):
		score_dict={}
		if(isinstance(score_list,list)!=True):
			print("build_dict_type_error: ", type(score_list))
			return
		else:
			pos=0
			while(pos<len(score_list)):
				score_dict[score_list[pos][0]]=score_list[pos][1]
				pos=pos+1
		return score_dict

	def fastCosineScore(self, query, k=5):
		score = {}
		relatedDoc = []
		for d in self.indexer.doc_len:
			score[int(d)] = 0   # json doesn't allowed integer key
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
			score[doc] = score[doc] / self.indexer.doc_len[str(doc)] # json doesn't allowed integer key

		return sorted(score.iteritems(), key=lambda d:d[1], reverse = True)[0:k]

	def query(self,query_clause,k=5):
		start_pos=0;
		or_set=[]
		and_set=["",""]
		and_flag=False
		for i in self.keyword.finditer(query_clause):
			if(and_flag):
				sub_query_clause=query_clause[start_pos:i.start()]
				result_list=self.fastCosineScore(sub_query_clause,100)
				and_set[0]=SSE_Query.AND_operation(and_set[0],SSE_Query.build_dict(result_list))
				and_flag=False
			else:
				sub_query_clause=query_clause[start_pos:i.start()]
				result_list=self.fastCosineScore(sub_query_clause,100)
				and_set[0]=SSE_Query.build_dict(result_list)

			if(i.group()=='AND'):
				and_flag=True
				start_pos=i.start()+3;
			else:
				start_pos=i.start()+2;
				or_set.append(and_set[0])

		if(and_flag):
			sub_query_clause=query_clause[start_pos:]
			result_list=self.fastCosineScore(sub_query_clause,100)
			and_set[0]=SSE_Query.AND_operation(and_set[0],SSE_Query.build_dict(result_list))
			or_set.append(and_set[0])
		else:
			sub_query_clause=query_clause[start_pos:]
			result_list=self.fastCosineScore(sub_query_clause,100)
			or_set.append(SSE_Query.build_dict(result_list))

		while len(or_set)!=1:
			or_set[0]=SSE_Query.OR_operation(or_set[0],or_set[1]);
			del or_set[1]

		result=or_set[0]
		return sorted(or_set[0].iteritems(), key=lambda d:d[1], reverse = True)[0:k]


# test
if __name__ == '__main__':
	SQ = SSE_Query( SSE_Indexer() )
	while True:
		query = raw_input("input a test query:")
		result = SQ.query(query)
		print(result)