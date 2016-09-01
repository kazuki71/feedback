import sut as SUT

class Pool:
	"""
	This class represents structure for Pool
	"""

	def __init__(self, pid):
		self.pid = pid			# unique id for this pool
		self.sut = SUT.sut()		# SUT object
		self.nseqs = [[]]		# list of non-error sequences
		self.eseqs = []			# list of error sequences
		self.set_nseqs = set()		# set of non-error sequences
		self.set_eseqs = set()		# set of error sequences
		self.dict_cover = dict()	# dictionary, key: coverage by this pool, value: frequency of coverage by this pool
		self.time = 0.0			# time of using this pool
		self.count = 0			# frequency of using this pool
		self.score = 0.0			# score of this pool
		self.uniqueness = 0.0		# uniqueness of this pool
