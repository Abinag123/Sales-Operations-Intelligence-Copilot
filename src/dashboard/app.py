import os

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
from pathlib import Path

# =====================================================
# CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="Sales Intelligence | Command Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = os.environ.get("DASHBOARD_API_URL", "http://127.0.0.1:8000")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data" / "raw" / "sales_leads_raw.csv"

# =====================================================
# PROFESSIONAL DARK THEME + ANIMATIONS
# =====================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 10% 0%, #172554 0%, transparent 28%),
        radial-gradient(circle at 90% 10%, #164e63 0%, transparent 25%),
        #080d18;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #111827, #080d18);
    border-right: 1px solid #263449;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
}

.hero {
    padding: 28px;
    border-radius: 20px;
    background: linear-gradient(120deg, #172554, #164e63, #312e81);
    background-size: 200% 200%;
    animation: gradientMove 8s ease infinite, fadeIn 0.8s ease;
    border: 1px solid rgba(255,255,255,0.12);
    margin-bottom: 25px;
}

.hero h1 {
    font-size: 35px;
    font-weight: 800;
    color: white;
    margin: 0;
}

.hero p {
    color: #cbd5e1;
    margin-top: 10px;
    font-size: 15px;
}

.metric-card {
    background: linear-gradient(145deg, #172337, #101827);
    border: 1px solid #293b55;
    border-radius: 16px;
    padding: 20px;
    min-height: 125px;
    animation: fadeUp 0.7s ease both;
    transition: transform 0.25s ease, border-color 0.25s ease;
}

.metric-card:hover {
    transform: translateY(-5px);
    border-color: #38bdf8;
}

.metric-label {
    color: #94a3b8;
    font-size: 13px;
    font-weight: 600;
}

.metric-value {
    color: #f8fafc;
    font-size: 30px;
    font-weight: 800;
    margin-top: 12px;
}

.section-title {
    color: #f8fafc;
    font-size: 21px;
    font-weight: 700;
    margin-top: 20px;
}

.status-pill {
    display: inline-block;
    padding: 7px 13px;
    border-radius: 30px;
    color: #86efac;
    background: rgba(34,197,94,0.12);
    border: 1px solid rgba(34,197,94,0.35);
    font-size: 12px;
    font-weight: 700;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes fadeUp {
    from { opacity: 0; transform: translateY(18px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes gradientMove {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# DATA LOADING
# =====================================================

@st.cache_data
def load_sales_data():
    if not DATA_PATH.exists():
        return None

    df = pd.read_csv(DATA_PATH)

    required_columns = {
        "lead_source",
        "industry",
        "company_size",
        "budget",
        "website_visits",
        "emails_opened",
        "calls_made",
        "previous_interactions",
        "response_time_hours",
        "converted"
    }

    if not required_columns.issubset(df.columns):
        return None

    return df


# =====================================================
# PLOTLY THEME
# =====================================================

PLOT_LAYOUT = {
    "template": "plotly_dark",
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"color": "#dbeafe"},
    "margin": dict(l=20, r=20, t=55, b=20),
    "transition": {"duration": 500}
}


def style_chart(fig, height=350):
    fig.update_layout(**PLOT_LAYOUT)
    fig.update_layout(height=height)
    return fig


# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.markdown("## ⚡ INTELLIGENCE")
st.sidebar.caption("SALES & OPERATIONS PLATFORM")
st.sidebar.divider()

page = st.sidebar.radio(
    "NAVIGATION",
    [
        "Command Center",
        "Lead Prediction",
        "AI Knowledge Assistant"
    ]
)

st.sidebar.divider()
st.sidebar.markdown("### SYSTEM STATUS")

try:
    health = requests.get(f"{API_URL}/health", timeout=3)
    backend_status = "ONLINE" if health.status_code == 200 else "OFFLINE"
except requests.RequestException:
    backend_status = "OFFLINE"

if backend_status == "ONLINE":
    st.sidebar.markdown(
        '<span class="status-pill">● API ONLINE</span>',
        unsafe_allow_html=True
    )
else:
    st.sidebar.error("API OFFLINE")

st.sidebar.caption("ML • RAG • FastAPI • Streamlit")


# =====================================================
# COMMAND CENTER
# =====================================================

if page == "Command Center":

    # Automatic refresh every 30 seconds
    refresh_count = st_autorefresh(
        interval=30000,
        key="dashboard_refresh"
    )

    refresh_col1, refresh_col2 = st.columns([3, 1])

    with refresh_col1:
        st.caption(f"Refresh cycle: {refresh_count}")

    with refresh_col2:
        if st.button("↻ Refresh Now", width="stretch"):
            st.cache_data.clear()
            st.rerun()

    st.caption(
        "Last dashboard render: "
        + datetime.now().strftime("%d %b %Y | %I:%M:%S %p")
    )

    df = load_sales_data()
    st.markdown("""
    <div class="hero">
        <h1>⚡ SALES INTELLIGENCE</h1>
        <p>
        AI-powered command center for lead analytics,
        conversion intelligence and business knowledge.
        </p>
        <span class="status-pill">● INTELLIGENCE SYSTEM ACTIVE</span>
    </div>
    """, unsafe_allow_html=True)

    if df is None:
        st.error(
            "Dataset not found or required columns are missing. "
            "Check data/raw/sales_leads_raw.csv."
        )
        st.stop()

    # Convert target safely
    df = df.copy()
    df["converted"] = pd.to_numeric(
        df["converted"], errors="coerce"
    )
    df = df.dropna(subset=["converted"])
    df = df[df["converted"].isin([0, 1])]

    total_leads = len(df)
    converted_leads = int((df["converted"] == 1).sum())
    not_converted = int((df["converted"] == 0).sum())

    conversion_rate = (
        converted_leads / total_leads * 100
        if total_leads else 0
    )

    average_budget = df["budget"].mean()
    average_visits = df["website_visits"].mean()

    # KPI cards
    st.markdown('<div class="section-title">BUSINESS OVERVIEW</div>',
                unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)

    metrics = [
        (c1, "TOTAL LEADS", f"{total_leads:,}"),
        (c2, "CONVERTED LEADS", f"{converted_leads:,}"),
        (c3, "CONVERSION RATE", f"{conversion_rate:.2f}%"),
        (c4, "AVERAGE BUDGET", f"{average_budget:,.0f}")
    ]

    for col, label, value in metrics:
        with col:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.write("")

    # Interactive filters
    st.markdown(
        '<div class="section-title">ANALYTICS FILTERS</div>',
        unsafe_allow_html=True
    )

    f1, f2 = st.columns(2)

    with f1:
        industries = sorted(df["industry"].dropna().unique().tolist())
        selected_industries = st.multiselect(
            "Filter by Industry",
            industries,
            default=industries
        )

    with f2:
        sources = sorted(df["lead_source"].dropna().unique().tolist())
        selected_sources = st.multiselect(
            "Filter by Lead Source",
            sources,
            default=sources
        )

    filtered = df[
        df["industry"].isin(selected_industries)
        & df["lead_source"].isin(selected_sources)
    ]

    if filtered.empty:
        st.warning("No records match the selected filters.")
        st.stop()

    # Chart row 1
    st.markdown(
        '<div class="section-title">CONVERSION INTELLIGENCE</div>',
        unsafe_allow_html=True
    )

    left, right = st.columns(2)

    with left:
        source_data = (
            filtered.groupby("lead_source")["converted"]
            .mean()
            .mul(100)
            .reset_index(name="conversion_rate")
        )

        fig = px.bar(
            source_data,
            x="lead_source",
            y="conversion_rate",
            color="conversion_rate",
            color_continuous_scale="Teal",
            title="Conversion Rate by Lead Source",
            labels={
                "lead_source": "Lead Source",
                "conversion_rate": "Conversion Rate (%)"
            },
            text_auto=".1f"
        )

        fig.update_traces(
            marker_line_width=0,
            hovertemplate="%{x}<br>Conversion: %{y:.2f}%<extra></extra>"
        )

        st.plotly_chart(
            style_chart(fig),
            width="stretch"
        )

    with right:
        outcome = pd.DataFrame({
            "Outcome": ["Converted", "Not Converted"],
            "Count": [
                int((filtered["converted"] == 1).sum()),
                int((filtered["converted"] == 0).sum())
            ]
        })

        fig = px.pie(
            outcome,
            names="Outcome",
            values="Count",
            hole=0.65,
            title="Lead Conversion Distribution",
            color="Outcome",
            color_discrete_map={
                "Converted": "#22c55e",
                "Not Converted": "#64748b"
            }
        )

        fig.update_traces(
            textinfo="percent+label",
            marker=dict(line=dict(color="#0b1220", width=3))
        )

        st.plotly_chart(
            style_chart(fig),
            width="stretch"
        )

    # Chart row 2
    st.markdown(
        '<div class="section-title">LEAD BEHAVIOUR ANALYTICS</div>',
        unsafe_allow_html=True
    )

    left, right = st.columns(2)

    with left:
        fig = px.scatter(
            filtered,
            x="website_visits",
            y="budget",
            color=filtered["converted"].map({
                0: "Not Converted",
                1: "Converted"
            }),
            size="calls_made",
            hover_data=[
                "lead_source",
                "industry",
                "emails_opened",
                "response_time_hours"
            ],
            title="Website Engagement vs Budget",
            labels={
                "website_visits": "Website Visits",
                "budget": "Budget",
                "color": "Lead Outcome"
            },
            color_discrete_map={
                "Converted": "#22c55e",
                "Not Converted": "#f97316"
            }
        )

        st.plotly_chart(
            style_chart(fig),
            width="stretch"
        )

    with right:
        fig = px.histogram(
            filtered,
            x="response_time_hours",
            color=filtered["converted"].map({
                0: "Not Converted",
                1: "Converted"
            }),
            nbins=25,
            barmode="overlay",
            opacity=0.8,
            title="Lead Response Time Distribution",
            labels={
                "response_time_hours": "Response Time (Hours)",
                "color": "Lead Outcome"
            },
            color_discrete_map={
                "Converted": "#22c55e",
                "Not Converted": "#f97316"
            }
        )

        st.plotly_chart(
            style_chart(fig),
            width="stretch"
        )

    # Chart row 3
    st.markdown(
        '<div class="section-title">INDUSTRY PERFORMANCE</div>',
        unsafe_allow_html=True
    )

    industry_data = (
        filtered.groupby("industry")["converted"]
        .mean()
        .mul(100)
        .reset_index(name="conversion_rate")
        .sort_values("conversion_rate", ascending=True)
    )

    fig = px.bar(
        industry_data,
        x="conversion_rate",
        y="industry",
        orientation="h",
        color="conversion_rate",
        color_continuous_scale="Viridis",
        title="Conversion Rate by Industry",
        labels={
            "industry": "Industry",
            "conversion_rate": "Conversion Rate (%)"
        },
        text_auto=".1f"
    )

    st.plotly_chart(
        style_chart(fig, height=400),
        width="stretch"
    )

    # Dataset preview
    with st.expander("Explore filtered lead records"):
        st.dataframe(filtered, width="stretch")

    st.caption(
        "Analytics are calculated from the local sales leads dataset. "
        "They describe the dataset, not live CRM activity."
    )


# =====================================================
# LEAD PREDICTION
# =====================================================

elif page == "Lead Prediction":

    st.title("🎯 Lead Conversion Intelligence")
    st.caption("AI-powered lead scoring")

    with st.form("lead_prediction_form"):

        c1, c2, c3 = st.columns(3)

        with c1:
            lead_source = st.selectbox(
                "Lead Source",
                ["Website", "Social Media", "Advertisement", "Referral"]
            )

            industry = st.selectbox(
                "Industry",
                ["IT", "Retail", "Healthcare", "Manufacturing", "Finance"]
            )

            company_size = st.selectbox(
                "Company Size",
                ["Small", "Medium", "Large"]
            )

        with c2:
            budget = st.number_input(
                "Budget", min_value=0.0, value=50000.0
            )

            website_visits = st.number_input(
                "Website Visits", min_value=0, value=12
            )

            emails_opened = st.number_input(
                "Emails Opened", min_value=0, value=5
            )

        with c3:
            calls_made = st.number_input(
                "Calls Made", min_value=0, value=3
            )

            previous_interactions = st.number_input(
                "Previous Interactions", min_value=0, value=2
            )

            response_time_hours = st.number_input(
                "Response Time (Hours)", min_value=0.0, value=4.0
            )

        submitted = st.form_submit_button(
            "⚡ ANALYZE LEAD",
            width="stretch"
        )

    if submitted:

        lead_data = {
            "lead_source": lead_source,
            "industry": industry,
            "company_size": company_size,
            "budget": budget,
            "website_visits": website_visits,
            "emails_opened": emails_opened,
            "calls_made": calls_made,
            "previous_interactions": previous_interactions,
            "response_time_hours": response_time_hours
        }

        try:
            response = requests.post(
                f"{API_URL}/predict",
                json=lead_data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                probability = result["conversion_probability"]

                st.success("Lead analysis completed")

                a, b = st.columns(2)

                a.metric(
                    "Conversion Probability",
                    f"{probability * 100:.2f}%"
                )

                b.metric("Prediction", result["prediction"])

                fig = go.Figure(
                    go.Indicator(
                        mode="gauge+number",
                        value=probability * 100,
                        number={"suffix": "%"},
                        title={"text": "Conversion Probability"},
                        gauge={
                            "axis": {"range": [0, 100]},
                            "bar": {"color": "#38bdf8"},
                            "steps": [
                                {"range": [0, 50], "color": "#7f1d1d"},
                                {"range": [50, 75], "color": "#78350f"},
                                {"range": [75, 100], "color": "#14532d"}
                            ],
                            "threshold": {
                                "line": {"color": "white", "width": 4},
                                "thickness": 0.8,
                                "value": result["threshold"] * 100
                            }
                        }
                    )
                )

                fig.update_layout(
                    **PLOT_LAYOUT,
                    height=350
                )

                st.plotly_chart(fig, width="stretch")

                st.caption(
                    f"Classification threshold: "
                    f"{result['threshold'] * 100:.0f}%"
                )

            else:
                st.error(response.text)

        except requests.RequestException as error:
            st.error(f"Backend connection failed: {error}")


# =====================================================
# AI KNOWLEDGE ASSISTANT
# =====================================================

elif page == "AI Knowledge Assistant":

    st.title("💬 AI Knowledge Intelligence")
    st.caption("Grounded answers from company documents")

    question = st.text_area(
        "Ask your company knowledge question",
        placeholder="Example: Who approves discounts?",
        height=120
    )

    if st.button("⚡ ASK AI", width="stretch"):

        if len(question.strip()) < 3:
            st.warning("Enter a question with at least 3 characters.")

        else:
            try:
                with st.spinner("Retrieving knowledge and generating answer..."):

                    response = requests.post(
                        f"{API_URL}/ask",
                        json={"question": question},
                        timeout=180
                    )

                if response.status_code == 200:
                    result = response.json()

                    st.success("Answer generated")

                    st.markdown("### AI Answer")
                    st.write(result["answer"])

                    st.markdown("### Evidence and Citations")

                    for citation in result["citations"]:
                        with st.expander(
                            f"{citation['citation']} | "
                            f"{citation['filename']}"
                        ):
                            st.write(
                                "Chunk:",
                                citation["chunk_id"]
                            )
                            st.write(citation["supporting_text"])

                else:
                    st.error(response.text)

            except requests.RequestException as error:
                st.error(f"Backend connection failed: {error}")


# =====================================================
# FOOTER
# =====================================================

st.divider()

st.markdown(
    "<center style='color:#64748b;'>"
    "SALES & OPERATIONS INTELLIGENCE COPILOT"
    "<br>Powered by Machine Learning • RAG • FastAPI • Streamlit"
    "</center>",
    unsafe_allow_html=True
)