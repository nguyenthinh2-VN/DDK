import pymysql

DATABASE_URL = "mysql+pymysql://root:root@localhost:3306/ddk_ocr"

def fix_db():
    print("Connecting to database...")
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='123456',
            database='ddk_ocr',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            # 1. Check if column exists
            cursor.execute("""
                SELECT COUNT(*) as cnt
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = 'ddk_ocr' 
                  AND TABLE_NAME = 'scan_results' 
                  AND COLUMN_NAME = 'workflow_status'
            """)
            result = cursor.fetchone()
            if result['cnt'] == 0:
                print("Adding 'workflow_status' and 'current_assignee_role' columns...")
                cursor.execute("""
                    ALTER TABLE scan_results
                    ADD COLUMN workflow_status VARCHAR(50) DEFAULT 'DRAFT' COMMENT 'DRAFT | PENDING_KE_TOAN | PENDING_THU_QUY | PENDING_CEO | COMPLETED | REJECTED',
                    ADD COLUMN current_assignee_role VARCHAR(50) NULL COMMENT 'Role đang chờ duyệt'
                """)
                connection.commit()
                print("Columns added successfully!")
            else:
                print("Columns already exist!")
                
            # 2. Check if scan_approvals table exists
            cursor.execute("""
                SELECT COUNT(*) as cnt
                FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = 'ddk_ocr' 
                  AND TABLE_NAME = 'scan_approvals'
            """)
            result = cursor.fetchone()
            if result['cnt'] == 0:
                print("Creating 'scan_approvals' table...")
                cursor.execute("""
                    CREATE TABLE scan_approvals (
                        id VARCHAR(36) PRIMARY KEY,
                        scan_result_id VARCHAR(36) NOT NULL,
                        user_id VARCHAR(36) NOT NULL,
                        role VARCHAR(50) NOT NULL COMMENT 'Role lúc duyệt (e.g. KE_TOAN, THU_QUY)',
                        action VARCHAR(20) NOT NULL COMMENT 'APPROVED | REJECTED',
                        note VARCHAR(500) NULL COMMENT 'Lý do reject (nếu có)',
                        signature_id VARCHAR(36) NULL COMMENT 'Chữ ký đã dùng để duyệt',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT fk_scan_approval_scan FOREIGN KEY (scan_result_id) REFERENCES scan_results(id) ON DELETE CASCADE,
                        CONSTRAINT fk_scan_approval_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                """)
                connection.commit()
                print("Table created successfully!")
            else:
                print("Table 'scan_approvals' already exists!")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()
            print("Connection closed.")

if __name__ == "__main__":
    fix_db()
