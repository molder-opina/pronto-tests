import uuid
from http import HTTPStatus
import pytest
from unittest.mock import MagicMock, patch
from pronto_shared.models import DiningSession, Table, Order
from pronto_shared.services.dining_session_service import move_session_to_table

@pytest.fixture
def mock_db_session():
    """Fixture for a mocked database session."""
    db_session = MagicMock()
    
    # Mock the get method to return a specific object based on the ID
    def get_side_effect(model, obj_id):
        if model == DiningSession:
            if obj_id == uuid.UUID("00000000-0000-0000-0000-000000000001"):
                session1 = DiningSession(id=obj_id, table_id=1, table_number="T1")
                session1.orders = []
                return session1
            if obj_id == uuid.UUID("00000000-0000-0000-0000-000000000002"):
                session2 = DiningSession(id=obj_id, table_id=2, table_number="T2")
                session2.orders = []
                return session2
        if model == Table:
            if obj_id == 1:
                return Table(id=1, table_number="T1", is_active=True)
            if obj_id == 2:
                return Table(id=2, table_number="T2", is_active=True)
        return None
    
    db_session.get.side_effect = get_side_effect

    # Mock execute for other queries
    def execute_side_effect(statement):
        # For finding a table by number
        if "pronto_tables" in str(statement):
            if "T2" in str(statement):
                return MagicMock(scalars=MagicMock(first=lambda: Table(id=2, table_number="T2", is_active=True)))
        
        # For checking occupancy
        if "pronto_dining_sessions" in str(statement) and "status" in str(statement):
            # This is the check for an active session on the target table
            # In our test case, table T2 is occupied by session 2
            return MagicMock(scalars=MagicMock(first=lambda: DiningSession(id=uuid.UUID("00000000-0000-0000-0000-000000000002"))))
            
        return MagicMock(scalars=MagicMock(first=lambda: None))

    db_session.execute.side_effect = execute_side_effect
    
    return db_session

def test_move_session_to_occupied_table_fails(mock_db_session):
    """
    Test that moving a session to an occupied table returns a conflict error.
    """
    session_id_to_move = "00000000-0000-0000-0000-000000000001"
    occupied_table_number = "T2"

    with patch('pronto_shared.db.get_session') as get_session_mock:
        get_session_mock.return_value.__enter__.return_value = mock_db_session
        response, status_code = move_session_to_table(
            session_id=session_id_to_move,
            new_table_number=occupied_table_number
        )

    assert status_code == HTTPStatus.CONFLICT
    assert "ya está ocupada" in response.get("error", "")
