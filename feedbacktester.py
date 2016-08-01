import argparse
import math
import random
import sut as SUT
import sys
import time
from collections import namedtuple

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

def covered(pool):
	for b in pool[0].currBranches():
		if b in pool[4]:
			pool[4][b] += 1
		else:
			pool[4][b] = 1

def createNewPool():
	return [SUT.sut(), [[]], [], 0.0, dict(), 0.0]

def deletePools(pools, num):
	newpools = []
	for pool in pools:
		if len(pool[4]) == 0:
			newpools.append(pool)
			if len(newpools) == num:
				return newpools
	for pool in pools:
		if len(pool[4]) != 0:
			pool[5] = getUniquness(pool, pools)
	sortedpools = sorted(pools, key = lambda x : x[5], reverse = True)
	while len(newpools) < num:
		for pool in sortedpools:
			if len(pool[4]) != 0:
				newpools.append(pool)
	return newpools

def feedback(pool, keys):
	global config, fid, R, start
	elapsed = time.time()
	sut = pool[0]
	seq = R.choice(pool[1])[:]
	sut.replay(seq)
	if time.time() - start > config.timeout:
		return
	if R.randint(0, 9) == 0:
		n = R.randint(2, 100)
	else:
		n = 1
	skipped = 0
	for i in xrange(n):
		a = sut.randomEnabled(R)
		key = getKey(seq, a, sut)
		if key in keys:
			skipped += 1
			continue
		seq.append(a)
		if not sut.safely(a):
			keys.add(key)
			pool[2].append(seq)
			pool[3] += (time.time() - elapsed)
			fid = handle_failure(sut, fid)
			if time.time() - start > config.timeout:
				return
	if n == skipped:
		return
	keys.add(key)
	if config.inp != 1:
		covered(pool)
	pool[1].append(seq)
	pool[3] += (time.time() - elapsed)
	return

def getKey(seq, a, sut):
	key = long()
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
	if pool[3] == 0.0 or len(pool[0].allBranches()) == 0:
		return float('inf')
	return len(pool[0].allBranches()) / pool[3]

def getUniquness(pool, pools):
	uniquness = 0.0
	for c in pool[4]:
		uniquness += getUniqunessHelper(pool, c, pools)
	return uniquness / len(pool[4])

def getUniqunessHelper(pool, c, pools):
	totalcovered = 0.0
	for p in pools:
		if c in p[4]:
			totalcovered += p[4][c]
	return pool[4][c] / totalcovered

def handle_failure(sut, fid):
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
	global config, fid, R, start
	parsed_args, parser = parse_args()
	config = make_config(parsed_args, parser)
	print('Feedback-controlled random testing using config={}'.format(config))
	R = random.Random(config.seed)
	fid = 0
	start = time.time()
	pools = []
	keys = set()
	for i in xrange(config.inp):
		pools.append(createNewPool())
	lastadded = time.time()
	while time.time() - start < config.timeout:
		if config.inp != 1 and time.time() - lastadded > config.nseconds:
			pools.append(createNewPool())
			lastadded = time.time()
		if config.inp != 1:
			pool = selectPool(pools)
		else:
			pool = pools[0]
		feedback(pool, keys)
		if time.time() - start > config.timeout:
			break
		if config.inp != 1 and len(pools) > config.mnp:
			pools = deletePools(pools, config.mnp / 2)
		if time.time() - start > config.timeout:
			break
	if config.internal:
		internal(pools)

if __name__ == '__main__':
	main()
