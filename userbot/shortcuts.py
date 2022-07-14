import re
from dataclasses import dataclass
from urllib.parse import quote_plus

from httpx import AsyncClient

from .modules import ShortcutTransformersModule

shortcuts = ShortcutTransformersModule()


@dataclass()
class GitHubMatch:
    username: str
    repo: str | None
    issue: str | None
    branch: str | None
    path: str | None
    line1: str | None
    line2: str | None


@shortcuts.add(r"yt:([a-zA-Z0-9_\-]{11})")
async def youtube(match: re.Match[str]) -> str:
    """Sends a link to a YouTube video"""
    return f"https://youtu.be/{match[1]}"


@shortcuts.add(r"@(\d+)(?::(.+)@)?")
async def mention(match: re.Match[str]) -> str:
    """Mentions a user by ID"""
    return f"<a href='tg://user?id={match[1]}'>{match[2] or match[1]}</a>"


async def github(match: re.Match[str], *, client: AsyncClient) -> str:
    """Sends a link to a GitHub repository"""
    m = GitHubMatch(**match.groupdict())
    url = f"https://github.com/{m.username}"
    text = m.username
    if not m.repo:
        return f"<b>GitHub:</b> <a href='{url}'>{text}</a>"
    if m.repo == "@":
        m.repo = m.username
    url += f"/{m.repo}"
    text += f"/{m.repo}"
    if not m.branch and m.path:
        m.branch = (await client.get(f"/repos/{m.username}/{m.repo}")).json()["default_branch"]
        url += f"/tree/{m.branch}/{m.path}"
        text += f":/{m.path}"
    elif m.branch:
        path = m.path or ""
        url += f"/tree/{m.branch}/{path}"
        if len(m.branch) == 40:  # Full commit hash
            text += f"@{m.branch[:7]}"
        else:
            text += f"@{m.branch}"
        if path:
            text += f":/{path}"
    elif m.issue:
        url += f"/issues/{m.issue}"
        text += f"#{m.issue}"
    if not m.path:
        return f"<b>GitHub:</b> <a href='{url}'>{text}</a>"
    if m.line1:
        url += f"#L{m.line1}"
        text += f"#L{m.line1}"
        if m.line2:
            url += f"-L{m.line2}"
            text += f"-L{m.line2}"
    return f"<b>GitHub:</b> <a href='{url}'>{text}</a>"


@shortcuts.add(r":uwu(\d+)?:")
async def uwu(match: re.Match[str]) -> str:
    """Sends `🥺👉👈` emoji or `👉👈` emoji with the specified number of finger pairs"""
    if not match[1]:
        return "🥺👉👈"
    count = int(match[1])
    return "👉" * count + "👈" * count


@shortcuts.add(r"google://(.+)/")
async def google(match: re.Match[str]) -> str:
    """Sends a link to a Google search"""
    link = f"https://www.google.com/search?q={quote_plus(match[1])}"
    return f"<b>Google:</b> <a href='{link}'>{match[1]}</a>"


@shortcuts.add(r":shrug:")
async def shrug(_: re.Match[str]) -> str:
    """Sends shrug kaomoji"""
    return "¯\\_(ツ)_/¯"
