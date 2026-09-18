"""Install pinned official CI binaries after verifying their archive checksums."""

import argparse
import hashlib
import json
import platform
import subprocess
import tarfile
import tempfile
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "scripts/ci-tools.json").read_text())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tools", nargs="+", choices=sorted(manifest))
    args = parser.parse_args()
    machine = {"arm64": "arm64", "aarch64": "arm64", "x86_64": "amd64"}.get(
        platform.machine(), platform.machine()
    )
    target = f"{platform.system().lower()}-{machine}"
    directory = root / ".ci-tools/bin"
    directory.mkdir(parents=True, exist_ok=True)
    for name in args.tools:
        release = manifest[name]
        if target not in release["platforms"]:
            raise SystemExit(f"No pinned {name} binary for {target}; see docs/CI.md")
        archive = release["platforms"][target]
        executable = directory / name
        stamp = directory / f"{name}.sha256"
        if executable.exists() and stamp.exists():
            installed = hashlib.sha256(executable.read_bytes()).hexdigest()
            if stamp.read_text() == f"{archive['sha256']} {installed}":
                continue
        with tempfile.TemporaryDirectory(prefix="patient-sim-tool-") as temporary:
            package = Path(temporary) / "release.tar.gz"
            subprocess.run(
                [
                    "curl",
                    "--fail",
                    "--location",
                    "--silent",
                    "--show-error",
                    "--retry",
                    "2",
                    "--output",
                    str(package),
                    archive["url"],
                ],
                check=True,
                timeout=120,
            )
            if hashlib.sha256(package.read_bytes()).hexdigest() != archive["sha256"]:
                raise SystemExit(f"Checksum mismatch for {name}; refusing to install")
            with tarfile.open(package) as bundle:
                member = next(
                    m for m in bundle.getmembers() if m.isfile() and Path(m.name).name == name
                )
                source = bundle.extractfile(member)
                if source is None:
                    raise SystemExit(f"Missing executable in {name} archive")
                data = source.read()
            executable.write_bytes(data)
            executable.chmod(0o755)
            stamp.write_text(f"{archive['sha256']} {hashlib.sha256(data).hexdigest()}")
            print(f"Installed {name} {release['version']} ({target}); checksum verified")


if __name__ == "__main__":
    main()
