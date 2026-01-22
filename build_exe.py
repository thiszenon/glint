import PyInstaller.__main__
import os
import shutil

def build():
    print("building Glint v1.0...")
    
    # Clean previous builds
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    if os.path.exists('build'):
        shutil.rmtree('build')

    # Define paths
    base_dir = os.path.abspath(os.path.dirname(__file__))
    src_dir = os.path.join(base_dir, 'src')
    
    # PyInstaller arguments
    args = [
        'src/glint/cli/main.py',           # entry point
        '--name=glint',                    # name of the executable
        '--onefile',                       # single file
        '--clean',
        '--noconsole',                         # clean cache
        '--noconfirm',                     # overwrite existing
        
        # Include data files (source:destination
        f'--add-data={os.path.join(src_dir, "glint/web/templates")};glint/web/templates',
        f'--add-data={os.path.join(src_dir, "glint/web/static")};glint/web/static',
        f'--add-data={os.path.join(src_dir, "glint/assets")};glint/assets',
        
        # Hidden imports (sometimes missed by PyInstaller)
        '--hidden-import=sqlmodel',
        '--hidden-import=sqlalchemy',
        '--hidden-import=typer',
        '--hidden-import=rich',
        '--hidden-import=flask',
        '--hidden-import=plyer',
        '--hidden-import=requests',
        '--hidden-import=urllib3',
        '--hidden-import=questionary',
        '--hidden-import=customtkinter' # Still needed if referenced in imports even if unused
    ]
    
    # Run PyInstaller
    PyInstaller.__main__.run(args)
    
    print("\n build complete! Executable is in dist/glint.exe")

if __name__ == "__main__":
    build()
