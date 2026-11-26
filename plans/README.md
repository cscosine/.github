# Plans

The plans of the organisation and their progress: each plan has a status line, its steps a **Status** column
(`todo` / `doing` / `done` / `dropped`). The PR that completes a step updates it here. A finished plan moves to
`done/`.

| Plan | Status | Open steps |
|---|---|---|
| [PLAN-cscosine-org.md](PLAN-cscosine-org.md): templates, rules, skills, GitHub practices | approved, in progress | S6–S7 (S4, S5 done 2026-11-22; next: S6, after approving the csorchestrator plan; S7 after R4; csopencvcuda low priority) |
| [PLAN-licensing.md](PLAN-licensing.md): the open points of the licensing policy ([LICENSING.md](../LICENSING.md)) | open | L1, L3, L4, L6–L8 |
| [PLAN-csopencvcuda.md](PLAN-csopencvcuda.md): csopencvcuda back into the chain, then build time, CUDA install, Jetson | low priority (unused for now) | C0 (rc1 built, to check), C1–C6 |
| [PLAN-csorchestrator-architecture.md](PLAN-csorchestrator-architecture.md): csorchestrator as a mature framework | to approve | R0–R9 |
| [PLAN-libraries.md](PLAN-libraries.md): the first-party libraries: review, documentation, agent instructions | in progress: LB2 (csLie) | LB1–LB7 (LB2: L0–L7, L1 WIP on `feature/cslie-accuracy`) |
| [PLAN-python-bindings.md](PLAN-python-bindings.md): Python bindings of the C++ libraries (nanobind) | not started (nanobind packaged in third_party_base_libs) | P1–P5 |
| [PLAN-vscode.md](PLAN-vscode.md): VS Code as an IDE on the build folders of the workspace | rolled out (template v1.2.3 on every repository, 2026-11-24) | V3 (Windows), V6, V9 (with csorchestrator R5); V4, V8, V10 parked |

This table is written by hand for now; a script may generate it later, once the plans' status lines share one structure
([TODO-org.md](TODO-org.md)).

Finished: [done/](done/) (the stable-dev round and its review, 2026-11).

Small organisation-level items: [TODO-org.md](TODO-org.md).
