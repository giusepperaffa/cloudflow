# ========================================
# Import Python Modules (Standard Library)
# ========================================
from setuptools import setup, find_packages

setup(
    name='cloudflow',
    version='0.0.1',
    description='Tool to perform data flow analysis of serverless applications',
    author='Giuseppe Raffa',
    author_email='giuseppe.raffa@hotmail.com',
    packages=find_packages(),
    entry_points="""
    [console_scripts]
    cloudflow=cloudflow.main:main
    """,
)
