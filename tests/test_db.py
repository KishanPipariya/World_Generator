from __future__ import annotations

import os
from unittest.mock import patch

from app.config import load_settings


def test_env_loading_sqlite_path(tmp_path):
    env_content = """
WORLD_GENERATOR_SQLITE_PATH=/tmp/world-generator-test.sqlite3
    """
    fake_env = tmp_path / ".env"
    fake_env.write_text(env_content)

    with patch.dict(os.environ, {}, clear=True), patch("app.config.load_dotenv") as mock_dotenv:
        # We manually load the fake env to simulate dotenv behavior
        def side_effect(*args, **kwargs):
            os.environ["WORLD_GENERATOR_SQLITE_PATH"] = "/tmp/world-generator-test.sqlite3"
            
        mock_dotenv.side_effect = side_effect
        settings = load_settings()
        
        assert settings.sqlite_path == "/tmp/world-generator-test.sqlite3"
