# setup.py
from setuptools import setup
from mypyc.build import mypycify

setup(
    name="entities",
    version="0.1",
    packages=["common.entities", "common.biomes"],
    ext_modules=mypycify([
        "common/entities/Entity_mypyc.py",
        "common/entities/properties/TestEntityX_mypyc.py",
        "common/biomes/Chunk.py",
    ],
    opt_level="3",
    debug_level="0"),
)