from pathlib import Path

BASE_URL = "https://scandoc.qaoverflow.com"
BROWSER = "chromium"
HEADLESS = True
DATA_DIR = str(Path(__file__).resolve().parent / "data")
GLOBAL_TIMEOUT = "30s"
SCAN_TIMEOUT = "300s"
