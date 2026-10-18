"""Freeze the installed production dependency graph after intentional root-pin updates."""
from importlib.metadata import distribution, version
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

roots = ["fastapi", "starlette", "pydantic", "pydantic-core", "uvicorn", "pip"]
resolved: set[str] = set()


def visit(name: str) -> None:
    name = canonicalize_name(name)
    if name in resolved:
        return
    resolved.add(name)
    for raw in distribution(name).requires or []:
        requirement = Requirement(raw)
        if requirement.marker is None or requirement.marker.evaluate({"extra": ""}):
            visit(requirement.name)


for root in roots:
    visit(root)
text = "# Pinned installed production graph; regenerate deliberately with lock_requirements.py.\n"
text += "\n".join(f"{name}=={version(name)}" for name in sorted(resolved))+"\n"
Path("requirements.txt").write_text(text)
print(text)
