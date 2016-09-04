class Variables:
	"""
	This class represents structure to wrap variables
	"""

	def __init__(self):
		self.fid = 0			# unique id for output of failure test
		self.num_nseqs = 0		# total number of non-error sequences
		self.num_eseqs = 0		# total number of error sequences
		self.num_redundancies = 0	# total number of creating redundancies
		self.sequences = set()		# a set of sequences (non-error + error)
		self.branches = set()		# a set of branches coverage
		self.statements = set()		# a set of statements coverage
		self.pool_frequency = dict()	# key is Pool.pid, value is how many times Pool.pid is selected for Pool.feedback()
