# Updating the wiki

This guide covers everyday work: adding sources, asking questions, tidying up. You don't write wiki pages by hand — you give the AI assistant a source and review what it produces.

> **First time?** Do the setup in [`../ONBOARDING.md`](../ONBOARDING.md) first (GitHub, Obsidian, an AI assistant).

## The golden rules

Changes go straight to `main` with no reviewer, so these habits are what keep the wiki healthy. The AI handles the rest of `CLAUDE.md`.

1. **Pull before you start.** That way the AI sees the latest `index.md` and `source-registry.md`, and won't redo a source someone else has already ingested.
2. **Pull again right before you push.** A bot commits to `main` after every push, so your copy is usually one commit behind.
3. **You are the reviewer.** Read the AI's change summary and the diff before you commit (Step 5 below).
4. **Make sure the bookkeeping got done:** `wiki/index.md`, `wiki/log.md` and `wiki/source-registry.md` updated. This is the step that gets lost when a session is cut short.
5. **Never commit anything from `raw-private/`.**
6. **Ask the AI to do renames, splits and deletes.** It knows to check `.navtree/output/redirects.toml` first.

"Pull" means **Pull origin** in GitHub Desktop, or `git pull --rebase` in a terminal. *Fetch* on its own only checks for changes and doesn't apply them.

Want a second pair of eyes on a big or uncertain change? Use a branch and pull request instead (see "Optional: ask for review" in [`../ONBOARDING.md`](../ONBOARDING.md)).

---

## Before every session (1 minute)

1. **Pull the latest changes** (golden rule 1). GitHub Desktop: *Fetch origin* → *Pull origin*. Terminal: `git pull --rebase`.
2. **Open the project in your AI assistant.**
   - *Claude Code:* open a terminal in the repo folder and run `claude`. It reads `CLAUDE.md` automatically.
   - *Other tools:* make sure the tool has `CLAUDE.md` loaded (see "Setting Up Your AI Assistant" in [`../README.md`](../README.md)).
3. **Optional:** open the repo folder as a vault in Obsidian, so you can watch pages appear and follow links.

---

## Task 1 — Add a new source (ingest)

Use this for a report, article, booklet, notes, or a document full of links.

### Step 1: Put the file in the right folder

| The source is… | Put it in | Committed to GitHub? |
|---|---|---|
| Public, or yours to share (`.docx`, `.md`, `.pdf`) | `raw/` | Yes |
| Copyrighted, paid, login-only, or confidential | `raw-private/` | **No** (gitignored) |

Don't rename or edit files once they're in `raw/` — they're the permanent record of what was ingested.

**Private source with links behind a login?** Next to the file, add a companion file with the same name plus `.links.toml`, listing which links the AI must not fetch:

```toml
# raw-private/report.links.toml
["https://intranet.example.org/data"]
access = "restricted"
reason = "Requires organizational login"
```

Links not listed are treated as public.

### Step 2: Ask the AI to ingest it

Type:

```
ingest raw/your-file.pdf
```

(or `ingest raw-private/your-file.pdf`)

### Step 3: Discuss before it writes

The AI will first summarise the key takeaways and propose which topic(s) it belongs to and which pages to create or update. **This is your moment to steer.** Useful replies:

- "Yes, go ahead."
- "This belongs under *X*, not *Y*."
- "Don't create a new page for that — add it to the existing *…* page."
- "Skip the links to … — they're not relevant."
- "Give the main report its own Sources page."

### Step 4: Let it work

The AI will:

- create/update pages under the right topic folder in `wiki/`
- write detailed literature notes in `wiki/Sources/` for important external resources
- fetch each external link, summarise it **in its own words**, and keep the URL
- record every fetched URL in `wiki/source-registry.md`
- update `wiki/index.md` and append an entry to `wiki/log.md`
- flag contradictions with what the wiki already says
- end with a change summary

### Step 5: Review

Nobody else checks this before it goes live, so take two minutes. Read the AI's change summary, look at the changed files (GitHub Desktop shows a diff for each one), then go through the checklist (it's also in the pull request template):

