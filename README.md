# Lambda Utils [![Build Status](https://travis-ci.org/developerDemetri/lambda-utils.svg?branch=master)](https://travis-ci.org/developerDemetri/lambda-utils) 

Useful little Lambda collection


## Developer Setup
1) Ensure you're running Python 3.7.x ([pyenv](https://github.com/pyenv/pyenv/blob/master/README.md) is suggested for managing Python versions)
2) Run `pip install requirements.txt` to install testing requirements


## Repository Structure

Each directory under [`functions`](https://github.com/developerDemetri/lambda-utils/tree/master/functions) is the name of the Lambda Function that it contains.

Each Lambda has:

1) `__init__.py`, `index.py`, and other required source code files

2) `test.py` file that defines pytests

3) `requirements.txt` that defines dependencies


```
lambda_func
├── __init__.py
├── index.py
├── requirements.txt
└── test.py
```

The [`sceptre`](https://github.com/developerDemetri/lambda-utils/tree/master/sceptre) directory contains a [Sceptre](https://sceptre.cloudreach.com/latest/about.html) setup for orchestrating AWS Resources.
