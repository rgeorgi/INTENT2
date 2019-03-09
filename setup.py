from setuptools import setup, find_packages

setup(
    name="intent",
    version='2.0a6',
    packages=find_packages(),
    scripts=['scripts/intent',
             'scripts/merge-xigt',
             'scripts/intent-train-classifier',
             'scripts/intent-filter',
             'scripts/intent-eval-pos']
)