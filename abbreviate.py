import string, re, nltk
import cluster

def tokenize_list_of_strings(string_list):
    # Initialize an empty list to store all tokens
    all_tokens = []

    # Loop over each string in the list
    for string in string_list:
        # Tokenize the string and add the tokens to the list of all tokens
        all_tokens.extend(nltk.word_tokenize(string))

    # Return the list of all tokens
    return all_tokens

def to_lowercase(str):
	return str.lower()

def remove_punctuation(str):
	# Create a translation table that replaces all punctuation characters with spaces
	translator = str.maketrans(string.punctuation, " " * len(string.punctuation))

	# Modify the translation table to exclude the '+' character
	#translator[ord('+')] = '+'
	return str.translate(translator)

def split_letters_numbers(str):
	pattern = re.compile(r'(\d+|\D+)')
	return pattern.findall(str)

def is_digit(str):
	return str.isdigit()


def clean_explode(string_list):
	string_list = [to_lowercase(w) for w in string_list]
	string_list = [remove_punctuation(w) for w in string_list]
	exploded = []
	for w in string_list:
		exploded += [w.strip() for w in split_letters_numbers(w)]
	exploded = tokenize_list_of_strings(exploded)
	return exploded

def make_abbreviations(strings, ignore_list):
	abbrevs = {}
	next_abbrev = ord('a')+1000

	strings = clean_explode(strings)

	print("Abbreviating")
	tokens = list(set(tokenize_list_of_strings(strings)))

	cf = cluster.get_cluster_finder(tokens, ignore_list, scoring_algorithm=cluster.levenshtein_cutoff_stringent, save_filename="make_abbreviations", abbreviations = False)

	corresponding_clusters, clusters_with_labeled_nodes = cluster.get_cluster_names(cf)

	for c in clusters_with_labeled_nodes:
		for node in c:
			abbrevs[node] = chr(next_abbrev)
		next_abbrev += 1

	print("Done")
	return abbrevs

def original_and_abbreviated_dict(strings, ignore_list, echo=False):
	abbrev_dict = make_abbreviations(strings, ignore_list)
	abbreviations = {}
	ignore_list = sorted(ignore_list, reverse=True)
	for s in strings:
		if echo:
			print(s)
		parts = clean_explode([s])
		abbreviated = []
		for part in parts:
			if part in ignore_list:
				if echo:
					print("\tignored", part)
				continue
			elif part in abbrev_dict.keys():
				if echo:
					print("\t", part, "abbreviated to", abbrev_dict[part])
				abbreviated += abbrev_dict[part]
			else:
				if echo:
					print("\t", part)
				abbreviated += part
		abbreviations[s] = ''.join(abbreviated)
		if echo:
			print("\t", s, "abbreviated to", abbreviations[s])

	return abbreviations, abbrev_dict