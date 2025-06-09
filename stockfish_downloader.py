import platform
import sys
import os
import requests
import tarfile
import zipfile
from tqdm import tqdm

def get_system_info():
    os_name = platform.system()
    arch = platform.machine()
    return os_name, arch

def get_latest_release_info():
    url = "https://api.github.com/repos/official-stockfish/Stockfish/releases/latest"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to fetch release info.")
        sys.exit(1)

def download_file(url, dest_path):
    response = requests.get(url, stream=True)
    total = int(response.headers.get('content-length', 0))
    with open(dest_path, 'wb') as file, tqdm(
        desc=dest_path,
        total=total,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            bar.update(size)

def extract_archive(file_path, extract_to):
    if file_path.endswith('.zip'):
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
    elif file_path.endswith(('.tar.gz', '.tgz', '.tar')):
        with tarfile.open(file_path, 'r:*') as tar_ref:
            tar_ref.extractall(extract_to)
    else:
        print("Unsupported archive format.")
        sys.exit(1)

def download_stockfish():
    os_name, arch = get_system_info()
    print(f"Detected OS: {os_name}, Architecture: {arch}")
    if not (os.path.exists(os.path.abspath('./stockfish/')) and any(
            f.startswith('stockfish') for f in os.listdir(os.path.abspath('./stockfish/')))):

        release_info = get_latest_release_info()
        assets = release_info.get('assets', [])

        # Determine the appropriate asset name based on OS and architecture
        asset_name = None
        if os_name == "Windows":
            if arch in ["AMD64", "x86_64"]:
                asset_name = "stockfish-windows-x86-64.zip"
        elif os_name == "Linux":
            if arch in ["x86_64", "AMD64"]:
                asset_name = "stockfish-ubuntu-x86-64.tar"
        elif os_name == "Darwin":
            if arch in ["x86_64", "AMD64"]:
                asset_name = "stockfish-macos-x86-64.tar"
            elif arch in ["arm64", "aarch64"]:
                asset_name = "stockfish-macos-m1-apple-silicon.tar"

        if not asset_name:
            print("Unsupported OS or architecture.")
            sys.exit(1)

        # Find the download URL for the selected asset
        download_url = None
        for asset in assets:
            if asset['name'] == asset_name:
                download_url = asset['browser_download_url']
                break

        if not download_url:
            print(f"{asset_name} not found in the latest release assets.")
            sys.exit(1)

        print(f"Downloading {asset_name}...")
        download_file(download_url, asset_name)

        print("Extracting the archive...")
        extract_dir = os.path.abspath('./')
        extract_archive(asset_name, extract_dir)

        stockfish_path = './stockfish'
        for file in os.listdir('./stockfish'):
            if file.startswith('stockfish-'):
                stockfish_path = os.path.join(stockfish_path, file)
                break
        print(f"Stockfish has been downloaded and extracted to '{extract_dir}'.")
        return stockfish_path
    else:
        stockfish_path = './stockfish'
        for file in os.listdir('./stockfish'):
            if file.startswith('stockfish-'):
                stockfish_path = os.path.join(stockfish_path, file)
                break

        print(f"Stockfish is already downloaded. path: {os.path.abspath(stockfish_path)}")
        return stockfish_path
