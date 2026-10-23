# Gym Back Office

Web app that gyms use to manage members and check-ins. Many gyms share one
install; each gym only ever sees its own data.

Built with Python, Django and HTMX.

## What works so far

- **Gym signup**: a new gym creates its account and becomes the owner.
- **Staff logins**: owners add front desk logins. Front desk staff can't manage staff.
- **Members**: add, edit, search (name, email, phone or check-in code), filter by
  status, photo, and a unique check-in code for a QR card or keyfob.
- **Three looks**: each gym owner picks Athletic bold (default), Dark dashboard or
  Soft and friendly in Settings. Styles live in `static/css/app.css`.

Coming next: the check-in kiosk screen, then attendance reports.

## Run it locally

Needs Python 3.12 or newer.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000/signup/ and create a gym.

To use the Django admin (all gyms), run `python manage.py createsuperuser`
and go to http://127.0.0.1:8000/admin/.

## Tests

```bash
python manage.py test
```

## Configuration

Local development uses SQLite with no setup. In production set:

| Variable | Example |
|---|---|
| `SECRET_KEY` | a long random string |
| `DEBUG` | `0` |
| `ALLOWED_HOSTS` | `app.example.com` |
| `DATABASE_URL` | `postgres://user:pass@host:5432/gym` |

## How gyms are kept apart

Every staff login and member belongs to a `Gym`. Views use
`accounts.mixins.GymStaffMixin`, which only queries rows for the logged-in
user's gym. New views that show gym data should use it too.
