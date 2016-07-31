import sys
import os
import random
import time
import sut as SUT
import traceback

R = random.Random(1)

start = time.time()
elapsed = time.time() - start

failCount = 0
quickCount = 0
repeatCount = 0
failures = []
cloudFailures = []

sut = SUT.sut()

tacts = sut.actions()
a = None
sawNew = False

nops = 0
ntests = 0
reduceTime = 0.0
opTime = 0.0
checkTime = 0.0
guardTime = 0.0
restartTime = 0.0

checkResult = True

# default for config.maxtests = -1
maxtests = -1
# default for config.depth = 100
depth = 100
# default for config.timeout = 3600
timeout = 5
# default for config.uncaught = False
uncaught = False
# default for config.multiple = False
multiple = False
# default for config.output = "failure." + str(os.getpid()) + ".test"
output = "failure." + str(os.getpid()) + ".test"
# default for config.ignoreprops = False
ignoreprops = False

def handle_failure(test, msg, checkFail, newCov = False):
	global failCount, reduceTime, repeatCount, failures, quickCount, failCloud, cloudFailures, allClouds
	test = list(test)
	sys.stdout.flush()
	if not newCov:
		failCount += 1
		print msg
		f = sut.failure()
		print "ERROR:", f
		print "TRACEBACK:"
		traceback.print_tb(f[2])
		sut.saveTest(test, output + ".full")
	print "Original test has", len(test), "steps"
	cloudMatch = False
	outf = None
	print
	print "FINAL VERSION OF TEST, WITH LOGGED REPLY:"
	i = 0
	sut.restart()
	for s in test:
		steps = "# step " + str(i)
		print sut.prettyName(s[0]).ljust(80 - len(steps), ' '), steps
		sut.safely(s)
		if checkFail:
			sut.check()
		i += 1

while (maxtests == -1) or (ntests < maxtests):
	ntests += 1

	startRestart = time.time()
	sut.restart()
	restartTime += time.time() - startRestart

	testFailed = False

	for s in xrange(0, depth):
		startGuard = time.time()
		a = sut.randomEnabled(R)
		if a == None:
			print "WARNING: DEADLOCK (NO ENABLED ACTIONS)"
		guardTime += time.time() - startGuard

		elapsed = time.time() - start
		if elapsed > timeout:
			print "STOPPING TEST DUE TO TIMEOUT, TERMINATED AT LENGTH", len(sut.test())
			break

		if a == None:
			print "TERMINATING TEST DUE TO NO ENABLED ACTIONS"
			break

		startOp = time.time()
		stepOk = sut.safely(a)
		thisOpTime = time.time() - startOp
		nops += 1
		opTime += thisOpTime

		startCheck = time.time()
		if (not uncaught) and (not stepOk):
			testFailed = True
			handle_failure(sut.test(), "UNCAUGHT EXCEPTION", False)
			if not multiple:
				print "STOPPING TESTING DUE TO FAILED TEST"
			break

		elapsed = time.time() - start
		if elapsed > timeout:
			print "STOPPING TEST DUE TO TIMEOUT, TERMINATED AT LENGTH", len(sut.test())
			break

	if (not multiple) and (failCount > 0):
		break
	if elapsed > timeout:
		print "STOPPING TEST DUE TO TIMEOUT"
		break

print time.time() - start, "TOTAL RUNTIME"
print ntests, "EXECUTED"
print nops, "TOTAL TEST OPERATIONS"
print opTime, "TIME SPENT EXECUTING TEST OPERATIONS"
print guardTime, "TIME SPENT EVALUATING GUARDS AND CHOOSING ACTIONS"
print restartTime, "TIME SPENT RESTARTING"
print reduceTime, "TIME SPENT REDUCING TEST CASES"
