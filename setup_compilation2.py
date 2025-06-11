from setuptools import setup
from Cython.Build import cythonize

setup(
    package=["common/entities"],
    ext_modules=cythonize(["common/entities/Entity_c.pyx"], language_level="3"),
)