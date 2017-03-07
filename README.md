<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-generate-toc again -->
**Table of Contents**

- [Coverxygen](#coverxygen)
- [How to](#how-to)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Configure doxygen](#configure-doxygen)
    - [Run Coverxygen](#run-coverxygen)
    - [Run lcov or genhtml](#run-lcov-or-genhtml)
    - [Results](#results)
- [Credits](#credits)
- [Project status](#project-status)

<!-- markdown-toc end -->

# Coverxygen


# How to

First, run doxygen with XML output on your project, Coverxygen will read generated file and produce an lcov compatible output.
Finally, run `lcov` or `genhtml` to produce the coverage output.

## Prerequisites

Coverxygen relies on both doxygen (to generate the documentation information) and lcov to generate the reports.
```bash
sudo apt-get install doxygen lcov
```

## Installation

From pip

```bash
pip3 install coverxygen
```
From PPA Packages

link : https://launchpad.net/~psycofdj/+archive/ubuntu/coverxygen
```bash
sudo add-apt-repository ppa:psycofdj/coverxygen
sudo apt-get update
# with python2 (default)
sudo apt-get install python-coverxygen        
# or with python3
sudo apt-get install python3-coverxygen
```

## Configure doxygen

Tell doxygen to generate an XML version of your doxyfile.cfg configuration
```
GENERATE_XML = YES
```

Then run doxygen
```bash
doxygen <path_to_your_doxygen.cfg>
```

## Run Coverxygen
```bash
python -m coverxygen --xml-path <path_to_doxygen_xml_dir> --output doc-coverage.info
```

Full usage :
```
usage: coverxygen [-h] [--version] [--verbose] [--json JSON] [--format FORMAT] --xml-dir XML_DIR --output OUTPUT --src-dir ROOT_DIR [--prefix PREFIX] [--scope SCOPE] [--kind KIND]

optional arguments:
  -h, --help           show this help message and exit
  --version            prints version
  --verbose            enabled verbose output
  --json JSON          (deprecated) same as --format json-legacy
  --format FORMAT      output file format : 
                       lcov        : lcov compatible format (default)
                       json-legacy : legacy json format
                       lcov        : simpler json format
  --xml-dir XML_DIR    path to generated doxygen XML directory
  --output OUTPUT      destination output file (- for stdout)
  --src-dir ROOT_DIR   root source directory used to match prefix forrelative path generated files
  --prefix PREFIX      keep only file matching given path prefix
  --scope SCOPE        comma-separated list of items' scope to include : 
                        - public    : public member elements
                        - protected : protected member elements
                        - private   : private member elements
                        - all       : all above
  --kind KIND          comma-separated list of items' type to include : 
                        - enum      : enum definitions 
                        - typedef   : typedef definitions
                        - variable  : variable definitions
                        - function  : function definitions
                        - class     : class definitions
                        - struct    : struct definitions
                        - define    : define definitions
                        - file      : file definitions
                        - namespace : namespace definitions
                        - page      : page definitions
                        - all       : all above
```

## Run lcov or genhtml

If you want an simple console output :
```
lcov --summary doc-coverage.info
```

More interesting, produce a html-browsable coverage detail :
```bash
genhtml --no-function-coverage --no-branch-coverage doc-coverage.info -o .
# browse results in index.html
```

## Results

Summary

![Summary](./docs/coverage-summary.png)

Details

![Details](./docs/coverage-details.png)

# Credits
Special thanks to Alvaro Lopez Ortega <[alvaro@gnu.org](mailto:alvaro@gnu.org)> who found a smart and efficient solution to retrieve doxygen informations from the generated xml.

You can find his work at [alobbs/doxy-coverage](https://github.com/alobbs/doxy-coverage)


# Project status

Unstable but usable.
[![PyPI version](https://badge.fury.io/py/coverxygen.svg)](https://badge.fury.io/py/coverxygen)


<!--  LocalWords:  doxyfile cfg xml alobbs doxy -->
<!-- Local Variables: -->
<!-- ispell-local-dictionary: "american" -->
<!-- End: -->
