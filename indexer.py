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
		self.compressed = False

	def lookup_index_table(self, input_term ):
		if input_term in self.indexTable.keys():
			return self.indexTable[ input_term ]

	def wildcard_lookup(self, regxTerm):
		"""regxTerm is regular form term such as r'he[a-zA-Z_0-9]*' """
		result = {}
		for t in self.indexTable:
			if re.match(regxTerm, t):
				result[t]=self.indexTable[t]
		return result
	
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
		# return tokens
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
		docId = filename.split('/')[-1].split('.')[0]
		# if self.compressed:
		docId = int(docId)
		print(docId)
		self.handledFiles.append(docId)
		with open(filename, "r") as f:
			try:
				text = f.read().decode('utf-8').encode('utf-8')
			except:
				pass
		terms = self.tokenize( text )
		handledTerms = []
		for term in terms:
			if term in handledTerms:
				continue
			if term not in self.indexTable:     # A new term without index
				# print "new index"
				new_post=dict()
				new_post['doc']=docId
				new_post['tf']=terms.count(term)
				new_postingList=[]                        #create a postingList
				new_postingList.append(new_post)
				self.indexTable[term]=new_postingList
			else:
				# print "upate index"
				new_post=dict()
				new_post['doc']=docId
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

	# def compress_postinglist(self, pl):
	# 	pass
	def store_index(self,compressed = False):
		self.compressed = compressed
		index_file_name = './index.json'
		if self.compressed:
			index_file_name = './index_compressed.json'
			for term in self.indexTable:
				pl = sorted( self.indexTable[term], key=lambda d:d['doc'])
				first_post = True
				previous_docId = 0
				for p in pl:
					if first_post:
						first_post = False
						previous_docId = p['doc']
					else:
						dist = p['doc'] - previous_docId
						previous_post = p['doc']
						p['doc'] = dist
				self.indexTable[term] = pl
		print(self.indexTable['the'])
		with io.open(index_file_name, 'w', encoding='utf-8') as f:
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

	def load_index(self, filename = './index.json' , compressed = False):
		self.compressed = compressed
		with io.open(filename, 'r', encoding='utf-8') as f:
			data=f.read()
			self.indexTable=json.loads(data)
		print(self.indexTable['the'])
		if self.compressed:
			for term in self.indexTable:
				pl = self.indexTable[term]
				first_post = True
				previous_docId = 0
				for p in pl:
					if first_post:
						first_post = False
						# previous_docId = p['doc']
					else:
						p['doc'] += previous_docId
					previous_docId = p['doc']
				self.indexTable[term] = pl

		print(self.indexTable['the'])
		print("[----read index done----]")


	def load_idf(self, filename = './idf.json'):
		with io.open(filename, 'r', encoding='utf-8') as f:
			data=f.read()
			self.idf_table=json.loads(data)
		print("read idf table done")
	
	def load_doc_len(self, filename = './doc_len.json'):
		with io.open(filename, 'r', encoding='utf-8') as f:
			data=f.read()
			self.doc_len=json.loads(data)
		print("read idf table done")

	def load_default(self):
		self.load_index()
		self.load_idf()
		self.load_doc_len()

	def store_default(self):
		self.store_index()
		self.store_idf()
		self.store_doc_len()

	def handle_query(self, input):
		"""test function"""
		tokens = self.tokenize( input )
		common = [ x for x in tokens if x in self.indexTable.keys()  ]
		return { key:self.indexTable[key] for key in common }

	def get_n_gram(self, input , n = 2):
		"""query string to n-gram term list"""
		return [ x for x in ngrams(self.tokenize(input), n ) ]

# test
if __name__ == '__main__':
	indexer = SSE_Indexer(['./test'])
	indexer.index_files()
	indexer.store_index(compressed = True)
	# indexer.load_default()
	indexer.load_index('./index_compressed.json', compressed = True)

	while 1:
		# docId = int(raw_input("input a docID:"))
		query = raw_input("input a test query:\n\t")
		match = indexer.handle_query( query )
		print( match )
		