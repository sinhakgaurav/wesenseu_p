# Documentation maintenance policy

All technical and product documentation in this repository must stay **aligned with the code**. Out-of-date docs are treated as defects.

## After every meaningful implementation

When you merge a feature, fix, API change, model change, or integration change, update documentation in the same PR (or immediately follow-up) — **do not leave docs for “later”.**

### Minimum checklist (pick what applies)

| Change type | Update |
|-------------|--------|
| New or changed REST route / schema | [ARCHITECTURE_SPEC_CHECKLIST.md](./ARCHITECTURE_SPEC_CHECKLIST.md) relevant rows; [SPEC_VS_REPO.md](./SPEC_VS_REPO.md) if it closes a **Gap** or moves **Partial** → **Implemented**; run/revise **§0** verification rows in the checklist if you touched core routers (e.g. `departments`, `verification`). Update **`Monitour.postman_collection.json`** and [API_TOOLS.md](./API_TOOLS.md) when routes or auth/dev defaults change. |
| WesenseU contract (payloads, URLs, callbacks) | [FUNCTIONAL_DECISIONS_VERIFICATION.md](./FUNCTIONAL_DECISIONS_VERIFICATION.md) §A–E; [SPEC_VS_REPO.md](./SPEC_VS_REPO.md) §13 integration. Update sibling **`WesenseU/WesenseU.postman_collection.json`** and [API_TOOLS.md](./API_TOOLS.md) when the microservice API changes. |
| DB models / migrations | Checklist DB sections; [SPEC_VS_REPO.md](./SPEC_VS_REPO.md) §5 if table names or concepts changed. |
| README behavior (ports, env, quick start) | [README.md](../README.md). |
| User-visible product scope | [README.md](../README.md) overview if positioning changes. |

### Verification log

After releases or large merges, refresh **§0 Verification log** in [ARCHITECTURE_SPEC_CHECKLIST.md](./ARCHITECTURE_SPEC_CHECKLIST.md): set **Last verified** date and re-run the listed checks (or note what was skipped).

### Status vocabulary (keep consistent)

- **ARCHITECTURE_SPEC_CHECKLIST.md:** Implemented | Partial | Planned  
- **FUNCTIONAL_DECISIONS_VERIFICATION.md:** Verified | Partial | Gap  
- **SPEC_VS_REPO.md:** Implemented | Partial | Not implemented | Different  

When implementation fixes a documented **Gap** or **Not implemented** item, **change the status and date** in the same change set.

## Doc map

| Document | Role |
|----------|------|
| [README.md](../README.md) | Onboarding, stack, links to all spec docs. |
| [ARCHITECTURE_SPEC_CHECKLIST.md](./ARCHITECTURE_SPEC_CHECKLIST.md) | Stakeholder spec checklist + §0 audit log. |
| [FUNCTIONAL_DECISIONS_VERIFICATION.md](./FUNCTIONAL_DECISIONS_VERIFICATION.md) | Agreed features + WesenseU wiring + action list. |
| [SPEC_VS_REPO.md](./SPEC_VS_REPO.md) | Full PDF-style architecture vs repository (honest deltas). |
| [API_TOOLS.md](./API_TOOLS.md) | Postman collections, OpenAPI URLs, headers (Monitour + WesenseU). |
| [DOCUMENTATION_POLICY.md](./DOCUMENTATION_POLICY.md) | This file — maintenance rules. |

## AI / automation

When using coding agents: include in the task prompt *“Update docs per DOCUMENTATION_POLICY.md”* so checklist and spec-vs-repo tables stay current.
