import sut as SUT
import time

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

	def covered(self, config):
		coverages = self.sut.currStatements() if config.which else self.sut.currBranches()
		for c in coverages:
			if config.notcount:
				if not c in self.dict_cover:
					self.dict_cover[c] = 1
			else:
				if c in self.dict_cover:
					self.dict_cover[c] += 1
				else:
					self.dict_cover[c] = 1

	def feedback(self, config, V, R, start):
		elapsed = time.time()
		if self.pid in V.pool_frequency.keys():
			V.pool_frequency[self.pid] += 1
		else:
			V.pool_frequency[self.pid] = 1
		seq = R.choice(self.nseqs)[:]
		self.sut.replay(seq)
		if time.time() - start > config.timeout:
			return False
		n = R.randint(2, 100) if R.randint(0, 9) == 0 else 1
		num_skips = 0
		for i in xrange(n):
			a = self.sut.randomEnabled(R)
			seq.append(a)
			tuple_seq = tuple(seq)
			if self.redundant(tuple_seq, V):
				del seq[-1]
				num_skips += 1
				if n == num_skips:
					V.num_redundancies += 1
					return True
				continue
			ok = self.sut.safely(a)
			self.update_coverages(a, config, V, start)
			if not ok:
				print "FIND BUG in ", time.time() - start, "SECONDS by pool", self.pid
				V.num_eseqs += 1
				V.sequences.add(tuple_seq)
				self.eseqs.append(seq)
				self.set_eseqs.add(tuple_seq)
				self.time += (time.time() - elapsed)
				self.handle_failure(V, start)
				return True
			if time.time() - start > config.timeout:
				return False
		if not config.single:
			self.covered(config)
		V.num_nseqs += 1
		V.sequences.add(tuple_seq)
		self.nseqs.append(seq)
		self.set_nseqs.add(tuple_seq)
		self.time += (time.time() - elapsed)
		return True

	def handle_failure(self, V, start):
		filename = 'failure' + `V.fid` + '.test'
		sut.saveTest(self.sut.test(), filename)
		V.fid = V.fid + 1

	def redundant(self, tuple_seq, V):
		if tuple_seq in V.sequences:
			return True
		else:
			return False

	def update_coverages(self, a, config, V, start):
		flag = True
		if self.sut.newBranches() != set([]):
			for b in self.sut.newBranches():
				if not b in V.branches:
					V.branches.add(b)
					if config.running:
						if flag:
							print "ACTION:", sel.sut.prettyName(a[0])
							flag = False
						print time.time() - start, len(V.branches), "New branch", b
		if self.sut.newStatements() != set([]):
			for s in self.sut.newStatements():
				if not s in V.statements:
					V.statements.add(s)

	def update_score(self, config):
		if self.time == 0.0 or self.count == 0 or len(self.sut.allBranches()) == 0 or len(self.sut.allStatements()) == 0:
			self.score = float('inf')
		elif config.which:
			self.score = len(self.sut.allStatements()) * 1.0e9 / self.time
		else:
			self.score = len(self.sut.allBranches()) * 1.0e9 / self.time

	def update_uniqueness(self, pools):
		if self.time == 0.0 or self.count == 0 or len(self.sut.allBranches()) == 0 or len(self.sut.allStatements()) == 0:
			self.uniqueness = float('inf')
			return
		uniqueness = 0.0
		for c in self.dict_cover:
			uniqueness += self._update_uniqueness_helper(c, pools)
		self.uniqueness = uniqueness / len(self.dict_cover)

	def _update_uniqueness_helper(self, c, pools):
		totalcovered = 0.0
		for p in pools:
			if c in p.dict_cover:
				totalcovered += p.dict_cover[c]
		return self.dict_cover[c] / totalcovered
