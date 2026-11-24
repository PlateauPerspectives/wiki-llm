# Docs

How-to guides for working with this wiki. The rules themselves live in [`../CLAUDE.md`](../CLAUDE.md); these guides explain how to use them day to day.

| I want to… | Read |
|---|---|
| Add a source, update pages, ask the wiki a question | [Updating the wiki](updating-the-wiki.md) |
| Start a new wiki like this one on a different subject | [Creating a sibling wiki](creating-a-sibling-wiki.md) |
| Set up GitHub, Obsidian and an AI assistant for the first time | [`../ONBOARDING.md`](../ONBOARDING.md) |
| Understand the navigation-tree build and CI | [`../.navtree/README.md`](../.navtree/README.md) |

## The 30-second picture

```
raw/  ──(you add a file)──►  AI assistant reads CLAUDE.md + the source
                                     │
                                     ▼
                     wiki/  pages created / updated,
                            index.md, log.md, source-registry.md kept current
                                     │
                         you review, commit, push to main
                                     │
                                     ▼
              GitHub Action rebuilds .navtree/output/ and commits it
                                     │
                                     ▼
                     apps (navtree-app, etc.) read the tree
```

`docs/` is for people. It is not part of the wiki itself and is not included in the navigation tree.
