import logging
from typing import Optional, Dict
from app.models import Integration, IntegrationCreate
from app.repositories.database_repository import Database


class IntegrationsService:
    def __init__(self, database: Database):
        self.database = database
        self.logger = logging.getLogger(__name__)

    def save_integration(self, user_id: int, integration: IntegrationCreate) -> Integration:
        try:
            cursor = self.database.cursor
            assert cursor is not None

            # Check if integration already exists for this user and type
            cursor.execute(
                "SELECT id FROM integrations WHERE user_id = ? AND integration_type = ?",
                (user_id, integration.integration_type)
            )
            existing = cursor.fetchone()

            if existing:
                # Update existing
                cursor.execute(
                    "UPDATE integrations SET token_value = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (integration.token_value, existing[0])
                )
                integration_id = existing[0]
            else:
                # Insert new
                cursor.execute(
                    "INSERT INTO integrations (user_id, integration_type, token_value) VALUES (?, ?, ?)",
                    (user_id, integration.integration_type, integration.token_value)
                )
                integration_id = cursor.lastrowid

            self.database.commit()

            # Return the integration
            return self.get_integration_by_id(integration_id)
        except Exception as e:
            self.logger.exception(f"Error saving integration for user {user_id}: {e}")
            raise Exception("Failed to save integration") from e

    def get_user_integrations(self, user_id: int) -> Dict[str, str]:
        try:
            cursor = self.database.cursor
            assert cursor is not None
            cursor.execute(
                "SELECT integration_type, token_value FROM integrations WHERE user_id = ?",
                (user_id,)
            )
            rows = cursor.fetchall()
            return {row[0]: row[1] for row in rows}
        except Exception as e:
            self.logger.exception(f"Error getting integrations for user {user_id}: {e}")
            raise Exception("Failed to get integrations") from e

    def get_integration_by_id(self, integration_id: int) -> Optional[Integration]:
        try:
            cursor = self.database.cursor
            assert cursor is not None
            cursor.execute(
                "SELECT id, user_id, integration_type, token_value, created_at, updated_at FROM integrations WHERE id = ?",
                (integration_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return Integration(
                id=row[0],
                user_id=row[1],
                integration_type=row[2],
                token_value=row[3],
                created_at=row[4],
                updated_at=row[5]
            )
        except Exception as e:
            self.logger.exception(f"Error getting integration {integration_id}: {e}")
            raise Exception("Failed to get integration") from e

    def get_integrations_by_type(self, integration_type: str) -> list[Dict[str, any]]:
        try:
            cursor = self.database.cursor
            assert cursor is not None
            cursor.execute(
                "SELECT user_id, token_value FROM integrations WHERE integration_type = ?",
                (integration_type,)
            )
            rows = cursor.fetchall()
            return [{"user_id": row[0], "token_value": row[1]} for row in rows]
        except Exception as e:
            self.logger.exception(f"Error getting integrations by type {integration_type}: {e}")
            raise Exception("Failed to get integrations by type") from e
