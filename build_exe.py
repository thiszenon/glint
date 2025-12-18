import PyInstaller.__main__
import os
import shutil

def build():
    print("🚀 Building Glint v1.0...")
    
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
        'src/glint/cli/main.py',           # Entry point
        '--name=glint',                    # Name of the executable
        '--onefile',                       # Single file
        '--clean',
        '--noconsole',                         # Clean cache
        '--noconfirm',                     # Overwrite existing
        
        # Include data files (source:destination)
        # Windows uses ; as separator
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
    
    print("\n✅ Build complete! Executable is in dist/glint.exe")

if __name__ == "__main__":
    build()
