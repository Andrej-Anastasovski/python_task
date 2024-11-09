import pytest
import sys
import os
import io
import logging
from werkzeug.datastructures import FileStorage

# Setup logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Adding app's directory to path for import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importing necessary modules
from app import create_app
from db import init_db, clear_db, drop_db


@pytest.fixture
def app():
    """Fixture for setting up and tearing down the app context and database."""
    app = create_app({'TESTING': True, 'DATABASE': 'test.db'})
    with app.app_context():
        drop_db(app.config['DATABASE']) 
        init_db(app.config['DATABASE'])
        yield app
        clear_db(app.config['DATABASE'])


@pytest.fixture
def client(app):
    """Fixture to provide a test client."""
    return app.test_client()


def test_compute_authorization(client):
    """Test for handling authorization errors."""
    response = client.post('/api/compute', headers={'Authorization': 'wrong_passphrase'})
    assert response.status_code == 401
    assert response.get_json() == {"error": "Unauthorized"}


def test_compute_no_file(client):
    """Test for missing file in request."""
    response = client.post('/api/compute', headers={'Authorization': 'Qz5!r9P#3uVl'})
    assert response.status_code == 400
    assert response.get_json() == {"error": "No file part"}


def test_compute_invalid_file_type(client):
    """Test for invalid file type in request."""
    file_data = io.BytesIO(b"A,O,B\n1,+,2\n3,*,4")
    file_storage = FileStorage(stream=file_data, filename='test.txt', content_type='text/plain')

    response = client.post('/api/compute', headers={'Authorization': 'Qz5!r9P#3uVl'}, data={'file': file_storage})
    assert response.status_code == 400
    assert response.get_json() == {'error': 'File type not allowed, must be CSV'}


def test_compute_invalid_csv_structure(client):
    """Test for invalid CSV structure."""
    file_data = io.BytesIO(b"X,Y,Z\n1,+,2\n3,-,4\n")
    file_storage = FileStorage(stream=file_data, filename='test.csv', content_type='text/csv')

    response = client.post('/api/compute', headers={'Authorization': 'Qz5!r9P#3uVl'}, data={'file': file_storage})
    assert response.status_code == 400
    assert response.get_json() == {"error": "Invalid CSV structure, must contain columns A, O, B"}


def test_compute_columns_are_not_numeric(client):
    """Test for non-numeric values in columns A and B."""
    file_data = io.BytesIO(b"A,O,B\none,+,2\n3,-,four\n")
    file_storage = FileStorage(stream=file_data, filename='test.csv', content_type='text/csv')

    response = client.post('/api/compute', headers={'Authorization': 'Qz5!r9P#3uVl'}, data={'file': file_storage})
    assert response.status_code == 400
    assert response.get_json() == {"error": "Columns A and B must contain numeric values"}


def test_compute_valid_calculation(client):
    """Test for valid computation of results."""
    data = {
        'file': (io.BytesIO(b'A,O,B\n1,+,2\n3,*,4\n5,-,6\n8,/,4\n'), 'test.csv')
    }
    response = client.post('/api/compute', headers={'Authorization': 'Qz5!r9P#3uVl'}, content_type='multipart/form-data', data=data)
    assert response.status_code == 200
    assert response.get_json() == {"message": "File processed successfully", "result": 16.0}


def test_compute_division_by_zero(client):
    """Test for handling division by zero errors."""
    file_data = io.BytesIO(b"A,O,B\n1,+,2\n3,-,4\n5,/,0\n")
    file_storage = FileStorage(stream=file_data, filename='test.csv', content_type='text/csv')

    logger.debug("Sending request to /api/compute with division by zero test case")
    response = client.post('/api/compute', headers={'Authorization': 'Qz5!r9P#3uVl'}, data={'file': file_storage})

    logger.debug(f"Response: {response.status_code}, Body: {response.get_json()}")
    
    assert response.status_code == 400
    assert response.get_json() == {"error": "Division by zero"}
