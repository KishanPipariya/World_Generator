from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any


class SQLiteDriver:
    def __init__(self, path: str) -> None:
        self.path = path
        db_path = Path(path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize_schema()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize_schema(self) -> None:
        with self._connect() as conn:
            initialize_sqlite_schema(conn)

    def create_user(self, values: dict[str, Any]) -> dict[str, Any]:
        return self._insert("users", values)

    def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        return self._one("SELECT * FROM users WHERE id = ?", [user_id])

    def get_user_by_username_or_email(self, username: str, email: str) -> dict[str, Any] | None:
        return self._one("SELECT * FROM users WHERE username = ? OR email = ?", [username, email])

    def user_count(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT count(*) AS count FROM users").fetchone()
            return int(row["count"]) if row else 0

    def assign_legacy_worlds(self, owner_id: str) -> int:
        with self._connect() as conn:
            cur = conn.execute("UPDATE worlds SET owner_id = ? WHERE owner_id IS NULL", [owner_id])
            return cur.rowcount

    def create_world(self, values: dict[str, Any]) -> dict[str, Any]:
        return self._insert("worlds", values)

    def get_world(self, world_id: str, owner_id: str | None = None) -> dict[str, Any] | None:
        sql = "SELECT * FROM worlds WHERE id = ?"
        params: list[Any] = [world_id]
        if owner_id is not None:
            sql += " AND owner_id = ?"
            params.append(owner_id)
        return self._one(sql, params)

    def list_worlds(self, owner_id: str | None = None) -> list[dict[str, Any]]:
        if owner_id is None:
            return self._all("SELECT * FROM worlds ORDER BY created_at DESC")
        return self._all("SELECT * FROM worlds WHERE owner_id = ? ORDER BY created_at DESC", [owner_id])

    def delete_world(self, world_id: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM worlds WHERE id = ?", [world_id])
            return cur.rowcount > 0

    def create_entity(self, values: dict[str, Any]) -> dict[str, Any] | None:
        if not self.get_world(str(values["world_id"])):
            return None
        return self._insert("entities", values)

    def get_entity(self, world_id: str, entity_id: str) -> dict[str, Any] | None:
        return self._one("SELECT * FROM entities WHERE id = ? AND world_id = ?", [entity_id, world_id])

    def list_entities(self, world_id: str, order_by: str = "entity_type ASC, name ASC") -> list[dict[str, Any]]:
        return self._all(f"SELECT * FROM entities WHERE world_id = ? ORDER BY {order_by}", [world_id])

    def update_entity(self, world_id: str, entity_id: str, values: dict[str, Any]) -> dict[str, Any] | None:
        return self._update("entities", world_id, entity_id, values)

    def delete_entity(self, world_id: str, entity_id: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM entities WHERE id = ? AND world_id = ?", [entity_id, world_id])
            return cur.rowcount > 0

    def create_relationship(self, values: dict[str, Any]) -> dict[str, Any] | None:
        world_id = str(values["world_id"])
        source = self.get_entity(world_id, str(values["source_entity_id"]))
        target = self.get_entity(world_id, str(values["target_entity_id"]))
        if not source or not target:
            return None
        self._insert("relationships", values)
        return self.get_relationship(world_id, str(values["id"]))

    def get_relationship(self, world_id: str, relationship_id: str) -> dict[str, Any] | None:
        rows = self._relationship_rows("r.world_id = ? AND r.id = ?", [world_id, relationship_id])
        return rows[0] if rows else None

    def list_relationships(self, world_id: str) -> list[dict[str, Any]]:
        return self._relationship_rows("r.world_id = ?", [world_id])

    def delete_relationship(self, world_id: str, relationship_id: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM relationships WHERE id = ? AND world_id = ?",
                [relationship_id, world_id],
            )
            return cur.rowcount > 0

    def create_world_record(self, table: str, values: dict[str, Any]) -> dict[str, Any] | None:
        if not self.get_world(str(values["world_id"])):
            return None
        return self._insert(table, values)

    def create_planning_card(self, values: dict[str, Any]) -> dict[str, Any] | None:
        if not self.get_world_record("planning_boards", str(values["world_id"]), str(values["board_id"])):
            return None
        return self._insert("planning_cards", values)

    def get_world_record(self, table: str, world_id: str, record_id: str) -> dict[str, Any] | None:
        return self._one(f"SELECT * FROM {table} WHERE id = ? AND world_id = ?", [record_id, world_id])

    def list_world_records(
        self,
        table: str,
        world_id: str,
        order_by: str,
        extra_where: str = "",
        extra_params: list[Any] | None = None,
    ) -> list[dict[str, Any]]:
        sql = f"SELECT * FROM {table} WHERE world_id = ?"
        params: list[Any] = [world_id]
        if extra_where:
            sql += f" AND {extra_where}"
            params.extend(extra_params or [])
        sql += f" ORDER BY {order_by}"
        return self._all(sql, params)

    def update_world_record(
        self, table: str, world_id: str, record_id: str, values: dict[str, Any]
    ) -> dict[str, Any] | None:
        return self._update(table, world_id, record_id, values)

    def delete_world_record(self, table: str, world_id: str, record_id: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute(f"DELETE FROM {table} WHERE id = ? AND world_id = ?", [record_id, world_id])
            return cur.rowcount > 0

    def _relationship_rows(self, where: str, params: list[Any]) -> list[dict[str, Any]]:
        return self._all(
            f"""
            SELECT r.*,
                   s.name AS source_entity_name,
                   t.name AS target_entity_name
            FROM relationships r
            JOIN entities s ON s.id = r.source_entity_id AND s.world_id = r.world_id
            JOIN entities t ON t.id = r.target_entity_id AND t.world_id = r.world_id
            WHERE {where}
            ORDER BY r.created_at DESC
            """,
            params,
        )

    def _insert(self, table: str, values: dict[str, Any]) -> dict[str, Any]:
        columns = list(values)
        placeholders = ", ".join("?" for _ in columns)
        with self._connect() as conn:
            conn.execute(
                f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
                [values[column] for column in columns],
            )
        return values

    def _update(self, table: str, world_id: str, record_id: str, values: dict[str, Any]) -> dict[str, Any] | None:
        if not values:
            return self.get_world_record(table, world_id, record_id)
        columns = list(values)
        with self._connect() as conn:
            cur = conn.execute(
                f"UPDATE {table} SET {', '.join(f'{column} = ?' for column in columns)} "
                "WHERE id = ? AND world_id = ?",
                [values[column] for column in columns] + [record_id, world_id],
            )
            if cur.rowcount == 0:
                return None
        return self.get_world_record(table, world_id, record_id)

    def _one(self, sql: str, params: list[Any] | None = None) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(sql, params or []).fetchone()
            return dict(row) if row else None

    def _all(self, sql: str, params: list[Any] | None = None) -> list[dict[str, Any]]:
        with self._connect() as conn:
            return [dict(row) for row in conn.execute(sql, params or []).fetchall()]


def initialize_sqlite_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS worlds (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            tone TEXT,
            era_notes TEXT,
            seed TEXT,
            created_at TEXT NOT NULL,
            owner_id TEXT REFERENCES users(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS entities (
            id TEXT PRIMARY KEY,
            world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            description TEXT NOT NULL,
            structured_fields_json TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS relationships (
            id TEXT PRIMARY KEY,
            world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
            source_entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
            target_entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
            relation_type TEXT NOT NULL,
            notes TEXT,
            category TEXT,
            strength INTEGER,
            history TEXT,
            stance TEXT,
            color TEXT,
            display_priority INTEGER,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS canon_issues (
            id TEXT PRIMARY KEY,
            world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
            fingerprint TEXT NOT NULL,
            code TEXT NOT NULL,
            severity TEXT NOT NULL,
            message TEXT NOT NULL,
            target_type TEXT NOT NULL,
            entity_id TEXT,
            relationship_id TEXT,
            status TEXT NOT NULL,
            note TEXT,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS canon_suggestions (
            id TEXT PRIMARY KEY,
            world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
            instruction TEXT NOT NULL,
            content TEXT NOT NULL,
            suggested_name TEXT,
            suggested_type TEXT,
            status TEXT NOT NULL,
            candidate_kind TEXT,
            source_type TEXT,
            source_id TEXT,
            source_excerpt TEXT,
            payload_json TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS timeline_events (
            id TEXT PRIMARY KEY,
            world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            event_order INTEGER NOT NULL,
            description TEXT,
            participants_json TEXT,
            causes TEXT,
            consequences TEXT,
            date_label TEXT,
            era_label TEXT,
            depends_on_json TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS graph_views (
            id TEXT PRIMARY KEY,
            world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            layout_mode TEXT NOT NULL,
            filters_json TEXT,
            camera_json TEXT,
            node_positions_json TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS planning_boards (
            id TEXT PRIMARY KEY,
            world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            board_type TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS planning_cards (
            id TEXT PRIMARY KEY,
            board_id TEXT NOT NULL REFERENCES planning_boards(id) ON DELETE CASCADE,
            world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            description TEXT,
            lane TEXT,
            position INTEGER,
            entity_links_json TEXT,
            relationship_links_json TEXT,
            timeline_event_links_json TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS campaign_sessions (
            id TEXT PRIMARY KEY,
            world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
            session_number INTEGER NOT NULL,
            title TEXT NOT NULL,
            played_date TEXT,
            in_world_date TEXT,
            recap TEXT,
            player_actions TEXT,
            consequences TEXT,
            linked_entity_ids_json TEXT,
            linked_relationship_ids_json TEXT,
            linked_timeline_event_ids_json TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS lore_notes (
            id TEXT PRIMARY KEY,
            world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            body TEXT,
            subject_type TEXT NOT NULL,
            subject_id TEXT,
            visibility TEXT NOT NULL,
            truth_state TEXT NOT NULL,
            reveal_condition TEXT,
            handout_text TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS faction_clocks (
            id TEXT PRIMARY KEY,
            world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            linked_entity_id TEXT,
            segments INTEGER NOT NULL,
            filled_segments INTEGER NOT NULL,
            stakes TEXT,
            status TEXT NOT NULL,
            linked_session_ids_json TEXT,
            linked_entity_ids_json TEXT,
            linked_relationship_ids_json TEXT,
            linked_timeline_event_ids_json TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS draft_passages (
            id TEXT PRIMARY KEY,
            world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            status TEXT NOT NULL,
            linked_entity_ids_json TEXT,
            linked_relationship_ids_json TEXT,
            linked_timeline_event_ids_json TEXT,
            check_history_json TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS revision_versions (
            id TEXT PRIMARY KEY,
            world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
            entity_id TEXT,
            subject_type TEXT NOT NULL,
            field_name TEXT NOT NULL,
            previous_value TEXT,
            new_value TEXT,
            source TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_worlds_owner ON worlds(owner_id);
        CREATE INDEX IF NOT EXISTS idx_entities_world ON entities(world_id);
        CREATE INDEX IF NOT EXISTS idx_relationships_world ON relationships(world_id);
        CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_entity_id);
        CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_entity_id);
        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_canon_issues_world ON canon_issues(world_id);
        CREATE INDEX IF NOT EXISTS idx_canon_suggestions_world ON canon_suggestions(world_id);
        CREATE INDEX IF NOT EXISTS idx_timeline_events_world ON timeline_events(world_id);
        CREATE INDEX IF NOT EXISTS idx_graph_views_world ON graph_views(world_id);
        CREATE INDEX IF NOT EXISTS idx_planning_boards_world ON planning_boards(world_id);
        CREATE INDEX IF NOT EXISTS idx_planning_cards_world ON planning_cards(world_id);
        CREATE INDEX IF NOT EXISTS idx_campaign_sessions_world ON campaign_sessions(world_id);
        CREATE INDEX IF NOT EXISTS idx_lore_notes_world ON lore_notes(world_id);
        CREATE INDEX IF NOT EXISTS idx_faction_clocks_world ON faction_clocks(world_id);
        CREATE INDEX IF NOT EXISTS idx_draft_passages_world ON draft_passages(world_id);
        CREATE INDEX IF NOT EXISTS idx_revision_versions_world ON revision_versions(world_id);
        """
    )
