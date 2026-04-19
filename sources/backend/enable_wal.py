from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    # 启用 WAL 模式，解决 SQLite 并发锁定问题
    db.session.execute(text("PRAGMA journal_mode=WAL"))
    # 设置繁忙等待超时为 10 秒
    db.session.execute(text("PRAGMA busy_timeout=10000"))
    db.session.commit()
    print("SQLite WAL mode activated and timeout increased to 10s.")
