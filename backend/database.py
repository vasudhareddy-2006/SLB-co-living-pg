import asyncio
import logging
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from backend.auth.security import hash_password
from backend.config import settings

logger = logging.getLogger("slb_database")

# Check for psycopg2 and prisma
PSYCOPG2_AVAILABLE = False
try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    pass

PRISMA_AVAILABLE = False
try:
    from prisma import Prisma
    PRISMA_AVAILABLE = True
except (ImportError, RuntimeError):
    pass


class DatabaseService:
    def __init__(self):
        self.mode = "sqlite"  # "postgres" or "sqlite"
        self._sqlite_conn: Optional[sqlite3.Connection] = None
        if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
            self.sqlite_path = Path("/tmp") / "local_dev.db"
        else:
            self.sqlite_path = Path(__file__).resolve().parent / "local_dev.db"
        self._ensure_connected()

    def _ensure_connected(self):
        """Auto-configure connection mode."""
        db_url = settings.DATABASE_URL.strip()
        is_real_postgres = (
            db_url.startswith("postgresql://") or db_url.startswith("postgres://")
        ) and "samplepass" not in db_url and "YOUR-PASSWORD" not in db_url
        if is_real_postgres and PSYCOPG2_AVAILABLE:
            self.mode = "postgres"
        else:
            self.mode = "sqlite"
            if not self._sqlite_conn:
                self._init_sqlite()

    def _get_pg_conn(self):
        """Get a fresh PostgreSQL connection to Supabase with SSL."""
        conn = psycopg2.connect(
            settings.DATABASE_URL.strip(),
            cursor_factory=psycopg2.extras.RealDictCursor,
            connect_timeout=10,
            sslmode="require",
        )
        conn.autocommit = True
        return conn

    async def connect(self):
        """Initialize connection to Supabase or SQLite fallback."""
        db_url = settings.DATABASE_URL.strip()
        is_real_postgres = (
            db_url.startswith("postgresql://") or db_url.startswith("postgres://")
        ) and "samplepass" not in db_url and "YOUR-PASSWORD" not in db_url

        if is_real_postgres and PSYCOPG2_AVAILABLE:
            try:
                conn = self._get_pg_conn()
                with conn.cursor() as cur:
                    cur.execute("SELECT 1;")
                conn.close()
                self.mode = "postgres"
                logger.info("Successfully connected to Supabase PostgreSQL via psycopg2!")
            except Exception as e:
                logger.warning(f"Could not connect to Supabase PostgreSQL ({e}). Using SQLite fallback.")
                self.mode = "sqlite"
                self._init_sqlite()
        else:
            self.mode = "sqlite"
            self._init_sqlite()

        # Seed initial admin if needed
        await self._ensure_seed_admin()

    async def disconnect(self):
        if self._sqlite_conn:
            try:
                self._sqlite_conn.close()
            except Exception:
                pass

    def _init_sqlite(self):
        """Initialize local SQLite database schema for dev/testing."""
        self._sqlite_conn = sqlite3.connect(
            str(self.sqlite_path),
            check_same_thread=False
        )
        self._sqlite_conn.row_factory = sqlite3.Row
        with self._sqlite_conn:
            self._sqlite_conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    passwordHash TEXT NOT NULL,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'ADMIN',
                    createdAt TEXT NOT NULL,
                    updatedAt TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS callback_leads (
                    id TEXT PRIMARY KEY,
                    fullName TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    roomType TEXT NOT NULL,
                    moveInDate TEXT NOT NULL,
                    preferredCallTime TEXT NOT NULL DEFAULT 'ASAP',
                    requirements TEXT,
                    status TEXT NOT NULL DEFAULT 'PENDING_CALL',
                    adminNotes TEXT,
                    assignedToId TEXT,
                    createdAt TEXT NOT NULL,
                    updatedAt TEXT NOT NULL,
                    FOREIGN KEY(assignedToId) REFERENCES users(id)
                );
            """)

    async def _ensure_seed_admin(self):
        """Ensure default administrator accounts exist."""
        try:
            admin = await self.get_user_by_email(settings.ADMIN_DEFAULT_EMAIL)
            if not admin:
                logger.info(f"Seeding default admin: {settings.ADMIN_DEFAULT_EMAIL}")
                hashed = hash_password(settings.ADMIN_DEFAULT_PASSWORD)
                await self.create_user(
                    email=settings.ADMIN_DEFAULT_EMAIL,
                    password_hash=hashed,
                    name=settings.ADMIN_DEFAULT_NAME,
                    role="ADMIN"
                )
            
            # Also ensure vasudhareddy9398@gmail.com exists
            personal_admin = await self.get_user_by_email("vasudhareddy9398@gmail.com")
            if not personal_admin:
                hashed = hash_password(settings.ADMIN_DEFAULT_PASSWORD)
                await self.create_user(
                    email="vasudhareddy9398@gmail.com",
                    password_hash=hashed,
                    name="Vasudha Reddy",
                    role="ADMIN"
                )
        except Exception as e:
            logger.warning(f"Error checking seed admin: {e}")

    # -------------------------------------------------------------
    # User Operations
    # -------------------------------------------------------------
    async def get_user_by_email(self, email: str) -> Optional[dict[str, Any]]:
        email = email.strip().lower()
        if self.mode == "postgres":
            conn = self._get_pg_conn()
            try:
                with conn.cursor() as cur:
                    cur.execute('SELECT * FROM users WHERE lower(email) = %s LIMIT 1;', (email,))
                    row = cur.fetchone()
                    return dict(row) if row else None
            finally:
                conn.close()

        cursor = self._sqlite_conn.cursor()
        cursor.execute("SELECT * FROM users WHERE lower(email) = ?", (email,))
        row = cursor.fetchone()
        return dict(row) if row else None

    async def get_user_by_id(self, user_id: str) -> Optional[dict[str, Any]]:
        if self.mode == "postgres":
            conn = self._get_pg_conn()
            try:
                with conn.cursor() as cur:
                    cur.execute('SELECT * FROM users WHERE id = %s LIMIT 1;', (user_id,))
                    row = cur.fetchone()
                    return dict(row) if row else None
            finally:
                conn.close()

        cursor = self._sqlite_conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    async def create_user(
        self, email: str, password_hash: str, name: str, role: str = "ADMIN"
    ) -> dict[str, Any]:
        email = email.strip().lower()
        now_dt = datetime.now(timezone.utc)
        user_id = str(uuid.uuid4())

        if self.mode == "postgres":
            conn = self._get_pg_conn()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        '''
                        INSERT INTO users (id, email, "passwordHash", name, role, "createdAt", "updatedAt")
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING *;
                        ''',
                        (user_id, email, password_hash, name, role, now_dt, now_dt)
                    )
                    row = cur.fetchone()
                    return dict(row) if row else {}
            finally:
                conn.close()

        now_str = now_dt.isoformat()
        with self._sqlite_conn:
            self._sqlite_conn.execute(
                """
                INSERT INTO users (id, email, passwordHash, name, role, createdAt, updatedAt)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, email, password_hash, name, role, now_str, now_str),
            )
        return {
            "id": user_id,
            "email": email,
            "passwordHash": password_hash,
            "name": name,
            "role": role,
            "createdAt": now_str,
            "updatedAt": now_str,
        }

    # -------------------------------------------------------------
    # Lead / Call-back Request Operations
    # -------------------------------------------------------------
    async def create_lead(
        self,
        full_name: str,
        phone: str,
        room_type: str,
        move_in_date: str,
        preferred_call_time: str = "ASAP",
        requirements: Optional[str] = None,
    ) -> dict[str, Any]:
        now_dt = datetime.now(timezone.utc)
        lead_id = str(uuid.uuid4())

        if self.mode == "postgres":
            conn = self._get_pg_conn()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        '''
                        INSERT INTO callback_leads (
                            id, "fullName", phone, "roomType", "moveInDate",
                            "preferredCallTime", requirements, status, "adminNotes", "createdAt", "updatedAt"
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING *;
                        ''',
                        (
                            lead_id, full_name, phone, room_type, move_in_date,
                            preferred_call_time or "ASAP", requirements, "PENDING_CALL", "", now_dt, now_dt
                        )
                    )
                    row = cur.fetchone()
                    return dict(row) if row else {}
            finally:
                conn.close()

        now_str = now_dt.isoformat()
        with self._sqlite_conn:
            self._sqlite_conn.execute(
                """
                INSERT INTO callback_leads (
                    id, fullName, phone, roomType, moveInDate, preferredCallTime,
                    requirements, status, adminNotes, createdAt, updatedAt
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lead_id, full_name, phone, room_type, move_in_date,
                    preferred_call_time or "ASAP", requirements, "PENDING_CALL", "", now_str, now_str
                ),
            )
        return {
            "id": lead_id,
            "fullName": full_name,
            "phone": phone,
            "roomType": room_type,
            "moveInDate": move_in_date,
            "preferredCallTime": preferred_call_time or "ASAP",
            "requirements": requirements,
            "status": "PENDING_CALL",
            "adminNotes": "",
            "createdAt": now_dt,
            "updatedAt": now_dt,
        }

    async def get_leads(
        self,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        if self.mode == "postgres":
            conn = self._get_pg_conn()
            try:
                query = 'SELECT * FROM callback_leads WHERE 1=1'
                params = []
                if status and status.upper() != "ALL":
                    query += ' AND status = %s'
                    params.append(status)
                if search:
                    query += ' AND ("fullName" ILIKE %s OR phone ILIKE %s)'
                    params.extend([f"%{search}%", f"%{search}%"])
                query += ' ORDER BY "createdAt" DESC LIMIT %s OFFSET %s;'
                params.extend([limit, offset])

                with conn.cursor() as cur:
                    cur.execute(query, params)
                    rows = cur.fetchall()
                    return [dict(r) for r in rows]
            finally:
                conn.close()

        query = "SELECT * FROM callback_leads WHERE 1=1"
        params: list[Any] = []
        if status and status.upper() != "ALL":
            query += " AND status = ?"
            params.append(status)
        if search:
            query += " AND (fullName LIKE ? OR phone LIKE ?)"
            params.append(f"%{search}%")
            params.append(f"%{search}%")

        query += " ORDER BY createdAt DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = self._sqlite_conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_lead_by_id(self, lead_id: str) -> Optional[dict[str, Any]]:
        if self.mode == "postgres":
            conn = self._get_pg_conn()
            try:
                with conn.cursor() as cur:
                    cur.execute('SELECT * FROM callback_leads WHERE id = %s LIMIT 1;', (lead_id,))
                    row = cur.fetchone()
                    return dict(row) if row else None
            finally:
                conn.close()

        cursor = self._sqlite_conn.cursor()
        cursor.execute("SELECT * FROM callback_leads WHERE id = ?", (lead_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    async def update_lead(
        self,
        lead_id: str,
        status: Optional[str] = None,
        admin_notes: Optional[str] = None,
        assigned_to_id: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        now_dt = datetime.now(timezone.utc)

        if self.mode == "postgres":
            conn = self._get_pg_conn()
            try:
                updates = ['"updatedAt" = %s']
                params = [now_dt]
                if status:
                    updates.append("status = %s")
                    params.append(status)
                if admin_notes is not None:
                    updates.append('"adminNotes" = %s')
                    params.append(admin_notes)
                if assigned_to_id:
                    updates.append('"assignedToId" = %s')
                    params.append(assigned_to_id)
                params.append(lead_id)

                query = f'UPDATE callback_leads SET {", ".join(updates)} WHERE id = %s RETURNING *;'
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    row = cur.fetchone()
                    return dict(row) if row else None
            finally:
                conn.close()

        now_str = now_dt.isoformat()
        updates_sql = ["updatedAt = ?"]
        params_sql: list[Any] = [now_str]
        if status:
            updates_sql.append("status = ?")
            params_sql.append(status)
        if admin_notes is not None:
            updates_sql.append("adminNotes = ?")
            params_sql.append(admin_notes)
        if assigned_to_id:
            updates_sql.append("assignedToId = ?")
            params_sql.append(assigned_to_id)
        params_sql.append(lead_id)

        query = f"UPDATE callback_leads SET {', '.join(updates_sql)} WHERE id = ?"
        with self._sqlite_conn:
            self._sqlite_conn.execute(query, params_sql)

        return await self.get_lead_by_id(lead_id)

    async def delete_lead(self, lead_id: str) -> bool:
        if self.mode == "postgres":
            conn = self._get_pg_conn()
            try:
                with conn.cursor() as cur:
                    cur.execute('DELETE FROM callback_leads WHERE id = %s;', (lead_id,))
                    return cur.rowcount > 0
            finally:
                conn.close()

        with self._sqlite_conn:
            cursor = self._sqlite_conn.execute(
                "DELETE FROM callback_leads WHERE id = ?", (lead_id,)
            )
            return cursor.rowcount > 0

    async def get_stats(self) -> dict[str, int]:
        if self.mode == "postgres":
            conn = self._get_pg_conn()
            try:
                with conn.cursor() as cur:
                    cur.execute('SELECT COUNT(*) as count FROM callback_leads;')
                    total = cur.fetchone()["count"]
                    cur.execute("SELECT COUNT(*) as count FROM callback_leads WHERE status = 'PENDING_CALL';")
                    pending = cur.fetchone()["count"]
                    cur.execute("SELECT COUNT(*) as count FROM callback_leads WHERE status = 'CALLED';")
                    called = cur.fetchone()["count"]
                    cur.execute("SELECT COUNT(*) as count FROM callback_leads WHERE status = 'VISIT_SCHEDULED';")
                    visit = cur.fetchone()["count"]
                    cur.execute("SELECT COUNT(*) as count FROM callback_leads WHERE status = 'BOOKED';")
                    booked = cur.fetchone()["count"]
                    return {
                        "total": total,
                        "pendingCalls": pending,
                        "called": called,
                        "visitsScheduled": visit,
                        "booked": booked,
                    }
            finally:
                conn.close()

        cursor = self._sqlite_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM callback_leads")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM callback_leads WHERE status = 'PENDING_CALL'")
        pending = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM callback_leads WHERE status = 'CALLED'")
        called = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM callback_leads WHERE status = 'VISIT_SCHEDULED'")
        visit = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM callback_leads WHERE status = 'BOOKED'")
        booked = cursor.fetchone()[0]

        return {
            "total": total,
            "pendingCalls": pending,
            "called": called,
            "visitsScheduled": visit,
            "booked": booked,
        }

db_service = DatabaseService()
