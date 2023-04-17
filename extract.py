import re, string, os, multiprocessing, re
import gptner

def extract_targets_from_title_and_abstract(input_filename, output_filename, count = None, echo=True):
	if count is None:
		count = -1
	gptner.setup()
	gptner.max_tokens = 100

	# Order the headers
	headers = ["year", "page", "title", "abstract", "extract"]

	# Don't try to load abstract targets, just year, page, title, abstract
	scopus = gptner.from_spreadsheet(input_filename, headers[:4], count=count)

	# Combine titles and abstracts from individual articles into tuples
	pairs = list(zip(scopus["title"], scopus["abstract"]))

	# Convert tuples to lists
	pairs = [list(x) for x in pairs]

	# Create a list of responses in the same order as the articles are listed in the original spreadsheet
	responses = []


	# Iterate through all abstract-title pairs
	for i in range(len(pairs)):
		# Combine abstract and title into a single string
		dynamic_content = ' '.join(pairs[i])

		prompt = """Scientists selected one or more aptamers during SELEX.
		The aptamer(s) bind one or more targets, and can be used in assays to detect that target.
		Sometimes multiple aptamer targets are mentioned, and we want to note all of them.
		However, sometimes other molecules (like ions) bind aptamers to produce or quench a signal, which are not considered the aptamer's target.
		Other times, aptamers are part of a complex targeting system involving nanoparticles or drugs, which are also not the aptamer's target.
		Based on the following text, suggest what the aptamer's SELEX target might have been.

		\n\nText: """ + dynamic_content + "Suggest the target(s) of the aptamers: "

		# Get the chatbot response and add it to the responses
		responses.append(gptner.chatbot_response_robust(prompt, model = gptner.models["standard"]).replace("\n", " "))

		print(i+1, "/", len(pairs))
		print(pairs[i][0])
		print("Response:", responses[-1])
		print()

	# Incorporate responses into the dict for the spreadsheet columns
	scopus[headers[-1]] = responses

	# Save the output
	gptner.to_spreadsheet(output_filename, scopus, ordered_headers = headers)

def clean_responses(input_filename, output_filename, model, io_headers, skip = 0, count = None, echo=True):
	gptner.setup()
	gptner.max_tokens = 30

	# Don't try to load abstract targets, just year, page, title, abstract
	headers = gptner.get_spreadsheet_headers(input_filename)
	spreadsheet = gptner.from_spreadsheet(input_filename)
	to_clean = spreadsheet[io_headers[0]]

	# Create a list of responses in the same order as the articles are listed in the original spreadsheet
	responses = []

	if count is None:
		count = len(to_clean)

	# Iterate through all abstract-title pairs
	for i in range(skip, skip+count):
		prompt = to_clean[i]
		if prompt.strip() == "":
			responses.append("")
			continue
		prompt += "   ###   "

		# Get the chatbot response and add it to the responses
		response = gptner.chatbot_response_robust(prompt, model = model)
		response_clean = response.replace("\n", " ").split("###")[0].strip()
		responses.append(response_clean)

		print(str(len(responses)) + "/" + str(count) + "\t" + prompt + "\t" + responses[-1])

	# Incorporate responses into the dict for the spreadsheet columns
	padding = []
	for i in range(skip+count):
		padding += ""
	spreadsheet.setdefault(io_headers[1], padding)
	spreadsheet[io_headers[1]][skip:skip+count] = responses

	# Save the output
	headers.append(io_headers[1])
	gptner.to_spreadsheet(output_filename, spreadsheet, ordered_headers = headers)

def train_cleaning_model(input_filename, output_filename, model, count, model_suffix = "", headers = ["extract", "completion_tagged"]):
	gptner.setup()
	cols = gptner.from_spreadsheet(input_filename, headers, count=count)
	pc_dict = dict(list(x) for x in zip(cols[headers[0]], cols[headers[1]]))
	
	gptner.to_jsonl_prep_spreadsheet(output_filename, pc_dict)
	jsonl_filename = output_filename.split(".tsv")[0] + "_prepared.jsonl"
	if os.path.exists(jsonl_filename):
		os.remove(jsonl_filename)
	gptner.ft_prep_from_jsonl_prep_spreadsheet(output_filename)
	input("Press enter to train")
	gptner.ft_train(model, jsonl_filename, model_suffix)

def combine_dicts(dicts):
	combined = dicts[0]
	for k in combined.keys():
		for d in dicts[1:]:
			if k in d:
				combined[k].extend(d[k])
	return combined

def split_targets(targets):
	split = []
	for t in targets:
		split_t = re.split(r'[;,]\s+', t)
		split += split_t
	return split

def extract_all_scopus_targets_costs_forty_five_dollars():
	# Warning, these cost money to run!
	# Costs about $45 to train and clean the entire Scopus extract!
	# When I did this, I copied this python file three times, split the scopus_aptamer_4_4_2023 file into three equal parts,
	# then ran the program simultaneously on the three parts to ~triple the extraction speed. It's ~necessary to do it this way
	# because the extraction method uses multiprocessing, and you can't launch multiple threads from within a thread.
	# This is why the three cleaned extract files had to be re-aggregated in the second half below. This step isn't necessary if 
	# you're extracting and cleaning the entire file from within a single instance of the program.
	#train_extract_cleaning_model("scopus_extracts.csv", "scopus_extracts_ft_clean_tagged.tsv", "curie", "clean_extracts")
	#extract_targets_from_title_and_abstract("scopus_aptamer_4_4_2023.csv", "scopus_extracts.csv")
	#clean_responses("scopus_extracts.csv", "scopus_extracts_cleaned.csv")

	"""
	# Used to aggregate cleaned 
	headers = ["year", "page", "title", "abstract", "extract", "cleaned"]
	extracts = ["scopus_extracts_cleaned_1.csv", "scopus_extracts_cleaned_2.csv", "scopus_extracts_cleaned_3.csv"]
	extract_dicts = [gptner.from_spreadsheet(filename, headers) for filename in extracts]
	combined = combine_dicts(extract_dicts)
	gptner.to_spreadsheet("scopus_extracts_cleaned_combined.csv", combined, ordered_headers = headers)
	"""
	pass

# Used to evaluate the results of cleaning.
def sample_extract_clean_data():
	random.seed(0)
	headers = ["year", "page", "title", "abstract", "extract", "cleaned"]
	combined = gptner.from_spreadsheet("results/scopus_extracts_cleaned_combined.csv", headers)
	sample = gptner.sample_from_spreadsheet(combined, headers, 20)
	gptner.to_spreadsheet("results/scopus_extracts_cleaned_sample.csv", sample, headers)

