import argparse
import math
import random
import sut as SUT
import sys
import time
from collections import namedtuple
from Variables import *
from Pools import *

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
	parsed_args, parser = parse_args()
	config = make_config(parsed_args, parser)
	print('Feedback-directed/controlled random testing using config={}'.format(config))
	P = Pools()
	R = random.Random(config.seed)
	V = Variables()
	start = time.time()
	n = 1 if config.single else config.inp
	for i in xrange(n):
		P.create_pool()
	last_added = time.time()
	while time.time() - start < config.timeout:
		if not config.single and time.time() - last_added > config.nseconds:
			P.create_pool()
			last_added = time.time()
		if not P.select_pool(config).feedback(config, V, R, start):
			break
		if not config.single and len(P.pools) == config.mnp:
			P.delete_pools(config.mnp / 2, config, V)
	print time.time() - start, "TOTAL RUNTIME"
	print len(V.sequences), "SEQUENCES (NON ERROR + ERROR)"
	print V.num_nseqs, "NON ERROR SEQUENCES"
	print V.num_eseqs, "ERROR SEQUENCES"
	print V.num_redundancies, "REDUNDANCIES (CREATED SEQUENCE WHICH HAS BEEN CREATED BEFORE)"
	print len(V.branches), "BRANCHES COVERED"
	print len(V.statements), "STATEMENTS COVERED"

if __name__ == '__main__':
	main()
