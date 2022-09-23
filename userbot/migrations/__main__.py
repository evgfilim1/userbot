"""This script runs all needed migrations in order"""
import logging
import os
from importlib import import_module
from pathlib import Path

logging.basicConfig(level=logging.INFO)
_log = logging.getLogger(__name__)


def _migration_runner(name: str) -> bool:
    """Run a migration by name"""
    _log.info("Running %r", name)
    # noinspection PyBroadException
    try:
        migration = import_module(f"userbot.migrations.{name}")
        _log.info("%s", migration.__doc__ or "(No description provided)")
        migration.main()
    except Exception:
        _log.exception("Failed to run migration %r", name)
        return False
    return True


def main():
    data_dir = Path(os.getenv("DATA_LOCATION", ".dockerdata/userbot")).resolve()

    _log.debug("Checking data directory %s", data_dir)
    if not data_dir.exists():
        _log.warning("You don't have a data directory so migrations are not required.")
        return

    storage_version_file = data_dir / ".storageversion"
    try:
        _log.debug("Reading storage version")
        storage_version = int(storage_version_file.read_text().strip())
    except FileNotFoundError:
        _log.debug("Storage version file not found, assuming 0")
        storage_version = 0
    else:
        _log.debug("Storage version is %02d", storage_version)

    for name in sorted(os.listdir("userbot/migrations")):
        if name.endswith(".py") and name != "__main__.py":
            if storage_version >= int(name[:2]):
                _log.info(f"Skipping {name}")
                continue
            if not _migration_runner(name.removesuffix(".py")):
                _log.error("Aborting")
                return
            storage_version_file.write_text(name[:2])


main()
