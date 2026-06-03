import asyncio
import aiomysql

async def seed_db():
    with open('scripts/seed.sql', 'r', encoding='utf-8') as f:
        sql_script = f.read()

    # Tách các statement theo dấu chấm phẩy
    statements = sql_script.split(';')

    try:
        conn = await aiomysql.connect(host='localhost', port=3306, user='root', password='123456', db='ddk_ocr')
        cur = await conn.cursor()
        
        for statement in statements:
            stmt = statement.strip()
            if stmt and not stmt.startswith('SELECT') and not stmt.startswith('--'):
                # Xóa comment nếu có ở đầu
                lines = [line for line in stmt.split('\n') if not line.strip().startswith('--')]
                clean_stmt = '\n'.join(lines).strip()
                if clean_stmt:
                    try:
                        await cur.execute(clean_stmt)
                    except Exception as e:
                        print(f"Lỗi khi thực thi: {clean_stmt}\nChi tiết: {e}")
                        
        await conn.commit()
        await cur.close()
        conn.close()
        print("Database seeded successfully.")
    except Exception as e:
        print(f"Failed to seed db: {e}")

asyncio.run(seed_db())
