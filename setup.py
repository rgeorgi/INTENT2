from setuptools import setup, find_packages
import intent2

setup(
    name="intent",
    version=intent2.__version__,
    packages=find_packages(),
    scripts=['scripts/intent',
             'scripts/merge-xigt',
             'scripts/intent-train-classifier',
             'scripts/intent-filter',
             'scripts/intent-eval-pos']
)