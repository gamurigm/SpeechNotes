# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import os

block_cipher = None

# ---------------------------------------------------------------------------
# Hidden imports – only what the app actually uses
# ---------------------------------------------------------------------------
hiddenimports = [
    # Uvicorn internals that are loaded dynamically
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',

    # FastAPI / web
    'fastapi',
    'multipart',            # python-multipart
    'passlib',
    'jwt',
    'engineio.async_drivers.asgi',

    # AI / LLM
    'pydantic_ai',
    'openai',
    'smolagents',

    # Chroma (vector store) – be specific, NOT the whole langchain tree
    'langchain_chroma',
    'chromadb',
    'chromadb.api',
    'chromadb.api.segment',
    'chromadb.db.impl',
    'chromadb.db.impl.sqlite',

    # NVIDIA gRPC client
    'nvidia_riva_client',

    # SQLite (for our SQLiteManager)
    'sqlite3',
]

hiddenimports += collect_submodules('pydantic')
# Only collect chromadb sub-modules (not the whole langchain universe)
hiddenimports += collect_submodules('chromadb')
# Collect all backend and src sub-modules so `from backend.xxx` resolves
hiddenimports += collect_submodules('backend')
hiddenimports += collect_submodules('src')

# ---------------------------------------------------------------------------
# Data files
# ---------------------------------------------------------------------------
datas = []
try:
    datas += collect_data_files('chromadb')
except Exception:
    pass  # chromadb data collection may fail; it is optional

# ---------------------------------------------------------------------------
# Excludes – heavy packages that get pulled transitively but are NOT needed
# ---------------------------------------------------------------------------
excludes = [
    # Scientific stack (pulled via langchain/chromadb transitive deps)
    'scipy',
    'pandas',
    'matplotlib',
    'sklearn',
    'scikit-learn',

    # AWS (pulled by botocore → langchain_community)
    'botocore',
    'boto3',
    'aiobotocore',
    's3transfer',

    # Interactive / dev tools
    'IPython',
    'jedi',
    'parso',
    'notebook',
    'nbformat',
    'nbconvert',
    'jupyter',
    'jupyter_client',
    'jupyter_core',

    # GUI toolkits not needed for a headless backend
    'tkinter',
    '_tkinter',
    'tcl',

    # Testing frameworks
    'pytest',
    'py',

    # Other heavy unused deps
    'torch',
    'tensorflow',
    'tf_keras',
    'keras',
    'h5py',
    'tensorboard',
    'transformers',
    'sentence_transformers',
    'onnxruntime',
    'pillow',
    'PIL',
    'black',
    'pylint',
    'astroid',
    'openpyxl',
    'sqlalchemy',

    # Additional heavy transitive deps
    'faiss',
    'faiss_cpu',
    'sympy',
    'lxml',
    'psutil',

    # logfire Pydantic plugin calls inspect.getsource() which fails in frozen bundles
    'logfire',
]

a = Analysis(
    ['backend/main.py'],
    pathex=['.'],           # project root so `from backend…` / `from src…` resolve
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[os.path.join(SPECPATH, 'desktop', 'pyi_rth_paths.py')],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='speechnotes-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True, # Set to False in production if you want a silent background process
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='speechnotes-backend',
)
