import multiprocessing, random, string, nltk, sys, runtime
from convenience import *

# Score is a tuple containing (size of largest string, levenshtein distance)
def levenshtein(string1, string2, i, j):
	return (nltk.edit_distance(string1, string2), i, j)

def random_string(char_count):
	return ''.join(random.choices(string.ascii_uppercase, k=char_count))

class CompareMatrix:
	def __init__(self):
		self.matrix = []
		self.data = None

	def setup(self, data_or_size, default = None):
		self.matrix = []
		matrix_size = len(data_or_size) if type(data_or_size) == list else data_or_size
		for i in range(matrix_size):
			self.matrix.append([default for _ in range(matrix_size)])
		if type(data_or_size) == list:
			self.data = data_or_size

	def matrix_size(self):
		if len(self.matrix) > 0 and sum([len(x) for x in self.matrix]) != len(self.matrix)*len(self.matrix):
			raise Exception("CompareMatrix is not square!")
		return len(self.matrix)

	# data_matrix: the list of data values represented by the indices of the matrix
	# comparison_function: a function taking two values from data_matrix and the indices i, j as arguments, returning some output from the comparison (such as Levenshtein distance)
	# processes: the number of processes used in multithreading the comparisons
	# max_memory_size_gb: the maximum amount of memory each process can use 
	def compare(self, comparison_function, top_right_only = False, include_main_diagonal = True, processes=10, max_memory_gb = 1, max_chunks = 10, echo=False):
		if type(self.data) is None or type(self.data) != list:
			raise Exception("No data specified in CompareMatrix.data!")

		runtime_estimate = runtime.RuntimeEstimate()

		# Set up multiple processes
		with multiprocessing.Pool(processes=processes) as pool:
			# Store pairs of strings along with their indices
			arg_tuples = []

			# Keep track of how many memory chunks have been used
			chunk_id = 0

			# Get the size of the matrix
			size = self.matrix_size()

			# Track the number of bytes used in the current chunk
			memory_used_bytes = 0

			# Calculate the maximum number of bytes to use per chunk (converting from Gb)
			max_memory_size_bytes = max_memory_gb*1024**3

			final_i = [[size-1, size-1],[size-2, size-1]][top_right_only][include_main_diagonal]
			final_j = [[size-2, size-1],[size-1, size-1]][top_right_only][include_main_diagonal]

			if echo:
				print("Preparing data for processing...")

			runtime_estimate.start()

			# Iterate through all pairs
			for i in range(size):
				# Set where to start j depending on value of top_right_only
				j_start = [0, i][top_right_only]

				for j in range(j_start, size):
				
					# Skip the main diagonal if that's how it's set up
					if not include_main_diagonal and i == j:
						continue

					# Add a single comparison along with matrix indices to the list of tuples to evaluate
					arg_tuples.append((self.data[i], self.data[j], i, j))

					# Add the size of the tuple to track how much memory is used in the current chunk
					memory_used_bytes += sum([sys.getsizeof(x) for x in arg_tuples[-1]]) + sys.getsizeof(arg_tuples[-1])

					# If we've exceeded max memory size per process or have reached the last tuple, save a .pickle of the chunk tuples
					if (memory_used_bytes > max_memory_size_bytes and max_memory_gb is not None) or (i == final_i and j == final_j):

						# Set the filename
						filename_designator = "cluster_finder_score_chunk_"+str(chunk_id)

						# Save the pickle
						quickle_out(arg_tuples, filename_designator)

						# Reset the memory addition variables
						memory_used_bytes = 0
						chunk_id += 1
						arg_tuples = []

						if echo:
							print("On chunk", chunk_id)

						# Alert user if we've used too much memory
						if chunk_id >= max_chunks and max_chunks is not None:
							raise Exception("Too many chunks used during ClusterFinder scoring - increase chunk size or number of chunks, or run fewer comparisons!")
				if echo and i % 100 == 99:
					runtime_estimate.update_progress(i/size)
					print(runtime_estimate)

			runtime_estimate.start()
			# Use multiprocessing to run comparisons on chunks
			for i in range(chunk_id):

				# Get filename of tuple
				filename_designator = "cluster_finder_score_chunk_" + str(i)

				# Load the tuple
				arg_tuple = quickle_in(filename_designator)

				# Delete the pickle of the tuple we just loaded in
				quickle_delete(filename_designator)

				if echo:
					print("done.")
					print("Scoring chunk", i, "/", chunk_id, "...\t", end="")
				# Collect results from multiprocessing the comparisons
				results = pool.starmap(comparison_function, arg_tuple)

				if echo:
					print("done.")

				# Assign the results to the matrix
				for r in results:
					result = r[0]
					j = r[1]
					k = r[2]
					self.matrix[j][k] = result

				runtime_estimate.update_progress((i+1)/chunk_id)
				print(runtime_estimate)

	def print(self, convert = {}, chr_per_cell=None, padding=" "):
		lines = []
		max_len = 0
		for i in range(self.matrix_size()):
			lines.append([])
			for j in range(self.matrix_size()):
				disp = self.matrix[i][j]
				if disp in convert.keys():
					disp = convert[disp]
				disp = str(disp)
				if chr_per_cell is not None:
					disp = disp[:chr_per_cell]
				max_len = max(max_len, len(disp))
				lines[-1].append(disp)
		for line in lines:
			s = ""
			for d in line:
				for i in range(max_len - len(d)):
					s += " "
				s += padding + d

			print(s)

	def select_comparisons(self, criterion_function, top_right_only = False, include_main_diagonal=True):
		comparisons = []
		for i in range(self.matrix_size()):

			# Set where to start j depending on value of top_right_only
			j_start = [0, i][top_right_only]
			for j in range(j_start, self.matrix_size()):
				if not include_main_diagonal and j == i:
					continue
				if criterion_function(self.matrix[i][j]):
					comparisons.append((self.data[i], self.data[j], i, j))
		return comparisons



