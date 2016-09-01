import argparse
import math
import random
import sut as SUT
import sys
import time
from collections import namedtuple
from Variables import *
from Pool import *

def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('-d', '--delete', action = 'store_true',
                            help = 'Delete corresponding sequences from all_seqs when delete pool.')
	parser.add_argument('-i', '--inp', type = int, default = 10,
                            help = 'Initial number of pools (10 default).')
	parser.add_argument('-m', '--mnp', type = int, default = 100,
                            help = 'Maximum number of pools (100 default).')
	parser.add_argument('-n', '--nseconds', type = int, default = 1,
                            help = 'Each n seconds new pool is added (default each 1 second).')
	parser.add_argument('-q', '--quickTests', action = 'store_true',
                            help = 'Produce quick tests for coverage.')
	parser.add_argument('-r', '--running', action = 'store_true',
                            help = 'Produce running branch coverage report.')
	parser.add_argument('-s', '--seed', type = int, default = None,
                            help = 'Random seed (default = None).')
	parser.add_argument('-t', '--timeout', type = int, default = 3600,
                            help = 'Timeout in seconds (3600 default).')
	parser.add_argument('-w', '--which', action = 'store_true',
                            help = 'Using statement coverages to select and delete pool instead of branch coverages.')
	parser.add_argument('-N', '--notcount', action = 'store_true',
                            help = 'Not count number of coverages to delete pool. Instead of it, 1 if pool covers coverage.')
        parser.add_argument('-I', '--internal', action = 'store_true',
                            help = 'Produce internal coverage report at the end.')
	parser.add_argument('-S', '--single', action = 'store_true',
                            help = 'Using only single pool instead of multi pools.')
	parsed_args = parser.parse_args(sys.argv[1:])
	return (parsed_args, parser)

def make_config(pargs, parser):
	pdict = pargs.__dict__
	key_list = pdict.keys()
	arg_list = [pdict[k] for k in key_list]
	Config = namedtuple('Config', key_list)
	nt_config = Config(*arg_list)
	return nt_config

def covered(pool):
	global config
	coverages = pool.sut.currStatements() if config.which else pool.sut.currBranches()
	for c in coverages:
		if config.notcount:
			if not c in pool.dict_cover:
				pool.dict_cover[c] = 1
		else:
			if c in pool.dict_cover:
				pool.dict_cover[c] += 1
			else:
				pool.dict_cover[c] = 1

def delete_pools(pools, num):
	global config, V
	if config.delete:
		V.sequences.clear()
	for key, value in sorted(V.pool_frequency.iteritems(), key = lambda (k, v): (k, v)):
		print "pool", key, "is used", value, "times"
	V.pool_frequency.clear()
	newpools = []
	for pool in pools:
		pool.uniqueness = get_uniqueness(pool, pools)
	sortedpools = sorted(pools, key = lambda x: x.uniqueness, reverse = True)
	for pool in sortedpools:
		newpools.append(pool)
		if config.delete:
			V.sequences = V.sequences.union(pool.set_nseqs).union(pool.set_eseqs)
		if len(newpools) == num:
			break
	sortednewpools = sorted(newpools, key = lambda x: x.pid)
	for pool in sortednewpools:
		print "pick pool", pool.pid, "time", pool.time, "count", pool.time, "score", pool.score, "uniqueness", pool.uniqueness
	return newpools

def feedback(pool):
	global config, V, R, start
	elapsed = time.time()
	if pool.pid in V.pool_frequency.keys():
		V.pool_frequency[pool.pid] += 1
	else:
		V.pool_frequency[pool.pid] = 1
	seq = R.choice(pool.nseqs)[:]
	pool.sut.replay(seq)
	if time.time() - start > config.timeout:
		return False
	n = R.randint(2, 100) if R.randint(0, 9) == 0 else 1
	num_skips = 0
	for i in xrange(n):
		a = pool.sut.randomEnabled(R)
		seq.append(a)
		tuple_seq = tuple(seq)
		if redundant(tuple_seq):
			del seq[-1]
			num_skips += 1
			if n == num_skips:
				V.num_redundancies += 1
				return True
			continue
		ok = pool.sut.safely(a)
		update_coverages(a, pool)
		if not ok:
			print "FIND BUG in ", time.time() - start, "SECONDS by pool", pool.pid
			V.num_eseqs += 1
			V.sequences.add(tuple_seq)
			pool.eseqs.append(seq)
			pool.set_eseqs.add(tuple_seq)
			pool.time += (time.time() - elapsed)
			handle_failure(pool, start)
			return True
		if time.time() - start > config.timeout:
			return False
	if not config.single:
		covered(pool)
	V.num_nseqs += 1
	V.sequences.add(tuple_seq)
	pool.nseqs.append(seq)
	pool.set_nseqs.add(tuple_seq)
	pool.time += (time.time() - elapsed)
	return True

