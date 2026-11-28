# mas-problem
Online súťaž Máš problém?!

## Runtime and dependency updates

Use CPython 3.15 (tested with 3.15.2) and Django 6.1.3. These are the current
stable [Python](https://www.python.org/downloads/source/) and
[Django](https://www.djangoproject.com/download/) releases as of 2026-11-28.
The supported Python series is recorded in `.python-version`.

Create a fresh environment when switching Python versions:

```sh
python3.15 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
```

Direct dependencies live in `requirements.in`; `requirements.txt` pins their
complete dependency graph. Refresh the generated file with
[uv](https://docs.astral.sh/uv/):

```sh
uv pip compile --universal --python-version 3.15 requirements.in -o requirements.txt
```

Development tools are kept out of deployment installs. Install them with
`python -m pip install -r requirements-dev.txt`. After updating runtime pins,
refresh the development lock as well:

```sh
uv pip compile --universal --python-version 3.15 requirements-dev.in -o requirements-dev.txt
```

The unused `nose`/`django-nose` dependencies were removed; tests use Django's
standard test runner.

Secret files under `.secrets` still work. Environment variables can also supply
`DJANGO_SECRET_KEY` and `FAKTURY_API_KEY`. CI uses dummy values and the in-memory
email backend; it never needs deployment secrets.

Run isolated checks with `DJANGO_SETTINGS_MODULE=mas_problem.settings_ci`
(and the dummy secret environment variables shown in `.github/workflows/ci.yaml`
where required). This selects an in-memory SQLite database and in-memory email,
and collects static files under the system temporary directory:

```sh
export DJANGO_SETTINGS_MODULE=mas_problem.settings_ci
export DJANGO_SECRET_KEY=ci-only-not-for-deployment
export FAKTURY_API_KEY=ci-only-not-for-deployment
python manage.py check
python manage.py migrate --noinput
python manage.py test --noinput
python manage.py collectstatic --noinput
```

The CI workflow installs the pinned dependencies and runs these checks on Python
3.15. Local validation covered clean per-project environments, migrations, tests,
and static collection.

Email confirmation now uses allauth's public `EmailAddress.send_confirmation()`
API, and allauth's required account middleware and current settings are enabled.
PDF certificate uploads use maintained `pypdf` in place of `PyPDF2`; the upload
regression test verifies that an individual certificate page is saved and readable.

The deployment image uses `python:3.15-trixie`. Daphne is pinned in the runtime
lock instead of installed separately without a version. Local validation includes
HTTP startup through Daphne. CI also builds the deployment image on Linux;
Docker is not installed on the local validation host.
