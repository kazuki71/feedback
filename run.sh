#!/bin/bash
for i in `seq 1 6`
do
	python feedbacktester.py >> out$i
done
