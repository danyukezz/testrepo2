# 🛒 Mini Shop — Django Demo Project

A tiny but **complete** Django project that demonstrates **every library** from the
spec in a minimal, working way.  One app (`core`), three models, SQLite, and a
handful of API endpoints — nothing more.

---

## File structure

```
myproject/
├── manage.py
├── requirements.txt
├── README.md
├── myproject/              # Django project package
│   ├── settings.py         # ← all library configs live here
│   ├── urls.py             # root URL routing
│   ├── asgi.py             # ASGI entry-point (Django + Bolt)
│   └── wsgi.py
└── core/                   # the single "Mini Shop" app
    ├── apps.py             # AppConfig – registers Product with django-eav2
    ├── models.py           # Product, Order, Payment, CustomerNote
    ├── serializers.py      # DRF serializers (tags, EAV, payments …)
    ├── filters.py          # django-filter FilterSet (price, tag)
    ├── views.py            # ViewSets + /api/me/
    ├── urls.py             # DRF router
    ├── admin.py            # ModelAdmin registrations
    ├── bolt_api.py         # Django-Bolt /bolt/ping endpoint
    ├── tests.py            # 8 tests covering every library
    └── management/commands/
        └── seed_data.py    # creates demo products, order, note
```

---

## Quick start

```bash
# 1 – Create & activate a virtualenv
python3 -m venv .venv && source .venv/bin/activate

# 2 – Install dependencies
pip install -r requirements.txt

# 3 – Apply migrations
python manage.py migrate

# 4 – Load sample data (3 products, 1 order+payment, 1 encrypted note)
python manage.py seed_data

# 5 – Create a superuser for /admin/
python manage.py createsuperuser

# 6 – Run the dev server
python manage.py runserver

# 7 – Run the test suite
python manage.py test core -v2
```

---

## Library-by-library guide

### 1. Django + Django REST Framework

| What | Where |
|------|-------|
| **Settings** | `settings.py` → `INSTALLED_APPS` (`rest_framework`), `REST_FRAMEWORK` dict |
| **Models** | `core/models.py` — `Product`, `Order`, `Payment`, `CustomerNote` |
| **Serializers** | `core/serializers.py` — `ProductSerializer`, `OrderSerializer`, etc. |
| **Views** | `core/views.py` — `ProductViewSet`, `OrderViewSet`, `CustomerNoteViewSet`, `me_view` |
| **URLs** | `core/urls.py` — DRF `DefaultRouter`; `myproject/urls.py` mounts at `/api/` |

**How to test:**

```bash
# List all products (public, no auth needed)
curl http://localhost:8000/api/products/ | python3 -m json.tool

# Browsable API — open in your browser:
open http://localhost:8000/api/
```

---

### 2. django-filter

Adds declarative `FilterSet` classes that plug into DRF views.

| What | Where |
|------|-------|
| **Settings** | `settings.py` → `REST_FRAMEWORK["DEFAULT_FILTER_BACKENDS"]` includes `DjangoFilterBackend` |
| **Filter class** | `core/filters.py` — `ProductFilter` with `min_price`, `max_price`, `tag` |
| **Wired to view** | `core/views.py` — `ProductViewSet.filterset_class = ProductFilter` |

**How to test:**

```bash
# Only products ≥ $10
curl "http://localhost:8000/api/products/?min_price=10"

# Only products tagged "electronics"
curl "http://localhost:8000/api/products/?tag=electronics"

# Combine both
curl "http://localhost:8000/api/products/?min_price=5&max_price=15&tag=cotton"
```

---

### 3. django-taggit

Provides a `TaggableManager` — a many-to-many "tags" field with its own table.

| What | Where |
|------|-------|
| **Settings** | `settings.py` → `INSTALLED_APPS` includes `"taggit"` |
| **Model field** | `core/models.py` — `Product.tags = TaggableManager(blank=True)` |
| **Serializer** | `core/serializers.py` — `TagListSerializerField` renders tags as `["clothing", "cotton"]` |
| **Seed data** | `seed_data.py` — `p1.tags.add("clothing", "cotton")` |

