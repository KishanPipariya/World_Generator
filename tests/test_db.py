from __future__ import annotations

import os
from unittest.mock import MagicMock, patch
from uuid import UUID

from app.config import load_settings
from app.schemas.world import WorldCreate
from app.services.world_service import WorldService


def test_env_loading_db_credentials(tmp_path):
    env_content = """
WORLD_GENERATOR_NEO4J_URI=bolt://mock:7687
WORLD_GENERATOR_NEO4J_USER=mock_user
WORLD_GENERATOR_NEO4J_PASSWORD=mock_pass
    """
    fake_env = tmp_path / ".env"
    fake_env.write_text(env_content)

    with patch.dict(os.environ, {}, clear=True), patch("app.config.load_dotenv") as mock_dotenv:
        # We manually load the fake env to simulate dotenv behavior
        def side_effect(*args, **kwargs):
            os.environ["WORLD_GENERATOR_NEO4J_URI"] = "bolt://mock:7687"
            os.environ["WORLD_GENERATOR_NEO4J_USER"] = "mock_user"
            os.environ["WORLD_GENERATOR_NEO4J_PASSWORD"] = "mock_pass"
            
        mock_dotenv.side_effect = side_effect
        settings = load_settings()
        
        assert settings.neo4j_uri == "bolt://mock:7687"
        assert settings.neo4j_user == "mock_user"
        assert settings.neo4j_password == "mock_pass"


def test_cypher_queries_structure():
    mock_session = MagicMock()
    mock_session.run.return_value = MagicMock(single=lambda: None)
    mock_session.__enter__.return_value = mock_session
    mock_session.__exit__.return_value = None

    mock_driver = MagicMock()
    mock_driver.session.return_value = mock_session

    svc = WorldService(driver=mock_driver)
    
    # Test Create Cypher properties
    svc.create(WorldCreate(title="Cypher World", tone="bright"))
    called_queries = [call[0][0] for call in mock_session.run.call_args_list]
    
    # Validate the generated cypher string contains valid keywords
    assert any("CREATE (w:World" in query for query in called_queries)
    assert any("id: $id" in query for query in called_queries)

    # Reset mock for GET
    mock_session.run.reset_mock()
    fake_id = UUID("00000000-0000-0000-0000-000000000001")
    svc.get(fake_id)
    called_queries_get = [call[0][0] for call in mock_session.run.call_args_list]
    assert any("MATCH (w:World {id: $id})" in query for query in called_queries_get)

    # Reset mock for LIST
    mock_session.run.reset_mock()
    mock_session.run.return_value = iter([])
    svc.list_worlds()
    called_queries_list = [call[0][0] for call in mock_session.run.call_args_list]
    assert any("MATCH (w:World)" in query and "ORDER BY w.created_at DESC" in query for query in called_queries_list)
