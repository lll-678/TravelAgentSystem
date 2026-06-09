# Stage 31 Admin/User Auth

## Scope

This stage implements the login-state split between normal users and administrators.

The project should keep one account system and one login endpoint. User/admin separation should be role-based, not two independent login systems.

## Delivered

- `POST /api/v1/users/register`, `POST /api/v1/users/login`, and `GET /api/v1/users/me` exist.
- Login returns a demo HMAC bearer token that includes `role`.
- `users.role` supports `user` and `admin`.
- Admin APIs under `/api/v1/admin/*` are protected by `require_admin`.
- Frontend stores `{ token, user, role }`, hides the admin navigation entry for normal users, and attaches bearer tokens to admin API calls.
- `admin01` is seeded as the deterministic admin account.

## Target Contract

| Area | Behavior |
| --- | --- |
| User table | `users.role` has allowed values `user` and `admin`; default is `user` |
| Login API | Reuses `POST /api/v1/users/login`; response includes user profile and `role` |
| Token | Include `user_id`, `role`, and expiry in the signed token payload |
| Current user | `GET /api/v1/users/me` returns `role` |
| Admin guard | `/api/v1/admin/*` requires a valid bearer token whose role is `admin` |
| Frontend state | Store `{ token, user, role }`; hide or block admin page for normal users |
| Seed data | Provide at least one normal demo account and one admin demo account |

## Demo Accounts

Use deterministic seed accounts for offline demonstration:

```text
user01 / demo123456 / role=user
admin01 / admin123456 / role=admin
```

Do not hard-code these passwords in frontend source. They belong in seed data and documentation only.

## Backend Implementation

1. Added `role` to `User` model and seed data.
2. Added schema compatibility for old SQLite dev DBs without `users.role`.
3. Backfilled existing users as `role=user`.
4. Marked `admin01` as `role=admin`.
5. Extended token creation and verification to carry role.
6. Added reusable dependencies:
   - `get_current_user`
   - `require_admin`
7. Applied `require_admin` to `/api/v1/admin/*`.
8. Missing/invalid token returns `401`; non-admin token returns `403`.
9. Added tests for user token, admin token, forbidden admin access, and router dependency registration.

## Frontend Implementation

1. Added a small auth state helper for token, user, and role.
2. LoginPage stores login role; App header displays the current account and role.
3. App navigation hides the admin item unless the stored auth state is admin.
4. Router blocks direct `/admin` visits for non-admin users.
5. AdminDashboardPage attaches bearer token to admin API calls.

## Acceptance Criteria

- Normal user can log in and continue using recommendation, rating, favorites, diaries, and food flows.
- Admin user can log in and access the admin dashboard.
- Normal user cannot call admin stats, map import, content edit, or diary moderation APIs.
- Missing token on admin API returns `401`.
- Valid normal-user token on admin API returns `403`.
- Valid admin token on admin API succeeds.
- Frontend does not show the admin menu for normal users.
- Documentation lists both seed accounts and explains that one login endpoint is role-aware.

## Validation

```bash
PYTHONPATH=backend pytest backend/tests/test_stage16_user_preferences.py backend/tests/test_stage9_food_aigc_admin.py backend/tests/test_stage31_admin_auth.py -q
bash scripts/check_frontend.sh
bash scripts/check_all.sh
```