**How to test:**

```bash
# Tags appear in every product response
curl http://localhost:8000/api/products/ | python3 -m json.tool
# → each product has "tags": ["clothing", "cotton"]

# Create a product with tags via the API
curl -X POST http://localhost:8000/api/products/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Mug", "price": "6.99", "tags": ["kitchen", "gift"]}'
```

---

### 4. django-eav2

Entity-Attribute-Value: lets you attach **dynamic attributes** (like "color",
"size") to any model without altering the DB schema.

| What | Where |
|------|-------|
| **Settings** | `settings.py` → `INSTALLED_APPS` includes `"eav"`, plus `EAV2_PRIMARY_KEY_FIELD` |
| **Registration** | `core/apps.py` → `eav.register(Product)` in `CoreConfig.ready()` |
| **Serializer** | `core/serializers.py` → `get_eav_attrs()` returns a dict like `{"color": "blue"}` |
| **API endpoint** | `core/views.py` → `ProductViewSet.set_eav` action at `POST /api/products/<id>/set-eav/` |
| **Seed data** | `seed_data.py` — `p1.eav.color = "blue"; p1.eav.size = "M"` |

**How to test:**

```bash
# EAV attrs are in the product response under "eav_attrs"
curl http://localhost:8000/api/products/1/ | python3 -m json.tool
# → "eav_attrs": {"color": "blue", "size": "M"}

# Set new EAV attributes on product #2
curl -X POST http://localhost:8000/api/products/2/set-eav/ \
  -H "Content-Type: application/json" \
  -d '{"color": "white", "material": "nylon"}'
```

---

### 5. django-model-utils

Provides handy base classes and fields.  We use two of them:

| Utility | Where |
|---------|-------|
| `TimeStampedModel` | `core/models.py` — `Product`, `Order`, `CustomerNote` all inherit from it → auto `created` / `modified` fields |
| `StatusField` + `Choices` | `core/models.py` — `Order.STATUS = Choices("new", "paid", "shipped", "cancelled")` and `Order.status = StatusField()` |

**How to test:**

```bash
# Every product / order response has "created" and "modified" timestamps
curl http://localhost:8000/api/products/1/ | python3 -m json.tool

# Order status is auto-set to "new" (the first choice)
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo1234"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['access'])")

curl http://localhost:8000/api/orders/ -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# → "status": "new"
```

---

### 6. django-lifecycle

Declarative hooks that run at specific moments in a model's lifecycle
(`AFTER_CREATE`, `BEFORE_UPDATE`, etc.) — like Rails callbacks but explicit.

| What | Where |
|------|-------|
| **Mixin** | `core/models.py` — `Order` inherits `LifecycleModelMixin` |
| **Hook** | `core/models.py` — `@hook(AFTER_CREATE) def create_payment_record(self)` |
| **Effect** | Creating an `Order` **automatically** creates a `Payment` record linked to it |

**How to test:**

```bash
# Create a new order (requires auth)
TOKEN=<your JWT token from login>

curl -X POST http://localhost:8000/api/orders/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product": 2, "quantity": 3}'

# The response includes an auto-generated payment!
# → "payments": [{"status": "waiting", "total": "28.50", ...}]
```

The test `test_order_creates_payment` in `core/tests.py` proves this:
it creates an Order and asserts `order.payments.count() == 1`.

---

### 7. django-fernet-encrypted-fields

Provides model fields whose values are **Fernet-encrypted at rest** in the database.
You read/write normal Python strings; the library encrypts/decrypts transparently.

| What | Where |
|------|-------|
| **Settings** | `settings.py` → `SALT_KEY` (used together with `SECRET_KEY` to derive the Fernet key) |
| **Model field** | `core/models.py` — `CustomerNote.private_note = EncryptedTextField(…)` |
| **API** | `core/views.py` → `CustomerNoteViewSet` at `/api/notes/` |
| **Seed data** | `seed_data.py` creates a note: `"This note is Fernet-encrypted at rest! 🔐"` |

**How to test:**

