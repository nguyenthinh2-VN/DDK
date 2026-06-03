import asyncio
import aiomysql

async def create_db():
    try:
        conn = await aiomysql.connect(host='localhost', port=3306, user='root', password='123456')
        cur = await conn.cursor()
        await cur.execute("CREATE DATABASE IF NOT EXISTS ddk_ocr CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        await cur.close()
        conn.close()
        print("Database 'ddk_ocr' created successfully.")
    except Exception as e:
        print(f"Failed to create db: {e}")

asyncio.run(create_db())
