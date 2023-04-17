import openai, multiprocessing, os, re, pickle, csv, time, timeit, random, math, subprocess

random.seed(0)
max_tokens = 50
models = {}


def setup(model_type = "standard", openai_key_filename = "openai_key.txt"):
    global models
    if openai_key_filename is not None and os.path.isfile(openai_key_filename):
        openai_key = open(openai_key_filename).read().strip()
    os.environ["OPENAI_API_KEY"] = openai_key
    openai.api_key = openai.api_key = os.getenv("OPENAI_API_KEY")

    models = {"standard":"gpt-3.5-turbo-0301",
                "extraction_clean":"curie:ft-personal:clean-extracts-2023-04-10-07-29-19",
                "consensus_name_clean":"curie:ft-personal:clean-alias1-2023-04-11-05-31-18",
                "amplification_clean":"curie:ft-personal:clean-amp-2023-04-09-19-32-13",
                "alias1_specific_clean":"curie:ft-personal:alias1-specific-clean-2023-04-12-23-54-32"}
    openai_model = models[model_type]
    

# Define a method to wait for a limited amount of time or until a queue filled by another process is non-empty
def limited_wait(wait_s, queue): 
    # Record the current time as the start time
    start = timeit.default_timer()
    
    # Loop until either the elapsed time exceeds the specified limit or the queue has been filled by another process
    while timeit.default_timer() - start < wait_s and queue.empty():    
        # Continue waiting
        continue

    #Return whether or not the queue was filled before the time expired
    return not queue.empty()

def chatbot_response(content, model, queue):
    #Used for basic ChatGPT 3.5 without fine-tuning
    if model == models["standard"]:
        response =  openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": content}],
            max_tokens=max_tokens,
            n=1,
            temperature=0,
        )
        queue.put(response["choices"][0]["message"]["content"])
    
    else:
        response = openai.Completion.create(
            model = model,
            max_tokens=max_tokens,
            prompt = content,
            temperature=0)
        queue.put(response["choices"][0]["text"])
    

# Define a method to get a response from a chatbot model using multiprocessing
def chatbot_response_robust(content, model = None, wait_s = 15, max_tries=10, echo_delay = True):
    if model is None:
        model = models["standard"]

    # Loop through the specified number of attempts
    for i in range(max_tries):
        
        # Create a new multiprocessing queue and process
        queue = multiprocessing.Queue()
        p = multiprocessing.Process(target=chatbot_response, args=(content, model, queue,))
        p.start()
        
        # Check if the response has been received within the specified time limit
        if limited_wait(wait_s, queue):
            return queue.get()
        else:
            # If the response has not been received, terminate the process and try again
            if echo_delay:
                print("No response in time limit, trying attempt " + str(i+1) + "/" + str(max_tries))

            p.terminate()

def find_header_indices(header_words, header_line):
    header_column_indices = {}
    for word in header_words:
        header_column_indices[word] = header_line.index(word)
    return header_column_indices

def get_spreadsheet_headers(filename):
    with open(filename, 'r', encoding='utf8') as f:
        return f.readlines()[0].strip().split('\t')    

def from_spreadsheet(filename, headers = [], count = -1, delimeter='\t'):
    if headers == []:
        with open(filename, 'r', encoding='utf8') as f:
            headers = f.readlines()[0].strip().split('\t')
    columns = {}
    header_column_indices = {}
    column_count = 0
    for h in headers:
        columns.setdefault(h, [])

    with open(filename, 'r', encoding='utf8') as f:
        for line in f:
            line = line.strip().split('\t')
            
            # Check if we have identified the headers yet.
            if header_column_indices == {}:
                column_count = len(line)
                # Set the headers and which column they correspond to
                header_column_indices = find_header_indices(headers, line)

                # Create an empty list to store column data
                for k in header_column_indices:
                    columns.setdefault(k, [])
            elif count == -1 or count > 0:
                # Add blank entries for the line to ensure there is at least a blank entry corresponding to each header
                for i in range(column_count):
                    line.append("")
                for h in headers:
                    columns[h].append(line[header_column_indices[h]].strip())
                count = count - 1 if count > 0 else count
                if count == 0:
                    break

    return columns

def fill_spreadsheet_column(spreadsheet, header, default_text, count):
    spreadsheet.setdefault(header, [])
    for i in range(count):
        if i == len(spreadsheet[header])-1:
            spreadsheet[header].append(default_text)
    return spreadsheet

