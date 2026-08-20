"""
Database connection module for CognoDB (Neo4j-compatible).
Connection details are read exclusively from environment variables.
"""

import os
from contextlib import contextmanager
from typing import Generator, Optional

from neo4j import GraphDatabase, Driver, Session
from dotenv import load_dotenv

load_dotenv()

_driver: Optional[Driver] = None


def get_driver() -> Driver:
    """Return a singleton Neo4j/CognoDB driver."""
    global _driver
    if _driver is None:
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER", "cognodb")
        password = os.getenv("NEO4J_PASSWORD")

        if not uri or not password:
            raise RuntimeError(
                "NEO4J_URI and NEO4J_PASSWORD must be set in environment variables. "
                "Copy .env.example to .env and fill in your CognoDB credentials."
            )

        _driver = GraphDatabase.driver(uri, auth=(user, password))
    return _driver


def close_driver() -> None:
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Context manager that yields a session and guarantees cleanup."""
    driver = get_driver()
    session = driver.session()
    try:
        yield session
    finally:
        session.close()


def verify_connectivity() -> bool:
    """Return True if the database is reachable."""
    try:
        driver = get_driver()
        driver.verify_connectivity()
        return True
    except Exception:
        return False
