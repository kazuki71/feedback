from Pool import *

class Pools:
	"""
	This class represents structure for handling each Pool
	"""

	def __init__(self):
		self.pools = list()
		self.pid = 0

	def length(self):
		return len(self.pools)

	def get_all_pools(self):
		return self.pools

	def _update_pools(self, newpools):
		self.pools = newpools

	def create_pool(self):
		self.pid += 1
		self.pools.append(Pool(self.pid))

	def select_pool(self, config):
		"""
		select pool which has maxmum coverage score
		"""
		return self._select_pool_helper(config)

	def _select_pool_helper(self, config):
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
		print "*****************************************************"
		print "*****************************************************"
		for key, value in sorted(V.pool_frequency.iteritems(), key = lambda (k, v): (k, v)):
			print "pool", key, "is selected", value, "times"
		V.pool_frequency.clear()
		newpools = []
		all_pools = self.get_all_pools()
		for pool in all_pools:
			pool.update_uniqueness(all_pools, config)
		sortedpools = sorted(all_pools, key = lambda x: x.uniqueness, reverse = True)
		for pool in sortedpools:
			newpools.append(pool)
			if config.delete:
				V.sequences = V.sequences.union(pool.set_nseqs).union(pool.set_eseqs)
			if len(newpools) == num:
				self._update_pools(newpools)
				break
		for p in sorted(newpools, key = lambda x: x.pid):
			print "pool", p.pid, "is selected"
