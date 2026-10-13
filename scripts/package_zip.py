"""ZIP Packaging Utility for BAGR Project Distribution."""

import os
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_ZIP = ROOT_DIR / "BAGR_Gemma4_Developer_Agent_Lab.zip"

EXCLUDE_DIRS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    ".venv",
    "venv",
    ".idea",
    ".vscode",
}

EXCLUDE_EXTS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".zip",
}

def create_archive():
    print(f"[*] Packaging project from: {ROOT_DIR}")
    print(f"[*] Output archive: {OUTPUT_ZIP}")
    
    file_count = 0
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(ROOT_DIR):
            # Modify dirs in-place to skip excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for file in files:
                file_path = Path(root) / file
                if file_path == OUTPUT_ZIP:
                    continue
                if file_path.suffix in EXCLUDE_EXTS:
                    continue
                
                rel_path = file_path.relative_to(ROOT_DIR)
                zipf.write(file_path, arcname=str(rel_path))
                file_count += 1

    size_mb = OUTPUT_ZIP.stat().st_size / (1024 * 1024)
    print(f"[OK] Created {OUTPUT_ZIP.name} ({file_count} files, {size_mb:.2f} MB)")

if __name__ == "__main__":
    create_archive()
