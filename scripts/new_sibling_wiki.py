#!/usr/bin/env python3
"""Scaffold a sibling LLM wiki repo on a different topic set.

Copies the conventions, tooling and CI from this repo (but none of its wiki
content) into a new folder, rewrites the topic-specific parts, seeds empty
wiki pages for each top topic, and runs the navtree build to verify.

Usage (run from anywhere):

    python3 scripts/new_sibling_wiki.py ../wiki-water \\
        --title "Water & Land Stewardship" \\
        --topic "Water Governance" \\
        --topic "Soil Health=Soil Health & Regeneration" \\
        --topic "Rangeland Restoration"

Each --topic is a folder name, optionally followed by "=Display Title".
See docs/creating-a-sibling-wiki.md for the full walkthrough.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent  # this repo's root
TODAY = date.today().isoformat()

DISPATCH_STEP = """
      - name: Dispatch sync to downstream navtree repo
        if: steps.commit.outputs.changed == 'true'
        run: |
          gh api repos/{repo}/dispatches \\
            -f event_type=navtree-updated
        env:
          GH_TOKEN: ${{{{ secrets.NAVTREE_SYNC_TOKEN }}}}
"""

NUMBER_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
                6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten"}

# Files/dirs copied verbatim (relative to repo root).
COPY_FILES = [
    ".gitignore",
    ".github/pull_request_template.md",
    ".navtree/build_navtree.py",
    ".navtree/build.toml",
    ".navtree/README.md",
    ".obsidian/app.json",
    ".obsidian/appearance.json",
    ".obsidian/core-plugins.json",
    ".obsidian/community-plugins.json",
    ".obsidian/graph.json",
    "scripts/new_sibling_wiki.py",
]
COPY_DIRS = [".obsidian/plugins/homepage", "docs"]


class Topic:
    def __init__(self, spec: str):
        folder, _, title = spec.partition("=")
        self.folder = folder.strip()
        self.title = (title or folder).strip()
        if not self.folder or "/" in self.folder:
            sys.exit(f"Invalid --topic {spec!r}: folder name must be non-empty and contain no '/'")
        self.slug = kebab(self.folder)

    @property
    def link(self) -> str:
        return f"{self.folder}/{self.slug}"


def kebab(name: str) -> str:
    s = re.sub(r"[^\w\s-]", "", name.lower())
    return re.sub(r"[\s_]+", "-", s).strip("-")


def sub_once(pattern: str, repl: str, text: str, what: str, flags: int = 0, count: int = 1) -> str:
    """re.sub that fails loudly if the pattern no longer matches."""
    new, n = re.subn(pattern, repl, text, count=count, flags=flags)
    if n == 0:
        sys.exit(f"Template drift: could not find {what}. Update scripts/new_sibling_wiki.py.")
    return new


def rewrite_claude_md(text: str, topics: list[Topic]) -> str:
    n = len(topics)
    word = NUMBER_WORDS.get(n, str(n))
    text = sub_once(r"### 1\. \w+ Top Topics Are Fixed",
                    f"### 1. {word.capitalize()} Top Topics Are Fixed", text, "Rule 1 heading")
    text = sub_once(r"under exactly \w+ top-level topics", f"under exactly {word} top-level topics",
                    text, "Rule 1 intro")
    topic_list = "\n".join(f"{i}. **{t.title}** — `wiki/{t.folder}/`" for i, t in enumerate(topics, 1))
    text = sub_once(r"(?:^\d+\. \*\*.+?\*\* — `wiki/.+?/`\n)+", topic_list + "\n", text,
                    "Rule 1 topic list", flags=re.M)
    for phrase in ["these {} topics", "all {} topics", "the {} top topics"]:
        text = sub_once(re.escape(phrase.format("three")).replace("three", r"\w+"),
                        phrase.format(word), text, f"phrase '{phrase}'", count=0)
    width = max(len(t.folder) for t in topics) + 2
    layout = "".join(f"  {(t.folder + '/').ljust(width)} # Topic {i}\n" for i, t in enumerate(topics, 1))
    text = sub_once(r"(?:^  .+/\s+# Topic \d+\n)+", layout, text, "directory layout topics", flags=re.M)
    text = sub_once(r"Wikilinks include subfolder: `\[\[.+?\]\]`",
                    f"Wikilinks include subfolder: `[[{topics[0].folder}/example-page]]`",
                    text, "naming-convention example")
    return text


def rewrite_readme(text: str, title: str, topics: list[Topic]) -> str:
    n = len(topics)
    word = NUMBER_WORDS.get(n, str(n))
    names = [t.title for t in topics]
    joined = names[0] if n == 1 else ", ".join(names[:-1]) + f", and {names[-1]}"
    text = sub_once(r"^# .+$", f"# LLM Wiki — {title}", text, "README title", flags=re.M)
    text = sub_once(r"covering \w+ interconnected domains: .+?\. Built",
                    f"covering {word} interconnected domains: {joined}. Built", text, "README intro")
    width = max(len(t.folder) for t in topics) + 2
    layout = "".join(f"  {(t.folder + '/').ljust(width)} # Topic {i}\n" for i, t in enumerate(topics, 1))
    text = sub_once(r"(?:^  .+/\s+# Topic \d+.*\n)+", layout, text, "README structure topics", flags=re.M)
    text = sub_once(r"The \w+ top-level topics are fixed", f"The {word} top-level topics are fixed",
                    text, "README key rule")
    return text


def rewrite_workflow(text: str, sync_repo: str | None) -> str:
    # Drop any existing downstream dispatch step (it is always the last step)...
    text = re.sub(r"\n      - name: Dispatch sync.*\Z", "\n", text, flags=re.S).rstrip("\n") + "\n"
    # ...and add one for the new repo if requested.
    if sync_repo:
        text += DISPATCH_STEP.format(repo=sync_repo)
    return text


def rewrite_onboarding(text: str, org: str, repo: str) -> str:
    m = re.search(r"git clone git@github\.com:([\w.-]+)/([\w.-]+?)\.git", text)
    if not m:
        sys.exit("Template drift: could not find the git clone line in ONBOARDING.md.")
    old_full, old_name = f"{m.group(1)}/{m.group(2)}", m.group(2)
    text = text.replace(old_full, f"{org}/{repo}")
    return text.replace(f"`{old_name}`", f"`{repo}`").replace(f"cd {old_name}", f"cd {repo}")


def frontmatter(title: str, type_: str, extra: str = "") -> str:
    return (f'---\ntitle: "{title}"\ntype: {type_}\ntags: []\nsources: []\n'
            f"{extra}last_updated: {TODAY}\n---\n")


def topic_page(t: Topic, topics: list[Topic]) -> str:
    others = [o for o in topics if o is not t]
    related = "\n".join(f"- [[{o.link}]] — {o.title}" for o in others) or "- (none yet)"
    return (frontmatter(t.title, "topic") +
            f"\n## Overview\n\n_Top-level page for **{t.title}**. "
            f"Written on the first ingest that touches this topic._\n\n"
            f"## Subtopics\n\n_Subtopic pages are linked here as they are created._\n\n"
            f"## Related\n\n{related}\n\n## Sources\n\n_None yet._\n")


def index_page(topics: list[Topic]) -> str:
    sections = "\n".join(f"## {t.title}\n- [[{t.link}]] — Top-level topic page\n" for t in topics)
    return ("# Wiki Index\n\n\n" + sections +
            "\n---\n\n## Sources (Literature Notes)\n\n_None yet._\n\n---\n\n## Meta\n"
            "- [[log]] — Append-only operation log (what changed, when, why)\n"
            "- [[source-registry]] — Tracks all fetched external URLs (status, dates, focus)\n")


def log_page(topics: list[Topic]) -> str:
    created = "\n".join(f"- [[{t.link}]]" for t in topics)
    return ('---\ntitle: "Operation Log"\ntype: log\n'
            f"last_updated: {TODAY}\n---\n\n# Operation Log\n\n"
            "Append-only record of all ingest and update operations.\n\n---\n\n"
            f"## {TODAY} — Wiki scaffolded\n\n"
            f"Created from the wiki-llm template with {len(topics)} top topics.\n\n"
            f"**Pages created ({len(topics)}):**\n{created}\n\n**Index updated:** Yes\n")


def registry_page() -> str:
    return ('---\ntitle: "Source Registry"\ntype: registry\n'
            f"last_updated: {TODAY}\n---\n\n# Source Registry\n\n"
            "Tracks all external URLs that have been fetched and summarised into wiki pages. "
            "Use this to avoid duplicate work, flag URLs for revisit, and detect when sources "
            "may have been updated.\n\n## Status Key\n\n"
            "- **done** — fetched and summarised\n"
            "- **revisit** — needs another pass (new focus, or source updated)\n"
            "- **failed** — fetch failed (paywall, 403, dead link)\n"
            "- **restricted** — not fetched (login/paywall, per a `.links.toml`)\n\n"
            "## Fetch Method Key\n\n"
            "- **WebFetch** — the AI assistant's built-in web fetch tool\n"
            "- **curl+meta** — curl returns 200; content extracted from HTML meta tags / page body\n"
            "- **CrossRef** — DOI metadata and abstract via api.crossref.org (no auth needed)\n"
            "- **known** — summarised from prior knowledge; URL not successfully fetched\n"
            "- **n/a** — not attempted (lightweight reference, one-liner sufficient)\n\n"
            "## Registry\n\n"
            "| URL | Status | Method | Last Fetched | Source Page | Pages Updated | Focus / Notes |\n"
            "|-----|--------|--------|-------------|-------------|---------------|---------------|\n")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", type=Path, help="New repo folder (must not exist or be empty)")
    ap.add_argument("--title", required=True, help='Wiki title, e.g. "Water & Land Stewardship"')
    ap.add_argument("--topic", action="append", required=True, metavar="FOLDER[=TITLE]",
                    help="A fixed top topic (repeat for each, in order)")
    ap.add_argument("--org", default="PlateauPerspectives", help="GitHub org/user (default: %(default)s)")
    ap.add_argument("--repo", help="GitHub repo name (default: target folder name)")
    ap.add_argument("--sync-repo", metavar="OWNER/REPO",
                    help="Downstream repo to notify after navtree rebuilds (omit to drop that CI step)")
    ap.add_argument("--no-git", action="store_true", help="Don't run git init")
    args = ap.parse_args()

    topics = [Topic(s) for s in args.topic]
    if len(topics) < 2:
        sys.exit("Give at least two --topic values (a one-topic wiki doesn't need the topic structure).")
    if len({t.slug for t in topics}) != len(topics):
        sys.exit("Two topics produce the same page slug; rename one.")
    target: Path = args.target.resolve()
    if target.exists() and any(target.iterdir()):
        sys.exit(f"{target} already exists and is not empty.")
    if SRC == target or SRC in target.parents:
        sys.exit("Target must be outside this repo (e.g. a sibling folder like ../wiki-water).")
    repo = args.repo or target.name

    # 1. Copy tooling and conventions.
    for rel in COPY_FILES:
        dst = target / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SRC / rel, dst)
    for rel in COPY_DIRS:
        if (SRC / rel).exists():
            shutil.copytree(SRC / rel, target / rel)

    # 2. Rewrite topic-specific files.
    (target / "CLAUDE.md").write_text(rewrite_claude_md((SRC / "CLAUDE.md").read_text(), topics))
    (target / "README.md").write_text(rewrite_readme((SRC / "README.md").read_text(), args.title, topics))
    (target / "ONBOARDING.md").write_text(
        rewrite_onboarding((SRC / "ONBOARDING.md").read_text(), args.org, repo))
    wf = target / ".github/workflows/navtree.yml"
    wf.parent.mkdir(parents=True, exist_ok=True)
    wf.write_text(rewrite_workflow((SRC / ".github/workflows/navtree.yml").read_text(), args.sync_repo))

    # 3. Seed the wiki.
    wiki = target / "wiki"
    for t in topics:
        (wiki / t.folder).mkdir(parents=True, exist_ok=True)
        (wiki / t.folder / f"{t.slug}.md").write_text(topic_page(t, topics))
    (wiki / "Sources").mkdir(exist_ok=True)
    (wiki / "Sources/.gitkeep").write_text("")
    (wiki / "index.md").write_text(index_page(topics))
    (wiki / "log.md").write_text(log_page(topics))
    (wiki / "source-registry.md").write_text(registry_page())
    (target / "raw").mkdir(exist_ok=True)
    (target / "raw/.gitkeep").write_text("")

    # 4. Verify with a navtree build.
    result = subprocess.run([sys.executable, "build_navtree.py"], cwd=target / ".navtree",
                            capture_output=True, text=True)
    print(result.stdout.rstrip())
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit("navtree build failed — see output above.")
    shutil.rmtree(target / ".navtree/__pycache__", ignore_errors=True)

    if not args.no_git:
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=target, check=True)

    print(f"\nCreated {target}")
    print("Next steps (see docs/creating-a-sibling-wiki.md):")
    print(f"  1. Review CLAUDE.md and README.md in {target.name}/")
    print(f"  2. Create the empty GitHub repo {args.org}/{repo}, then:")
    print(f"       cd {target} && git add -A && git commit -m 'Scaffold wiki' \\")
    print(f"         && git remote add origin git@github.com:{args.org}/{repo}.git && git push -u origin main")
    if args.sync_repo:
        print("  3. Add the NAVTREE_SYNC_TOKEN secret in the new repo's GitHub settings")


if __name__ == "__main__":
    main()
