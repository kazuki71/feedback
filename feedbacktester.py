import argparse
import math
import random
import sut as SUT
import sys
import time
from collections import namedtuple

def createNewPool():
	return [SUT.sut(), 0.0, [[]], []]

def deletePools(pools, num):
	newpools = []
	return newpools

def feedback(pool, keys):
	global config, R, start
	elapsed = time.time()
	sut = pool[0]
	seq = R.choice(pool[2])[:]
	sut.replay(seq)
	if time.time() - start > config.timeout:
		return
	if R.randint(0, 9) == 0:
		n = R.randint(2, 100)
	else:
		n = 1
	for i in xrange(n):
		a = sut.randomEnabled(R)
		key = getKey(seq, a, sut)
		if key in keys:
			continue
		seq.append(a)
		if not sut.safely(a):
			print "FIND LOG BUG in ", time.time() - start, "seconds"
			keys.add(key)
			pool[3].append(seq)
			pool[1] += (time.time() - elapsed)
			return
		if time.time() - start > config.timeout:
			return
	if n == 1 and key in keys:
		return
	keys.add(key)
	pool[2].append(seq)
	pool[1] += (time.time() - elapsed)

def getKey(seq, a, sut):
	key = 0
	for i in seq:
		key = getKeyHelper(key, sut.actOrder(i))
	return getKeyHelper(key, sut.actOrder(a))

def getKeyHelper(key, aorder):
	ndigits = int(math.log10(aorder)) + 1
	for i in xrange(ndigits):
		msb = aorder / int(math.pow(10, ndigits - i - 1))
		key = key * 10 + msb
		aorder %= int(math.pow(10, ndigits - i - 1))
	return key

def getScore(pool):
	if pool[1] == 0.0 or len(pool[0].allBranches()) == 0:
		return float('inf')
	return len(pool[0].allBranches()) / pool[1]

def make_config(pargs, parser):
	pdict = pargs.__dict__
	key_list = pdict.keys()
	arg_list = [pdict[k] for k in key_list]
	Config = namedtuple('Config', key_list)
	nt_config = Config(*arg_list)
	return nt_config

def parse_args():
	parser = argparse.ArgumentParser()
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
	parsed_args = parser.parse_args(sys.argv[1:])
	return (parsed_args, parser)

def selectPool(pools):
	maxscore = -1.0
	for pool in pools:
		score = getScore(pool)
		if score == float('inf'):
			return pool
		if score > maxscore:
			maxscore = score
			selected = pool
	return selected

def main():
	global config, R, start
	parsed_args, parser = parse_args()
	config = make_config(parsed_args, parser)
	print('Feedback-controlled random testing using config={}'.format(config))
	R = random.Random(config.seed)
	start = time.time()
	pools = []
	keys = set()
	for i in xrange(config.inp):
		pools.append(createNewPool())
	lastadded = time.time()
	while time.time() - start < config.timeout:
		if time.time() - lastadded > config.nseconds:
			pools.append(createNewPool())
			lastadded = time.time()
		feedback(selectPool(pools), keys)
		if time.time() - start > config.timeout:
			break
		if len(pools) > config.mnp:
			pools = deletePools(pools, config.mnp / 2)
		if time.time() - start > config.timeout:
			break

if __name__ == '__main__':
	main()
