import os
import io
import requests
import streamlit as st
import pandas as pd
import altair as alt

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(
    page_title="AegisVision | Drone Detection",
    page_icon="🛰️",
    layout="wide",
)

# ---------------------------------------------------------------------------
# 스타일
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
        .main { background-color: #0e1117; }
        .metric-card {
            background: #161b22;
            border: 1px solid #262c36;
            border-radius: 12px;
            padding: 1.2rem 1.4rem;
        }
        .status-dot {
            height: 10px;
            width: 10px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }
        .status-ok { background-color: #3fb950; }
        .status-bad { background-color: #f85149; }
        h1, h2, h3 { letter-spacing: -0.02em; }
        .stTabs [data-baseweb="tab-list"] { gap: 4px; }
        .metric-card, .metric-card b, .metric-card div {
            color: #e6edf3 !important;
        }
        .metric-card b {
            color: #8ab4f8 !important;
            font-weight: 600;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def api_get(path: str, **kwargs):
    try:
        res = requests.get(f"{API_BASE_URL}{path}", timeout=10, **kwargs)
        res.raise_for_status()
        return res.json(), None
    except Exception as e:
        return None, str(e)


def api_post_file(path: str, file_bytes: bytes, filename: str):
    try:
        files = {"file": (filename, file_bytes, "image/jpeg")}
        res = requests.post(f"{API_BASE_URL}{path}", files=files, timeout=30)
        res.raise_for_status()
        return res, None
    except Exception as e:
        return None, str(e)


# ---------------------------------------------------------------------------
# 헤더 + 상태
# ---------------------------------------------------------------------------
header_col, status_col = st.columns([3, 1])

with header_col:
    st.title("🛰️ AegisVision")
    st.caption("드론 탐지 MLOps 대시보드")

with status_col:
    health, err = api_get("/health")
    st.markdown("<br>", unsafe_allow_html=True)
    if health and health.get("status") == "ok":
        st.markdown(
            '<span class="status-dot status-ok"></span>**서버 정상**',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="status-dot status-bad"></span>**서버 연결 실패**',
            unsafe_allow_html=True,
        )

st.divider()

# ---------------------------------------------------------------------------
# 탭 구성
# ---------------------------------------------------------------------------
tab_detect, tab_metrics, tab_training, tab_model = st.tabs(
    ["🔍 탐지", "📊 운영 지표", "📈 학습 이력", "⚙️ 모델 정보"]
)

# --- 탐지 탭 ---------------------------------------------------------------
with tab_detect:
    left, right = st.columns([1, 1])

    with left:
        st.subheader("이미지 업로드")
        uploaded = st.file_uploader(
            "드론이 있을 것으로 예상되는 이미지를 올려주세요",
            type=["jpg", "jpeg", "png"],
        )
        if uploaded:
            st.image(uploaded, caption="원본 이미지", use_container_width=True)
            run = st.button("탐지 실행", type="primary", use_container_width=True)
        else:
            run = False

    with right:
        st.subheader("탐지 결과")
        if uploaded and run:
            file_bytes = uploaded.getvalue()

            with st.spinner("모델이 이미지를 분석하는 중..."):
                res, err = api_post_file("/predict/visualize", file_bytes, uploaded.name)

            if err:
                st.error(f"요청 실패: {err}")
            else:
                st.image(res.content, caption="탐지 결과", use_container_width=True)

                detail, err2 = api_post_file("/predict", file_bytes, uploaded.name)
                if detail is not None and not err2:
                    data = detail.json()
                    detections = data.get("detections", [])
                    if detections:
                        df = pd.DataFrame(detections)
                        df["confidence"] = (df["confidence"] * 100).round(1).astype(str) + "%"
                        st.dataframe(df, use_container_width=True, hide_index=True)
                    else:
                        st.info("탐지된 객체가 없습니다.")
        else:
            st.info("왼쪽에서 이미지를 올리고 '탐지 실행'을 눌러주세요.")

# --- 운영 지표 탭 ------------------------------------------------------------
with tab_metrics:
    st.subheader("API 운영 지표")

    metrics, err = api_get("/metrics")
    if err:
        st.error(f"지표를 불러오지 못했습니다: {err}")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("총 요청 수", metrics.get("total_requests", 0))
        c2.metric("총 탐지 수", metrics.get("total_detections", 0))
        c3.metric("평균 confidence", f"{metrics.get('avg_confidence', 0):.2f}")
        c4.metric("평균 추론 시간", f"{metrics.get('avg_inference_time_ms', 0):.0f} ms")

        st.markdown("#### 엔드포인트별 호출 수")
        by_endpoint = metrics.get("requests_by_endpoint", {})
        if by_endpoint:
            df = pd.DataFrame(
                {"endpoint": list(by_endpoint.keys()), "count": list(by_endpoint.values())}
            )
            chart = (
                alt.Chart(df)
                .mark_bar(color="#1f77b4")
                .encode(
                    x=alt.X("endpoint", sort=None, axis=alt.Axis(labelAngle=0, title=None)),
                    y=alt.Y("count", title=None),
                )
                .properties(height=300)
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("아직 기록된 요청이 없습니다.")

# --- 학습 이력 탭 ------------------------------------------------------------
with tab_training:
    st.subheader("학습 세션 이력")

    history, err = api_get("/model/training-history")
    if err:
        st.error(f"학습 이력을 불러오지 못했습니다: {err}")
    else:
        c1, c2 = st.columns(2)
        c1.metric("총 학습 세션", history.get("total_sessions", 0))
        c2.metric("누적 완료 epoch", history.get("total_epochs", 0))

        runs = history.get("runs", [])
        if runs:
            df = pd.DataFrame(runs)
            df = df[["run_name", "status", "actual_epochs", "mAP50", "mAP50_95", "precision", "recall"]]
            st.dataframe(df, use_container_width=True, hide_index=True)

            chart_df = pd.DataFrame(runs).dropna(subset=["mAP50"])
            if not chart_df.empty:
                st.markdown("#### 세션별 mAP50 추이")
                chart = (
                    alt.Chart(chart_df)
                    .mark_line(point=True, color="#1f77b4")
                    .encode(
                        x=alt.X("run_name", sort=None, axis=alt.Axis(labelAngle=0, title=None)),
                        y=alt.Y("mAP50", title=None, scale=alt.Scale(domain=[0, 1])),
                    )
                    .properties(height=300)
                )
                st.altair_chart(chart, use_container_width=True)
        else:
            st.info("학습 기록이 없습니다.")

# --- 모델 정보 탭 ------------------------------------------------------------
with tab_model:
    st.subheader("현재 서빙 중인 모델")

    info, err = api_get("/model/info")
    if err:
        st.error(f"모델 정보를 불러오지 못했습니다: {err}")
    else:
        st.markdown(
            f"""
            <div class="metric-card">
                <b>모델 경로</b><br>{info.get('model_path')}<br><br>
                <b>클래스 수</b><br>{info.get('num_classes')}<br><br>
                <b>클래스 목록</b><br>{", ".join(info.get('classes', {}).values())}
            </div>
            """,
            unsafe_allow_html=True,
        )
