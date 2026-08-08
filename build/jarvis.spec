# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Define the project root (parent of build directory)
import os
import sys

# In spec file execution, we need to determine project root differently
# The spec file is in build/, project root is its parent
spec_file_path = globals().get('_specfile', '')
if spec_file_path:
    spec_file_dir = os.path.dirname(spec_file_path)
else:
    # Fallback: assume spec file is in build/ subdirectory of project root
    spec_file_dir = os.path.join(os.getcwd(), 'build')
    
project_root = os.path.dirname(spec_file_dir)

# main_gui.py is in project root, not in build/
main_gui_path = os.path.join(project_root, 'main_gui.py')

# Data directories are relative to project_root
config_dir = os.path.join(project_root, 'config')
gui_dir = os.path.join(project_root, 'gui')
core_dir = os.path.join(project_root, 'core')
automation_dir = os.path.join(project_root, 'automation')
llm_dir = os.path.join(project_root, 'llm')
memory_dir = os.path.join(project_root, 'memory')
vision_dir = os.path.join(project_root, 'vision')
voice_dir = os.path.join(project_root, 'voice')
plugins_dir = os.path.join(project_root, 'plugins')

a = Analysis(
    [main_gui_path],
    pathex=[project_root],
    binaries=[],
    datas=[
        (config_dir, 'config'),
        (gui_dir, 'gui'),
        (core_dir, 'core'),
        (automation_dir, 'automation'),
        (llm_dir, 'llm'),
        (memory_dir, 'memory'),
        (vision_dir, 'vision'),
        (voice_dir, 'voice'),
        (plugins_dir, 'plugins'),
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