```bash
# Read your encrypted note through the API (returns plain text)
curl http://localhost:8000/api/notes/ -H "Authorization: Bearer $TOKEN"
# → "private_note": "This note is Fernet-encrypted at rest! 🔐"

# Peek at the raw database — the value is cipher-text, not plain text:
python manage.py shell_plus -c "
from core.models import CustomerNote
import sqlite3, pathlib
conn = sqlite3.connect(str(pathlib.Path('db.sqlite3')))
row = conn.execute('SELECT private_note FROM core_customernote LIMIT 1').fetchone()
print('Raw DB value:', row[0][:80], '…')
"
```

The test `test_encrypted_note_round_trip` writes "top secret 🔑", reads it
back from the DB, and confirms it matches.

---

### 8. django-payments

A pluggable payment framework.  We use the built-in **DummyProvider** (no real
credit card needed).

| What | Where |
|------|-------|
| **Settings** | `settings.py` → `PAYMENT_HOST`, `PAYMENT_MODEL = "core.Payment"`, `PAYMENT_VARIANTS` with `DummyProvider` |
| **Model** | `core/models.py` — `Payment(BasePayment)` with FK to `Order`, plus `get_failure_url`, `get_success_url`, `get_purchased_items` |
| **URLs** | `myproject/urls.py` → `path("payments/", include("payments.urls"))` for payment callbacks |
| **Created by** | The `django-lifecycle` hook on `Order` (see #6) — you never create payments manually |

**How to test:**

```bash
# Payments show up embedded in every order response
curl http://localhost:8000/api/orders/ -H "Authorization: Bearer $TOKEN"
# → "payments": [{"variant": "default", "status": "waiting", "total": "39.98", …}]

# You can also browse in admin:
open http://localhost:8000/admin/core/payment/
```

---

### 9. django-extensions

A collection of management-command helpers.  We use `shell_plus` and
`graph_models`.

| What | Where |
|------|-------|
| **Settings** | `settings.py` → `INSTALLED_APPS` includes `"django_extensions"`, plus `GRAPH_MODELS` dict |

**How to test:**

```bash
# shell_plus — auto-imports all models
python manage.py shell_plus
>>> Product.objects.count()
3

# graph_models — generate a model diagram (requires pydot + graphviz)
#   brew install graphviz   # macOS
python manage.py graph_models core -o myapp_models.png
open myapp_models.png
```

---

### 10. Django-Bolt

A high-performance ASGI micro-framework that sits **beside** Django.
We mount a single Bolt endpoint at `/bolt/ping`.

| What | Where |
|------|-------|
| **Settings** | `settings.py` → `INSTALLED_APPS` includes `"django_bolt"` |
| **Bolt app** | `core/bolt_api.py` — `BoltAPI()` with one `@bolt_app.get("/ping")` handler |
| **ASGI router** | `myproject/asgi.py` — routes `/bolt/*` to Bolt, everything else to Django |

**How to test:**

```bash
# Bolt runs on ASGI, so use uvicorn instead of runserver:
pip install uvicorn
uvicorn myproject.asgi:application --reload --port 8000

# Hit the Bolt endpoint
curl http://localhost:8000/bolt/ping
# → {"message": "pong from django-bolt 🚀"}

# All other Django endpoints still work as usual:
curl http://localhost:8000/api/products/
```

> **Note:** `python manage.py runserver` uses WSGI and won't serve Bolt routes.
> Use `uvicorn` (or `daphne`) for the ASGI path.

---

### 11. django-allauth

Full-featured authentication: registration, login, logout, email verification,
social login, and more.

| What | Where |
|------|-------|
| **Settings** | `settings.py` → `INSTALLED_APPS` (`allauth`, `allauth.account`, `allauth.socialaccount`), `AUTHENTICATION_BACKENDS`, `ACCOUNT_*` settings, `SITE_ID`, allauth middleware |
| **URLs** | `myproject/urls.py` → `path("accounts/", include("allauth.urls"))` |

**How to test:**

```bash
# Browser-based registration (HTML form):
open http://localhost:8000/accounts/signup/

# Browser-based login:
open http://localhost:8000/accounts/login/
```

---

### 12. drf-auth-kit

Wraps **django-allauth + simplejwt** to expose REST API endpoints for
registration, login (JWT), logout, password reset, and a `/user` endpoint.

| What | Where |
|------|-------|
| **Settings** | `settings.py` → `AUTH_KIT` dict, `SIMPLE_JWT` dict, `REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]` uses `JWTCookieAuthentication` |
| **URLs** | `myproject/urls.py` → `path("api/auth/", include("auth_kit.urls"))` |
| **Protected view** | `core/views.py` → `me_view` at `/api/me/` with `IsAuthenticated` |

**How to test:**

```bash
# ── Register a new user ──────────────────────────────────────────────
curl -X POST http://localhost:8000/api/auth/registration \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password1":"myPass123","password2":"myPass123"}'
# → {"detail": "Successfully registered."}

# ── Login (get JWT tokens) ───────────────────────────────────────────
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo1234"}'
# → {"access": "eyJ…", "user": {"pk":1, "username":"demo", …}}

# ── Use the access token on protected endpoints ─────────────────────
TOKEN="<paste the access token here>"

curl http://localhost:8000/api/me/ -H "Authorization: Bearer $TOKEN"
# → {"id": 1, "username": "demo", "email": "demo@example.com"}

# ── Quick one-liner (login + hit /api/me/) ───────────────────────────
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo1234"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['access'])")

curl -s http://localhost:8000/api/me/ -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

## All API endpoints at a glance

| Method | URL | Auth? | Library demonstrated |
|--------|-----|-------|---------------------|
| GET | `/api/products/` | No | DRF, django-filter, django-taggit, django-eav2 |
| POST | `/api/products/` | No | DRF, django-taggit |
| GET | `/api/products/<id>/` | No | DRF, django-eav2 |
| POST | `/api/products/<id>/set-eav/` | No | django-eav2 |
| GET | `/api/orders/` | **Yes** | DRF, django-model-utils, django-lifecycle, django-payments |
| POST | `/api/orders/` | **Yes** | django-lifecycle (auto-creates Payment) |
| GET | `/api/notes/` | **Yes** | django-fernet-encrypted-fields |
| POST | `/api/notes/` | **Yes** | django-fernet-encrypted-fields |
| GET | `/api/me/` | **Yes** | drf-auth-kit (JWT) |
| POST | `/api/auth/login` | No | drf-auth-kit + django-allauth |
| POST | `/api/auth/registration` | No | drf-auth-kit + django-allauth |
| POST | `/api/auth/logout` | Yes | drf-auth-kit |
| GET | `/accounts/signup/` | No | django-allauth (HTML) |
| GET | `/accounts/login/` | No | django-allauth (HTML) |
| GET | `/bolt/ping` | No | Django-Bolt (ASGI only) |
| GET | `/admin/` | Staff | Django admin |

---

## Test suite

```
$ python manage.py test core -v2

test_me_authenticated          ✓   (drf-auth-kit JWT)
test_me_unauthenticated        ✓   (drf-auth-kit rejects anon)
test_eav_attribute             ✓   (django-eav2 set + read)
test_encrypted_note_round_trip ✓   (django-fernet-encrypted-fields)
test_order_creates_payment     ✓   (django-lifecycle → django-payments)
test_filter_by_price           ✓   (django-filter)
test_filter_by_tag             ✓   (django-filter + django-taggit)
test_product_creation          ✓   (Django + django-taggit)

Ran 8 tests — OK
```

---

## Sample data

The `seed_data` command creates:

| Object | Details |
|--------|---------|
| **User** `demo` | password `demo1234` |
| **Product** T-Shirt | $19.99, tags: clothing/cotton, EAV: color=blue, size=M |
| **Product** USB-C Cable | $9.50, tags: electronics/accessories, EAV: color=black |
| **Product** Notebook | $4.99, tags: stationery |
| **Order #1** | 2× T-Shirt for user `demo` |
| **Payment #1** | Auto-created, $39.98, status=waiting |
| **CustomerNote** | Encrypted note for user `demo` |
