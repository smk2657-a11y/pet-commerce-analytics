import streamlit as st

def apply_design_tokens():
    css = """
    <style>

    :root{
        --primary:#4F46E5;
        --primary-dark:#4338CA;

        --bg-main:#F5F7FB;
        --bg-card:#FFFFFF;
        --bg-soft:#F3F4F6;

        --text-main:#111827;
        --text-sub:rgba(0,0,0,0.65);
        --text-caption:rgba(0,0,0,0.55);

        --success:#22C55E;
        --warning:#F59E0B;
        --danger:#EF4444;

        --radius-card:18px;
        --radius-soft:12px;

        --space-section:24px;
        --space-card:18px;

        --shadow-soft:0 10px 25px rgba(0,0,0,0.06);
    }

    /* ===== 기본 배경 ===== */

    div[data-testid="stAppViewContainer"]{
        background:var(--bg-main);
    }

    /* ===== 타이포 ===== */

    .h1{
        font-size:42px;
        font-weight:900;
        letter-spacing:-0.03em;
        color:var(--text-main);
    }

    .sub{
        font-size:14px;
        color:var(--text-sub);
        margin-bottom:var(--space-section);
    }

    h3{
        margin-top:var(--space-section);
        margin-bottom:12px;
    }

    /* ===== 카드 ===== */

    .card{
        background:var(--bg-card);
        border-radius:var(--radius-card);
        padding:var(--space-card);
        box-shadow:var(--shadow-soft);
        border:1px solid rgba(0,0,0,0.05);
        margin-bottom:16px;
    }

    .card-soft{
        background:var(--bg-soft);
        border-radius:var(--radius-soft);
        padding:14px 16px;
    }

    /* ===== KPI GRID ===== */

    .kpi-grid{
        display:grid;
        grid-template-columns:repeat(3,1fr);
        gap:14px;
        margin-bottom:18px;
    }

    .kpi{
        background:white;
        border-radius:var(--radius-card);
        padding:18px;
        border:1px solid rgba(0,0,0,0.06);
        box-shadow:var(--shadow-soft);
    }

    .kpi h4{
        font-size:13px;
        color:var(--text-caption);
        margin-bottom:6px;
    }

    .kpi .v{
        font-size:38px;
        font-weight:900;
        letter-spacing:-0.02em;
    }

    /* ===== alert ===== */

    .alert{
        border-radius:var(--radius-card);
        padding:16px;
        background:rgba(239,68,68,0.08);
        border:1px solid rgba(239,68,68,0.18);
        margin-top:12px;
    }

    /* ===== plotly chart wrapper ===== */

    .chart-card{
        background:white;
        border-radius:var(--radius-card);
        border:1px solid rgba(0,0,0,0.06);
        padding:16px;
        box-shadow:var(--shadow-soft);
        margin-bottom:18px;
    }

    /* ===== dataframe spacing ===== */

    div[data-testid="stDataFrame"]{
        border-radius:var(--radius-card);
        border:1px solid rgba(0,0,0,0.06);
        overflow:hidden;
    }

    </style>
    """
    st.markdown(css, unsafe_allow_html=True)