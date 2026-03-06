from PyInstaller.utils.hooks import (
    collect_submodules,
    collect_data_files,
    collect_dynamic_libs,
)

block_cipher = None

pyside6_datas = collect_data_files("PySide6")
pyside6_bins = collect_dynamic_libs("PySide6")
mpl_datas = collect_data_files("matplotlib")

hiddenimports = (
    collect_submodules("PySide6")
    + collect_submodules("matplotlib")
    + ["matplotlib.backends.backend_qtagg"]
)

a = Analysis(
    ["run_gui.py"],
    pathex=[".", "../.."],
    binaries=[
        *pyside6_bins,
    ],
    datas=[
        ("../../src/ade_insight/gui/style.qss", "ade_insight/gui"),
        ("../../src/ade_insight/gui/assets", "ade_insight/gui/assets"),
        *pyside6_datas,
        *mpl_datas,
    ],
    hiddenimports=hiddenimports,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ade-insight",
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="ade-insight",
)
