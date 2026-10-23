# Gym Back Office

Web app that gyms use to manage members and check-ins. Many gyms share one
install; each gym only ever sees its own data.

Built with Python, Django and HTMX (served from `static/js`).

## What works so far

- **Gym signup**: a new gym creates its account and becomes the owner.
- **Staff logins**: owners add front desk logins. Front desk staff can't manage staff.
- **Members**: add, edit, search (name, email, phone or check-in code), filter by
  status, photo, and a unique check-in code for a QR card or keyfob.
- **Three looks**: each gym owner picks Athletic bold (default), Dark dashboard or
  Soft and friendly in Settings. Styles live in `static/css/app.css`.

- **Check-in kiosk** at `/checkins/kiosk/`: members scan in when they arrive and
  again when they leave. Green, blue or red screen with the member's photo. Frozen and
  cancelled members are refused. A visit with no scan out closes after 3 hours.
- **Check-ins page**: who's in the gym now, today's visits, refused entries, and
  front desk check in or out by hand.
- **Member stats**: days this month, week streak, time this week, average visit.

Coming next: the member portal, payment reminder emails, then attendance reports.

## Kiosk setup

Log in as a staff user on the door tablet or PC and open **Kiosk**. A USB barcode
scanner works out of the box: it types the code and presses Enter.

Run `python manage.py close_stale_visits` every 15 minutes (cron or your host's
scheduler) so forgotten scan-outs close on time. Pages also close them when loaded.

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
