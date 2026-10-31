# API Contract Checklist

Use this reference when a PocketOS client must connect to an existing backend.

1. Search the repository, archives, project files, and manifests for the requested OpenAPI artifact.
2. If missing, do not reconstruct it from memory. Import the executable backend and derive observed routes and response envelopes.
3. Compare required prefixes, especially `/api/v1`, with served routes. Report conflicts and obtain the canonical choice before implementation.
4. Prefer a thin alias/router layer for versioning so legacy console routes remain stable and authority logic is not duplicated.
5. Add server-side response models where possible; bare `dict[str, Any]` responses are drift-prone.
6. Exclude admin/demo/test mutators from production client contracts.
7. Keep authenticated mutations protected by server permissions. Ignore client-supplied authority claims.
8. Verify representative GETs, unauthorized POSTs, live stream route registration, and legacy route compatibility.
9. Document unsupported domains as `BACKEND SUPPORT REQUIRED`; never fake completed features with fixtures.
10. Keep the mobile transport domain-typed and explicitly configured with the canonical API base URL.
