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

	def _update_pools(self, newpools):
		self.pools = newpools

	def create_pool(self):
		self.pid += 1
		self.pools.append(Pool(self.pid))

	def select_pool(self, config):
		"""
		select pool which has maxmum coverage score
		"""
		if config.directed:
			self.pools[0].count += 1
			return self.pools[0]
		else:
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
		for pool in self.pools:
			pool.update_uniqueness(self.pools, config)
		sorted_pools = sorted(self.pools, key = lambda x: x.uniqueness, reverse = True)
		newpools = []
		for pool in sorted_pools:
			newpools.append(pool)
			if len(newpools) == num:
				self._update_pools(newpools)
				break
