# Durable paper-processing queue

The catalog is a bibliography, not a completion ledger. `paper_figure.queue`
records independent checkpoints in `data/queue/<catalog-id>.json`. It does not
modify the catalog, download papers, recreate figures, run applications, or
publish files. Workers perform those actions and submit the observed evidence.

## Initialize and inspect

Run from the repository root (Python 3.10+, POSIX/Linux/macOS):

```sh
python research/queue.py init
python research/queue.py status
python research/queue.py status aspire-agentic-skills-discovery-for-robotics
python research/queue.py status --verify-files
```

Use `--repository /absolute/repository` **before** the subcommand for another
checkout. `init --catalog data/catalog.json` selects an alternate relative
catalog. Initialization validates all IDs before writing, and can safely resume
an interrupted import. Existing records are preserved byte-for-byte, including
progress and their original catalog snapshots; catalog edits do not silently
rewrite previous evidence.

Importing the original 137-paper catalog yields:

- 134 `not_reviewed`
- 2 `recreated`, with recreation recorded as an imported `reported` claim
- 1 `blocked`, with the catalog's explicit restriction notes as imported evidence
- 0 `completed`

Imported recreation claims do not pass identity, access, selection, QA or
publication. Imported restrictions are attributed to the catalog, not to a new
independent inspection. The original row, catalog SHA256 and pinned source
commit are retained. No completed state can be imported from a catalog.

The six stages are `source_identity`, `source_access`, `figure_selection`,
`recreation`, `qa` and `published`. Stage statuses are `pending`, `reported`,
`in_progress`, `passed`, `failed` and `blocked`. `reported` deliberately means an
unverified claim. Overall nonterminal statuses are `not_reviewed`, `in_progress`
and `recreated`. Terminal outcomes are `completed`, `no_suitable_figure`,
`inaccessible`, `source_mismatch` and `blocked`; a new evidenced update can reopen
an outcome. Terminal here means an explicit disposition, not successful delivery.

`status` shows recorded state. `status --verify-files` also checks the existence
and current SHA256 of all passed-stage files, their cross-references, and stored
QA results. It **does not rerun application QA**, inspect figures visually or
infer that a human statement is correct. Any corrupt record or stale file makes
the command fail instead of silently omitting it from totals. Counts are a
best-effort snapshot across separate paper files, not a global transaction.

## Update a checkpoint

Save a JSON patch, then submit it with the revision you read:

```sh
python research/queue.py update new-paper evidence.json --expected-revision 1 --actor worker-a
```

Only `status`, `stages` and `terminal_evidence` are patchable. A named stage is
replaced completely, rather than merging old evidence into new assertions.
Every non-pending stage and every terminal outcome requires an evidence object:

```json
{
  "status": "in_progress",
  "stages": {
    "source_access": {
      "status": "in_progress",
      "evidence": {
        "summary": "Official PDF request returned HTTP 503; another attempt is needed.",
        "references": ["https://example.org/paper.pdf"],
        "attempted_at": "2026-10-09T20:00:00Z",
        "http_status": 503
      }
    }
  }
}
```

Additional evidence fields are retained in the audit history. References are
nonempty strings identifying URLs or repository evidence; generic references
are not automatically fetched. A temporary network failure should normally stay
`in_progress`, rather than claiming permanent inaccessibility. Record the actual
attempt and the reason for a terminal access disposition.

To reset a stage explicitly, use `{"status":"pending","evidence":null}`.
Reset affected downstream stages too: selection requires passed identity and
access; recreation requires passed selection; QA requires passed recreation;
publication requires passed QA. Returning to a nonterminal overall status clears
old terminal evidence while preserving its history. `recreated` requires at
least reported recreation; `not_reviewed` requires all stages pending.

All terminal updates explicitly include, for example:

```json
{
  "status": "blocked",
  "terminal_evidence": {
    "summary": "The recorded source license restricts the requested modified deliverable; rights review is needed.",
    "references": ["https://example.org/paper-license"]
  }
}
```

Additional terminal gates:

