from setuptools import setup
from mypyc.build import mypycify
import os
import shutil
import glob

# Liste des fichiers à compiler avec mypyc
mypyc_modules = [
    "common/entities/Entity_mypyc.py",
    "common/entities/properties/TestEntityX_mypyc.py",
]

setup(
    name="entities",
    version="0.1",
    packages=["common.entities", "test"],
    ext_modules=mypycify(
        mypyc_modules,
        opt_level="3",    # Niveau d'optimisation du compilateur (0-3). 3 = max optimisation.
        debug_level="0",  # Niveau des informations de debug (0 = pas de debug, 1 = lignes sources, 2 = info détaillée)
    ),
)

# === Post-traitement pour renommer les fichiers compilés ===
def rename_pyd_files():
    for source_path in mypyc_modules:
        base_dir = os.path.dirname(source_path)
        base_name = os.path.splitext(os.path.basename(source_path))[0]

        # Chercher le fichier compilé (ex: Entity_mypyc.cp312-win_amd64.pyd)
        pattern = os.path.join(base_dir, f"{base_name}*.pyd")
        compiled_files = glob.glob(pattern)
        if compiled_files:
            compiled_file = compiled_files[0]
            target_name = base_name.replace("_mypyc", "") + ".pyd"
            target_path = os.path.join(base_dir, target_name)

            # Sauvegarder l'ancien .py si présent
            py_path = os.path.join(base_dir, target_name.replace(".pyd", ".py"))
            if os.path.exists(py_path):
                shutil.move(py_path, py_path + ".bak")

            shutil.move(compiled_file, target_path)
            print(f"Renommé {compiled_file} en {target_path}")
            print(f"Renommé {py_path} en {py_path + '.bak'} (backup)")

rename_pyd_files()
