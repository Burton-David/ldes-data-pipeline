import psycopg2
from psycopg2.extras import DictCursor
from typing import Dict, Any
import json
from pathlib import Path

# Load fields
with open('/Users/davidburton/Sightline3/configs/fields.json', 'r') as f:
    FIELDS = json.load(f)

class DatabaseOperations:
    def __init__(self, host: str, port: str, dbname: str, user: str, password: str):
        self.conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password
        )
        self.cur = self.conn.cursor(cursor_factory=DictCursor)

        fields_path = Path(__file__).parent.parent.parent / 'configs' / 'fields.json'
        with open(fields_path, 'r') as f:
            self.fields = json.load(f)

    def create_table(self):
        columns = []
        for field, field_type in self.fields.items():
            column_name = field.lower().replace(' ', '_').replace('(', '').replace(')', '')
            if field == 'Project name':
                columns.append(f'"{column_name}" VARCHAR(255) PRIMARY KEY')
            elif 'date' in field.lower():
                columns.append(f'"{column_name}" DATE')
            elif 'capacity' in field.lower() or 'cost' in field.lower():
                columns.append(f'"{column_name}" NUMERIC')
            else:
                columns.append(f'"{column_name}" VARCHAR(255)"')

        columns_str = ", ".join(columns)
        self.cur.execute(f"""
            CREATE TABLE IF NOT EXISTS projects (
                {columns_str}
            )
        """)
        self.conn.commit()

    def insert_project(self, data: Dict[str, Any]):
        columns = ", ".join(data.keys())
        placeholders = ", ".join([f"%({key})s" for key in data.keys()])
        self.cur.execute(f"""
            INSERT INTO projects ({columns})
            VALUES ({placeholders})
            ON CONFLICT (project_name) DO UPDATE
            SET {', '.join([f"{key} = EXCLUDED.{key}" for key in data.keys() if key != 'Project name'])}
        """, data)
        self.conn.commit()

    def get_all_projects(self):
        self.cur.execute("SELECT * FROM projects")
        return self.cur.fetchall()

    def close(self):
        self.cur.close()
        self.conn.close()

if __name__ == "__main__":
    # Test the database operations
    db = DatabaseOperations(host="localhost", port="5432", dbname="ldes_data", user="ldes_user", password="password")
    db.create_table()

    test_data = {
        "Project name": "Project Alpha",
        "Energy Capacity (MWh)": "100.0",
        "Location": "California, USA",
        "Announced date": "2023-05-15",
        "Developer": "GreenEnergy Corp",
        "Technology": "Pumped hydro (PSH)",
        "Total Cost (Capex)": "50.00"
    }

    db.insert_project(test_data)

    projects = db.get_all_projects()
    for project in projects:
        print(project)

    db.close()
