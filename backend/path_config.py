"""
Path Configuration Module

This module handles Python path configuration for the project
to ensure imports work correctly from different execution contexts.
"""

import os
import sys

def setup_project_paths():
    """
    Setup Python paths for the project to ensure imports work correctly
    from any execution context (backend/, services/, or project root).
    """
    # Get the current file's directory
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)
    
    # Determine the backend directory (this file should be in backend/)
    if current_dir.endswith('backend'):
        backend_dir = current_dir
    elif os.path.basename(current_dir) == 'services':
        backend_dir = os.path.dirname(current_dir)
    else:
        # Assume we're in project root, look for backend/
        backend_dir = os.path.join(current_dir, 'backend')
    
    # Add paths to sys.path if not already present
    paths_to_add = [
        backend_dir,  # For importing from backend/
        os.path.join(backend_dir, 'services'),  # For importing from services/
        os.path.dirname(backend_dir),  # For project root imports
    ]
    
    for path in paths_to_add:
        if os.path.exists(path) and path not in sys.path:
            sys.path.insert(0, path)  # Insert at beginning for priority
    
    return backend_dir

def get_backend_dir():
    """Get the absolute path to the backend directory"""
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)
    
    if current_dir.endswith('backend'):
        return current_dir
    elif os.path.basename(current_dir) == 'services':
        return os.path.dirname(current_dir)
    else:
        return os.path.join(current_dir, 'backend')

def get_project_root():
    """Get the absolute path to the project root directory"""
    backend_dir = get_backend_dir()
    return os.path.dirname(backend_dir)

# Auto-setup paths when module is imported
setup_project_paths()
