#!/usr/bin/env python3
import argparse
import subprocess
import os
from pathlib import Path

def run(cmd, cwd=None, check=True, shell=False):
    """Run a command and return the result."""
    print(f"Running: {cmd if isinstance(cmd, str) else ' '.join(cmd)}")
    if isinstance(cmd, str) and not shell:
        # Convert string to list for non-shell execution
        cmd = cmd.split()
    return subprocess.run(cmd, cwd=cwd, check=check, shell=shell)

def main():
    parser = argparse.ArgumentParser(description='Initialize Homebrew in a custom root directory')
    parser.add_argument('--root', type=str, required=True,
                        help='Root directory where .brew (and later .venv, .staging) will be created')
    args = parser.parse_args()

    # Create root directory and set up brew inside it
    root_dir = Path(args.root).resolve()
    root_dir.mkdir(parents=True, exist_ok=True)
    brew_root = root_dir / ".brew"

    print(f"Using root directory: {root_dir}")
    print(f"Homebrew will be installed at: {brew_root}")

    script_dir = Path(__file__).parent.resolve()
    brewfile = script_dir / "Brewfile"

    # Clone homebrew if it doesn't exist
    if not brew_root.exists():
        run(["git", "clone", "--depth=1000",
             "https://github.com/Homebrew/brew.git", str(brew_root)])

    # Fetch and checkout specific version
    run(["git", "fetch"], cwd=brew_root)
    run(["git", "checkout", "4.6.8"], cwd=brew_root)

    # Set up environment
    env = os.environ.copy()
    env["HOMEBREW_PREFIX"] = str(brew_root)
    env["HOMEBREW_NO_AUTO_UPDATE"] = "1"
    env["HOMEBREW_NO_ANALYTICS"] = "1"
    env["PATH"] = f"{brew_root}/bin:{env.get('PATH', '')}"

    # Run brew bundle with Brewfile from script directory
    if not brewfile.exists():
        print(f"Warning: Brewfile not found at {brewfile}")
    else:
        subprocess.run(
            ["brew", "bundle", "install", "--file", str(brewfile), "--cleanup"],
            env=env,
            check=True
        )

    # Create symlink for python3
    bin_dir = brew_root / "bin"
    if bin_dir.exists():
        python_link = bin_dir / "python3"
        python_target = bin_dir / "python3.14"
        if python_target.exists() and not python_link.exists():
            python_link.symlink_to("python3.14")
            print(f"Created symlink: python3 -> python3.14")
    else:
        print(f"Warning: {bin_dir} does not exist, skipping python3 symlink")

    # Fix wget certificates
    wgetrc = brew_root / "etc" / "wgetrc"
    cert_pem = brew_root / "etc" / "ca-certificates" / "cert.pem"
    if wgetrc.exists() and cert_pem.exists():
        content = wgetrc.read_text()
        if "ca_certificate=" not in content:
            with wgetrc.open("a") as f:
                f.write(f"\nca_certificate={cert_pem}\n")
            print("Fixed wget certificates")

    # Fix OpenSSL certificates
    openssl_dir = brew_root / "etc" / "openssl@3"
    if openssl_dir.exists() and cert_pem.exists():
        openssl_cert = openssl_dir / "cert.pem"
        if not openssl_cert.exists():
            openssl_cert.symlink_to(cert_pem)
            print("Fixed OpenSSL certificates")

    # Fix curl certificates
    curlrc = brew_root / "etc" / "curlrc"
    if cert_pem.exists():
        # Ensure etc directory exists
        curlrc.parent.mkdir(parents=True, exist_ok=True)
        curlrc.write_text(f"cacert={cert_pem}\n")
        print("Fixed curl certificates")

    # Set up Python certificates
    pip_config_dir = Path.home() / ".config" / "pip"
    pip_config_dir.mkdir(parents=True, exist_ok=True)
    pip_config = pip_config_dir / "pip.conf"

    if cert_pem.exists():
        pip_config.write_text(f"[global]\ncert = {cert_pem}\n")
        print(f"Writing to {pip_config}")

    # Create virtual environment in <root>/.venv using brew's python
    venv_dir = root_dir / ".venv"
    python_bin = brew_root / "bin" / "python3"

    if python_bin.exists():
        if not venv_dir.exists():
            print(f"Creating virtual environment at: {venv_dir}")
            subprocess.run(
                [str(python_bin), "-m", "venv", str(venv_dir)],
                check=True
            )
            print(f"Virtual environment created at {venv_dir}")
        else:
            print(f"Virtual environment already exists at {venv_dir}")
    else:
        print(f"Warning: Python not found at {python_bin}, skipping venv creation")

    print("Setup complete!")

if __name__ == "__main__":
    main()
Mac:macos_prep michael$
Mac:macos_prep michael$ cat install.py
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
