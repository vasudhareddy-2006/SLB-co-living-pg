import asyncio
import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from backend.auth.security import hash_password
from backend.config import settings

logger = logging.getLogger("slb_database")

# Check if Prisma Client is available and generated
PRISMA_AVAILABLE = False
Prisma = None
try:
    from prisma import Prisma
    PRISMA_AVAILABLE = True
except (ImportError, RuntimeError):
    PRISMA_AVAILABLE = False
    Prisma = None

class DatabaseService:
    def __init__(self):
        self.use_prisma: bool = False
        self.prisma_client: Optional[Any] = None
        self.sqlite_path = Path(__file__).resolve().parent / "local_dev.db"
        self._sqlite_conn: Optional[sqlite3.Connection] = None

    async def connect(self):
        """Connect to Supabase via Prisma, or fall back to local dev database."""
        db_url = settings.DATABASE_URL.strip()
        is_real_postgres = (
            db_url.startswith("postgresql://") or db_url.startswith("postgres://")
        ) and "samplepass" not in db_url and "YOUR-PASSWORD" not in db_url

        if PRISMA_AVAILABLE and is_real_postgres:
            try:
                logger.info("Attempting connection to Supabase PostgreSQL via Prisma...")
                self.prisma_client = Prisma()
                await self.prisma_client.connect()
                self.use_prisma = True
                logger.info("Successfully connected to Supabase PostgreSQL!")
            except Exception as e:
                logger.warning(
                    f"Could not connect to Supabase PostgreSQL ({e}). Falling back to local development database."
                )
                self.use_prisma = False
                self._init_sqlite()
        else:
            logger.info("Using local development database for instant setup.")
            self.use_prisma = False
            self._init_sqlite()

        # Seed initial admin if needed
        await self._ensure_seed_admin()

    async def disconnect(self):
        if self.use_prisma and self.prisma_client:
            try:
                await self.prisma_client.disconnect()
            except Exception:
                pass
        if self._sqlite_conn:
            self._sqlite_conn.close()

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
        """Ensure the default administrator account exists."""
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

    # -------------------------------------------------------------
    # User Operations
    # -------------------------------------------------------------
    async def get_user_by_email(self, email: str) -> Optional[dict[str, Any]]:
        email = email.strip().lower()
        if self.use_prisma and self.prisma_client:
            user = await self.prisma_client.user.find_unique(where={"email": email})
            return user.model_dump() if user else None
        
        cursor = self._sqlite_conn.cursor()
        cursor.execute("SELECT * FROM users WHERE lower(email) = ?", (email,))
        row = cursor.fetchone()
        return dict(row) if row else None

    async def get_user_by_id(self, user_id: str) -> Optional[dict[str, Any]]:
        if self.use_prisma and self.prisma_client:
            user = await self.prisma_client.user.find_unique(where={"id": user_id})
            return user.model_dump() if user else None

        cursor = self._sqlite_conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    async def create_user(
        self, email: str, password_hash: str, name: str, role: str = "ADMIN"
    ) -> dict[str, Any]:
        email = email.strip().lower()
        now_str = datetime.now(timezone.utc).isoformat()
        user_id = str(uuid.uuid4())

        if self.use_prisma and self.prisma_client:
            user = await self.prisma_client.user.create(
                data={
                    "email": email,
                    "passwordHash": password_hash,
                    "name": name,
                    "role": role,
                }
            )
            return user.model_dump()

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
        now = datetime.now(timezone.utc)
        now_str = now.isoformat()
        lead_id = str(uuid.uuid4())

        if self.use_prisma and self.prisma_client:
            lead = await self.prisma_client.callbacklead.create(
                data={
                    "fullName": full_name,
                    "phone": phone,
                    "roomType": room_type,
                    "moveInDate": move_in_date,
                    "preferredCallTime": preferred_call_time or "ASAP",
                    "requirements": requirements,
                    "status": "PENDING_CALL",
                }
            )
            return lead.model_dump()

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
                    lead_id,
                    full_name,
                    phone,
                    room_type,
                    move_in_date,
                    preferred_call_time or "ASAP",
                    requirements,
                    "PENDING_CALL",
                    "",
                    now_str,
                    now_str,
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
            "createdAt": now,
            "updatedAt": now,
        }

    async def get_leads(
        self,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        if self.use_prisma and self.prisma_client:
            where_clause: dict[str, Any] = {}
            if status and status.upper() != "ALL":
                where_clause["status"] = status
            if search:
                where_clause["OR"] = [
                    {"fullName": {"contains": search, "mode": "insensitive"}},
                    {"phone": {"contains": search}},
                ]
            leads = await self.prisma_client.callbacklead.find_many(
                where=where_clause,
                take=limit,
                skip=offset,
                order={"createdAt": "desc"},
            )
            return [lead.model_dump() for lead in leads]

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
        if self.use_prisma and self.prisma_client:
            lead = await self.prisma_client.callbacklead.find_unique(where={"id": lead_id})
            return lead.model_dump() if lead else None

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
        now = datetime.now(timezone.utc)
        now_str = now.isoformat()

        if self.use_prisma and self.prisma_client:
            data: dict[str, Any] = {}
            if status:
                data["status"] = status
            if admin_notes is not None:
                data["adminNotes"] = admin_notes
            if assigned_to_id:
                data["assignedToId"] = assigned_to_id

            lead = await self.prisma_client.callbacklead.update(
                where={"id": lead_id},
                data=data,
            )
            return lead.model_dump() if lead else None

        updates: list[str] = ["updatedAt = ?"]
        params: list[Any] = [now_str]

        if status:
            updates.append("status = ?")
            params.append(status)
        if admin_notes is not None:
            updates.append("adminNotes = ?")
            params.append(admin_notes)
        if assigned_to_id:
            updates.append("assignedToId = ?")
            params.append(assigned_to_id)

        params.append(lead_id)
        query = f"UPDATE callback_leads SET {', '.join(updates)} WHERE id = ?"

        with self._sqlite_conn:
            self._sqlite_conn.execute(query, params)

        return await self.get_lead_by_id(lead_id)

    async def delete_lead(self, lead_id: str) -> bool:
        if self.use_prisma and self.prisma_client:
            try:
                await self.prisma_client.callbacklead.delete(where={"id": lead_id})
                return True
            except Exception:
                return False

        with self._sqlite_conn:
            cursor = self._sqlite_conn.execute(
                "DELETE FROM callback_leads WHERE id = ?", (lead_id,)
            )
            return cursor.rowcount > 0

    async def get_stats(self) -> dict[str, int]:
        if self.use_prisma and self.prisma_client:
            total = await self.prisma_client.callbacklead.count()
            pending = await self.prisma_client.callbacklead.count(where={"status": "PENDING_CALL"})
            called = await self.prisma_client.callbacklead.count(where={"status": "CALLED"})
            visit = await self.prisma_client.callbacklead.count(where={"status": "VISIT_SCHEDULED"})
            booked = await self.prisma_client.callbacklead.count(where={"status": "BOOKED"})
            return {
                "total": total,
                "pendingCalls": pending,
                "called": called,
                "visitsScheduled": visit,
                "booked": booked,
            }

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
