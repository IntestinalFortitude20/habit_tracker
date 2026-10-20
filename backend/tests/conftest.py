import os
import tempfile
from pathlib import Path

import pytest

_TMP_DIR = Path(tempfile.mkdtemp(prefix="habit_tracker_tests_"))
os.environ["DATABASE_URL"] = f"sqlite:///{(_TMP_DIR / 'test_habits.db').as_posix()}"

from app.core.config import settings  # noqa: E402
from app.db.session import Base, engine  # noqa: E402

DEV_DB_NAME = "habit_tracker.db"


def _assert_not_dev_database() -> None:
    url = settings.database_url
    if not url.startswith("sqlite") or Path(url.split("///", 1)[-1]).name == DEV_DB_NAME:
        pytest.exit(
            f"Refusing to run tests: DATABASE_URL ({url!r}) is not an isolated test database "
            f"(must be a sqlite file other than {DEV_DB_NAME}).",
            returncode=2,
        )


def pytest_sessionstart(session):
    _assert_not_dev_database()


@pytest.fixture(scope="session", autouse=True)
def _cleanup_test_databases():
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    for path in list(_TMP_DIR.glob("test_*.db")) + list(Path.cwd().glob("test_*.db")):
        path.unlink(missing_ok=True)
    if not any(_TMP_DIR.iterdir()):
        _TMP_DIR.rmdir()