- `inaccessible`: access must be `failed` or `blocked`, with its own evidence
- `source_mismatch`: identity must be `failed`, with the observed mismatch recorded
- `no_suitable_figure`: verified, accessible source; failed selection; selection
  evidence includes a nonempty `reviewed_pages` list of valid 1-based PDF pages
- `completed`: all six stages must pass the evidence gates below

Do not use an exception outcome merely because a paper has not been reviewed.

## Passed-stage evidence and completion gates

Every passed-stage evidence object includes `summary` and `references` plus:

1. `source_identity`: `matches_catalog: true`, `observed_title`, `source_url`
   (HTTP/S), and `source_sha256` equal to the verified source PDF hash
2. `source_access`: `source: {"path":"output/new-paper/paper.pdf","sha256":"…"}`
   and a positive integer `page_count`. The file must exist, be nonempty, match
   the hash and start with PDF bytes. Page counts and identity are observations
   supplied by the source-review worker; this module does not parse PDF content
3. `figure_selection`: `figure` (such as `Figure 2`) and `pdf_page` (1-based,
   within the reported page count); describe the selection rationale in `summary`
4. `recreation`: `artifacts` containing exactly `scene`, `pptx`, `drawio`,
   `preview`, `original`. Each value is a `{path, sha256}` file reference. Expected
   extensions are `.json`, `.pptx`, `.drawio`, `.png`, `.png`; paths are distinct
5. `qa`: `report` containing a `{path, sha256}` reference to a JSON QA report
6. `published`: `output_directory`, a paper-specific directory under `output/`.
   The verified source PDF, PPTX, draw.io, preview and original must reside inside
   it; the editable scene may remain under `data/`

Files must be repository-relative, nonempty, inside the repository after symlink
resolution, and match their recorded hashes. Absolute paths and traversal are
rejected. Hashes attest to bytes, not file-format validity or visual quality;
export validation and actual application/source checks remain mandatory worker
responsibilities documented in the QA report.

The QA report must bind the **current** source, selected figure/page, and all five
artifact hashes. It must contain nonempty `reviewer` and `notes`, plus:

```json
{
  "source_sha256": "<64 lowercase hex characters>",
  "figure": "Figure 2",
  "pdf_page": 3,
  "artifact_sha256": {
    "scene": "<scene hash>",
    "pptx": "<PPTX hash>",
    "drawio": "<draw.io hash>",
    "preview": "<preview hash>",
    "original": "<source crop hash>"
  },
  "checks": {
    "source_comparison": "passed",
    "pptx_open_render": "passed",
    "drawio_open_render": "passed"
  },
  "reviewer": "Identifiable worker or reviewer",
  "notes": "Actual check methods, results, limitations and supporting evidence references"
}
```

This is a schema example, not valid evidence. Populate it only after the checks
are genuinely performed. An old QA report cannot approve changed file bytes,
a different source PDF, or a different selected figure/page. `completed` with a
manual flag, missing artifacts or omitted application checks is rejected.

## Durability and parallelism

The Python API exposes `initialize_queue(repository)`,
`read_checkpoint(repository, paper_id, verify_files=False)`,
`update_checkpoint(repository, paper_id, patch, expected_revision=None, actor='operator')`
and `queue_status(repository, verify_files=False)`.

Updates use a per-paper POSIX advisory lock, write a same-directory temporary
file, fsync it, atomically replace the checkpoint, then fsync the directory. The
OS releases the lock after process exit, including crashes. Different papers do
not share a write lock. Same-paper updates serialize; `expected_revision` rejects
stale work instead of overwriting a newer checkpoint. For coordination among
workers, use revisions; this module does not lease or automatically assign work.

Each successful update increments `revision` and appends timestamp, actor,
complete patch and previous-checkpoint SHA256 to `history`. Failed validation
leaves the old record untouched. This is an inspectable local audit trail, not a
signed/tamper-proof log. External editing bypasses its protections.

Track `data/queue/*.json` in version control. Do not commit
`data/queue/.locks/` or temporary files. A hard crash before atomic replacement
can leave a harmless hidden `.tmp` file; it is never counted as a checkpoint.
After an interrupted write, reread the current revision before retrying.
