#!/usr/bin/env python3
import sys
import subprocess
import tempfile
import shutil
import os
from pathlib import Path

REPO = "tweakoz/ork.build"
FOLDER = "macos_prep"

def main():
    # Get branch from env var, command line arg, or use default
    branch = os.environ.get("BRANCH") or (sys.argv[1] if len(sys.argv) > 1 else "toz-2025-dev287")

    print(f"Downloading {FOLDER} from {REPO}@{branch}...")

    # Create temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # Download and extract the branch tarball
        tarball_url = f"https://github.com/{REPO}/archive/refs/heads/{branch}.tar.gz"

        subprocess.run(
            ["curl", "-fsSL", tarball_url],
            stdout=subprocess.PIPE,
            check=True
        )

        # Download and extract in one go
        curl_proc = subprocess.Popen(
            ["curl", "-fsSL", tarball_url],
            stdout=subprocess.PIPE
        )

        subprocess.run(
            ["tar", "-xz", "-C", tmpdir],
            stdin=curl_proc.stdout,
            check=True
        )
        curl_proc.wait()

        # Find the extracted folder
        extracted_dirs = list(Path(tmpdir).glob("ork.build-*"))
        if not extracted_dirs:
            print("Error: Could not find extracted directory")
            sys.exit(1)

        extracted = extracted_dirs[0]

        # Copy macos_prep to current directory
        src_folder = extracted / FOLDER
        dest_folder = Path.cwd() / FOLDER

        if dest_folder.exists():
            shutil.rmtree(dest_folder)
        shutil.copytree(src_folder, dest_folder)

        # Run inithb.sh
        os.chdir(dest_folder)
        init_script = Path("inithb.sh")
        init_script.chmod(0o755)

        subprocess.run(["./inithb.sh"], check=True)

    print("Setup complete!")

if __name__ == "__main__":
    main()
