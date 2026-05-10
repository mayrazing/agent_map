#!/usr/bin/env python3
"""
安装脚本：将 map.py 和 CLAUDE.md 规则复制到目标项目。
Install script: copies map.py and CLAUDE.md rules into the target project.
"""

import shutil
import subprocess
import sys
from pathlib import Path

SELF_DIR = Path(__file__).parent
MAP_PY = SELF_DIR / "map.py"
CLAUDE_MD = SELF_DIR / "CLAUDE.md"

SEPARATOR = "\n\n# --- project_map rules (appended by install.py) ---\n\n"


def install(target: Path) -> None:
    if not target.exists():
        print(f"Error: target directory does not exist: {target}")
        sys.exit(1)

    # 复制 map.py
    dest_map = target / "map.py"
    shutil.copy2(MAP_PY, dest_map)
    print(f"copied map.py -> {dest_map}")

    # 处理 CLAUDE.md
    src_content = CLAUDE_MD.read_text(encoding="utf-8")
    dest_claude = target / "CLAUDE.md"

    if dest_claude.exists():
        existing = dest_claude.read_text(encoding="utf-8")
        dest_claude.write_text(existing + SEPARATOR + src_content, encoding="utf-8")
        print(f"appended rules -> {dest_claude}")
    else:
        shutil.copy2(CLAUDE_MD, dest_claude)
        print(f"created CLAUDE.md -> {dest_claude}")

    # 处理 .gitignore
    gitignore_entry = ".project-index/"
    dest_gitignore = target / ".gitignore"

    if dest_gitignore.exists():
        existing = dest_gitignore.read_text(encoding="utf-8")
        if gitignore_entry not in existing.splitlines():
            dest_gitignore.write_text(existing.rstrip("\n") + "\n" + gitignore_entry + "\n", encoding="utf-8")
            print(f"appended {gitignore_entry} -> {dest_gitignore}")
        else:
            print(f"skipped .gitignore ({gitignore_entry} already present)")
    else:
        dest_gitignore.write_text(gitignore_entry + "\n", encoding="utf-8")
        print(f"created .gitignore -> {dest_gitignore}")

    # 安装完立即生成索引
    print("\nRunning map.py to generate the index...")
    result = subprocess.run([sys.executable, str(dest_map)], cwd=target)
    if result.returncode != 0:
        print("Warning: map.py exited with an error. Run it manually to retry.")
    else:
        print("Done.")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 install.py /path/to/your-project")
        sys.exit(1)

    target = Path(sys.argv[1]).resolve()
    install(target)


if __name__ == "__main__":
    main()
