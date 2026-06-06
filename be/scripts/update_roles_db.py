import pymysql
import os

DATABASE_URL = "mysql+pymysql://root:123456@localhost:3306/ddk_ocr"

def run_update():
    print("Connecting to database...")
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='123456',
            database='ddk_ocr',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        sql_path = os.path.join(os.path.dirname(__file__), "update_roles.sql")
        with open(sql_path, "r", encoding="utf-8") as f:
            sql_script = f.read()
            
        statements = sql_script.split(';')
        
        with connection.cursor() as cursor:
            for stmt in statements:
                stmt = stmt.strip()
                if stmt and not stmt.startswith('--'):
                    print(f"Executing: {stmt[:50]}...")
                    cursor.execute(stmt)
            connection.commit()
            print("Roles updated successfully! The role names now match the workflow logic.")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()
            print("Connection closed.")

if __name__ == "__main__":
    run_update()
