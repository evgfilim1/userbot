__all__ = [
    "GitHubClient",
]

from .base_client import BaseClient


class GitHubClient(BaseClient, base_url="https://api.github.com"):
    async def get_default_branch(self, owner: str, repo: str) -> str:
        return (await self._client.get(f"/repos/{owner}/{repo}")).json()["default_branch"]
