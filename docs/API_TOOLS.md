# API tooling (Postman & OpenAPI)

Use these when exercising or documenting the HTTP surface without the SPA.

## Monitour

| Resource | Location / URL |
|----------|------------------|
| Postman collection (v2.1) | Repository root: `Monitour.postman_collection.json` |
| Swagger UI | `http://localhost:8000/api/docs` |
| ReDoc | `http://localhost:8000/api/redoc` |
| OpenAPI JSON (Postman: Import → Link) | `http://localhost:8000/openapi.json` |

After importing the collection, set **`baseUrl`** to `http://localhost:8000`. Login requests set **`accessToken`**. For **Departments**, super admin must set **`propertyId`** (UUID); **List Departments** can populate **`departmentId`** from the first row of the response.

Dev seed passwords are aligned with **`backend/app/db/init_db.py`** (see root `README.md`).

## WesenseU

| Resource | Location / URL |
|----------|------------------|
| Postman collection | `WesenseU/WesenseU.postman_collection.json` (sibling repo) |
| Docs | `http://localhost:8001/docs` |
| OpenAPI JSON | `http://localhost:8001/openapi.json` |

All protected routes expect header **`X-API-Key`** (match `API_KEY` in WesenseU and `WESENSEU_API_KEY` in Monitour). Room verify uses multipart field **`files`**; run a WesenseU **Celery worker** for jobs to complete.

## Docker (Monitour compose)

When you start the stack from **`Monitour/docker-compose.yml`**, Monitour is on **8000**, WesenseU on **8001**, and both Celery workers are included. See the Monitour root **README** → *Docker (full stack)*.
