import argparse
import math
import random
import sut as SUT
import sys
import time
from collections import namedtuple

def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('-d', '--delete', action = 'store_true',
                            help = 'Delete corresponding sequences from all_sequences when delete pool.')
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
	coverages = pool[1].currStatements() if config.which else pool[1].currBranches()
	for c in coverages:
		if config.notcount:
			if not c in pool[6]:
				pool[6][c] = 1
		else:
			if c in pool[6]:
				pool[6][c] += 1
			else:
				pool[6][c] = 1

def create_new_pool():
	global pid
	pid += 1
	### pool[0]: unique pool id
	### pool[1]: sut object
	### pool[2]: list of non-error sequences
	### pool[3]: list of error sequences
	### pool[4]: set of non-error sequences
	### pool[5]: set of error sequences
	### pool[6]: dictionary, key - coverage, value - number of counts the coverage is covered 
	### pool[7]: time of using this pool by feedback()
	### pool[8]: number of counts this pool is selected by select_pool
	### pool[9]: score by score()
	### pool[10]: uniquness by uniquness()
	return [pid, SUT.sut(), [[]], [], set(), set(), dict(), 0.0, 0, 0.0, 0.0]

def delete_pools(pools, num):
	global all_sequences, config, pool_frequency
	if config.delete:
		all_sequences.clear()
	#for key, value in sorted(pool_frequency.iteritems(), key = lambda (k, v): (k, v)):
	#	print "pool", key, "is used", value, "times"
	#pool_frequency.clear()
	newpools = []
	for pool in pools:
		pool[10] = uniquness(pool, pools)
	sortedpools = sorted(pools, key = lambda x: x[10], reverse = True)
	for pool in sortedpools:
		newpools.append(pool)
		if config.delete:
			all_sequences = all_sequences.union(pool[4]).union(pool[5])
		if len(newpools) == num:
			break
	#sortednewpools = sorted(newpools, key = lambda x: x[0])
	#for pool in sortednewpools:
	#	print "pick pool", pool[0], "time", pool[7], "count", pool[8], "score", pool[9], "uniquness", pool[10]
	return newpools

def feedback(pool, all_sequences, all_branches, all_statements):
	global config, fid, num_redundancies, num_nonerrorseqs, num_errorseqs, pool_frequency, R, start
	elapsed = time.time()
	#if pool[0] in pool_frequency.keys():
	#	pool_frequency[pool[0]] += 1
	#else:
	#	pool_frequency[pool[0]] = 1
	sut = pool[1]
	seq = R.choice(pool[2])[:]
	sut.replay(seq)
	if time.time() - start > config.timeout:
		return False
	n = R.randint(2, 100) if R.randint(0, 9) == 0 else 1
	num_skips = 0
	for i in xrange(n):
		a = sut.randomEnabled(R)
		seq.append(a)
		tuple_seq = tuple(seq)
		if redundant(tuple_seq, all_sequences):
			del seq[-1]
			num_skips += 1
			if n == num_skips:
				num_redundancies += 1
				return True
			continue
		ok = sut.safely(a)
		update_coverages(a, all_branches, all_statements, sut)
		if not ok:
			print "FIND BUG in ", time.time() - start, "SECONDS by pool", pool[0]
			num_errorseqs += 1
			all_sequences.add(tuple_seq)
			pool[3].append(seq)
			pool[5].add(tuple_seq)
			pool[7] += (time.time() - elapsed)
			fid = handle_failure(sut, fid, start)
			return True
		if time.time() - start > config.timeout:
			return False
	if not config.single:
		covered(pool)
	num_nonerrorseqs += 1
	all_sequences.add(tuple_seq)
	pool[2].append(seq)
	pool[5].add(tuple_seq)
	pool[7] += (time.time() - elapsed)
	return True

def handle_failure(sut, fid, start):
	filename = 'failure' + `fid` + '.test'
	sut.saveTest(sut.test(), filename)
	return fid + 1

def internal(pools):
	i = 0
	for pool in pools:
		print "Producing internal coverage report for pool", i, "..."
		pool[1].internalReport()
		i += 1

def redundant(tuple_seq, all_sequences):
	if tuple_seq in all_sequences:
		return True
	else:
		return False

def score(pool):
	global config
	if pool[7] == 0.0 or pool[8] == 0 or len(pool[1].allBranches()) == 0 or len(pool[1].allStatements()) == 0:
		return float('inf')
	if config.which:
		return len(pool[1].allStatements()) * 1.0e9 / pool[7]
	else:
		return len(pool[1].allBranches()) * 1.0e9 / pool[7]

def select_pool(pools):
	global config
	if config.single:
		return pools[0]
	maxscore = -1.0
	for pool in pools:
		pool[9] = score(pool)
		if pool[9] == float('inf'):
			pool[8] += 1
			return pool
		if pool[9] > maxscore:
			maxscore = pool[9]
			selected = pool
	selected[8] += 1
	return selected

def uniquness(pool, pools):
	if pool[7] == 0.0 or pool[8] == 0 or len(pool[1].allBranches()) == 0 or len(pool[1].allStatements()) == 0:
		return float('inf')
	uniquness = 0.0
	for c in pool[6]:
		uniquness += _uniquness_helper(pool, c, pools)
	return uniquness / len(pool[6])

def _uniquness_helper(pool, c, pools):
	totalcovered = 0.0
	for p in pools:
		if c in p[6]:
			totalcovered += p[6][c]
	return pool[6][c] / totalcovered

def update_coverages(a, all_branches, all_statements, sut):
	global config, start
	flag = True
	if sut.newBranches() != set([]):
		for b in sut.newBranches():
			if not b in all_branches:
				all_branches.add(b)
				if config.running:
					if flag:
						print "ACTION:", sut.prettyName(a[0])
						flag = False
					print time.time() - start, len(all_branches), "New branch", b
	if sut.newStatements() != set([]):
		for s in sut.newStatements():
			if not s in all_statements:
				all_statements.add(s)

def main():
	global all_sequences, config, fid, num_redundancies, num_nonerrorseqs, num_errorseqs, pid, pool_frequency, R, start
	parsed_args, parser = parse_args()
	config = make_config(parsed_args, parser)
	print('Feedback-directed/controlled random testing using config={}'.format(config))
	R = random.Random(config.seed)
	fid = 0
	pid = 0
	num_nonerrorseqs = 0
	num_errorseqs = 0
	num_redundancies = 0
	start = time.time()
	pools = []
	all_sequences = set()
	all_branches = set()
	all_statements = set()
	pool_frequency = dict()
	n = 1 if config.single else config.inp
	for i in xrange(n):
		pools.append(create_new_pool())
	last_added = time.time()
	while time.time() - start < config.timeout:
		if not config.single and time.time() - last_added > config.nseconds:
			pools.append(create_new_pool())
			last_added = time.time()
		if not feedback(select_pool(pools), all_sequences, all_branches, all_statements):
			break
		if not config.single and len(pools) == config.mnp:
			pools = delete_pools(pools, config.mnp / 2)
	if config.internal:
		internal(pools)
	print time.time() - start, "TOTAL RUNTIME"
	print len(all_sequences), "SEQUENCES (NON ERROR + ERROR)"
	print num_nonerrorseqs, "NON ERROR SEQUENCES"
	print num_errorseqs, "ERROR SEQUENCES"
	print num_redundancies, "REDUNDANCIES (CREATED SEQUENCE WHICH HAS BEEN CREATED BEFORE)"
	print len(all_branches), "BRANCHES COVERED"
	print len(all_statements), "STATEMENTS COVERED"

if __name__ == '__main__':
	main()
