import sys, ast, re
import gptner, aliases, abbreviate, extract, convenience
from convenience import *
import nltk, string, multiprocessing
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter

# Score is a tuple containing (size of largest string, levenshtein distance)
def levenshtein(string1, string2, i, j):
	return ((max(len(string1), len(string2)), nltk.edit_distance(string1, string2)), i, j)

def levenshtein_below_threshold(string1, string2, multiplier, multiplier_subset):
	if len(string1) == 0 or len(string2) == 0:
		return False

	chars1 = set(string1)
	chars2 = set(string2)
	subset = chars1.issubset(chars2) or chars2.issubset(chars1)

	multiplier = multiplier_subset if chars1.issubset(chars2) or chars2.issubset(chars1) else multiplier


	longer_string = max(len(string1), len(string2))
	cutoff = float(longer_string)*multiplier
	levenshtein = float(nltk.edit_distance(string1, string2))
	levenshtein_below_cutoff = levenshtein < cutoff

	return levenshtein_below_cutoff

def levenshtein_cutoff_stringent(string1, string2, i, j):
	return (levenshtein_below_threshold(string1, string2, .15, .25), i, j)

# Score is whether or not the levenshtein distance is less than 34% the length fo the longer string
# Or one is a subset of the other
def levenshtein_cutoff(string1, string2, i, j):
	return (levenshtein_below_threshold(string1, string2, .33, .5), i, j)

def plot_graph(G, labels):
	custom_labels = {}
	for i in range(len(labels)):
		custom_labels[i] = labels[i]
	# Draw the graph with custom labels
	pos = nx.spring_layout(G)
	nx.draw(G, pos, with_labels=False, node_color='lightblue', node_size=1, width=1, alpha=.2, style='dashed')
	nx.draw_networkx_labels(G, pos, labels=custom_labels, font_size=7)

	# Display the graph using Matplotlib
	plt.show()

class ClusterFinder:
	def __init__(self):
		self.matrix = []
		self.original_names = []
		self.names_to_score = []
		self.abbrev_dict = {}

	def set_names_to_score(self, names_to_score, abbrev_dict = None):
		self.abbrev_dict = abbrev_dict
		if type(names_to_score) is list:
			self.original_names = names_to_score[:]
			self.names_to_score = names_to_score[:]
		elif type(names_to_score) is dict:
			items = names_to_score.items()
			self.original_names = [item[0] for item in items]
			self.names_to_score = [item[1] for item in items]
		self.matrix = []
		for i in range(len(self.names_to_score)):
			self.matrix.append([])
			for j in range(len(self.names_to_score)):
				self.matrix[i].append(None)

	def matrix_size(self):
		return len(self.matrix)

	def score(self, scoring_algorithm = levenshtein_cutoff, processes=10, max_memory_size_gb = 1, max_chunks = 100):
		print("Scoring")
		with multiprocessing.Pool(processes=processes) as pool:
			arg_tuples = []
			chunk_id = 0
			size = self.matrix_size()
			memory_used_bytes = 0
			max_memory_size_bytes = max_memory_size_gb*1024**3

			for i in range(size):
				for j in range(i+1, size):
					arg_tuples.append((self.names_to_score[i], self.names_to_score[j], i, j))
					memory_used_bytes += sum([sys.getsizeof(x) for x in arg_tuples[-1]]) + sys.getsizeof(arg_tuples[-1])

					if memory_used_bytes > max_memory_size_bytes or (i == size-2 and j == size-1):
						print("Chunk", chunk_id, "i", i, "j", j)
						filename_designator = "cluster_finder_score_chunk_"+str(chunk_id)
						quickle_out(arg_tuples, filename_designator)
						memory_used_bytes = 0
						chunk_id += 1
						arg_tuples = []
						if chunk_id >= max_chunks:
							raise Exception("Too many chunks used during ClusterFinder scoring!")

			for i in range(chunk_id):
				filename_designator = "cluster_finder_score_chunk_" + str(i)
				arg_tuple = quickle_in(filename_designator)
				quickle_delete(filename_designator)
				results = pool.starmap(scoring_algorithm, arg_tuple)

				for r in results:
					score = r[0]
					i = r[1]
					j = r[2]
					self.matrix[i][j] = score

	def convert(self, convert):
		for i in range(self.matrix_size()):
			for j in range(self.matrix_size()):
				if self.matrix[i][j] in convert.keys():
					self.matrix[i][j] = convert[self.matrix[i][j]]

	# Copy the top right to the bottom left
	def top_right_to_bottom_left(self):
		for i in range(self.matrix_size()):
			for j in range(i+1, self.matrix_size()):
				self.matrix[j][i] = self.matrix[i][j]

	def print(self, convert = {}, chr_per_cell=None):
		for i in range(self.matrix_size()):
			for j in range(self.matrix_size()):
				disp = self.matrix[i][j]
				if disp in convert.keys():
					disp = convert[disp]
				disp = str(disp)
				if chr_per_cell is not None:
					disp = disp[:chr_per_cell]
				print(disp, end=" ")
			print()

	def to_graph(self, top_right_to_bottom_left = True, convert = {None:False}):
		if top_right_to_bottom_left:
			self.top_right_to_bottom_left()
		self.convert(convert)
		adj_array = np.array(self.matrix, dtype=bool)

		# Convert the adjacency matrix to a graph
		G = nx.from_numpy_array(adj_array)

		return G

