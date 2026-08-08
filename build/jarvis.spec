# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Define the project root (parent of build directory)
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

a = Analysis(
    ['main_gui.py'],
    pathex=[project_root],
    binaries=[],
    datas=[
        ('config', 'config'),
        ('gui', 'gui'),
        ('core', 'core'),
        ('automation', 'automation'),
        ('llm', 'llm'),
        ('memory', 'memory'),
        ('vision', 'vision'),
        ('voice', 'voice'),
        ('plugins', 'plugins'),
    ],
    hiddenimports=[
        # PySide6 / customtkinter dependencies
        'customtkinter',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        
        # Automation
        'pyautogui',
        'pyperclip',
        'pygetwindow',
        'mss',
        'numpy',
        'cv2',
        'opencv_python',
        
        # Voice
        'vosk',
        'sounddevice',
        'torch',
        
        # Core utilities
        'yaml',
        'requests',
        
        # Database
        'sqlite3',
        
        # Threading and concurrency
        '_thread',
        'queue',
        
        # Encoding
        'encodings',
        'encodings.utf_8',
        'encodings.cp1252',
        
        # Platform specific
        'ctypes',
        'winreg',
        
        # Ollama client
        'ollama',
        
        # Other potential hidden imports
        'pkg_resources.py2_warn',
        'pkg_resources.extern.appdirs',
        'pkg_resources.extern.packaging',
        'pkg_resources.extern.pyparsing',
        'pkg_resources.extern.six',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'pandas',
        'jupyter',
        'notebook',
        'IPython',
        'test',
        'tests',
        'unittest',
        'doctest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Jarvis',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # False for GUI app (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path if available: icon='gui/icon.ico'
)
