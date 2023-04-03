__all__ = [
    "call_subprocess",
    "SubprocessResult",
]

import asyncio
from dataclasses import dataclass


@dataclass()
class SubprocessResult:
    """Represents the result of a subprocess call."""

    return_code: int
    stdout: bytes
    stderr: bytes

    def __bool__(self) -> bool:
        return self.return_code == 0


async def call_subprocess(
    executable: str,
    *args: str,
) -> SubprocessResult:
    """Calls the given executable with the given arguments."""
    proc = await asyncio.subprocess.create_subprocess_exec(
        "/usr/bin/env",
        executable,
        *args,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()
    return SubprocessResult(proc.returncode, out, err)
