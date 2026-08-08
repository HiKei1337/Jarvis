"""
Path resolver for PyInstaller compatibility.

Provides unified path resolution that works both:
1. During normal Python development
2. Inside PyInstaller bundled executable
"""

import os
import sys


def get_resource_path(relative_path: str) -> str:
    """
    Get absolute path to resource, works for dev and PyInstaller.
    
    Args:
        relative_path: Relative path from project root (e.g., 'config/config.yaml')
    
    Returns:
        Absolute path to the resource
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        # sys._MEIPASS points to the temporary bundle directory
        base_path = sys._MEIPASS
    else:
        # Running in normal Python environment
        # Use the directory containing this file's parent (project root)
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    return os.path.join(base_path, relative_path)


def get_project_root() -> str:
    """
    Get the project root directory.
    
    Returns:
        Absolute path to project root
    """
    if getattr(sys, 'frozen', False):
        # For PyInstaller, use the directory containing the executable
        return os.path.dirname(sys.executable)
    else:
        # For development, go up from this file to project root
        return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def get_config_path() -> str:
    """
    Get path to config file.
    
    Returns:
        Absolute path to config/config.yaml
    """
    return get_resource_path('config/config.yaml')


def get_gui_resources_path(subpath: str = '') -> str:
    """
    Get path to GUI resources.
    
    Args:
        subpath: Optional subpath within gui/resources
    
    Returns:
        Absolute path to GUI resources
    """
    base = get_resource_path('gui')
    if subpath:
        return os.path.join(base, subpath)
    return base
