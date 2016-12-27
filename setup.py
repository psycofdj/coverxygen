#!/usr/bin/env python3
# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

import sys
from setuptools import setup
sys.path.insert(0, ".")
import coverxygen

setup(
  name            = "coverxygen",
  packages        = ['coverxygen'],
  version         = coverxygen.__version__,
  description     = coverxygen.__description__,
  author          = coverxygen.__author__.split("<")[0].strip(),
  author_email    = coverxygen.__author__.split("<")[1].split(">")[0].strip(),
  url             = coverxygen.__url__,
  download_url    = coverxygen.__download_url__,
  keywords        = coverxygen.__keywords__,
  classifiers     = coverxygen.__classifiers__
)
