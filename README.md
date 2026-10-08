# Fieldnotes

A responsive publishing site for technical notes, learning resources, and a field journal. It uses Django server-rendered pages, Django authentication and permissions, PostgreSQL in production, and private S3-compatible storage for uploads.

## Architecture

- **Django 6.1** serves the public site and account pages. Built-in auth supplies password hashing, sessions, password reset tokens, CSRF protection, and backend permissions.
- **PostgreSQL** is the production database. A persistent SQLite database is used locally so the project runs without extra services.
- **Django admin** is the publishing CMS. Model permissions gate each content operation; the private `/manage/` page provides an overview.
- **Markdown + nh3** render formatted technical writing and sanitize the resulting HTML. Pygments provides code block highlighting.
- **S3-compatible storage** holds production uploads. Local development uses the `media/` directory.
- **WhiteNoise** serves collected static files in production. No frontend build runtime is needed.

The machine used to scaffold this project has Python 3.14.3 and no Node.js. Django 6.1 supports Python 3.14; this project pins Django 6.1.2, which includes the October 2026 security and bug fixes. See the [Django 6.1.2 release notes](https://docs.djangoproject.com/en/6.1/releases/6.1.2/) and [Django authentication documentation](https://docs.djangoproject.com/en/6.1/topics/auth/default/).

## Project structure

```text
config/                  Settings and URL configuration
knowledge/               Models, validation, admin, views, migrations, tests
templates/               Public, account, error, and dashboard pages
static/css/site.css      Responsive visual system
media/                   Local development uploads
requirements.txt         Python dependencies
.env.example             Local and production environment variable reference
Dockerfile               Container deployment option
build.sh                 Dependency installation and static collection
```

## Database schema

- Django `User` and `Profile` hold accounts, bio, and website details. Django staff and model permissions control publishing access.
- `Category` and `Tag` organize content. The first migration seeds the requested subject categories; the admin can add, rename, reorder, or remove them.
- `Note` and `BlogPost` store Markdown content, summaries, authors, tags, optional cover art, draft/published state, and publication time. A future publication time remains hidden until that time.
- `SavedContent` points to exactly one note or post. Database constraints prevent duplicate or ambiguous saves.
- `UploadedAsset` stores attachment metadata and points to exactly one note or post. Files are validated and served through a route that checks whether the parent content is public.
- `ContactMessage` stores validated contact submissions in the private admin inbox.
- `RateLimitBucket` stores hashed client identifiers and request counts for login, signup, password reset, and contact submissions.

## Pages and user flows

Public pages include Home, the categorized Notes library, note detail, Journal listing, article detail, combined search, About, Contact, and branded 404/500 pages. Notes can be filtered by category and tag; journal articles can be searched and filtered by tag.

Readers can register, sign in, sign out, request a one-time password reset, edit their profile, change their password, save notes and posts, and review saved content. Staff can open `/manage/` and use the permission-checked content manager to create, preview, schedule, publish, unpublish, and delete content; manage categories, tags, and files; and review user and contact information.

## Local setup

Use Python 3.14.3 (the project also targets Django-supported Python 3.12 and 3.13 versions).

1. Create and activate an isolated environment:

   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```sh
   python -m pip install -r requirements.txt
   ```

3. Create a local environment file and replace the development secret:

   ```sh
   cp .env.example .env
   ```

   For local use, `DEBUG=true` and SQLite are enabled. Password reset links are printed to the terminal. No database URL is needed.

4. Create the database and the administrator account:

   ```sh
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. Start the website:

   ```sh
   python manage.py runserver
   ```

   Visit `http://127.0.0.1:8000`. The publishing area is at `/manage/`; the content manager is at `/manage/content/`.

6. Run the core workflow tests and Django checks:

   ```sh
   python manage.py test
   python manage.py check
   ```

To remove old rate-limit records periodically, run `python manage.py prune_rate_limits` (daily is suitable for a small site).

## Publishing

Sign in as a Django superuser or give a staff account the appropriate model permissions. Add categories and tags as needed. Create a note or journal entry, write its body in Markdown, choose a draft or published status, and set a publication time. Add approved cover images and attachments in the content form. Use the preview link before publishing. Django admin asks for confirmation before deleting records.

Accepted uploads are JPG, PNG, WebP, PDF, TXT, Markdown, CSV, and ZIP, up to 15 MB each. Image content is verified with Pillow; PDF and ZIP headers are checked. Uploaded content is restricted to staff through Django admin.

## Production environment

Set these values in the hosting platform's secret/environment settings; do not commit `.env`:

- `DEBUG=false`
- `SECRET_KEY`: generate a unique random value and keep it private
- `ALLOWED_HOSTS`: the platform hostname and any custom domain, comma-separated
- `CSRF_TRUSTED_ORIGINS`: full HTTPS origins, comma-separated
- `DATABASE_URL`: PostgreSQL connection URL
- `DEFAULT_FROM_EMAIL`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`: SMTP delivery for password reset links
- `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_ENDPOINT_URL`, `AWS_S3_REGION_NAME`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`: a private S3-compatible bucket with only the required object read/write access
- `ENABLE_HSTS=true` after HTTPS is confirmed end-to-end

For Cloudflare R2, use its account S3 endpoint and region `auto`; its S3 API is compatible with the boto3-based storage backend. See [R2 S3 API compatibility](https://developers.cloudflare.com/r2/api/s3/). AWS S3 can be used without an endpoint override.

## Deployment on Render

The project includes a Dockerfile and `build.sh`. For a Render native Python web service, use Python 3.14.3, set the build command to `bash build.sh`, and the start command to:

```sh
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3
```

Connect a managed Render PostgreSQL database through `DATABASE_URL`. Set the environment values above in the service dashboard. Set `python manage.py migrate` as the pre-deploy command so schema changes are applied before new code starts. Create the first administrator using the service shell with `python manage.py createsuperuser`. Render's [Django deployment guide](https://render.com/docs/deploy-django) documents the web service setup; its [Python version guide](https://render.com/docs/python-version) lists Python 3.14.3.

For a custom domain, add it to the web service in the Render dashboard, update DNS at the domain registrar as Render instructs, then add the HTTPS origin to `CSRF_TRUSTED_ORIGINS` and the hostname to `ALLOWED_HOSTS`. Render provisions TLS for configured custom domains. See [Render custom domains](https://render.com/docs/custom-domains).

Keep the object bucket private. The app issues short-lived signed URLs for cover images and streams attachments through a route that only exposes files attached to public content (or to a staff member with file-view permission). Enable storage versioning or scheduled exports where supported by the chosen provider.

## Backups and operations

- Enable automated PostgreSQL backups or point-in-time recovery on the selected database plan. Before risky schema changes, take a snapshot and verify restore into a staging database.
- Retain an encrypted off-platform PostgreSQL export on a regular schedule. A manual export can be made with `pg_dump --format=custom "$DATABASE_URL" --file=fieldnotes.dump`; store the dump in a separate private backup location.
- Enable object versioning or scheduled export for uploads. Database backups do not include S3 objects.
- Keep `SECRET_KEY`, SMTP credentials, database URLs, and storage keys only in the hosting secret store. Rotate a leaked key immediately.
- Before going live, run `python manage.py check --deploy`, verify HTTPS and email delivery, and confirm one database and one file restore path.

## Security notes and current scope

Server-side forms validate input. Database writes use Django's ORM. Django enforces CSRF tokens, password hashing, sessions, and admin permissions. Request limits are database-backed and keyed by an HMAC-SHA-256 of the client IP; raw IP values are not stored. By default the app uses `REMOTE_ADDR`. Only set `RATE_LIMIT_IP_HEADER=HTTP_X_FORWARDED_FOR` when a trusted reverse proxy replaces that header.

Contact submissions are persisted in the dashboard inbox; no outbound notification is configured. Email is used for password resets once SMTP is configured. Users do not have email verification or social login in this first version.
