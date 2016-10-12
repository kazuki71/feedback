import sut as SUT
import sys
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
		self.covered = dict()		# dictionary, key: coverage by this pool, value: frequency of coverage by this pool
		self.time = 0.0			# how many seconds this pool is used in feedback()
		self.count = 0			# how many times this pool is selected in select_pool()
		self.score = 0.0		# score of this pool
		self.uniqueness = 0.0		# uniqueness of this pool
		self.survived = 0		# how many times this pool is survived from delete_pools()

	def feedback(self, config, V, R, start):
		"""
		feedback directed random test generation
		"""
		seq = R.choice(self.nseqs)[:]
		self.sut.replay(seq)
		acTable = dict.fromkeys(self.sut.actionClasses(), 0)
		if time.time() - start > config.timeout:
			return False
		if config.directed:
			n = R.randint(2, 100) if R.randint(0, 9) == 0 else 1
		else:
			n = R.randint(1, 100)
		num_skips = 0
		doQuickTests = False
		snew = set()
		bnew = set()
		elapsed = time.time()
		for i in xrange(n):
			a = self.sut.randomEnabled(R)
			seq.append(a)
			tuple_seq = tuple(seq)
			if self.redundant(tuple_seq, V):
				num_skips += 1
				if n == num_skips:
					V.num_redundancies += 1
					return True
				continue
			ok = self.sut.safely(a)
			propok = self.sut.check()
			acTable[self.sut.actionClass(a)] += 1
			self.time += (time.time() - elapsed)
			if config.quickTests and ((self.sut.newCurrBranches() != set([]) and not self.sut.newCurrBranches().issubset(V.branches)) or (self.sut.newCurrStatements() != set([]) and not self.sut.newCurrStatements().issubset(V.statements))):
				snew.update(self.sut.newCurrStatements().difference(V.statements))
				bnew.update(self.sut.newCurrBranches().difference(V.branches))
				doQuickTests = True
			self.update_coverage(a, time.time() - start, config, V)
			elapsed = time.time()
			if (not ok) or (not propok):
				print "FIND BUG IN", time.time() - start, "SECONDS USING POOL", self.pid
				V.num_eseqs += 1
				V.sequences.add(tuple_seq)
				self.eseqs.append(seq)
				self.handle_failure(V, start)
				if config.quickTests and doQuickTests:
					self.quick_tests(snew, bnew, V, start)
				return True
			if time.time() - start > config.timeout:
				return False
		if config.directed:
			if max(acTable.values()) <= len(self.sut.actionClasses()) * 1.8:
				V.num_nseqs += 1
				self.nseqs.append(seq)
		else:
			if max(acTable.values()) <= len(self.sut.actionClasses()) * 5.0:
				V.num_nseqs += 1
				self.nseqs.append(seq)
		V.sequences.add(tuple_seq)
		if config.quickTests and doQuickTests:
			self.quick_tests(snew, bnew, V, start)
		return True
	
	def handle_failure(self, V, start):
		filename = 'failure' + `V.fid` + '.test'
		self.sut.saveTest(self.sut.test(), filename)
		V.fid = V.fid + 1

	def quick_tests(self, snew, bnew, V, start):
		test = list(self.sut.test())
		sys.stdout.flush()
		print "Handling new coverage for quick testing"
		for s in snew:
			print "NEW STATEMENT", s
		for b in bnew:
			print "NEW BRANCH", b
		trep = self.sut.replay(test, catchUncaught = True, checkProp = True)
		sremove = []
		scov = self.sut.currStatements()
		for s in snew:
			if s not in scov:
				print "REMOVING", s
				sremove.append(s)
		for s in sremove:
			snew.remove(s)
		bremove = []
		bcov = self.sut.currBranches()
		for b in bnew:
			if b not in bcov:
				print "REMOVING", b
				bremove.append(b)
		for b in bremove:
			bnew.remove(b)
		beforeReduceS = set(self.sut.allStatements())
		beforeReduceB = set(self.sut.allBranches())
		print "Original test has", len(test), "steps"
		failProp = self.sut.coversAll(snew, bnew, catchUncaught = True, checkProp = True)
		print "REDUCING..."
		startReduce = time.time()
		oritinal = test
		test = self.sut.reduce(test, failProp, True, False)
		print "Reduced test has", len(test), "steps"
		print "REDUCED IN", time.time() - startReduce, "SECONDS"
		self.sut.prettyPrintTest(test)
		sys.stdout.flush()
		for s in self.sut.allStatements():
			if s not in beforeReduceS:
				print "NEW STATEMENT FROM REDUCTION", s
		for b in self.sut.allBranches():
			if b not in beforeReduceB:
				print "NEW BRANCH FROM REDUCTION", b
		outname = 'quick' + `V.qid` + '.test'
		outf = open(outname, 'w')
		V.qid += 1
		print
		print "FINAL VERSION OF TEST, WITH LOGGED REPLAY:"
		self.sut.verbose(True)
		i = 0
		self.sut.restart()
		for s in test:
			steps = "# step " + str(i)
			print self.sut.prettyName(s[0]).ljust(80 - len(steps), ' '), steps
			self.sut.safely(s)
			i += 1
			outf.write(self.sut.serializable(s) + "\n")
		self.sut.verbose(False)
		sys.stdout.flush()
		outf.close()

	def redundant(self, tuple_seq, V):
		"""
		V.sequences is set where it contains all sequences (non-error + error) generated
	        by all pools
		"""
		if tuple_seq in V.sequences:
			return True
		else:
			return False

	def update_coverage(self, a, t, config, V):
		if config.running:
			if self.sut.newBranches() != set([]) and not self.sut.newBranches().issubset(V.branches):
				print "ACTION:", self.sut.prettyName(a[0])
				newBranches = self.sut.newBranches().difference(V.branches)
				for b in newBranches:
					print t, len(V.branches), "New branch", b
					sys.stdout.flush()
			if self.sut.newStatements() != set([]) and not self.sut.newStatements().issubset(V.statements):
				print "ACTION:", self.sut.prettyName(a[0])
				newStatements = self.sut.newStatements().difference(V.statements)
				for s in newStatements:
					print t, len(V.statements), "New branch", s
					sys.stdout.flush()
		if self.sut.currBranches() != set([]):
			for b in self.sut.currBranches():
				self.covered[b] = self.covered[b] + 1 if b in self.covered else 1
				if not b in V.branches:
					V.branches.add(b)
		if self.sut.currStatements() != set([]):
			for s in self.sut.currStatements():
				if not s in V.statements:
					V.statements.add(s)
		
	def update_score(self, config):
		"""
		if pool is not investigated enough, set score as infinite
		otherwise, score = len(coverage by the pool) / time of using the pool
		"""
		if self.time == 0.0 or self.count == 0 or len(self.sut.allBranches()) == 0 or len(self.sut.allStatements()) == 0:
			self.score = float('inf')
		else:
			self.score = len(self.sut.allBranches()) * 1.0e9 / self.time

	def update_uniqueness(self, pools, config):
		"""
		if pool is not investigated enough, set uniqueness as infinite
		otherwise, check how unique coverages the pool covers compared with other pools 
		"""
		if self.time == 0.0 or self.count == 0 or len(self.sut.allBranches()) == 0 or len(self.sut.allStatements()) == 0:
			self.uniqueness = float('inf')
		else:
			uniqueness = 0.0
			for c in self.covered:
				uniqueness += self._update_uniqueness_helper(c, pools)
			self.uniqueness = uniqueness / len(self.covered)

	def _update_uniqueness_helper(self, c, pools):
		totalcovered = 0.0
		for p in pools:
			if c in p.covered:
				totalcovered += p.covered[c]
		return self.covered[c] / totalcovered
