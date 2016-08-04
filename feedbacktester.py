import argparse
import math
import random
import sut as SUT
import sys
import time
from collections import namedtuple

def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('-c', '--coverages', type = int, default = 1,
                            help = 'Which coverages used for measuring uniquness of pool. If 1, branch coverages. If 0, statement coverages. (default = 1).')
	parser.add_argument('-i', '--inp', type = int, default = 10,
                            help = 'Initial number of pools (10 default).')
	parser.add_argument('-m', '--mnp', type = int, default = 100,
                            help = 'Maximum number of pools (100 default).')
	parser.add_argument('-n', '--nseconds', type = int, default = 1,
                            help = 'Each n seconds new pool is added (default each 1 second).')
	parser.add_argument('-s', '--seed', type = int, default = None,
                            help = 'Random seed (default = None).')
	parser.add_argument('-t', '--timeout', type = int, default = 3600,
                            help = 'Timeout in seconds (300 default).')
	parser.add_argument('-C', '--count', type = bool, default = True,
                            help = 'Whether count number of coverages or not for measuring uniquness of pool (default = True).')
        parser.add_argument('-I', '--internal', type = bool, default = False,
                            help = 'Produce internal coverage report at the end (default = False).')
	parsed_args = parser.parse_args(sys.argv[1:])
	return (parsed_args, parser)

def make_config(pargs, parser):
	pdict = pargs.__dict__
	key_list = pdict.keys()
	arg_list = [pdict[k] for k in key_list]
	Config = namedtuple('Config', key_list)
	nt_config = Config(*arg_list)
	return nt_config

def check_redundancy(seq, a, keys, sut):
	if not len(seq):
		return False
	index = 0
	for i in seq:
		if not check_redundancy_helper(sut.actOrder(i), keys, index, len(seq) + 1):
			return False
		index += 1
	return check_redundancy_helper(sut.actOrder(a), keys, index, len(seq) + 1)

def check_redundancy_helper(aorder, keys, index, length):
	return aorder in keys.keys() and (index, length) in keys[aorder]

def covered(pool):
	global config
	if config.coverages:
		coverages = pool[0].currBranches()
	else:
		coverages = pool[0].currStatements()
	for c in coverages:
		if config.count:
			if c in pool[4]:
				pool[4][c] += 1
			else:
				pool[4][c] = 1
		else:
			if not c in pool[4]:
				pool[4][c] = 1

def create_new_pool():
	return [SUT.sut(), [[]], [], 0.0, dict(), 0.0]

def delete_pools(pools, num):
	global config
	if config.inp == 1:
		return pools
	newpools = []
	for pool in pools:
		pool[5] = get_uniquness(pool, pools)
	sortedpools = sorted(pools, key = lambda x : x[5], reverse = True)
	for pool in sortedpools:
		newpools.append(pool)
		if len(newpools) == num:
			break
	return newpools

def feedback(pool, keys):
	global config, fid, R, start
	elapsed = time.time()
	sut = pool[0]
	seq = R.choice(pool[1])[:]
	sut.replay(seq)
	if time.time() - start > config.timeout:
		return False
	if R.randint(0, 9) == 0:
		n = R.randint(2, 100)
	else:
		n = 1
	skipped = 0
	for i in xrange(n):
		a = sut.randomEnabled(R)
		if check_redundancy(seq, a, keys, sut):
			skipped += 1
			if n == skipped:
				return True
			continue
		seq.append(a)
		if not sut.safely(a):
			print "FIND BUG in ", time.time() - start, "SECONDS"
			updaate_keys(seq, keys, sut)
			pool[2].append(seq)
			pool[3] += (time.time() - elapsed)
			fid = handle_failure(sut, fid, start)
			return True
		if time.time() - start > config.timeout:
			return False
	updaate_keys(seq, keys, sut)
	if config.inp != 1:
		covered(pool)
	pool[1].append(seq)
	pool[3] += (time.time() - elapsed)
	return True

def get_score(pool):
	global config
	if pool[3] == 0.0 or len(pool[0].allBranches()) == 0 or len(pool[0].allStatements()) == 0:
		return float('inf')
	if config.coverages:
		return len(pool[0].allBranches()) / pool[3]
	else:
		return len(pool[0].allStatements()) / pool[3]

def get_uniquness(pool, pools):
	if len(pool[4]) == 0:
		return float('inf')
	uniquness = 0.0
	for c in pool[4]:
		uniquness += get_uniquness_helper(pool, c, pools)
	return uniquness / len(pool[4])

def get_uniquness_helper(pool, c, pools):
	totalcovered = 0.0
	for p in pools:
		if c in p[4]:
			totalcovered += p[4][c]
	return pool[4][c] / totalcovered

def handle_failure(sut, fid, start):
	filename = 'failure' + `fid` + '.test'
	sut.saveTest(sut.test(), filename)
	return fid + 1

def internal(pools):
	i = 0
	for pool in pools:
		print "Producing internal coverage report for pool", i, "..."
		pool[0].internalReport()
		print ""
		i += 1

def select_pool(pools):
	global config
	if config.inp == 1:
		return pools[0]
	maxscore = -1.0
	for pool in pools:
		score = get_score(pool)
		if score == float('inf'):
			return pool
		if score > maxscore:
			maxscore = score
			selected = pool
	return selected

def updaate_keys(seq, keys, sut):
	index = 0
	for i in seq:
		if sut.actOrder(i) in keys.keys():
			if (index, len(seq)) in keys[sut.actOrder(i)]:
				continue
			else:
				keys[sut.actOrder(i)].add((index, len(seq)))
		else:
			keys[sut.actOrder(i)] = set((index, len(seq)))
		index += 1

def main():
	global config, fid, R, start
	parsed_args, parser = parse_args()
	config = make_config(parsed_args, parser)
	print('Feedback-controlled random testing using config={}'.format(config))
	R = random.Random(config.seed)
	fid = 0
	start = time.time()
	pools = []
	keys = dict()
	for i in xrange(config.inp):
		pools.append(create_new_pool())
	lastadded = time.time()
	while time.time() - start < config.timeout:
		if time.time() - lastadded > config.nseconds:
			pools.append(create_new_pool())
			lastadded = time.time()
		if not feedback(select_pool(pools), keys):
			break
		if len(pools) > config.mnp:
			pools = delete_pools(pools, config.mnp / 2)
	if config.internal:
		internal(pools)

if __name__ == '__main__':
	main()
