import re
import math
from indexer import SSE_Indexer
from query import SSE_Query

class Bool_Query(object):
	def __init__(self, standard_query):
		super(Bool_Query,self).__init__()
		self.standard_query=standard_query
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

	def query(self,query_clause,k=5):
		start_pos=0;
		or_set=[]
		and_set=["",""]
		and_flag=False
		for i in self.keyword.finditer(query_clause):
			if(and_flag):
				sub_query_clause=query_clause[start_pos:i.start()]
				result_list=self.standard_query.cosine_score(sub_query_clause,100)
				print "======sub query====="
				print sub_query_clause
				print result_list
				print "===================="
				and_set[0]=Bool_Query.AND_operation(and_set[0],Bool_Query.build_dict(result_list))
				and_flag=False
			else:
				sub_query_clause=query_clause[start_pos:i.start()]
				result_list=self.standard_query.cosine_score(sub_query_clause,100)
				print "======sub query====="
				print sub_query_clause
				print result_list
				print "===================="
				and_set[0]=Bool_Query.build_dict(result_list)

			if(i.group()=='AND'):
				and_flag=True
				start_pos=i.start()+3;
			else:
				start_pos=i.start()+2;
				or_set.append(and_set[0])

		if(and_flag):
			sub_query_clause=query_clause[start_pos:]
			result_list=self.standard_query.cosine_score(sub_query_clause,100)
			print "======sub query====="
			print sub_query_clause
			print result_list
			print "===================="
			and_set[0]=Bool_Query.AND_operation(and_set[0],Bool_Query.build_dict(result_list))
			or_set.append(and_set[0])
		else:
			sub_query_clause=query_clause[start_pos:]
			result_list=self.standard_query.cosine_score(sub_query_clause,100)
			print "======sub query====="
			print sub_query_clause
			print result_list
			print "===================="
			or_set.append(Bool_Query.build_dict(result_list))

		while len(or_set)!=1:
			or_set[0]=Bool_Query.OR_operation(or_set[0],or_set[1]);
			del or_set[1]

		result=or_set[0]
		return sorted(or_set[0].iteritems(), key=lambda d:d[1], reverse = True)[0:k]

	def test_query(self,query_clause,k=5):
		start_pos=0;
		or_set=[]
		and_set=["",""]
		and_flag=False
		for i in self.keyword.finditer(query_clause):
			if(and_flag):
				and_set[0]=and_set[0] & int(query_clause[start_pos:i.start()])
				and_flag=False
			else:
				and_set[0]=int(query_clause[start_pos:i.start()])

			if(i.group()=='AND'):
				and_flag=True
				start_pos=i.start()+3;
			else:
				start_pos=i.start()+2;
				or_set.append(and_set[0])

		if(and_flag):
			and_set[0]=and_set[0] & int(query_clause[start_pos:])
			or_set.append(and_set[0])
		else:
			or_set.append(int(query_clause[start_pos:]))

		while len(or_set)!=1:
			or_set[0]=or_set[0] | or_set[1];
			del or_set[1]

		print or_set[0]
		return or_set[0]


if __name__=='__main__':
	Engine=Bool_Query(SSE_Query(SSE_Indexer()))
	while True:
		query_clause=raw_input("please input the query clause:")
		result=Engine.query(query_clause);
		print(result)

