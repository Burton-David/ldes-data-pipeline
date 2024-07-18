from src.database.db_operations import DatabaseOperations
db = DatabaseOperations(host="localhost", port="5432", dbname="ldes_data", user="ldes_user", password="password")
results = db.get_all_projects()
for row in results:
    print(row)
db.close()