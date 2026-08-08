#!/usr/bin/env python3
"""
JARVIS Windows EXE Build Script

Builds Jarvis.exe using PyInstaller.

Usage:
    python build/build_exe.py

Output:
    dist/Jarvis.exe (or dist/Jarvis/ for onedir mode)
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent


def clean_build_artifacts(project_root):
    """Clean PyInstaller build artifacts without removing build script itself."""
    print("Cleaning previous build artifacts...")
    
    # Clean PyInstaller build directory (not our build script directory)
    build_dir = project_root / 'build'
    if build_dir.exists():
        # Remove only PyInstaller generated content, keep our scripts
        for item in build_dir.iterdir():
            if item.name not in ['build_exe.py', 'jarvis.spec']:
                if item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                else:
                    item.unlink()
    
    # Clean dist directory
    dist_dir = project_root / 'dist'
    if dist_dir.exists():
        shutil.rmtree(dist_dir, ignore_errors=True)
    
    # Clean spec file backup if exists
    spec_file = project_root / 'Jarvis.spec'
    if spec_file.exists():
        spec_file.unlink()
    
    print("  ✓ Cleaned build artifacts")


def install_dependencies():
    """Ensure PyInstaller is installed."""
    print("Checking dependencies...")
    try:
        import PyInstaller
        print(f"  ✓ PyInstaller {PyInstaller.__version__} found")
    except ImportError:
        print("  Installing PyInstaller...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
        print("  ✓ PyInstaller installed")


def build_exe(project_root):
    """Run PyInstaller to build the executable."""
    print("Building executable with PyInstaller...")
    
    spec_path = project_root / 'build' / 'jarvis.spec'
    
    if not spec_path.exists():
        print(f"  ✗ Error: Spec file not found at {spec_path}")
        return False
    
    # Run PyInstaller with the spec file
    cmd = [
        sys.executable,
        '-m', 'PyInstaller',
        '--clean',
        str(spec_path)
    ]
    
    print(f"  Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            check=True,
            capture_output=True,
            text=True
        )
        print("  ✓ PyInstaller completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ PyInstaller failed with exit code {e.returncode}")
        print(f"  STDOUT:\n{e.stdout}")
        print(f"  STDERR:\n{e.stderr}")
        return False


def verify_build(project_root):
    """Verify that the executable was created successfully."""
    print("Verifying build...")
    
    dist_dir = project_root / 'dist'
    
    if not dist_dir.exists():
        print("  ✗ Error: dist directory not created")
        return False
    
    # Check for both onefile and onedir modes
    exe_onelf = dist_dir / 'Jarvis.exe'
    exe_onedir = dist_dir / 'Jarvis' / 'Jarvis.exe'
    
    if exe_onelf.exists():
        print(f"  ✓ Executable created: {exe_onelf}")
        print(f"    Size: {exe_onelf.stat().st_size / (1024*1024):.1f} MB")
        return True
    elif exe_onedir.exists():
        print(f"  ✓ Executable created (onedir mode): {exe_onedir}")
        jarvis_dir = dist_dir / 'Jarvis'
        total_size = sum(f.stat().st_size for f in jarvis_dir.rglob('*') if f.is_file())
        print(f"    Total size: {total_size / (1024*1024):.1f} MB")
        return True
    else:
        print("  ✗ Error: No executable found in dist/")
        print(f"  Contents of dist/: {list(dist_dir.iterdir())}")
        return False


def main():
    """Main build function."""
    print("=" * 60)
    print("JARVIS EXE BUILD")
    print("=" * 60)
    
    project_root = get_project_root()
    print(f"Project root: {project_root}")
    
    # Step 1: Install dependencies
    install_dependencies()
    
    # Step 2: Clean previous builds
    clean_build_artifacts(project_root)
    
    # Step 3: Build executable
    if not build_exe(project_root):
        print("\n" + "=" * 60)
        print("BUILD FAILED")
        print("=" * 60)
        sys.exit(1)
    
    # Step 4: Verify build
    if not verify_build(project_root):
        print("\n" + "=" * 60)
        print("BUILD VERIFICATION FAILED")
        print("=" * 60)
        sys.exit(1)
    
    # Success
    print("\n" + "=" * 60)
    print("JARVIS BUILD SUCCESS")
    print("=" * 60)
    print("\nExecutable location:")
    dist_dir = project_root / 'dist'
    if (dist_dir / 'Jarvis.exe').exists():
        print(f"  {dist_dir / 'Jarvis.exe'}")
    elif (dist_dir / 'Jarvis' / 'Jarvis.exe').exists():
        print(f"  {dist_dir / 'Jarvis' / 'Jarvis.exe'}")
    
    print("\nTo run Jarvis:")
    print("  Double-click Jarvis.exe")
    print("  Or run from command line: dist\\Jarvis.exe")
    print("\nNote: Ensure Ollama is running with required models before using Jarvis.")
    print("=" * 60)


if __name__ == '__main__':
    main()
