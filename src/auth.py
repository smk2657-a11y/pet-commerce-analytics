from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st
import yaml

# bcrypt는 비밀번호 검증에 사용 (requirements.txt에 bcrypt 추가 권장)
import bcrypt  # type: ignore

# 프로젝트 루트의 users.yaml (app.py 옆)
USERS_FILE = Path(__file__).resolve().parents[1] / "users.yaml"

DEFAULT_USERS_YAML = {
    "credentials": {"usernames": {}},
    "cookie": {
        "name": "myapp_auth",
        "key": "CHANGE_THIS_TO_A_RANDOM_SECRET_KEY",
        "expiry_days": 30,
    },
    "preauthorized": {"emails": []},
}


def _ensure_users_file_exists() -> None:
    if USERS_FILE.exists():
        return
    USERS_FILE.write_text(
        yaml.safe_dump(DEFAULT_USERS_YAML, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _load_users() -> dict[str, Any]:
    _ensure_users_file_exists()
    with USERS_FILE.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    data.setdefault("credentials", {})
    data["credentials"].setdefault("usernames", {})
    return data


def _save_users(data: dict[str, Any]) -> None:
    with USERS_FILE.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


def _hash_password(password: str) -> str:
    # bcrypt 해시 문자열로 저장
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def signup_form() -> None:
    st.subheader("회원가입")

    with st.form("signup_form"):
        name = st.text_input("이름")
        username = st.text_input("아이디(로그인에 사용)")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        password2 = st.text_input("비밀번호 확인", type="password")
        ok = st.form_submit_button("가입하기", type="primary", use_container_width=True)

    if not ok:
        return

    if not (name and username and email and password and password2):
        st.error("모든 항목을 입력해주세요.")
        return
    if password != password2:
        st.error("비밀번호가 일치하지 않습니다.")
        return

    data = _load_users()
    users = data["credentials"]["usernames"]

    if username in users:
        st.error("이미 존재하는 아이디입니다.")
        return

    # 이메일 중복 체크
    for u in users.values():
        if (u.get("email") or "").lower() == email.lower():
            st.error("이미 사용 중인 이메일입니다.")
            return

    hashed_pw = _hash_password(password)
    users[username] = {"name": name, "email": email, "password": hashed_pw}
    _save_users(data)

    st.success("가입 완료! 이제 로그인해 주세요.")


def login_gate() -> tuple[bool, str | None, str | None]:
    """
    ✅ streamlit-authenticator UI를 쓰지 않고 직접 로그인 폼을 렌더링합니다.
    st.dialog() 안에서도 안정적으로 동작합니다.

    return: (authed, name, username)
    """
    st.caption("비회원(게스트)로도 이용할 수 있어요. 로그인하면 분석 기록이 저장됩니다.")

    with st.form("login_form"):
        username = st.text_input("아이디", placeholder="예: gildong")
        password = st.text_input("비밀번호", type="password")
        ok = st.form_submit_button("로그인", type="primary", use_container_width=True)

    if not ok:
        return False, None, None

    data = _load_users()
    users = data["credentials"]["usernames"]

    user = users.get(username)
    if not user:
        st.error("아이디 또는 비밀번호가 올바르지 않습니다.")
        return False, None, None

    hashed = user.get("password") or ""
    if not _verify_password(password, hashed):
        st.error("아이디 또는 비밀번호가 올바르지 않습니다.")
        return False, None, None

    name = user.get("name") or username
    return True, name, username