def get_score(pool):
	global config
	if pool.time == 0.0 or pool.count == 0 or len(pool.sut.allBranches()) == 0 or len(pool.sut.allStatements()) == 0:
		return float('inf')
	if config.which:
		return len(pool.sut.allStatements()) * 1.0e9 / pool.time
	else:
		return len(pool.sut.allBranches()) * 1.0e9 / pool.time

def get_uniqueness(pool, pools):
	if pool.time == 0.0 or pool.count == 0 or len(pool.sut.allBranches()) == 0 or len(pool.sut.allStatements()) == 0:
		return float('inf')
	uniqueness = 0.0
	for c in pool.dict_cover:
		uniqueness += _get_uniqueness_helper(pool, c, pools)
	return uniqueness / len(pool.dict_cover)

def _get_uniqueness_helper(pool, c, pools):
	totalcovered = 0.0
	for p in pools:
		if c in p.dict_cover:
			totalcovered += p.dict_cover[c]
	return pool.dict_cover[c] / totalcovered

def handle_failure(sut, start):
	global V
	filename = 'failure' + `V.fid` + '.test'
	sut.saveTest(pool.sut.test(), filename)
	V.fid = V.fid + 1

def internal(pools):
	print "NEED TO IMPLEMENT"

def quick_tests(pools):
	print "NEED TO IMPLEMENT"

def redundant(tuple_seq):
	global V
	if tuple_seq in V.sequences:
		return True
	else:
		return False

def select_pool(pools):
	maxscore = -1.0
	for pool in pools:
		pool.score = get_score(pool)
		if pool.score == float('inf'):
			pool.count += 1
			return pool
		elif pool.score > maxscore:
			maxscore = pool.score
			selected = pool
	selected.count += 1
	return selected

def update_coverages(a, pool):
	global config, V, start
	flag = True
	if pool.sut.newBranches() != set([]):
		for b in pool.sut.newBranches():
			if not b in V.branches:
				V.branches.add(b)
				if config.running:
					if flag:
						print "ACTION:", pool.sut.prettyName(a[0])
						flag = False
					print time.time() - start, len(V.branches), "New branch", b
	if pool.sut.newStatements() != set([]):
		for s in pool.sut.newStatements():
			if not s in V.statements:
				V.statements.add(s)

def main():
	global config, V, R, start
	parsed_args, parser = parse_args()
	config = make_config(parsed_args, parser)
	print('Feedback-directed/controlled random testing using config={}'.format(config))
	V = Variables()
	R = random.Random(config.seed)
	pools = []
	start = time.time()
	n = 1 if config.single else config.inp
	for i in xrange(n):
		V.pid += 1
		pools.append(Pool(V.pid))
	last_added = time.time()
	while time.time() - start < config.timeout:
		if not config.single and time.time() - last_added > config.nseconds:
			V.pid += 1
			pools.append(Pool(V.pid))
			last_added = time.time()
		if not feedback(select_pool(pools)):
			break
		if not config.single and len(pools) == config.mnp:
			pools = delete_pools(pools, config.mnp / 2)
	print time.time() - start, "TOTAL RUNTIME"
	print len(V.sequences), "SEQUENCES (NON ERROR + ERROR)"
	print V.num_nseqs, "NON ERROR SEQUENCES"
	print V.num_eseqs, "ERROR SEQUENCES"
	print V.num_redundancies, "REDUNDANCIES (CREATED SEQUENCE WHICH HAS BEEN CREATED BEFORE)"
	print len(V.branches), "BRANCHES COVERED"
	print len(V.statements), "STATEMENTS COVERED"

if __name__ == '__main__':
	main()
