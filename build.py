import sys
import shutil
import subprocess
from pathlib import Path


def build_with_nuitka(icon: Path, licence: Path, adb_path: Path):
    """
    Build the application using Nuitka with the provided icon and license file.
    """
    command = [
        sys.executable, "-m", "nuitka",
        "--onefile",
        f"--windows-icon-from-ico={icon}",
        f"--include-data-files={icon}={icon}",
        f"--include-data-files={licence}={licence}",
        fr"--include-data-files={adb_path}\adb.exe={adb_path}\adb.exe",
        fr"--include-data-files={adb_path}\AdbWinApi.dll={adb_path}\AdbWinApi.dll",
        fr"--include-data-files={adb_path}\AdbWinUsbApi.dll={adb_path}\AdbWinUsbApi.dll",
        f"--include-data-files={Path('assets/example_app_paths.txt')}=assets/example_app_paths.txt",
        "--enable-plugin=tk-inter",
        "--windows-console-mode=disable",
        "--python-flag=no_site",
        "--product-version=1.1.0.0",
        "--file-version=1.1",
        "--file-description=Android Debloater",
        "--company-name=ciwga",
        "--product-name=Android Debloater",
        "--copyright=© 2024 ciwga",
        "android_debloater.py",
    ]
    
    try:
        result = subprocess.run(command, check=True)
        print("Build is successful!")
    except subprocess.CalledProcessError as e:
        print(f"Error Code: {e.returncode}")
        print(f"Error: {e.stderr}")


def is_inno_setup_installed() -> bool:
    """
    Check if Inno Setup Compiler (ISCC) is installed and available in PATH.
    """
    return shutil.which("ISCC") is not None


def build_with_inno_setup(iss_file: Path):
    """
    Build the installer using Inno Setup with the provided .iss file.
    """
    if not iss_file.exists():
        print(f"Error: ISS file '{iss_file}' does not exist.")
        return

    if not is_inno_setup_installed():
        print("Error: Inno Setup Compiler (ISCC) is not installed or not in PATH.")
        return

    try:
        result = subprocess.run(["ISCC", str(iss_file)], check=True)
        print("Inno Setup build is successful!")
    except subprocess.CalledProcessError as e:
        print(f"Error Code: {e.returncode}")
        print(f"Error: {e.stderr}")


if __name__ == "__main__":
    icon_path = Path("assets/android_debloater.ico")
    licence_path = Path("License")
    adb = Path("assets/adb")

    print("Starting Nuitka build...")
    build_with_nuitka(icon_path, licence_path, adb)
    
    print("Starting Inno Setup build...")
    iss_file_path = Path("android_debloater.iss")
    build_with_inno_setup(iss_file_path)