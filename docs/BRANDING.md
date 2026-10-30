# Public-brand decision — RecastRoom Studio

Date: 2026-10-25

## Decision

The contest-facing public name is **RecastRoom Studio**.

The intended public repository slug is:

```text
recastroom-studio
```

## Why now

The competitor benchmark found an independent, earlier public repository named
`SydFloyd/openjutsu` that targets the same challenge. Continuing to publish our
entry as “OpenJutsu” would create avoidable judge and audience confusion.

## Why this name

1. The **Recast Room** is already the production flagship and core contest lane.
2. The name describes the actual function: recasting a performance in a controlled room.
3. It is short enough for a repository, UI masthead, release, and social post.
4. It does not imply a full Higgsfield clone or broad VFX platform.

## Collision check

GitHub repository search on 2026-10-25 returned:

```text
"RecastRoom":          0 repositories
"RecastRoom Studio":   0 repositories
"Performance Recast Studio": 0 repositories
"H3 Recast Studio":    0 repositories
```

The broader phrase “Recast Studio” already has multiple unrelated repositories,
so the public brand must use the complete **RecastRoom Studio** name rather than
the generic short form.

## Compatibility boundary

To preserve validated evidence, existing receipts, and workflow compatibility,
this release keeps internal technical identifiers unchanged:

```text
Python module:       openjutsu
workflow filename:   workflows/recastroom_h3_workflow.json
SDK bridge ID:       openjutsu_assets
legacy env prefix:   OPENJUTSU_*
```

The primary user-facing environment prefix and command are now:

```text
RECASTROOM_*
recastroom
```

Legacy `OPENJUTSU_*` settings remain accepted for this release, but new docs and
the public demo must use `RECASTROOM_*`. Internal identifiers are not public
brand claims and should not be used in the repository title, README headline,
demo title, release title, or submission name.

## Publication rule

Use **RecastRoom Studio** consistently in every owner-facing/public artifact:

```text
GitHub repository name
README headline
app title and masthead
demo video title card
release name
social post
Typeform project name
```

Do not publish under the old public name.
