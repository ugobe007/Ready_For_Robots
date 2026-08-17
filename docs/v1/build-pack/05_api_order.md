# API Implementation Order

## Product sequence (intent)

```text
1  POST /robots/analyze
2  GET  /robots/:id
3  PATCH /robots/:id
4  POST /internal/sources/ingest
5  GET  /internal/jobs/:id
6  GET  /internal/facilities/:id/work
7  POST /robots/:id/discover
8  GET  /discovery/:jobId
9  GET  /opportunities
10 GET  /opportunities/:id
11 GET  /opportunities/:id/questions
12 POST /opportunities/:id/questions/:qid/answer
13 POST /opportunities/:id/action
14 POST /opportunities/:id/feedback
15 POST /opportunities/:id/outcome
16 GET  /opportunities/:id/history
```

## Frozen OpenAPI mapping (implement these)

| Intent | OpenAPI (`/api/v1`) |
| --- | --- |
| analyze | `POST /robot-analyses` |
| get/confirm profile | `GET /robot-analyses/{id}`, `POST …/confirm` |
| discover | `POST /robots/{robotId}/opportunity-searches` |
| discovery job | `GET /opportunity-searches/{searchId}` |
| list / detail | `GET /robots/{id}/opportunities`, `GET /opportunities`, `GET /opportunities/{id}` |
| questions / answers | `GET …/qualification`, `POST …/answers` |
| action | `POST …/transitions` |
| outcome | `POST …/outcomes` |
| history | history section on detail or dedicated path when added to OpenAPI |

**Do not implement dual alias paths.** Amend OpenAPI in the same PR if a new public path is required (`/internal/*` may be admin-only and undocumented in public OpenAPI until E15).

## Sprint 0/1 API work

- Freeze enums in shared Python module + OpenAPI (no new product endpoints required for Sprint 0).
- Sprint 1: tenant-isolation tests on existing team-scoped routes; provenance utility used by Slice 1 analysis path.
