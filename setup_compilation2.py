from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize(["Entity_c.pyx"], language_level="3"),
)