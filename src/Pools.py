from Pool import *

class Pools:
	"""
	This class represents structure for handling each Pool
	"""
	def __init__(self):
		self.pools = list()
		self.pid = 0

	def create_pool(self):
		self.pid += 1
		self.pools.append(Pool(self.pid))

	def select_pool(self, config):
		"""
		select pool, which has maxmum coverage score
		"""
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
		if config.delete:
			V.sequences.clear()
		for key, value in sorted(V.pool_frequency.iteritems(), key = lambda (k, v): (k, v)):
			print "pool", key, "is used", value, "times"
		V.pool_frequency.clear()
		newpools = []
		for pool in self.pools:
			pool.update_uniqueness(self.pools)
		sortedpools = sorted(self.pools, key = lambda x: x.uniqueness, reverse = True)
		for pool in sortedpools:
			newpools.append(pool)
			if config.delete:
				V.sequences = V.sequences.union(pool.set_nseqs).union(pool.set_eseqs)
			if len(newpools) == num:
				break
		sortednewpools = sorted(newpools, key = lambda x: x.pid)
		for pool in sortednewpools:
			print "select pool", pool.pid, "time", pool.time, "count", pool.time, "score", pool.score, "uniqueness", pool.uniqueness
		self.pools = newpools
