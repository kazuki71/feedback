from Pools import *

class PoolsWithTwoLists(Pools):
        """ 
        this class is a subclass from class Pools
	the difference between Pools and PoolsWithTwolists is how to select pool by select_pool()
        """

        def __init__(self):
		"""
		new pool are stored in self.pools
		selected pools with high uniqueness in delete_pools() are stored in self.pools_with_high_uniqueness 
		"""
                Pools.__init__(self)
                self.pools_with_high_uniqueness = list()
                self.index = -1
		self.num = 1

	def length(self):
		return len(self.pools) + len(self.pools_with_high_uniqueness)

	def get_all_pools(self):
		return self.pools + self.pools_with_high_uniqueness

	def _update_pools(self, newpools):
		self.pools = list()
		self.pools_with_high_uniqueness = newpools
		self.index = 0

	def select_pool(self, config):
		"""
		if index == -1, select pool which has maxmum coverage score from self.pools
		otherwise, select pool by self.pools_with_high_uniqueness[index]
		"""
		if self.index == -1 and self.num > 0:
			selected = self._select_pool_helper(config)
			if len(self.pools_with_high_uniqueness):
				self.num -= 1
				if self.num == 0:
					self.index = 0
		else:
			selected = self.pools_with_high_uniqueness[self.index]
			self.index += 1
			if self.index == len(self.pools_with_high_uniqueness):
				if len(self.pools):
					self.num = self.index * 2
					self.index = -1
				else:
					self.index = 0

		return selected
