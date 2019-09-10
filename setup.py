#!/usr/bin/env python
"""Setup module."""

import pathlib
import codecs
from setuptools import setup, find_packages


HERE = pathlib.Path(__file__).parent


def parse_requirements(filename):
    """Read pip-formatted requirements from a file."""
    with open(filename, "r") as f:
        return [
            line.strip() for line in f.readlines()
            if not (line.startswith("#") or line.startswith("-"))
        ]


setup(
    name="socialnetwork",
    version="0.0.1",
    description="Social Network",
    packages=find_packages(exclude=["tests", "tests.*"]),
    include_package_data=True,
    long_description=codecs.open(HERE / "README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    install_requires=parse_requirements(HERE / "requirements.txt"),
    tests_require=parse_requirements(HERE / "requirements.txt"),
)
