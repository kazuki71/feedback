from Pool import *

class Pools:
	"""
	This class represents structure for handling each Pool
	"""

	def __init__(self):
		self.pools = list()
		self.pid = 0

	def internalReport(self):
		print "TSTL INTERNAL COVERAGE REPORT:"
		src_file_with_adata = dict()
		src_file_with_ldata = dict()
		branches = set()
		statements = set()
		for pool in self.pools:
			if pool.sut._sut__oldCovData == None:
				continue
			for src_file in pool.sut._sut__oldCovData.measured_files():
				if src_file not in src_file_with_adata:
					src_file_with_adata[src_file] = [[], set()]
				if src_file not in src_file_with_ldata:
					src_file_with_ldata[src_file] = [[], set()]
				adata = pool.sut._sut__oldCovData.arcs(src_file)
				for a in adata:
					if a not in src_file_with_adata[src_file][1]:
						src_file_with_adata[src_file][0].append(a)
						src_file_with_adata[src_file][1].add(a)
				ldata = list(set(pool.sut._sut__oldCovData.lines(src_file)))
				for l in ldata:
					if l not in src_file_with_ldata[src_file][1]:
						src_file_with_ldata[src_file][0].append(l)
						src_file_with_ldata[src_file][1].add(l)
				for (f, a) in pool.sut._sut__allBranches:
					if f == src_file and a not in adata:
						print "WARNING:", a, "VISITED BUT MISSING FROM COVERAGEDATA USING POOL", pool.pid
				for a in adata:
					if (src_file, a) not in pool.sut._sut__allBranches:
						print "WARNING:", a, "IN COVERAGEDATA BUT NOT IN TSTL COVERAGE USING POOL", pool.pid
				for (f, l) in pool.sut._sut__allStatements:
					if f == src_file and l not in ldata:
						print "WARNING:", l, "VISITED BUT MISSING FROM COVERAGEDATA USING POOL", pool.pid
				for l in ldata:
					if (src_file, l) not in pool.sut._sut__allStatements:
						print "WARNING:", l, "IN COVERAGEDATA BUT NOT IN TSTL COVERAGE USING POOL", pool.pid
			for (f, l) in pool.sut._sut__allStatements:
				if f not in pool.sut._sut__oldCovData.measured_files():
					print "WARNING:", (f, l), "IS NOT IN COVERAGEDATA USING POOL", pool.pid
			for b in pool.sut._sut__allBranches:
				branches.add(b)
			for s in pool.sut._sut__allStatements:
				statements.add(s)
		for (src_file, adata) in src_file_with_adata.items():
			print src_file, "ARCS:", len(adata[0]), sorted(adata[0])
		for (src_file, ldata) in src_file_with_ldata.items():
			print src_file, "ARCS:", len(ldata[0]), sorted(ldata[0])
		print "TSTL BRANCH COUNT:", len(branches)
		print "TSTL STATEMENT COUNT:", len(statements)

	def length(self):
		return len(self.pools)

	def _update_pools(self, newpools):
		self.pools = newpools

	def create_pool(self):
		self.pid += 1
		self.pools.append(Pool(self.pid))

	def select_pool(self, config, V):
		"""
		select pool which has maxmum coverage score
		"""
		if config.directed:
			self.pools[0].count += 1
			return self.pools[0]
		else:
			return self._select_pool_helper(config, V)

	def _select_pool_helper(self, config, V):
		V.ave_score = 0.0
		for pool in self.pools:
			pool.update_score(config)
			if pool.score == float('inf'):
				pool.count += 1
			V.ave_score += pool.score

		maxscore = -1.0
		for pool in self.pools:
			pool.update_score(config)
			if pool.score == float('inf'):
				pool.count += 1
				return pool
			elif pool.score > maxscore:
				maxscore = pool.score
				selected = pool
		selected.count += 1
		return selected

	def delete_pools(self, num, config, V):
		"""
		delete and select num pools which are more uniqueness than others
		"""
		for pool in self.pools:
			pool.update_uniqueness(self.pools, config)
		sorted_pools = sorted(self.pools, key = lambda x: x.uniqueness, reverse = True)
		newpools = []
		V.ave_uniqueness = 0.0
		for pool in sorted_pools:
			pool.survived += 1
			newpools.append(pool)
			V.ave_uniqueness += pool.uniqueness
			if len(newpools) == num:
				self._update_pools(newpools)
				V.ave_uniqueness /= num
				break
