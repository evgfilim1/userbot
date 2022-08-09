"""This script runs all needed migrations in order"""
import logging
import os
import subprocess
from pathlib import Path

logging.basicConfig(level=logging.DEBUG)
_log = logging.getLogger(__name__)


def main():
    data_dir = Path(os.getenv("DATA_LOCATION", ".dockerdata/userbot")).resolve()

    if not data_dir.exists():
        _log.warning("You don't have a data directory so migrations are not required.")
        return

    storage_version_file = data_dir / ".storageversion"
    try:
        storage_version = int(storage_version_file.read_text().strip())
    except FileNotFoundError:
        storage_version = 0

    for name in sorted(os.listdir("userbot/migrations")):
        if name.endswith(".py") and name != "__main__.py":
            if storage_version >= int(name[:2]):
                _log.info(f"Skipping {name}")
                continue
            _log.info(f"Running {name}")
            proc = subprocess.Popen(
                f"python3.10 -m userbot.migrations.{name.removesuffix('.py')}",
                shell=True,
            )
            return_code = proc.wait()
            if return_code != 0:
                _log.error(f"{name} failed with return code {return_code}")
                return
            storage_version_file.write_text(name[:2])


main()
