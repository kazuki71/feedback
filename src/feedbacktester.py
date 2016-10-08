import argparse
import math
import random
import sut as SUT
import sys
import time
from collections import namedtuple
from Pools import *
from Variables import *

def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('-d', '--directed', action = 'store_true',
                            help = 'Feedback directed random test generation instead of feedback controlled random test generation.')
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
        parser.add_argument('-I', '--internal', action = 'store_true',
                            help = 'Produce internal coverage report at the end.')
	parsed_args = parser.parse_args(sys.argv[1:])
	return (parsed_args, parser)

def make_config(pargs, parser):
	pdict = pargs.__dict__
	key_list = pdict.keys()
	arg_list = [pdict[k] for k in key_list]
	Config = namedtuple('Config', key_list)
	nt_config = Config(*arg_list)
	return nt_config

def internal():
	print "NEED TO IMPLEMENT"

def quick_tests():
	print "NEED TO IMPLEMENT"

def main():
	# parse command line arguments
	parsed_args, parser = parse_args()
	config = make_config(parsed_args, parser)
	print('Feedback directed/controlled random testing using config={}'.format(config))

	# init
	P = Pools()
	R = random.Random(config.seed)		
	V = Variables()	
	start = time.time()

	### feedback controlled random test generation
	# add n pools
	n = 1 if config.directed else config.inp
	for i in xrange(n):
		P.create_pool()
	last_added = time.time()

	while time.time() - start < config.timeout:
		# add a new pool for each n seconds
		if not config.directed and time.time() - last_added > config.nseconds:
			P.create_pool()
			last_added = time.time()

		# select a pool
		pool = P.select_pool(config)

		### feedback directed random test generation
		if pool.feedback(config, V, R, start):
			pool.update_coverage(config, V)
		else:
			break

		# delete pools when |pools| > mnp (maximum number of pools)
		if not config.directed and P.length() > config.mnp:
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
