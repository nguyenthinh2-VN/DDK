import asyncio
import aiomysql
import sys
import os

# Thêm thư mục gốc vào sys.path để import được các module từ app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.connection import engine
from app.database.base import Base

# Import tất cả các model để SQLAlchemy đăng ký tạo bảng
from app.models import scan_batch, scan_result, user, role, permission, role_permission, signature, scan_approval

async def main():
    print("1. Đang xóa và tạo lại Database 'ddk_ocr' mới hoàn toàn...")
    try:
        conn = await aiomysql.connect(host='localhost', port=3306, user='root', password='123456')
        cur = await conn.cursor()
        await cur.execute("DROP DATABASE IF EXISTS ddk_ocr;")
        await cur.execute("CREATE DATABASE ddk_ocr CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        await cur.close()
        conn.close()
        print("   -> Xóa và tạo Database thành công.")
    except Exception as e:
        print(f"Lỗi khi tạo database: {e}")
        return

    print("\n2. Đang tạo các bảng dựa trên SQLAlchemy Models...")
    try:
        async with engine.begin() as conn:
            # Lệnh này sẽ quét toàn bộ model và tự động tạo bảng kèm ĐẦY ĐỦ CÁC CỘT MỚI
            await conn.run_sync(Base.metadata.create_all)
        print("   -> Tạo bảng thành công.")
    except Exception as e:
        print(f"Lỗi khi tạo bảng: {e}")
        return

    print("\n3. Đang chèn dữ liệu khởi tạo (seed.sql)...")
    try:
        # Đường dẫn file seed.sql (phải chạy file này ở thư mục e:\DDK\be)
        seed_path = os.path.join(os.path.dirname(__file__), 'seed.sql')
        with open(seed_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()

        conn = await aiomysql.connect(host='localhost', port=3306, user='root', password='123456', db='ddk_ocr')
        cur = await conn.cursor()
        
        statements = sql_script.split(';')
        for statement in statements:
            stmt = statement.strip()
            if stmt and not stmt.startswith('SELECT') and not stmt.startswith('--'):
                lines = [line for line in stmt.split('\n') if not line.strip().startswith('--')]
                clean_stmt = '\n'.join(lines).strip()
                if clean_stmt:
                    await cur.execute(clean_stmt)
                    
        await conn.commit()
        await cur.close()
        conn.close()
        print("   -> Chèn dữ liệu thành công.")
    except Exception as e:
        print(f"Lỗi khi chèn dữ liệu: {e}")
        return

    print("\n✅ HOÀN TẤT! Database đã sẵn sàng.")

if __name__ == "__main__":
    asyncio.run(main())
