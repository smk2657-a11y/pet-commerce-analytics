import streamlit as st


def section_header(title, desc=None, right=None):

    col1, col2 = st.columns([6,1])

    with col1:
        st.markdown(f"### {title}")

        if desc:
            st.caption(desc)

    with col2:
        if right:
            right()


def insight_box(title, bullets, tone="info"):

    colors = {
        "info":"rgba(59,130,246,0.08)",
        "warn":"rgba(245,158,11,0.08)",
        "danger":"rgba(239,68,68,0.08)",
    }

    st.markdown(
        f"""
        <div class="card-soft" style="background:{colors[tone]}">
        <b>{title}</b>
        <ul>
        {''.join([f'<li>{b}</li>' for b in bullets])}
        </ul>
        </div>
        """,
        unsafe_allow_html=True
    )


def metric_card(label, value):

    st.markdown(
        f"""
        <div class="kpi">
            <h4>{label}</h4>
            <div class="v">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def chart_card(title, fig):

    st.markdown('<div class="chart-card">', unsafe_allow_html=True)

    st.markdown(f"**{title}**")

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)