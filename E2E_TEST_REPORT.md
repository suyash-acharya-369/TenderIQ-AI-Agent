# TenderIQ AI — E2E Test Report

---

## 1. Test Suite Overview
Automated tests execute against the single FastAPI backend application using `pytest` and Starlette `TestClient`.

---

## 2. Test Execution Log

```powershell
python -m pytest tests/ -v
```

### Execution Results:
```
tests/test_admin.py::test_admin_dashboards PASSED                        [ 10%]
tests/test_analytics.py::test_analytics_exports PASSED                    [ 20%]
tests/test_auth.py::test_password_hashing PASSED                         [ 30%]
tests/test_auth.py::test_jwt_token PASSED                                [ 40%]
tests/test_auth.py::test_login_api PASSED                                [ 50%]
tests/test_auth.py::test_protected_route_without_token PASSED            [ 60%]
tests/test_auth.py::test_protected_route_with_token PASSED               [ 70%]
tests/test_organizations.py::test_organizations_crud PASSED              [ 80%]
tests/test_tenders.py::test_tender_match_scores PASSED                   [ 90%]
tests/test_users.py::test_users_crud PASSED                              [100%]

======================= 10 passed in 2.54s =======================
```

---

## 3. Covered Test Scenarios

1. **User Authentication & Hashing**: Password hashing (Argon2), password verification, invalid password rejection.
2. **JWT Token Lifecycle**: Bearer access token encoding/decoding, expiration type validation, role claim verification.
3. **Auth API Integration**: `POST /api/v1/auth/login` authentication, token issuance, user payload schema validation.
4. **Security & Route Protection**: Unauthenticated requests to `/dashboard/kpis` return `401 Unauthorized`. Authenticated requests with Bearer headers return `200 OK`.
5. **User Management CRUD**: Administrator listing, creating user, updating user role to Administrator, deleting user account.
6. **Organization Management CRUD**: Listing procurement boards, creating organization profile, fetching org details, linking tenders.
7. **System Administration Dashboards**: Crawl history listing, queue status monitoring, AI cost tracking (`AILog`), audit event log query.
8. **Analytics & Export Suite**:
   - `GET /api/v1/analytics/export/csv` — Validated `text/csv` attachment header.
   - `GET /api/v1/analytics/export/excel` — Validated `openpyxl` XLSX workbook generation.
   - `GET /api/v1/analytics/export/pdf` — Validated `reportlab` PDF document generation (`application/pdf`).
9. **Matching & Scoring Engine**: Multi-keyword group scoring, negative keyword penalty check, mandatory keyword check, cosine & Jaccard semantic scoring.
