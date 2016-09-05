# feedbacktester

feedbacktester is random test generator in Python 2.x for The Template Scripting Testing Language (TSTL): https://github.com/agroce/tstl, which is a research project by Dr. Alex Groce. feedbacktester provides two random test generators: Feedback-directed Random Test Generation by Carlos Pacheco, Shuvendu K. Lahiri, Michael D. Ernst, and Thomas Ball, and Feedback-controlled Random Test Generation by Kohsuke Yatoh, Kazunori Sakamoto, Fuyuki Ishikawa and Shinichi Honiden.

## How to install

Firstly, need to install tstl.
```
git clone https://github.com/agroce/tstl.git
cd tstl
python setup.py install		# need to run this command as superuser, so make sure to run with su or sudo
```

Then,
```
git clone https://github.com/kazuki71/feedback.git
```

### How to run

For running feedbacktester, need to prepre software under test (sut) by TSTL. For example, supporse avl.py is our sut. Create tstl file to indicate what aspects of avl.py you want to test. Let this tstl file as avl.tstl. Then, type the following command to generate sut.py at the same directory with avl.py and avl.tstl:
```
tstl avl.tstl
```
There are avl.py and avl.tstl in example/ 
