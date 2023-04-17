from nltk.tokenize import word_tokenize
from string import punctuation

my_punctuation = punctuation.replace('-', '')
my_punctuation = my_punctuation.replace('(', '')
my_punctuation = my_punctuation.replace(')', '')


target_indicators = ["detect"]

def upper_count(s):
	count = 0
	for c in s:
		count += c.isupper()
	return count

def window(l, start, end):
	start = max(0, start)
	end = min(len(l)-1, end)
	return l[start:end+1]


def find_acronyms(tok):
	start = False
	acronym_start = 0
	acronym_parts = []
	acronyms = {}
	for i in range(len(tok)):
		if tok[i] == "(":
			start = True
			acronym_start = i + 1
		elif tok[i] == ")":
			start = False
			acronym = ' '.join(acronym_parts)
			pre_acronym = window(tok, acronym_start-1 - len(acronym) - 2, acronym_start - 2)
			acronyms[acronym] = ' '.join(pre_acronym)
		elif start:
			acronym_parts.append(tok[i])
	return acronyms






count = 0
abstract_words = {}
total_words = 0
with open("output.csv", encoding="utf8") as f:
	lines = f.readlines()

	i = 0
	for line in lines:
		if i == 0:
			i += 1
			continue
		line = line.split('\t')
		year = line[0]
		page = line[1]
		title = line[2]
		title_tokenized = word_tokenize(title)
		abstract = line[3]
		abstract = abstract.translate(str.maketrans("", "", my_punctuation)).lower()
		abstract_tokenized = word_tokenize(abstract)
		for word in abstract_tokenized:
			abstract_words.setdefault(word, 0)
			abstract_words[word] += 1
			total_words += 1

for word in abstract_words.keys():
	abstract_words[word] /= total_words

with open("words.csv", "w", encoding = "utf8") as f:
	for word in abstract_words.keys():
		f.write(word + "\t" + str(abstract_words[word]) + "\n")

with open("output.csv", encoding="utf8") as f:
	lines = f.readlines()

	i = 0
	for line in lines:
		if i == 0:
			i += 1
			continue
		line = line.split('\t')
		year = line[0]
		page = line[1]
		title = line[2]
		title_tokenized = word_tokenize(title)
		abstract = line[3]
		abstract = abstract.translate(str.maketrans("", "", my_punctuation)).lower()
		abstract_tokenized = word_tokenize(abstract)
		for word in abstract_tokenized:
			frequency_in_abstract = 
			representation = abstract_words[word]
