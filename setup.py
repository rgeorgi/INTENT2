from setuptools import setup, find_packages
import intent2

setup(
    name="intent2",
    version=intent2.__version__,
    packages=find_packages(),
    package_data={
      'intent2': ['./*.yml'],
   },
   include_package_data=True,
    scripts=['scripts/intent',
             'scripts/merge-xigt',
             'scripts/intent-train-classifier',
             'scripts/intent-filter',
             'scripts/intent-eval-pos']
)
