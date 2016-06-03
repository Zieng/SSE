import os
import os.path
import re
import json
import io
import nltk
import math
import sys
from nltk.stem import WordNetLemmatizer
from nltk.stem import SnowballStemmer
from nltk.stem.lancaster import LancasterStemmer
from nltk.stem.porter import PorterStemmer
from nltk.util import ngrams
from nltk.corpus import wordnet


class SSE_Indexer(object):
	"""docstring for SSE_Indexer"""
	def __init__(self, dirList = ['./Reuters'] ):
		super(SSE_Indexer, self).__init__()
		self.indexTable = dict()   # hashtable to store all index
		self.handledFiles=[]
		self.DataDirList = dirList
		self.lema = WordNetLemmatizer()
		self.idf_table = {}
		self.doc_len = {}

	def lookup_index_table(self, input_term ):
		if input_term in self.indexTable.keys():
			return self.indexTable[ input_term ]
	
	def get_wordnet_pos(self,treebank_tag):
	    if treebank_tag.startswith('J'):
	        return wordnet.ADJ
	    elif treebank_tag.startswith('V'):
	        return wordnet.VERB
	    elif treebank_tag.startswith('N'):
	        return wordnet.NOUN
	    elif treebank_tag.startswith('R'):
	        return wordnet.ADV
	    else:
	        return wordnet.NOUN

	def tokenize(self, input ):
		tokens = nltk.word_tokenize(input.lower())
		tag_tokens = nltk.pos_tag( tokens )
		return [self.lema.lemmatize(x,self.get_wordnet_pos(t)) for (x,t) in tag_tokens ]

	def index_files(self):
		for rootdir in self.DataDirList:
			for parent,dirnames,filenames in os.walk(rootdir):
				for relative_filename in filenames:
					filename=rootdir+"/"+relative_filename
					self.append_index( filename )
		return self.indexTable

	def append_index(self, filename ):
		if filename in self.handledFiles:
			print("duplicate file!\n")
			return
		self.handledFiles.append(filename)
		with open(filename, "r") as f:
			text = f.read().decode('utf-8').encode('utf-8')
			text = text.replace("&lt;","<")
		terms = self.tokenize( text )
		handledTerms = []
		for term in terms:
			if term in handledTerms:
				continue
			if term not in self.indexTable:     # A new term without index
				# print "new index"
				new_post=dict()
				new_post['doc']=filename
				new_post['tf']=terms.count(term)
				new_postingList=[]                        #create a postingList
				new_postingList.append(new_post)
				self.indexTable[term]=new_postingList
			else:
				# print "upate index"
				new_post=dict()
				new_post['doc']=filename
				new_post['tf']=terms.count(term)
				self.indexTable[term].append(new_post)
			handledTerms.append(term)

	def compute_idf(self):
		"""compute the inverse document frequency for each term"""
		self.idf_table = {}
		N = float(len( self.handledFiles ))
		for term in self.indexTable:
			postingList = self.indexTable[term]
			df = len( postingList )
			self.idf_table[term] = math.log10(N/df)
			# print( 'for {} df={}, N={}, idf={}'.format(term,df,N,self.idf_table[term]))

	def compute_doc_len(self):
		""" doc_len is the normalized factor for cosin score computation"""
		self.doc_len = {}
		for doc in self.handledFiles:
			self.doc_len[doc] = 0
		for term in self.indexTable:
			postingList = self.indexTable[term]
			for posting in postingList:
				doc = posting['doc']
				tf = posting['tf']
				weight = (1+math.log10(tf)) * self.idf_table[term]
				self.doc_len[doc] += weight**2
		for doc in self.handledFiles:
			self.doc_len[doc] = math.sqrt(self.doc_len[doc])

	def store_index(self):
		with io.open('./my_index.json', 'w', encoding='utf-8') as f:
			f.write(unicode(json.dumps(self.indexTable, ensure_ascii=False)))
		print("store index done\n")

	def store_idf(self):
		with io.open('./idf.json', 'w', encoding='utf-8') as f:
			f.write(unicode(json.dumps(self.idf_table, ensure_ascii=False)))
		print("store idf done\n")

	def store_doc_len(self):
		with io.open('./doc_len.json', 'w', encoding='utf-8') as f:
			f.write(unicode(json.dumps(self.doc_len, ensure_ascii=False)))
		print("store doc_len done\n")

	def load_index(self, filename = './my_index.json' ):
		with io.open(filename, 'r', encoding='utf-8') as f:
			data=f.read()
			self.indexTable=json.loads(data)
		print("read index done\n")

	def load_idf(self, filename = './idf.json'):
		with io.open(filename, 'r', encoding='utf-8') as f:
			data=f.read()
			self.idf_table=json.loads(data)
		print("read idf table done\n")
	
	def load_doc_len(self, filename = './doc_len.json'):
		with io.open(filename, 'r', encoding='utf-8') as f:
			data=f.read()
			self.doc_len=json.loads(data)
		print("read idf table done\n")

	def load_default(self):
		self.load_index()
		self.load_idf()
		self.load_doc_len()

	def store_default(self):
		self.store_index()
		self.store_idf()
		self.store_doc_len()

	def handle_query(self, input):
		tokens = self.tokenize( input )
		common = [ x for x in tokens if x in self.indexTable.keys()  ]
		return { key:self.indexTable[key] for key in common }

	def get_n_gram(self, input , n = 2):
		return [ x for x in ngrams(self.tokenize(input), n ) ]

# test
if __name__ == '__main__':
	indexer = SSE_Indexer(['./test'])
	# indexer.index_files()
	# indexer.compute_idf()
	# indexer.compute_doc_len()
	# indexer.store_default()
	while 1:
		query = raw_input("input a test query:")
		# results = indexer.handle_query( query )
		print( indexer.tokenize( query ))
		