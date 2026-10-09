# Recovery record

The prior temporary cloud execution filesystem was replaced between tasks. The unpushed v0.1 source commit `801383963cd8b51faaa21f159eb97770d1dbfe88` is not available in this checkout. This is a new local recovery repository, not a claim to reconstruct its original Git history.

The saved v0.1 sample archive was recovered from the user's Library. Its editable draw.io graphs retained native geometry, text, colors, connection endpoints, route waypoints, source notes and embedded image assets. `research/recover_v01.py` reconstructs those scene specifications. The prior semantic-redraw samples are preserved separately under `data/diagrams/legacy/`.

The exporter code has been reconstructed and expanded for source-vector fidelity, and tested afresh. A source archive accompanies the v0.2 deliverable so further recovery does not depend on a temporary filesystem. No remote push or publication has been performed.

## Authorized private GitHub delivery

For GitHub delivery, the recovered v0.2 snapshot is applied as a new development-branch commit on the actual upstream main commit `904512fbe6c170b48860c9340bc84ffd0fbeb893`. The original upstream `text` file was preserved, and main was not modified during that initial delivery. Unpacked deliverables are committed under `output/`; ZIP files, Git bundles and vendor/runtime binaries are not uploaded. Repository visibility was verified as private before upload.

## User-approved integration

The user subsequently approved reorganizing results per paper and merging the reviewed development branch into main. This change uses ordinary Git fast-forward/merge rules, preserves upstream history and the original `text` file, and keeps each paper's outputs under `output/aspire/` or `output/roboreact/`. No force push or branch deletion is required.
