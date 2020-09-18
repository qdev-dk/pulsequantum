# pulsequantum

# Description

# Installation

# Usage

## Running the tests

If you have gotten `pulsequantum` from source, you may run the tests locally.

Install `pulsequantum` along with its test dependencies into your virtual environment by executing the following in the root folder

```bash
$ pip install .
$ pip install -r test_requirements.txt
```

Then run `pytest` in the `tests` folder.

## Building the documentation

If you have gotten `pulsequantum` from source, you may build the docs locally.

Install `pulsequantum` along with its documentation dependencies into your virtual environment by executing the following in the root folder

```bash
$ pip install .
$ pip install -r docs_requirements.txt
```

You also need to install `pandoc`. If you are using `conda`, that can be achieved by

```bash
$ conda install pandoc
```
else, see [here](https://pandoc.org/installing.html) for pandoc's installation instructions.

Then run `make html` in the `docs` folder. The next time you build the documentation, remember to run `make clean` before you run `make html`.