def cluster(strings, ignore_list, scoring_algorithm, abbreviations):
	# Create a ClusterFinder to find clusters in the terms
	cf = ClusterFinder()

	if abbreviations:
		# Form a dicitonary of the original and abbreviated forms
		original_and_abbreviated_dict, abbrev_dict = abbreviate.original_and_abbreviated_dict(strings, ignore_list)

		# Set the names to score. Passing a dict as we are doing here makes it cluster according to the values (i.e. abbreviated versions)
		cf.set_names_to_score(original_and_abbreviated_dict, abbrev_dict)
	else:
		cf.set_names_to_score(strings)

	# Score according to whether or not levenshtein distance is < 33% of the longer of the two string lengths
	cf.score(scoring_algorithm = scoring_algorithm)

	return cf

def cluster_size_dict(cluster_finder):
	G = cluster_finder.to_graph()
	clusters = nx.connected_components(G)
	cluster_sizes = [len(c) for c in clusters]
	
	return dict(Counter(cluster_sizes))

def next_token_first(a, b, list_of_lists):
	b_first = 0
	for s in list_of_lists:
		b_first += 1 if a in s and b in s and s.index(b) < s.index(a) else -1
	return b_first > 0

def get_cluster_names(cluster_finder, lengths = None):
	G = cluster_finder.to_graph()
	clusters = list(nx.connected_components(G))
	cluster_list = [list(c) for c in clusters]
	cluster_with_labeled_nodes = []
	corresponding_clusters = []
	for c in cluster_list:
		cluster_node_labels = []
		if lengths is None or len(c) in lengths:
			corresponding_clusters.append(c)
			for node in c:
				cluster_node_labels.append(cluster_finder.original_names[node])
			cluster_with_labeled_nodes.append(cluster_node_labels)
	return corresponding_clusters, cluster_with_labeled_nodes

def get_cluster_finder(targets_input, ignore_list, scoring_algorithm = levenshtein_cutoff, save_filename = "", target_count = None, abbreviations = True, echo=True):
	gptner.setup()
	gptner.max_tokens=100

	target_set = []
	if type(targets_input) == str:
		targets = gptner.from_spreadsheet(targets_input, ["cleaned"])["cleaned"]
		target_set = list(set(extract.split_targets(targets)))
	else:
		target_set = list(set(extract.split_targets(targets_input)))

	if target_count is None:
		target_count = len(target_set)

	for rem in ["None", "none", ""]:
		if rem in target_set:
			target_set.remove(rem)

	target_set = target_set[:target_count]

	if echo:
		print("Clustering", len(target_set), "targets.")

	if type(ignore_list) != list:
		ignore_list = [] if ignore_list is None else [line.strip() for line in open(ignore_list, "r", encoding="utf8").readlines()]

	quickle_filename = "clustering_"+save_filename

	cf = quickle_runonce(quickle_filename, cluster, (target_set, ignore_list, scoring_algorithm, abbreviations))

	return cf

def assign_to_papers(paper_spreadsheet_filename, cf, labels = [], paper_count = None, quickle_filename="cluster_with_labeled_nodes_assign_to_papers"):
	corresponding_clusters_cf, cluster_with_labeled_nodes_cf = quickle_runonce(quickle_filename, get_cluster_names, (cf,))

	# Load papers
	headers = gptner.get_spreadsheet_headers(paper_spreadsheet_filename)
	paper_spreadsheet = gptner.from_spreadsheet(paper_spreadsheet_filename)

	# Create a new dictionary for a spreadsheet where we'll store the final list - two headers, 'Aptamer Target', containing cluster labels, and 'Sources', a list of sources separated by newlines
	spreadsheet2 = dict()
	headers = ["Aptamer Target", "Sources"]
	spreadsheet2["Aptamer Target"] = []
	spreadsheet2["Sources"] = []

	# Do all the papers if no specific number of papers supplied
	if paper_count is None:
		paper_count = len(paper_spreadsheet["abstract"])

	# Iterate through each paper
	for i in range(paper_count):
		# Get the list of targets identified for the original paper
		original_paper_targets = extract.split_targets([paper_spreadsheet["cleaned"][i]])

		# Find the label cluster that each original paper target was sorted to

		for original_paper_target in original_paper_targets:
			cluster_index = None

			# Search through each cluster
			for j in range(len(cluster_with_labeled_nodes_cf)):
				# If the original paper target is in the list of original paper targets for that cluster, store the cluster index and break
				if original_paper_target in cluster_with_labeled_nodes_cf[j]:
					cluster_index = j
					break

			if cluster_index is None:
				continue

			# Now we have the cluster index. Identify the cluster label. This is what we use as "Aptamer Target"
			cluster_label = labels[cluster_index]


			# Check if this label has already been listed as an Aptamer Target
			if cluster_label not in spreadsheet2["Aptamer Target"]:
				spreadsheet2["Aptamer Target"].append(cluster_label)
				spreadsheet2["Sources"].append([])

			# Format a source entry for the current paper
			entry = paper_spreadsheet["title"][i] + " (" + paper_spreadsheet["year"][i] + ")"

			# Get the index of the Aptamer Target corresponding to the current original target label from the current paper
			label_index = spreadsheet2["Aptamer Target"].index(cluster_label)

			# Append the entry to the Source Column at the position corresponding to the correct Aptamer Target
			spreadsheet2["Sources"][label_index].append(entry)

	# Format sources so newlines remain within-cell in .csv format

	for i in range(len(spreadsheet2["Sources"])):
		core = '\n'.join(spreadsheet2["Sources"][i]).strip()
		core = core.replace("\"", "")
		spreadsheet2["Sources"][i] = core

	spreadsheet2, headers = gptner.limit_cell_size(spreadsheet2, headers, 40000, enclose="\"")

	gptner.to_spreadsheet("results/The Aptamer List (V2, 4 April 2023 Scopus Extraction).csv", spreadsheet2, headers)











