#This script will setup everything you need for Pygram! ...Probably. Hopefully.

import sys
import subprocess
import os
import platform
from pathlib import Path
import shutil

print("Running setup! Please wait if it takes a minute!")
def check_python_version():
    print("Checking Python version!")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("Error Code 42: Python 3.8 or higher is required.")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        print("Sorry! Please upgrade Python and try again.")
        return False

    print(f"Python {version.major}.{version.minor}.{version.micro} is compatible!")
    return True

def check_pip():
    print("\nChecking pip...")

    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"],
                       check=True, capture_output=True)
        print("Pip is available!!")
        return True
    except subprocess.CalledProcessError:
        print("Error code 42: Pip is not available. Please install Pip!")
        return False
def install_requirements():
    print("\n Installing required packages!")

    requirements = [
        "PyQt6>=6.4.0",
        "PyQt6-Qt6>=6.4.0",
        "pytm>=1.3.0",
    ]
    optional_requirements = [
        "Pillow>=9.0.0",
        "reportlab>=3.6.0",
        "PyQt6-tools>=6.4.0",
    ]

    print("Installing core requirements!")
    for package in requirements:
        print(f"Installing {package}...")
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], check=True, capture_output=True)
            print(f"{package} installed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {package}!")
            print(f"Error 42: {e}")
            return False
    print("\nInstalling optional packages!")
    for package in optional_requirements:
        print(f"Installing {package}!")
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], check=True, capture_output=True)
            print(f"{package} installed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"Optional package {package} failed to install (this is fine)")
            print(f"You may have limited export functionality!")
    return True

def get_pygram_path():
    possible_names = ["main.py", "run.py", "pygram.py"] #main.py should be standard, but just in case it gets changed
    current_dir = Path.cwd()
    for name in possible_names:
        script_path = current_dir / name
        if script_path.exists():
            return script_path
    print("\n Error 42: Couldn't find main Pygram script!")
    script_name = input("What's the name of your main Python file? (example may be pygram.py):").strip()
    script_path = current_dir / script_name
    if script_path.exists():
        return script_path
    else:
        print(f"Error 42: {script_name} not found in current dirrectory!")
        return None

def create_desktop_shortcut():
    print("\n Setting up desktop shortcut!")
    script_path = get_pygram_path()
    if not script_path:
        print("Skipping desktop shortcut!")
        return False
    create_shortcut = input("Would you like to create a desktop shortcut? (y/n): ").strip().lower()
    if create_shortcut not in ['y', 'yes']:
        print("Skipping desktop shortcut creation!")
        return True
    
    system = platform.system()

    if system == "Windows":
        return create_windows_shortcut(script_path)
    elif system == "Darwin":
        return create_macOS_shortcut(script_path) #APPARENTLY ITS CALLED DARWIN??
    elif system == "Linux":
        return create_linux_shortcut(script_path)
    else:
        print(f"Desktop shortcut creation not supported for {system} :( Sorry!")
        return False

def create_windows_shortcut(script_path):
    try:
        import winshell # type: ignore
        print("Creating Windows desktop shortcut!")

        desktop = winshell.desktop()
        shortcut_path = os.path.join(desktop, "Pygram.lnk")
        with winshell.shortcut(shortcut_path) as shortcut:
            shortcut_path = sys.executable
            shortcut.arguments = str(script_path)
            shortcut.description = "Pygram - Python Threat Modelling Diagram App"
            shortcut.working_directory = str(script_path.parent)
        print(f"Desktop shortcut created: {shortcut_path}")
        return True
    except ImportError:
        print("Installing winshell for shortcut creation!")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "winshell"],
                           check=True, capture_output=True)
            return create_windows_shortcut(script_path)
        except subprocess.CalledProcessError:
            print("Error 42: Failed to install winshell! Creating batch file instead.")
            return create_windows_batch_file(script_path)

def create_windows_batch_file(script_path):
    try:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        batch_path = os.path.join(desktop, "Pygram.bat")
        with open(batch_path, 'w') as f:
            f.write(f'@echo off\n')
            f.write(f'cd /d "{script_path.parent}"\n')
            f.write(f'"{sys.executable}" "{script_path}"\n')
            f.write(f'pause\n')

            print(f"Desktop batch file created: {batch_path}")
            return True
    except Exception as e:
        print(f"Error code 42: Failed to create batch file: {e}")
        return False

def create_macOS_shortcut(script_path):    
    try:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        app_path = os.path.join(desktop, "Pygram.app")

        os.makedirs(os.path.join(app_path, "Contents", "MacOS"), exist_ok=True)
        exec_script = os.path.join(app_path, "Contents", "MacOS", "Pygram")
        with open(exec_script, 'w') as f:
            f.write(f'#!/bin/bash\n')
            f.write(f'cd "{script_path.parent}"\n')
            f.write(f'"{sys.executable}" "{script_path}"\n')
        
        os.chmod(exec_script, 0o755) #THE NUMBERS MASON

        info_plist = os.path.join(app_path, "Contents", "Info.plist")
        with open(info_plist, 'w') as f:
            f.write('''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple/DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
        <key>CFBundleExecutable</key>
    <string>Pygram</string>
    <key>CFBundleIdentifier</key>
    <string>com.user.pygram</string>
    <key>CFBundleName</key>
    <string>Pygram</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
</dict>
</plist>''')
            print(f"macOS app bundle created: {app_path}")
            return True
    except Exception as e:
        print(f"Error code 42: Failed to create macOS shortcut: {e}")
        return False

def create_linux_shortcut(script_path):
    try:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        shortcut_path = os.path.join(desktop, "Pygram.desktop")
        with open(shortcut_path, 'w') as f:
            f.write(f'[Desktop Entry]\n')
            f.write(f'Version=1.0\n')
            f.write(f'Type=Application\n')
            f.write(f'Name=Pygram\n')
            f.write(f'Comment=Python Threat Modelling Diagram App\n')
            f.write(f'Exec={sys.executable} {script_path}\n')
            f.write(f'Path={script_path.parent}\n')
            f.write(f'Terminal=false\n')
            f.write(f'StartupNotify=true\n')
            
        os.chmod(shortcut_path, 0o755)
        print(f"Desktop shortcut created! {shortcut_path}")
        return True
    
    except Exception as e:
        print(f"Failed to create Linux shortcut: {e}")
        return False

def main():
    print("=" * 50)
    print("Welcome to Pygram Setup!")
    print("=" * 50)
    if not check_python_version():
        return False
    if not check_pip():
        return False
    if not install_requirements():
        return False
    create_desktop_shortcut()

    print("\n" + "=" * 50)
    print("Setup complete!")
    print("You should now be able to run Pygram!!")

    run_now = input("\n Would you like to start Pygram? (y/n): ")
    if run_now in ['y', 'yes']:
        script_path = get_pygram_path()
        if script_path:
            print(f"Starting Pygram!")
            subprocess.run([sys.executable, str(script_path)])
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n Error 42: Setup interrupted by user.")
    except Exception as e:
        print(f"Setup failed with error: {e}")
        print("Please check the error and try again! Error code 42 (fatal).")
    
    input("\n Press Enter to exit.")