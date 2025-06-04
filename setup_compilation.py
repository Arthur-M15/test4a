# setup.py
from setuptools import setup
from mypyc.build import mypycify

setup(
    name="entities",
    version="0.1",
    packages=["common.entities", "common.biomes"],
    ext_modules=mypycify([
        "common/entities/Entity_c.py",
        "common/entities/properties/TestEntityX_c.py",
        "common/biomes/Chunk_c.py",
    ],
    opt_level="3",
    debug_level="0"),
)