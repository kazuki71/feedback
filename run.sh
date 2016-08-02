#!/bin/bash
for i in `seq 1 10`
do
	python feedbacktester.py -t 300 >> 300out$i
done

for i in `seq 1 3`
do
	python feedbacktester.py -t 3000 >> 3000out$i
done
