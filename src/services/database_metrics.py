"""
Database metrics collector for Prometheus.
Collects PostgreSQL connection and table metrics.
"""
import logging
import time
from typing import Dict, List
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from src.models import db
from src.metrics import (
    DATABASE_CONNECTIONS_TOTAL,
    DATABASE_CONNECTIONS_ACTIVE,
    DATABASE_CONNECTIONS_IDLE,
    DATABASE_TABLE_ROWS,
    DATABASE_QUERY_DURATION,
)

logger = logging.getLogger(__name__)


class DatabaseMetricsCollector:
    """Collects database-related metrics."""

    def __init__(self):
        """Initialize the database metrics collector."""
        self.monitored_tables = [
            "users",
            "devices",
            "device_auth",
            "device_configurations",
            "device_controls",
            "device_groups",
            "group_memberships",
        ]

    def collect_all_metrics(self) -> None:
        """Collect all database metrics."""
        try:
            self.collect_connection_metrics()
            self.collect_table_metrics()
            logger.debug("Database metrics collected successfully")
        except Exception as e:
            logger.error(f"Error collecting database metrics: {e}")

    def collect_connection_metrics(self) -> None:
        """Collect database connection metrics."""
        try:
            # Get connection statistics from PostgreSQL
            connection_query = text(
                """
                SELECT 
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active_connections,
                    count(*) FILTER (WHERE state = 'idle') as idle_connections
                FROM pg_stat_activity 
                WHERE datname = current_database()
            """
            )

            start_time = time.time()
            result = db.session.execute(connection_query)
            query_duration = time.time() - start_time

            row = result.fetchone()
            if row:
                DATABASE_CONNECTIONS_TOTAL.set(row.total_connections or 0)
                DATABASE_CONNECTIONS_ACTIVE.set(row.active_connections or 0)
                DATABASE_CONNECTIONS_IDLE.set(row.idle_connections or 0)

            # Record query duration
            DATABASE_QUERY_DURATION.labels(query_type="connection_stats").observe(query_duration)

        except SQLAlchemyError as e:
            logger.error(f"Error collecting database connection metrics: {e}")
        except Exception as e:
            logger.error(f"Unexpected error collecting database connection metrics: {e}")

    def collect_table_metrics(self) -> None:
        """Collect table row count metrics."""
        try:
            for table_name in self.monitored_tables:
                try:
                    self._collect_table_row_count(table_name)
                except Exception as e:
                    logger.error(f"Error collecting metrics for table {table_name}: {e}")

        except Exception as e:
            logger.error(f"Error collecting table metrics: {e}")

    def _collect_table_row_count(self, table_name: str) -> None:
        """Collect row count for a specific table."""
        try:
            # Use approximate count for better performance on large tables
            count_query = text(
                f"""
                SELECT 
                    CASE 
                        WHEN schemaname IS NOT NULL THEN n_tup_ins - n_tup_del
                        ELSE (SELECT count(*) FROM {table_name})
                    END as row_count
                FROM pg_stat_user_tables 
                WHERE relname = :table_name
                UNION ALL
                SELECT count(*) as row_count FROM {table_name}
                LIMIT 1
            """
            )

            start_time = time.time()
            result = db.session.execute(count_query, {"table_name": table_name})
            query_duration = time.time() - start_time

            row = result.fetchone()
            if row:
                row_count = row.row_count or 0
                DATABASE_TABLE_ROWS.labels(table=table_name).set(row_count)

            # Record query duration
            DATABASE_QUERY_DURATION.labels(query_type="table_count").observe(query_duration)

        except SQLAlchemyError as e:
            logger.error(f"Error getting row count for table {table_name}: {e}")
            # Set to 0 if we can't get the count
            DATABASE_TABLE_ROWS.labels(table=table_name).set(0)

    def collect_database_size_metrics(self) -> None:
        """Collect database size metrics."""
        try:
            size_query = text(
                """
                SELECT 
                    pg_database_size(current_database()) as database_size,
                    pg_size_pretty(pg_database_size(current_database())) as database_size_pretty
            """
            )

            start_time = time.time()
            result = db.session.execute(size_query)
            query_duration = time.time() - start_time

            row = result.fetchone()
            if row:
                # Could add database size metrics here if needed
                logger.debug(f"Database size: {row.database_size_pretty}")

            DATABASE_QUERY_DURATION.labels(query_type="database_size").observe(query_duration)

        except SQLAlchemyError as e:
            logger.error(f"Error collecting database size metrics: {e}")

    def test_database_connection(self) -> bool:
        """Test database connectivity."""
        try:
            start_time = time.time()
            result = db.session.execute(text("SELECT 1"))
            query_duration = time.time() - start_time

            DATABASE_QUERY_DURATION.labels(query_type="health_check").observe(query_duration)

            return result.scalar() == 1

        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    def get_database_info(self) -> Dict:
        """Get basic database information."""
        try:
            info_query = text(
                """
                SELECT 
                    version() as version,
                    current_database() as database_name,
                    current_user as current_user,
                    inet_server_addr() as server_addr,
                    inet_server_port() as server_port
            """
            )

            result = db.session.execute(info_query)
            row = result.fetchone()

            if row:
                return {
                    "version": row.version,
                    "database_name": row.database_name,
                    "current_user": row.current_user,
                    "server_addr": row.server_addr,
                    "server_port": row.server_port,
                }

        except Exception as e:
            logger.error(f"Error getting database info: {e}")

        return {}
