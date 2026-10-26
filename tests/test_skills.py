"""Every `python3 <script> --flag` a skill tells an agent to run must exist in that script's argparse."""

import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_FILES = sorted((ROOT / ".agents" / "skills").glob("*/SKILL.md"))
COMMAND = re.compile(r"python3 (?!-m )([\w/]+\.py)([^`\n|]*)")
FLAG = re.compile(r"(?<![\w-])(--?[a-zA-Z][\w-]*)")


def help_text(script: str, subcommand: str = "") -> str:
    cmd = [sys.executable, script] + ([subcommand] if subcommand else []) + ["--help"]
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=60).stdout


class SkillCommandsTest(unittest.TestCase):
    def test_skill_files_exist(self):
        self.assertEqual({p.parent.name for p in SKILL_FILES}, {"all", "dip", "fix", "master", "port"})

    def test_every_documented_flag_exists(self):
        helps = {}
        missing = []
        for skill in SKILL_FILES:
            for script, args in COMMAND.findall(skill.read_text(encoding="utf-8")):
                self.assertTrue((ROOT / script).exists(), f"{skill.parent.name}: {script} not found")
                args = args.split("#")[0]
                flags = FLAG.findall(args)
                if not flags:
                    continue
                # A script without argparse would run for real on --help and overwrite data/ and reports/.
                self.assertIn("argparse", (ROOT / script).read_text(encoding="utf-8"), f"{skill.parent.name}: {script} takes no flags")
                first = args.split()[0] if args.split() else ""
                key = (script, first if first.isalpha() and first.islower() else "")
                if key not in helps:
                    helps[key] = help_text(*key)
                for flag in flags:
                    if not re.search(rf"(?<![\w-]){re.escape(flag)}(?![\w-])", helps[key]):
                        missing.append(f"{skill.parent.name}: {script} {flag}")
        self.assertEqual(missing, [])


class AgentDocsTest(unittest.TestCase):
    def test_every_skill_points_to_agents_md(self):
        for skill in SKILL_FILES:
            self.assertIn("`AGENTS.md`", skill.read_text(encoding="utf-8"), skill.parent.name)

    def test_entry_files_import_agents_md(self):
        self.assertIn("@./AGENTS.md", (ROOT / "GEMINI.md").read_text(encoding="utf-8"))
        self.assertIn("@AGENTS.md", (ROOT / "CLAUDE.md").read_text(encoding="utf-8"))
        self.assertIn("AGENTS.md", (ROOT / ".agents" / "rules" / "project_essentials.md").read_text(encoding="utf-8"))

    def test_paths_named_in_agent_docs_exist(self):
        missing = []
        for doc in [ROOT / "AGENTS.md", ROOT / "docs" / "METHODOLOGY.md", *SKILL_FILES]:
            for path in re.findall(r"`((?:\.?[\w-]+/)+[\w.-]+\.(?:py|json|md|yml|js|html))`", doc.read_text(encoding="utf-8")):
                if "<" in path or "TICKER" in path or path.startswith(("/tmp", "reports/xxx", "data/.")):
                    continue
                if not (ROOT / path).exists():
                    missing.append(f"{doc.name}: {path}")
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