- [ ] Pages are under the right topic and read sensibly
- [ ] New pages appear in `wiki/index.md`
- [ ] `wiki/log.md` has a new entry for this ingest
- [ ] Every URL the AI fetched is in `wiki/source-registry.md`
- [ ] No files from `raw-private/` appear in the list of changed files
- [ ] Unsourced claims are marked `[needs verification]` rather than stated as fact
- [ ] Nothing was copied wholesale from a website or private document
- [ ] For private sources: `wiki/log.md` describes the source generically, **without** its filename

In Obsidian, broken links show as faint/unresolved links — a quick way to spot problems.

### Step 6: Commit and push

GitHub Desktop: tick the changed files → write a summary (e.g. *"Ingest FAO pastoral mobility report"*) → *Commit to main* → *Fetch origin* (pull if offered) → *Push origin*.

Terminal:

```bash
git add wiki/ raw/
git commit -m "Ingest FAO pastoral mobility report"
git pull --rebase && git push
```

About a minute later a `[navtree] Rebuild navigation tree` commit appears. That's the automation updating the navigation tree — nothing for you to do.

---

## Task 2 — Ask the wiki a question

```
query: what does the wiki say about water rights for mobile herders?
```

The AI answers from the wiki pages, with links to them, and asks whether to save the answer as a new page. Say yes only if it's something worth keeping — then commit as usual.

---

## Task 3 — Health check (lint)

Every few ingests, run:

```
lint the wiki
```

You get a report of orphan pages, broken links, stale pages, missing pages and misplaced pages. The AI asks before fixing anything.

---

## Task 4 — Revisit a source with a different focus

1. In `wiki/source-registry.md`, change that URL's **Status** to `revisit` and note the new focus in *Focus / Notes*.
2. Ask: `revisit the sources marked revisit in the source registry`.

New findings are added to the existing pages; earlier summaries are kept.

---

## Task 5 — Small manual edits

Fixing a typo or a sentence? Edit the page directly in Obsidian (or any editor) and commit. Still update `last_updated` in the page's frontmatter. Skip `wiki/log.md` for trivial fixes; add an entry for anything substantive.

---

## Things to be careful with

### Topics are fixed
The top topics listed in `CLAUDE.md` (Rule 1) must not be renamed, merged, removed or reordered. Under each topic, subfolders are free-form.

### `wiki/index.md` shapes the navigation tree
The navigation tree that apps show is built from `wiki/index.md` and the `[[wikilinks]]` inside each page:

- Each **top-level (non-indented) bullet** under a `##` heading is a root of the tree. The Sources and Meta sections are excluded automatically.
- A page's children are the pages it links to with `[[wikilinks]]`.
- Links into `Sources/` are not followed. Plain `[text](file.md)` links are not followed either.

So: if a new page doesn't show up in the app, it isn't linked with a `[[wikilink]]` from its topic page (or from a page beneath it).

### Renaming, splitting or deleting pages
Before you restructure a page, check `.navtree/output/redirects.toml`. If the page is listed there, it appears in more than one place in the tree — the AI must then also add an entry to `vault-changelog.toml` in the repo root (format in `CLAUDE.md`, "NavTree vault coordination"). Ask the AI to do the restructuring; it knows the rule. If `redirects.toml` doesn't exist, nothing is multi-position and you can restructure freely.

### Never commit `raw-private/`
It's gitignored, so this only happens if someone forces it. If a private file ever lands in a commit, tell the maintainer — removing it from git history takes extra steps.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Push rejected ("fetch first" / "non-fast-forward") | Pull, then push again. Terminal: `git pull --rebase && git push`. |
| A new page isn't in the navigation app | Link it with `[[Topic/page-name]]` from its topic page or a subtopic page. Then push. |
| The CI job failed | GitHub → repo → *Actions* tab → open the failed run. Usually a malformed `wiki/index.md` or frontmatter. To reproduce locally: `cd .navtree && python3 build_navtree.py`. |
| The AI fetched a URL that was already done | Remind it: "check `wiki/source-registry.md` first" (Rule 10). |
| The AI wants to rename or add a top topic | Say no — topics are fixed (Rule 1). |
