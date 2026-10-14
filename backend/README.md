# SLB Coliving PG — Backend Documentation

This backend is built using **FastAPI**, **Prisma ORM**, and **Supabase (PostgreSQL)**, providing a complete Call-back request management system and JWT Authentication.

---

## 🚀 Quick Start

### 1. Run the Backend Locally

Run the PowerShell runner script:
```powershell
.\run_backend.ps1
```

Or manually:
```powershell
$env:PATH = ".\backend\venv\Scripts;$env:PATH"
.\backend\venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
```

- **Website**: [http://localhost:8000](http://localhost:8000)
- **Admin Call-Back Portal**: [http://localhost:8000/admin](http://localhost:8000/admin)
- **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🔑 Default Admin Credentials

On first run, the system seeds a default staff/admin account:
- **Email**: `admin@slbcoliving.com`
- **Password**: `admin123`

You can also click the **"Fill Demo Credentials"** button on the `/admin` login page.

---

## 🗄️ Connecting to Supabase

1. Open your [Supabase Dashboard](https://supabase.com/dashboard) and create a project (or choose an existing one).
2. Go to **Project Settings** → **Database** → **Connection string**.
3. Select **URI** (Session or Transaction pooler).
4. Copy the connection string and open [`backend/.env`](file:///c:/Users/karun/OneDrive/Desktop/SLB/SLB-co-living-pg/backend/.env):
   ```env
   DATABASE_URL="postgresql://postgres.[your-project-ref]:[your-db-password]@aws-0-[region].pooler.supabase.com:6543/postgres?pgbouncer=true"
   ```
5. Push the schema to your Supabase PostgreSQL database:
   ```powershell
   $env:PATH = ".\backend\venv\Scripts;$env:PATH"
   .\backend\venv\Scripts\prisma.exe db push --schema backend/prisma/schema.prisma
   ```

*Note: While developing locally or offline before configuring Supabase, the backend automatically uses a local development SQLite database so you can test all features without interruption!*

---

## 📋 Features & API Endpoints

### 1. Call-Back Form & Leads (`/api/leads`)
- **`POST /api/leads`** *(Public)*:
  Interested visitors submit their contact details, room preference, check-in date, and best time to call.
- **`GET /api/leads`** *(Admin only)*:
  Lists all enquiries with optional filters:
  - `?status=PENDING_CALL` (need immediate callback)
  - `?status=CALLED`
  - `?status=VISIT_SCHEDULED`
  - `?status=BOOKED`
  - `?search=name_or_phone`
- **`PATCH /api/leads/{id}`** *(Admin only)*:
  Update lead status or add internal follow-up notes.
- **`DELETE /api/leads/{id}`** *(Admin only)*:
  Archive or delete a lead.

### 2. Admin Authentication (`/api/auth`)
- **`POST /api/auth/login`**:
  Validates credentials and issues a signed JWT access token.
- **`GET /api/auth/me`**:
  Returns the authenticated user's profile and role.
- **`POST /api/auth/register`**:
  Allows administrators to register additional staff members.

### 3. Analytics & Summary (`/api/stats`)
- **`GET /api/stats`** *(Admin only)*:
  Returns live metrics: Total Leads, Pending Calls, Visits Scheduled, and Booked.

---

## 📱 Admin Call-Back Management Portal (`/admin`)

The Admin Portal matches the PG's dark crimson aesthetic and provides:
- **Real-time Call Queue**: Direct 1-click `tel:` phone call link and WhatsApp chat link.
- **Urgent Call Badges**: Highlighting tenants who requested "Call me ASAP ⚡".
- **Instant Status Updating**: Dropdown menu that updates lead status in the database with 1 click.
- **Internal Notes**: Staff can type notes after speaking with the prospective tenant.
