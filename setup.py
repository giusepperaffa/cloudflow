# ========================================
# Import Python Modules (Standard Library)
# ========================================
import os
from setuptools import setup, find_packages

# ==============================
# Extract Dependencies From File
# ==============================
with open('requirements.txt') as reqs_file:
    requirements = reqs_file.read().splitlines()

# =========
# Functions
# =========
def get_version():
    with open(os.path.join(os.path.dirname(__file__), 'cloudflow', '__init__.py')) as f:
        for line in f:
            if line.startswith('__version__'):
                delim = '"' if '"' in line else "'"
                return line.split(delim)[1]
        raise RuntimeError("--- Unable to find version string ---")

# =====
# Setup
# =====
setup(
    name='cloudflow',
    version=get_version(),
    description='Tool to perform data flow analysis of serverless applications',
    author='Giuseppe Raffa',
    author_email='giuseppe.raffa@hotmail.com',
    packages=find_packages(),
    install_requires=requirements,
    entry_points="""
    [console_scripts]
    cloudflow=cloudflow.main:main
    """,
)
