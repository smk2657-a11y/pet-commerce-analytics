import streamlit as st
from src.style import apply_style, render_top_hero
from src.data_io import load_csv_or_sample_sidebar
from src.mapping_ui import mapping_step
from src.report_ui import report_step
from src.free_ui import free_report_step
from src.auth import login_gate, signup_form
from src.storage import init_db
from src.style_token import apply_design_tokens

st.set_page_config(
    page_title="Pet Commerce Analytics Churn & RFM Dashboard",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()
apply_style()
apply_design_tokens()
render_top_hero("Pet Commerce Analytics", "Churn & RFM Dashboard")

# -----------------------------
# Streamlit dialog 호환 처리
# -----------------------------
DIALOG = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)

# ---------------------------------
# 세션 기본값
# ---------------------------------
if "user_key" not in st.session_state:
    st.session_state["user_key"] = "guest"

if "service_mode" not in st.session_state:
    st.session_state["service_mode"] = "free"

if "pro_paid" not in st.session_state:
    st.session_state["pro_paid"] = False

# None / "login" / "signup" / "logout" / "payment"
if "modal" not in st.session_state:
    st.session_state["modal"] = None

if "step" not in st.session_state:
    st.session_state.step = 0

# ---------------------------------
# 상단 헤더 + 우상단 버튼
# ---------------------------------
top_l, top_r = st.columns([7, 2], gap="small")

with top_l:
    st.markdown(
        '<div class="h1" style="margin-top:2px;"> </div>',
        unsafe_allow_html=True,
    )

with top_r:
    if st.session_state["user_key"] != "guest":
        st.caption(f"👤 {st.session_state['user_key']}")
        if st.button("로그아웃", use_container_width=True):
            st.session_state["modal"] = "logout"
    else:
        c1, c2 = st.columns(2, gap="small")
        if c1.button("로그인", use_container_width=True):
            st.session_state["modal"] = "login"
        if c2.button("회원가입", use_container_width=True):
            st.session_state["modal"] = "signup"

modal = st.session_state.get("modal")

# ---------------------------------
# 공통 렌더 함수
# ---------------------------------
def _render_login_ui():
    authed, name, username = login_gate()

    if authed and username:
        st.session_state["user_key"] = username
        st.session_state["modal"] = None
        st.success("로그인 완료!")
        st.rerun()

    col1, col2 = st.columns(2)
    if col1.button("닫기", use_container_width=True, key="login_close_btn"):
        st.session_state["modal"] = None
        st.rerun()
    if col2.button("회원가입으로", use_container_width=True, key="login_to_signup_btn"):
        st.session_state["modal"] = "signup"
        st.rerun()


def _render_signup_ui():
    signup_form()

    if st.button("닫기", use_container_width=True, key="signup_close_btn"):
        st.session_state["modal"] = None
        st.rerun()


def _render_logout_ui():
    st.write("정말 로그아웃할까요?")
    col1, col2 = st.columns(2)
    if col1.button("취소", use_container_width=True, key="logout_cancel_btn"):
        st.session_state["modal"] = None
        st.rerun()
    if col2.button("로그아웃", type="primary", use_container_width=True, key="logout_confirm_btn"):
        st.session_state["user_key"] = "guest"
        st.session_state["modal"] = None
        st.session_state["service_mode"] = "free"
        st.session_state["pro_paid"] = False
        st.session_state.pop("analysis_saved", None)
        st.rerun()


def _render_payment_ui():
    st.markdown("### Pro 결제")
    st.caption("실제 결제는 아니며, 데모용 결제 팝업입니다.")

    with st.form("payment_form"):
        name = st.text_input("이름")
        email = st.text_input("이메일")
        card_number = st.text_input("카드번호", placeholder="1234-5678-9012-3456")
        expiry = st.text_input("유효기간", placeholder="MM/YY")
        cvc = st.text_input("CVC", placeholder="123")

        pay_ok = st.form_submit_button("결제하기", type="primary", use_container_width=True)

    if pay_ok:
        if not (name and email and card_number and expiry and cvc):
            st.error("모든 항목을 입력해주세요.")
        else:
            st.session_state["pro_paid"] = True
            st.session_state["service_mode"] = "pro"
            st.session_state["modal"] = None
            st.success("결제가 완료되었습니다. 전문가 분석 리포트를 엽니다.")
            st.rerun()

    col1, col2 = st.columns(2)
    if col1.button("취소", use_container_width=True, key="payment_cancel_btn"):
        st.session_state["modal"] = None
        st.rerun()
    if col2.button("무료버전 보기", use_container_width=True, key="payment_free_btn"):
        st.session_state["service_mode"] = "free"
        st.session_state["modal"] = None
        st.rerun()


