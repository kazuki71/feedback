# encapsulate variables to avoid global variables

class GlobalVariables:
	def __init__(self):
		self.fid = 0
		self.pid = 0
		self.num_nseqs = 0
		self.num_eseqs = 0
		self.num_redundancies = 0
		self.all_seqs = set()
		self.all_branches = set()
		self.all_statements = set()
		self.pool_frequency = dict()
