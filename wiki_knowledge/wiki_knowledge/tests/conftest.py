# -*- coding: utf-8 -*-
"""
Wiki 知识库测试配置

添加 AIBackend 到 sys.path 以便导入 common 模块。
连接真实 MySQL 数据库进行测试。
"""

from pathlib import Path

# 计算 AIBackend 根目录路径
# conftest.py → tests(1) → wiki_knowledge(2) → service(3) → app(4) → rag-pipeline-service(5) → AIBackend(6)
ROOT_DIR = Path(__file__).parent.parent.parent.parent.parent.parent

import sys  # noqa: E402

sys.path.insert(0, str(ROOT_DIR))

import pytest  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402


# MySQL 数据库连接配置
MYSQL_CONFIG = {
    "host": "",
    "port": 3306,
    "user": "",
    "password": "",
    "database": "i",
}


@pytest.fixture
def engine():
    """创建测试用数据库引擎（连接真实 MySQL）"""
    url = (
        f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}"
        f"@{MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{MYSQL_CONFIG['database']}"
    )
    engine = create_engine(url, pool_pre_ping=True, pool_recycle=300, echo=False)
    yield engine


@pytest.fixture
def db_session(engine):
    """创建测试用数据库会话"""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
