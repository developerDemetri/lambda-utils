# Lambda Utils
Useful little Lambda collection


## Developer Setup
1) Ensure you're running Python 3.7.x ([pyenv](https://github.com/pyenv/pyenv/blob/master/README.md) is suggested for managing Python versions)
2) Run `pip install requirements.txt` to install testing requirements
3) Install Lambda specific `requirements.txt` as needed


## Repository Structure

Each directory is the name of the Lambda Function that it contains.

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