def get_extra_headers(h, count):
    extra_headers = [h]
    for c in range(2, count+1):
        extra_headers.append(h + "_" + str(c))
    return extra_headers

def add_extra_headers(spreadsheet, headers, eh):
    for i in range(len(headers)):
        if headers[i] == eh[0]:
            for j in range(1, len(eh)):
                if eh[j] not in headers:
                    headers.insert(i+j, eh[j])
                    print(headers)
            break
    for header in eh:
        if header not in spreadsheet.keys():
            count = len(spreadsheet[headers[0]])
            spreadsheet[header] = []
            for c in range(count):
                spreadsheet[header].append("")
    return spreadsheet, headers


# This function identifies cells containing more than "max_cell_characters",
# builds a new column and moves any lines that go beyond the limit to the new column in the same row
def limit_cell_size(spreadsheet, headers, max_cell_characters, enclose = ""):
    for h in headers:
        for i in range(len(spreadsheet[h])):
            if len(spreadsheet[h][i]) > max_cell_characters:
                chunks = [""]
                for line in spreadsheet[h][i].split('\n'):
                    new_len = len(chunks[-1]) + len(line) + 1 + 2*len(enclose)
                    if new_len+1 > max_cell_characters:
                        chunks.append(line + "\n")
                    else:
                        chunks[-1] += line + "\n"
                for chunk in chunks:
                    print()
                    print("CHUNK LENGTH:", len(chunk))
                    print()
                print("Number of chunks:", len(chunks))
                eh = get_extra_headers(h, len(chunks))
                spreadsheet, headers = add_extra_headers(spreadsheet, headers, eh)
                print("Extra headers:", eh)
                for j in range(len(chunks)):
                    text = enclose + chunks[j].strip() + enclose
                    spreadsheet[eh[j]][i] = text
                    print()
                    print(text)
                    print()
    return spreadsheet, headers


def to_spreadsheet(filename, data, ordered_headers = None, delimeter='\t', count=None, enclose = "", max_char_cell = None, extra_headers = ""):
    if ordered_headers is None:
        ordered_headers = data.keys()

    max_column_length = 0
    for k in data.keys():
        max_column_length = max(max_column_length, len(data[k]))
    to_read = max_column_length if count is None else count

    with open(filename, 'w', newline='', encoding="utf8") as f:
        writer = csv.writer(f, delimiter=delimeter)
        writer.writerow(ordered_headers)

        for i in range(to_read):
            r = []
            for k in ordered_headers:
                val = data[k][i] if i < len(data[k]) else ''
                r.append(val)
            writer.writerow(r)

def sample_from_spreadsheet(spreadsheet, headers, count):
    # Get the number of data rows (excluding header)
    rows = list(range(1, len(spreadsheet[headers[0]])))

    # Choose a random sample without replacement
    sample_indices = sorted(random.sample(rows, count))

    # Create a new dict with the sampled rows
    sample_dict = {}

    # Set empty lists for each header
    for h in headers:
        sample_dict.setdefault(h, [])

    # Copy the row for each sample index
    for i in sample_indices:
        for h in headers:
            sample_dict[h].append(spreadsheet[h][i])

    return sample_dict

def ft_spreadsheet_from_gpt_pc_dict(filename, pc_dict, count=None):
    prompts = []
    completions = []
    for k in pc_dict.keys():
        pc_dict[k].replace("\n", " ")
        prompts.append(k)
        completions.append(pc_dict[k])

    out = {"prompt":prompts, "completion":completions}
    to_spreadsheet(filename, out, ordered_keys = ["prompt", "completion"], count=count)

def to_jsonl_prep_spreadsheet(filename, prompt_completion_pairs):
    with open(filename, "w", encoding="utf8") as f:
        f.write("prompt\tcompletion\n")

        for pc in prompt_completion_pairs.items():
            prompt = pc[0]
            prompt = prompt.replace("\t", "    ")
            prompt = prompt.replace("\n", " ")
            prompt += "   ###    "

            completion = pc[1].strip()
            completion = " " + completion
            completion = completion.replace("\t", "    ")
            completion += "   ###"
            f.write(prompt + "\t" + completion + "\n")

