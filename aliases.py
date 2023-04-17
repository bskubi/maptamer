import openai, multiprocessing, os, re, pickle, csv, time, timeit, gptner, extract
from convenience import *

def get_aliases(input_source, filename_out = "", ordered_headers = [], io_headers = ["alias1_specific_clean", "alias2"]):
    spreadsheet = None
    if type(input_source) == str:
        spreadsheet = gptner.from_spreadsheet(filename_in)
    elif type(input_source) == dict:
        spreadsheet = input_source
    elif type(input_source) == list:
        spreadsheet = {io_headers[0]:input_source}
    else:
        raise("Unexpected type for input_source in get_aliases")
    input_names = spreadsheet[io_headers[0]]
    aliases = []
    for name in input_names:
        if len(name.strip()) == 0 or name == "None":
            aliases.append("")
            continue
        prompt = "Is there another academic alias for " + name + "?"
        response = gptner.chatbot_response_robust(prompt, gptner.models["standard"])
        response = response.replace("\n", "")
        aliases.append(response)
        print(len(aliases),"/",len(input_names),name, response)
    spreadsheet[io_headers[1]] = aliases
    if filename_out != "":
        gptner.to_spreadsheet(filename_out, spreadsheet, ordered_headers)
    return aliases

def clean(names, model, echo=True):
    cleaned = []
    for name in names:
        response = gptner.chatbot_response_robust(name + "   ###   ", gptner.models[model])
        cleaned_response = response.replace("\n", "").split("###")[0].strip()
        cleaned.append(cleaned_response)
        print(name)
        print(cleaned_response)
        print()
    return cleaned

def gpt_consensus_names(labeled_clusters, echo = True):
    size_1 = "Fix the formatting if necessary, otherwise just reproduce the original text:\n\n"
    size_2_plus = "Give a nicely formatted consensus name for the following ways of spelling the same thing (which may be a molecule, cell, or other):\n\n"
    consensus_names = []
    for cluster in labeled_clusters:
        if len(cluster[0].strip()) == 0:
            consensus_names.append("None")
            continue
        dynamic_content = '\n'.join(cluster)
        if "(" in dynamic_content and ")" not in dynamic_content:
            dynamic_content += ")"
        prompt = size_1 + dynamic_content if len(cluster) == 1 else size_2_plus + dynamic_content
        response = gptner.chatbot_response_robust(prompt, gptner.models["standard"])

        response = response.replace("\n", "")
        response = response.replace("Consensus Name:", "")
        response = response.strip()

        consensus_names.append(response)

        if echo:
            print(dynamic_content)
            print("Consensus Name:", response)
            print(len(consensus_names), "/", len(labeled_clusters))
            print('\n')

    return consensus_names

def generate_aliases(output_filename, cluster_with_labeled_nodes):
    alias1_list = gpt_consensus_names(cluster_with_labeled_nodes)
    quickle_out(alias1_list, "alias1_list")
    #alias2_list = get_aliases(alias1_list_cleaned)
    #quickle_out(alias2_list, "alias2_list")
    #alias2_list_cleaned = clean(alias2_list, "amplification_clean")
    #quickle_out(alias2_list_cleaned, "alias2_list_cleaned")

    headers=["consensus_name"]

    spreadsheet = {"consensus_name":alias1_list}

    #spreadsheet = {"alias1":alias1_list,
    #                "alias1_cleaned":alias1_list_cleaned,
    #                "alias2":alias2_list,
    #                "alias2_cleaned":alias2_list_cleaned}
    gptner.to_spreadsheet(output_filename, spreadsheet, headers)

def zip_aliases(alias1, alias2):
    aliases = list(zip(alias1, alias2))
    for i in range(len(aliases)):
        aliases[i] = extract.split_targets([aliases[i][0]]) + extract.split_targets([aliases[i][1]])
    return aliases

def delete_generic(alias1_dict):
    pc_pairs = dict(list(zip(alias1_dict["alias1_cleaned"], alias1_dict["alias1_specific"])))
    
    gptner.to_jsonl_prep_spreadsheet("alias1_specific.tsv", pc_pairs)
    gptner.ft_prep_from_jsonl_prep_spreadsheet("alias1_specific.tsv")
    gptner.ft_train("curie", "alias1_specific_prepared.jsonl", "alias1_cleaned_specific")

def get_specific(spreadsheet_filename, io_header):
    headers = gptner.get_spreadsheet_headers(spreadsheet_filename)
    spreadsheet = gptner.from_spreadsheet(spreadsheet_filename)
    cleaned = spreadsheet[io_header[0]]

    specific = []
    for alias in cleaned:
        prompt = """You are a scientist classifying aptamer targets in academic abstracts.
        - Sometimes, the abstract mentions a specific cell type or molecule that the aptamer binds.
        - Other times, it gives a generic statement of the target, such as 'Other molecules involved in the transcription process', or 'A small organic effector'.
        - Occasionally, there will be a specific cell type mentioned, but the target is a molecule that is only referred to generically, as in 'specific membrane marks in breast cancer cells."
        \n\n
        Here is what the abstract says the aptamer binds:""" + alias + """\n\nCan you name the specific molecule or cell type (if so, what is it?), or is it just a generic or vague description?"""

        response = gptner.chatbot_response_robust(prompt, gptner.models["standard"])
        print(alias, "\t", response)
        specific.append(response)

    spreadsheet[io_header[1]] = specific
    if io_header[1] not in headers:
        headers.append(io_header[1])
    gptner.to_spreadsheet(spreadsheet_filename, spreadsheet, headers)