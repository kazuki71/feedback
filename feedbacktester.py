import argparse
import math
import random
import sut as SUT
import sys
import time
from collections import namedtuple

def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('-a', '--add', action = 'store_false',
                            help = 'Not adding new pool.')
	parser.add_argument('-d', '--delete', action = 'store_false',
                            help = 'Not deleting pools.' )
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
	parser.add_argument('-W', '--WHICH', action = 'store_true',
                            help = 'Using uniquness to select pool instead of coverage information.')

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
			if not c in pool[4]:
				pool[4][c] = 1
		else:
			if c in pool[4]:
				pool[4][c] += 1
			else:
				pool[4][c] = 1

def create_new_pool():
	global pid
	pid += 1
	### pool[0]: unique pool id
	### pool[1]: sut object
	### pool[2]: list of non-error sequences
	### pool[3]: list of error sequences
	### pool[4]: which coverage this pool covers
	### pool[5]: how long this pool is used
	### pool[6]: score of this pool
	### pool[7]: uniquness of this pool
	return [pid, SUT.sut(), [[]], [], dict(), 0.0, 0.0, 0.0]

def delete_pools(pools, num):
	global pool_frequency
	#for key, value in sorted(pool_frequency.iteritems(), key = lambda (k, v): (k, v)):
	#	print "pool", key, "is used", value, "times"
	#pool_frequency.clear()
	newpools = []
	for pool in pools:
		pool[7] = uniquness(pool, pools)
	sortedpools = sorted(pools, key = lambda x: x[7], reverse = True)
	#print "In delete_pools function..."
	for pool in sortedpools:
	#	print "pick pool", pool[0], "uniquness", pool[7], "score", pool[6]
		newpools.append(pool)
		if len(newpools) == num:
			break
	return newpools

def feedback(pool, sequences, branches, statements):
	global config, fid, R, start, num_redundancies, num_nonerrorseqs, num_errorseqs, pool_frequency
	#if pool[0] in pool_frequency.keys():
	#	pool_frequency[pool[0]] += 1
	#else:
	#	pool_frequency[pool[0]] = 1
	elapsed = time.time()
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
		if redundant(tuple_seq, sequences):
			del seq[-1]
			num_skips += 1
			if n == num_skips:
				num_redundancies += 1
				return True
			continue
		ok = sut.safely(a)
		update_coverages(a, branches, statements, sut)
		if not ok:
			print "FIND BUG in ", time.time() - start, "SECONDS using pool", pool[0]
			num_errorseqs += 1
			sequences.add(tuple_seq)
			pool[3].append(seq)
			pool[5] += (time.time() - elapsed)
			fid = handle_failure(sut, fid, start)
			return True
		if time.time() - start > config.timeout:
			return False
	if not config.single:
		covered(pool)
	num_nonerrorseqs += 1
	sequences.add(tuple_seq)
	pool[2].append(seq)
	pool[5] += (time.time() - elapsed)
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
		print ""
		i += 1

def redundant(seq, sequences):
	if tuple(seq) in sequences:
		return True
	else:
		return False

def score(pool):
	global config
	if pool[5] == 0.0 or len(pool[1].allBranches()) == 0 or len(pool[1].allStatements()) == 0:
		return float('inf')
	if config.which:
		return len(pool[1].allStatements()) / pool[5]
	else:
		return len(pool[1].allBranches()) / pool[5]

def select_pool(pools):
	global config
	if config.single:
		return pools[0]
	maxscore = -1.0
	for pool in pools:
		if config.WHICH:
			pool[7] = uniquness(pool, pools)
			s = pool[7]
		else:
			pool[6] = score(pool)
			s = pool[6]
		if s == float('inf'):
			return pool
		if s > maxscore:
			maxscore = s
			selected = pool
	return selected

def uniquness(pool, pools):
	if pool[5] == 0.0 or len(pool[1].allBranches()) == 0 or len(pool[1].allStatements()) == 0:
		return float('inf')
	uniquness = 0.0
	for c in pool[4]:
		uniquness += _uniquness_helper(pool, c, pools)
	return uniquness / len(pool[4])

def _uniquness_helper(pool, c, pools):
	totalcovered = 0.0
	for p in pools:
		if c in p[4]:
			totalcovered += p[4][c]
	return pool[4][c] / totalcovered

def update_coverages(a, branches, statements, sut):
	global config, start
	flag = True
	if sut.newBranches() != set([]):
		for b in sut.newBranches():
			if not b in branches:
				branches.add(b)
				if config.running:
					if flag:
						print "ACTION:", sut.prettyName(a[0])
						flag = False
					print time.time() - start, len(branches), "New branch", b
	if sut.newStatements() != set([]):
		for s in sut.newStatements():
			if not s in statements:
				statements.add(s)

def main():
	global config, fid, pid, R, start, sequences, num_redundancies, num_nonerrorseqs, num_errorseqs, pool_frequency
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
	sequences = set()
	branches = set()
	statements = set()
	pool_frequency = dict()
	n = 1 if config.single else config.inp
	for i in xrange(n):
		pools.append(create_new_pool())
	last_added = time.time()
	while time.time() - start < config.timeout:
		if config.add and not config.single and time.time() - last_added > config.nseconds:
			pools.append(create_new_pool())
			last_added = time.time()
		if not feedback(select_pool(pools), sequences, branches, statements):
			break
		#if config.delete and not config.single and len(pools) == config.mnp:
		if config.delete and not config.single and len(pools) > config.mnp:
			pools = delete_pools(pools, config.mnp / 2)
	if config.internal:
		internal(pools)
	print time.time() - start, "TOTAL RUNTIME"
	print len(sequences), "SEQUENCES (NON ERROR + ERROR)"
	print num_nonerrorseqs, "NON ERROR SEQUENCES"
	print num_errorseqs, "ERROR SEQUENCES"
	print num_redundancies, "REDUNDANCIES (CREATED SEQUENCE WHICH HAS BEEN CREATED BEFORE)"
	print len(branches), "BRANCHES COVERED"
	print len(statements), "STATEMENTS COVERED"

if __name__ == '__main__':
	main()