def jsonl_prep_spreadsheet_from_ft_spreadsheet(output_filename, input_filename, delimeter='\t'):
    data = from_spreadsheet(input_filename, ["prompt", "completion"], delimeter=delimeter)
    entry_count = len(data["prompt"])
    pc_pairs = {}
    for i in range(entry_count):
        prompt = data["prompt"][i]
        completion = data["completion"][i]
        pc_pairs[prompt] = completion
    to_jsonl_prep_spreadsheet(output_filename, pc_pairs)

def ft_prep_from_jsonl_prep_spreadsheet(input_filename):
    print("prepping")
    os.system("openai tools fine_tunes.prepare_data -f " + input_filename)

def ft_train(model, jsonl_filename, model_suffix = ""):
    if model_suffix != "":
        model_suffix = " --suffix " + model_suffix

    train_model_cmd = "openai api fine_tunes.create -t " + jsonl_filename + " -m " + model + model_suffix
    print(train_model_cmd)
    os.system(train_model_cmd)

def get_completions(prompts, delimeter = "   ###   ", take_before = "###", echo=True):
    pc_pairs = {}
    for prompt in prompts:
        prompt += delimeter
        completion = chatbot_response_robust(prompt, openai_model)
        if take_before is not None and take_before in completion:
            completion = completion.split(take_before)[0]
        pc_pairs[prompt] = completion
        print(prompt, "\n", completion, "\n")
    return pc_pairs

def split_spreadsheet(spreadsheet_filename, instance_name_base, copies, headers_in_all_instances = True):
    with open(spreadsheet_filename, "r", encoding="utf8") as f:
        lines = f.readlines()
        header = lines[0].split('\t')
        data_rows = len(lines)-1

        if data_rows < copies:
            raise Exception("More copies than data rows!")


        chunk_rows = math.floor(data_rows/copies)
        i = 0
        for copy in range(copies):
            temp_filename = instance_name_base + "_" + str(copy)
            first = i
            last = i + chunk_rows if copy < copies - 1 else len(lines)
            i = last
            with open(temp_filename, "w", encoding="utf8") as o:
                if headers_in_all_instances and copy > 0:
                    o.write(lines[0])
                for line in lines[first:last]:
                    o.write(line)


def recombine_split_spreadsheet(combined_spreadsheet_filename, instance_name_base, copies, headers_in_all_instances = True, cleanup = True):
    with open(combined_spreadsheet_filename, "w", encoding="utf8") as o:
        for copy in range(copies):
            input_filename = instance_name_base + "_" + str(copy)
            with open(input_filename, "r", encoding="utf8") as f:
                start = 1 if copy > 0 and headers_in_all_instances else 0
                lines = f.readlines()[start:]
                for line in lines:
                    o.write(line)
            if cleanup:
                os.remove(input_filename)

# DO NOT RUN FROM WITHIN gptner.py! WILL RUN RECURSIVELY WITHOUT END.
def run_multiple_gpt_instances(bash_filename, python_filename, spreadsheet_filename, python_filename_base, spreadsheet_instance_name_base, copies, static_args = "", cleanup = True):
    python_code = open(python_filename, "r", encoding="utf8").read()
    
    with open(bash_filename, "w", encoding="utf8") as b:
        for copy in range(copies):
            temp_python_filename = python_filename_base + "_" + str(copy) + ".py"
            temp_spreadsheet_filename = spreadsheet_instance_name_base + "_" + str(copy)
            cmd = "python3 " + temp_python_filename + " " + temp_spreadsheet_filename + " " + str(copy) + " " + static_args
            if copy < copies - 1:
                cmd += " &\n"
            b.write(cmd)

            with open(temp_python_filename, "w", encoding="utf8") as f:
                f.write(python_code)

    split_spreadsheet(spreadsheet_filename, spreadsheet_instance_name_base, copies)

    os.system("chmod +x " + bash_filename)
    os.system("./" + bash_filename)

    done = False
    while not done:
        done = True
        for i in range(copies):
            if not os.path.isfile("multi_launcher_instance_" + str(i) + "_complete"):
                done = False
                print("Waiting for instances to finish...")
                time.sleep(1)


    for i in range(copies):
        os.remove("multi_launcher_instance_" + str(i) + "_complete")

    print("All instances complete")

    recombine_split_spreadsheet(spreadsheet_filename, spreadsheet_instance_name_base, copies, cleanup)

    for copy in range(copies):
        temp_python_filename = python_filename_base + "_" + str(copy) + ".py"
        os.remove(temp_python_filename)

    if cleanup:
        os.remove(bash_filename)



