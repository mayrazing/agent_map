# Project Map — Mandatory Rules

Before locating any file, test, config, or business logic — and before modifying anything — you MUST query the project map first. Jumping directly to source, test, config, or business files without going through the map is prohibited.

## When you may skip the map

- The file is in the **top level of the current working directory** and the user has named it explicitly. You may open or edit it directly.
  - Examples: `AGENTS.md`, `map.py`
  - This exception applies only to top-level files; it does not apply to files in any subdirectory.
- The user has provided a path that **contains a path separator (`/`)**. Open it directly.
  - Examples: `src/components/Foo.jsx`, `backend/service/UserService.java`
- The current conversation context already contains an `ide_opened_file` tag pointing to the file. Path is known; open directly.
- The file has already been read in this session (path is in context). Proceed directly without re-locating.
- The filename the user described is **unique in the project** (e.g. a component name or class name). You may skip hop 1 and search the matching format bucket's `code-index.json` directly.

## When you must use the map

- Navigating into any subdirectory.
- Searching source, test, config, or business file directories.
- The user describes a symptom or feature but does not name a top-level file.
- You are unsure where the target file lives.

At session start, silently refresh the project map:
`rtk python3 map.py >/dev/null 2>&1 && echo "map.py done" || echo "map.py failed"`

Requirements:
- Output only `map.py done` or `map.py failed`
- Do not put map content or script output into the conversation context
- A refresh failure does not block the session; continue using the map flow

## Mandatory query order

### Hop 1 — small map only

The first lookup command must search only:
`.project-index/project-map.json`

Format:
`rtk rg "keyword1|keyword2|keyword3|...|keywordN" .project-index/project-map.json`

Hop 1 must NOT search:
- Any source directory
- Any test directory
- Any config file
- Any business file
- `.project-index/<format>/code-index.json`
- Multiple targets in a single command

### Hop 2 — bucket index only

Only after a small-map hit may you search the detailed index.
The `buckets` field in `.project-index/project-map.json` points to each format bucket. Hop 2 must select the `code-index.json` in the bucket that matches the file format of the hit.

Format:
`rtk rg "candidate-path|ClassName|functionName|keyword" .project-index/<format>/code-index.json`

Common bucket examples:
- `.jsx` files: `.project-index/jsx/code-index.json`
- `.js` files: `.project-index/js/code-index.json`
- `.java` files: `.project-index/java/code-index.json`
- `.xml` files: `.project-index/xml/code-index.json`
- `.yaml/.yml` files: `.project-index/yaml/code-index.json`
- `.properties` files: `.project-index/properties/code-index.json`
- `.sql` files: `.project-index/sql/code-index.json`
- `.css` files: `.project-index/css/code-index.json`

Cross-format issues may query multiple buckets in hop 2, but each command must target exactly one bucket's `code-index.json`.

Examples:
`rtk rg "Settings|updateSettings|save" .project-index/jsx/code-index.json`
`rtk rg "Settings|updateSettings" .project-index/java/code-index.json`
`rtk rg "UserSettingsMapper|update" .project-index/xml/code-index.json`

### Hop 3 — candidate files only

Based on small-map and bucket-index hits, pick the most relevant candidates (max 10) and read only those files.
Format:
`rtk sed -n '1,220p' candidate-file`

## Exceptions — direct source search allowed

Direct source, test, config, or business file search is allowed only when:
- Small map returns no hits
- Still no hits after re-running `map.py`
- The map has already narrowed the scope to a candidate file or small candidate directory
- The user explicitly requests an A/B token comparison between the map flow and direct source search
- The search target is a **value/content** rather than a **name**: the code index only records named symbols (function names, component names, class names, variable names) — not literal values. When searching for a CSS class, string literal, numeric constant, comment text, or any other content, the map will produce no hits; go directly to source.

## Map failure recovery

If map-based location fails:
1. Re-generate the map first:
   `rtk python3 map.py >/tmp/pick_word_map.log 2>&1 && echo "map.py done" || echo "map.py failed"`
2. Repeat the mandatory query order once
3. If still not found, fall back to `rg`, `find`, or direct file lookup

## Challenging the token savings

Normal tasks use only the map flow; do not run a "without map" control search just to prove the savings.

When the user challenges whether the map actually saves tokens and requests proof, run one A/B comparison on the same real task:
1. **Group A**: execute the map flow, record the `Original token count` from each tool output
2. **Group B**: skip the map, run an equivalent keyword search directly in the relevant source directory, record the `Original token count`
3. Formula: `savings rate = (Group B tokens − Group A tokens) / Group B tokens`

When reporting, you must note: the Group B control search itself wastes tokens; it is run only to respond to the challenge. Do not run Group B during normal operation.

Reporting language must distinguish:
- `Direct source search baseline`: the actual number obtained from Group B
- `Map-based actual`: the actual number obtained from Group A
- Never describe the baseline as a fixed or global savings figure; refer to it only as "this comparison"

## Absolute prohibitions

- `cat .project-index/project-map.json` directly
- `cat .project-index/*/code-index.json` directly
- Hop 1 searching source, test, config, or business files directly
- Hop 1 mixing multiple search targets in one command
- Hop 2 mixing the detailed index and source directories
- Hop 2 using `.project-index/*/code-index.json` glob
- Hop 2 mixing multiple format buckets in one command