# ---------------------------------
# dialog 지원 시: dialog 사용
# 미지원 시: 페이지 상단 패널 사용
# ---------------------------------
if DIALOG is not None:
    if modal == "login":

        @DIALOG("로그인")
        def _login_dialog():
            _render_login_ui()

        _login_dialog()

    elif modal == "signup":

        @DIALOG("회원가입")
        def _signup_dialog():
            _render_signup_ui()

        _signup_dialog()

    elif modal == "logout":

        @DIALOG("로그아웃")
        def _logout_dialog():
            _render_logout_ui()

        _logout_dialog()

    elif modal == "payment":

        @DIALOG("전문가 분석 업그레이드")
        def _payment_dialog():
            _render_payment_ui()

        _payment_dialog()

else:
    if modal in ("login", "signup", "logout", "payment"):
        st.markdown("---")
        st.markdown("### 계정" if modal != "payment" else "### 결제")

        if modal == "login":
            _render_login_ui()
        elif modal == "signup":
            _render_signup_ui()
        elif modal == "logout":
            _render_logout_ui()
        elif modal == "payment":
            _render_payment_ui()

        st.markdown("---")

st.divider()

# ---------------------------------
# 모드 선택 UI
# ---------------------------------
st.markdown("### 이용 모드 선택")

mode_col1, mode_col2 = st.columns(2)

with mode_col1:
    if st.button("🆓 무료버전 (쉬운 분석)", use_container_width=True):
        st.session_state["service_mode"] = "free"

with mode_col2:
    if st.button("⭐ 유료버전 (전문가 분석)", use_container_width=True):
        if st.session_state.get("pro_paid", False):
            st.session_state["service_mode"] = "pro"
        else:
            st.session_state["modal"] = "payment"

current_mode = "유료버전 ⭐" if st.session_state.get("service_mode") == "pro" else "무료버전 🆓"
pay_status = "✅ 결제완료" if st.session_state.get("pro_paid", False) else "미결제"

st.caption(f"현재 선택된 모드: **{current_mode}** · Pro 상태: {pay_status}")

st.divider()

# ---------------------------------
# step: 0 업로드 → 1 매핑 → 2 리포트
# ---------------------------------

# STEP 0: 업로드
if st.session_state.step == 0:
    df = load_csv_or_sample_sidebar()
    if df is None:
        st.markdown(
            """
            <div class="empty">
              <div class="icon">📄</div>
              <div class="title">데이터를 업로드해주세요</div>
              <div class="desc">좌측 사이드바에서 CSV 파일을 업로드하세요</div>
              <div class="info">
                <b>💡 이런 데이터를 분석할 수 있어요</b>
                <ul>
                  <li>고객별 구매 이력 (거래일시, 매출)</li>
                  <li>주문 정보 (주문번호, 상품, 카테고리)</li>
                  <li>채널 정보 (온/오프라인, 결제수단)</li>
                  <li>지역 정보 (시도)</li>
                </ul>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.session_state.df_raw = df
        st.session_state.step = 1
        st.rerun()

# STEP 1: 매핑/미리보기
elif st.session_state.step == 1:
    df_std = mapping_step(st.session_state.df_raw)
    if df_std is not None:
        st.session_state.df_std = df_std
        st.session_state.pop("analysis_saved", None)
        st.session_state.step = 2
        st.rerun()

# STEP 2: 리포트
else:
    if st.session_state.get("service_mode") == "free":
        free_report_step(st.session_state.df_std)
    else:
        if st.session_state.get("pro_paid", False):
            report_step(st.session_state.df_std, user_key=st.session_state["user_key"])
        else:
            st.warning("전문가 분석은 결제 후 이용할 수 있습니다.")
            if st.button("결제 팝업 열기", type="primary"):
                st.session_state["modal"] = "payment"
                st.rerun()