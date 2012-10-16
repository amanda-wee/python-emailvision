#!/usr/bin/env python
from setuptools import setup, find_packages

import emailvision

CLASSIFIERS = ["Development Status :: 3 - Alpha",
               "Intended Audience :: Developers",
               "License :: OSI Approved :: Apache Software License",
               "Natural Language :: English",
               "Operating System :: OS Independent",
               "Programming Language :: Python",
               "Topic :: Software Development :: Libraries :: Python Modules"]

KEYWORDS = "emailvision api wrapper"

REPO_URL = "https://github.com/eugene-wee/python-emailvision"

setup(name="python-emailvision",
      version=emailvision.__version__,
      description="""EmailVision API wrapper for Python.""",
      author=emailvision.__author__,
      url=REPO_URL,
      packages=find_packages(),
      download_url=REPO_URL + "/tarball/master",
      classifiers=CLASSIFIERS,
      keywords=KEYWORDS,
      zip_safe=True,
      install_requires=["distribute"])
