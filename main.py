import extract, gptner, aliases, abbreviate, cluster, runtime, random, compare

from convenience import *
import networkx as nx

def is_one(x):
	return x == 1



orig_tcs = list(set(extract.split_targets(gptner.from_spreadsheet("results/scopus_extracts_cleaned_combined.csv")["cleaned"])))
print(len(orig_tcs))

cf1 = cluster.get_cluster_finder("results/scopus_extracts_cleaned_combined.csv", "results/ignore.txt", save_filename="cf1")

#quickle_delete("cluster_with_labeled_nodes")
corresponding_clusters_cf1, cluster_with_labeled_nodes_cf1 = quickle_runonce("cluster_with_labeled_nodes_cf1", cluster.get_cluster_names, (cf1,))

print(len(cluster_with_labeled_nodes_cf1))
exit()

#aliases.generate_aliases("results/aliases.csv", cluster_with_labeled_nodes_cf1)

#names = []
#for c in cluster_with_labeled_nodes_cf1:
#	names.append(', '.join(c))

spreadsheet = gptner.from_spreadsheet("results/aliases.csv")
labels = spreadsheet["consensus_name_specific_clean"]

new_labels = [label for label in labels if label != "None"]

cm = compare.CompareMatrix()
cm.setup(new_labels)
cm.compare(compare.levenshtein, top_right_only = True, include_main_diagonal = False, echo=True)

print(cm.select_comparisons(is_one, top_right_only = True, include_main_diagonal = False))

#cluster.assign_to_papers("results/scopus_extracts_cleaned_combined.csv", cf1, labels=labels)

exit()

for c in cluster_with_labeled_nodes_cf1:
	if len(c) > 2:
		for node in c:
			print(node)
		print()

print("Total clusters:", len(cluster_with_labeled_nodes_cf1))
csd = cluster.cluster_size_dict(cf1)
print("Number G of clusters of size N:")
print("N\tG")
for s in sorted(csd.keys()):
	print(s, "\t", csd[s])

exit()





"""

amplified_targets = cf1.original_names[:]

alias_spreadsheet = gptner.from_spreadsheet("results/alias1_and_2.csv")
cluster_aliases = aliases.zip_aliases(alias_spreadsheet["alias1_specific_clean"][:], alias_spreadsheet["alias2_clean"])
amplified_targets += alias_spreadsheet["alias1_specific_clean"][:]
amplified_targets += alias_spreadsheet["alias2_clean"][:]

# So now we have a list of original target names and aliases
# We want to cluster all of these.
# Any clusters containing an alias from an alias set we group
# However, many alias sets contain "None" as an alias.
# We want to ignore those

# Converts targets to a set and scores them, removing "None", "none" and ""
cf2 = cluster.get_cluster_finder(amplified_targets, "results/ignore.txt", save_filename="cf2")

# Gets the clustered node numbers (no longer corresponding to original papers) labels (corresponding to TCs which can be linked to original papers)
corresponding_clusters_cf2, cluster_with_labeled_nodes_cf2 = quickle_runonce("cluster_with_labeled_nodes_cf2", cluster.get_cluster_names, (cf2,))

for alias in cluster_aliases:
	combine = []
	for i in range(len(cluster_with_labeled_nodes_cf2)):
		if set(alias).intersection(set(cluster_with_labeled_nodes_cf2[i])):
			combine.append(i)
	combined = []
	for i in reversed(combine):
		combined += cluster_with_labeled_nodes_cf2[i]
		del cluster_with_labeled_nodes_cf2[i]
	if len(combined) > 0:
		cluster_with_labeled_nodes_cf2.append(combined)

all_aliases = sum(cluster_aliases, [])

for c in cluster_with_labeled_nodes_cf2:
	c_aliases = []
	for alias in all_aliases:
		if alias in c:
			c_aliases.append(alias)
	print(c_aliases)
	for node in c:
		print(node)
	print()

print("Total clusters:", len(cluster_with_labeled_nodes_cf2))
csd = cluster.cluster_size_dict(cf2)
print("Number G of clusters of size N:")
print("N\tG")
for s in sorted(csd.keys()):
	print(s, "\t", csd[s])

"""