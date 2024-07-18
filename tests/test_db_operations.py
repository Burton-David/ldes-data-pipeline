import pytest
from unittest import mock
from database.db_operations import DatabaseOperations
from psycopg2 import connect, extensions

class TestDatabaseOperations:

    def test_mock_path_for_fields_json(self, mocker):
        mock_connect = mocker.patch('psycopg2.connect')
        mock_cursor = mocker.patch('psycopg2.extensions.cursor')
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='{"Project name": "VARCHAR(255)"}'))
        mock_json_load = mocker.patch('json.load', return_value={"Project name": "VARCHAR(255)"})
        
        db_ops = DatabaseOperations('localhost', '5432', 'testdb', 'user', 'password')
    
        mock_connect.assert_called_once_with(
            host='localhost',
            port='5432',
            dbname='testdb',
            user='user',
            password='password'
        )
        assert db_ops.cur is not None
        assert db_ops.fields == {"Project name": "VARCHAR(255)"}

    def test_valid_fields_json(self, mocker):
        mock_connect = mocker.patch('psycopg2.connect')
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='{"Project name": "VARCHAR(255)"}'))
        mock_json_load = mocker.patch('json.load', return_value={"Project name": "VARCHAR(255)"})

        db_ops = DatabaseOperations('localhost', '5432', 'testdb', 'user', 'password')

        mock_open.assert_called_once_with(mock.ANY, 'r')
        assert db_ops.fields == {"Project name": "VARCHAR(255)"}
