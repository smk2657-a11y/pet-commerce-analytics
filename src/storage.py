import sqlite3
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent   # 프로젝트 루트 (src의 한 단계 위)
DB_PATH = BASE_DIR / "app.db"

def get_conn():
    return sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)


# ---------------------------
# DB 초기화
# ---------------------------
def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # 1) 테이블 생성 (없으면)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS analysis_runs (
        run_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_key TEXT,
        run_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        metrics TEXT,
        report TEXT
    )
    """)

    # 2) ✅ 스키마 마이그레이션: run_name 컬럼 없으면 추가
    cols = [row[1] for row in cur.execute("PRAGMA table_info(analysis_runs)").fetchall()]
    if "run_name" not in cols:
        cur.execute("ALTER TABLE analysis_runs ADD COLUMN run_name TEXT;")

    conn.commit()
    conn.close()


# ---------------------------
# 분석 저장
# ---------------------------
def save_run(user_key, run_name, metrics, report):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO analysis_runs (user_key, run_name, metrics, report)
    VALUES (?, ?, ?, ?)
    """, (
        user_key,
        run_name,
        json.dumps(metrics),
        json.dumps(report)
    ))

    run_id = cur.lastrowid

    conn.commit()
    conn.close()

    return run_id


# ---------------------------
# 사용자 분석 목록
# ---------------------------
def list_runs(user_key: str):

    conn = get_conn()
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT run_id, run_name, created_at, metrics
        FROM analysis_runs
        WHERE user_key=?
        ORDER BY created_at DESC
    """, (user_key,)).fetchall()

    conn.close()

    result = []

    for r in rows:
        result.append({
            "run_id": r[0],
            "run_name": r[1],
            "created_at": r[2],
            "metrics": json.loads(r[3]),
        })

    return result


# ---------------------------
# 특정 분석 조회
# ---------------------------
def get_run(run_id: int):

    conn = get_conn()
    cur = conn.cursor()

    row = cur.execute("""
        SELECT run_id, run_name, created_at, metrics, report
        FROM analysis_runs
        WHERE run_id=?
    """, (run_id,)).fetchone()

    conn.close()

    if not row:
        return None

    return {
        "run_id": row[0],
        "run_name": row[1],
        "created_at": row[2],
        "metrics": json.loads(row[3]),
        "report": json.loads(row[4]),
    }
def delete_run(user_key: str, run_id: int) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        DELETE FROM analysis_runs
        WHERE run_id=? AND user_key=?
        """,
        (run_id, user_key),
    )
    deleted = cur.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

    cur.execute("""
        DELETE FROM analysis_runs
        WHERE run_id=? AND user_key=?
    """, (run_id, user_key))

    deleted = cur.rowcount > 0
    conn.commit()
    conn.close()
    return deleted