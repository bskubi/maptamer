import pickle, os

def quickle_out(data, filename_designator = "quickle_temp.quickle"):
	filename = "quickle/" + filename_designator + ".quickle"
	with open(filename, "wb") as file:
		pickle.dump(data, file)

def quickle_in(filename_designator = "quickle_temp.pickle"):
	filename = "quickle/" + filename_designator + ".quickle"
	if not os.path.exists(filename):
		return None
	return pickle.load(open(filename, "rb"))


def quickle_runonce(filename_designator, function, args = ()):
	filename = "quickle/" + filename_designator + ".quickle"
	stored = quickle_in(filename_designator)
	if stored is not None:
		print("Found stored version of", filename_designator)
		return stored
	result = function(*args) if len(args) > 0 else function()
	quickle_out(result, filename_designator)
	return result

def quickle_delete(filename_designator):
	delete("quickle/" + filename_designator + ".quickle")

def delete(filename):
	if os.path.exists(filename):
		os.remove(filename)

def quickle_cleanup(folder = "./"):
	pass
