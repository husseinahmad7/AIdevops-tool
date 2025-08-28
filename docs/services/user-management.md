# User Management Service

- URL (direct): http://localhost:8081
- Gateway: http://localhost/api/v1/auth, http://localhost/api/v1/users
- Health: GET /health

## Key Endpoints (via Gateway)
- POST /api/v1/auth/register
- POST /api/v1/auth/login (Content-Type: application/x-www-form-urlencoded)
- GET /api/v1/users/validate (Authorization: Bearer <token>)

## Seeding
- On startup, if SEED_ADMIN=true, creates default admin user.
- Env: DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD

## Example
- Login: curl -sS -X POST http://localhost/api/v1/auth/login -H 'Content-Type: application/x-www-form-urlencoded' -d 'username=demo&password=demo123'

## Troubleshooting
- 401/403: ensure token header is set; check Gateway logs
- DB errors: confirm Postgres is up and DATABASE_URL is correct
