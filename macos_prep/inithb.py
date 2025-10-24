#!/usr/bin/env python3
import sys
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
    # Get brew root from argument or use default
    brew_root = Path(sys.argv[1] if len(sys.argv) > 1 else ".brew").resolve()
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

    print("Setup complete!")

if __name__ == "__main__":
    main()
