from setuptools import setup
from setuptools import find_packages

def readme():
    with open("README.md", 'r') as f:
        return f.read()

setup(
    name = "uchicagoldrhrapi",
    description = "A RESTful API for creating and manipulating HierarchicalRecords.",
    long_description = readme(),
    version = "0.0.1dev",
    author = "Brian Balsamo, Tyler Danstrom",
    author_email = "balsamo@uchicago.edu, tdanstrom@uchicago.edu",
    packages = find_packages(
        exclude = [
            "build",
            "bin",
            "dist",
            "tests",
            "uchicagoldrhrapi.egg-info"
        ]
    ),
    dependency_links = [
        'https://github.com/uchicago-library/uchicagldrapi_core' +
        '/tarball/master#egg=uchicagoldrapicore'
    ],
    install_requires = [
        'uchicagoldrapicore'
    ]
)
