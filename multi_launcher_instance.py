import sys, time, gptner, extract, aliases, random

if len(sys.argv) == 3:
	gptner.setup()

	# Expecting spreadsheet filename, but you can specify the arguments these instances receive in the multi_launcher.py file
	filename = sys.argv[1]

	# Get ordered headers and spreadsheet from the file.
	headers = gptner.get_spreadsheet_headers(filename)
	spreadsheet = gptner.from_spreadsheet(filename)

	consensus_name_list = spreadsheet["consensus_name"]


	# Generate consensus name for cluster
	# Clean consensus names
	consensus_name_clean = aliases.clean(consensus_name_list, "consensus_name_clean")
	spreadsheet["consensus_name_clean"] = consensus_name_clean
	headers = headers + ["consensus_name_clean"]
	gptner.to_spreadsheet(filename, spreadsheet, headers)

	# Identify specific names

	aliases.get_specific(filename, ["consensus_name_clean", "consensus_name_specific"])

	#Clean
	extract.clean_responses(filename, filename, gptner.models["alias1_specific_clean"], ["consensus_name_specific", "consensus_name_specific_clean"])
	
	# Generate second alias

	#aliases.get_aliases(filename, filename, ["alias1_specific", "alias1_specific_clean", "alias2"], ["alias1_specific_clean", "alias2"])
	#extract.clean_responses(filename, filename, gptner.models["amplification_clean"], ["alias2", "alias2_clean"])
	
	# Utility code - should not need to be changed.
	open("multi_launcher_instance_" + sys.argv[2] + "_complete", "w")
	print("Done with ", sys.argv[2])

