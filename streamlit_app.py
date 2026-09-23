import io
import os
from typing import Any

import altair as alt
import pandas as pd
import requests
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(
    page_title="AegisVision",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _error_message(response: requests.Response) -> str:
    try:
        body = response.json()
        detail = body.get("detail", body)
        return f"HTTP {response.status_code}: {detail}"
    except Exception:
        return f"HTTP {response.status_code}: {response.text[:300]}"


@st.cache_data(ttl=10, show_spinner=False)
def get_json(path: str) -> tuple[Any, str | None]:
    try:
        response = requests.get(f"{API_BASE_URL}{path}", timeout=10)
        response.raise_for_status()
        return response.json(), None
    except requests.RequestException as exc:
        if getattr(exc, "response", None) is not None:
            return None, _error_message(exc.response)
        return None, str(exc)


def post_image(path: str, file_bytes: bytes, filename: str):
    try:
        response = requests.post(
            f"{API_BASE_URL}{path}",
            files={"file": (filename, file_bytes)},
            timeout=60,
        )
        response.raise_for_status()
        return response, None
    except requests.RequestException as exc:
        if getattr(exc, "response", None) is not None:
            return None, _error_message(exc.response)
        return None, str(exc)


def draw_detections(image: Image.Image, detections: list[dict]) -> Image.Image:
    """Draw API detection results on the original image in Streamlit."""
    result = image.convert("RGB").copy()
    draw = ImageDraw.Draw(result)

    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 15)
    except OSError:
        font = ImageFont.load_default()

    for detection in detections:
        bbox = detection.get("bbox", [])
        if len(bbox) != 4:
            continue

        x1, y1, x2, y2 = [int(float(v)) for v in bbox]
        class_name = detection.get("class_name", "object")
        confidence = float(detection.get("confidence", 0.0))
        label = f"{class_name} {confidence:.0%}"

        draw.rectangle((x1, y1, x2, y2), outline="red", width=3)
        left, top, right, bottom = draw.textbbox((x1, y1), label, font=font)
        label_top = max(0, y1 - (bottom - top) - 6)
        draw.rectangle((x1, label_top, right + 6, y1), fill="red")
        draw.text((x1 + 3, label_top + 2), label, fill="white", font=font)

    return result


def status_badge(status: str) -> str:
    status_map = {
        "FINISHED": "🟢 FINISHED",
        "RUNNING": "🟡 RUNNING",
        "FAILED": "🔴 FAILED",
        "KILLED": "⚫ KILLED",
    }
    return status_map.get(status, f"⚪ {status}")


st.title("🛰️ AegisVision")
st.caption("드론 객체 탐지 · FastAPI · YOLO · MLflow MLOps Dashboard")

with st.sidebar:
    st.subheader("시스템")
    st.code(API_BASE_URL, language=None)

    health, health_error = get_json("/health")
    if health_error:
        st.error("API 연결 실패")
        st.caption(health_error)
    else:
        st.success("API 정상")
        st.caption(
            "모델 로드 상태: "
            + ("정상" if health.get("model_loaded") else "미로드")
        )

    # 파일 업로더를 초기화하기 위한 key
    if "uploader_key" not in st.session_state:
        st.session_state["uploader_key"] = 0

    if st.button("🔄 데이터 새로고침", width="stretch"):
        # API 캐시 삭제
        get_json.clear()

        # 기존 탐지 결과 삭제
        st.session_state.pop("last_detection", None)
        st.session_state.pop("last_filename", None)

        # 파일 업로더 자체를 새로 생성
        st.session_state["uploader_key"] += 1

        # 화면 전체 재실행
        st.rerun()

st.divider()

tab_detect, tab_dashboard, tab_training, tab_model = st.tabs(
    ["🔍 객체 탐지", "📊 운영 대시보드", "📈 학습 이력", "⚙️ 모델 정보"]
)

with tab_detect:
    st.subheader("이미지 객체 탐지")
    st.caption("이미지를 업로드하면 FastAPI의 YOLO 모델로 탐지하고 결과를 표시합니다.")

    uploaded = st.file_uploader(
        "이미지 선택",
        type=["jpg", "jpeg", "png", "webp"],
        help="JPG, PNG, WEBP 이미지를 지원합니다.",
        key=f"uploader_{st.session_state['uploader_key']}",
    )

    if uploaded is None:
        st.info("이미지를 업로드해주세요.")
    else:
        original_bytes = uploaded.getvalue()
        original_image = Image.open(io.BytesIO(original_bytes)).convert("RGB")

        left, right = st.columns(2)

        with left:
            st.markdown("#### 원본")
            st.image(original_image, use_container_width=True)

        with right:
            st.markdown("#### 탐지 결과")

            if st.button("🚀 탐지 실행", type="primary", use_container_width=True):
                with st.spinner("YOLO 모델이 이미지를 분석하는 중..."):
                    response, error = post_image(
                        "/predict",
                        original_bytes,
                        uploaded.name,
                    )

                if error:
                    st.error(f"탐지 요청 실패: {error}")
                else:
                    st.session_state["last_detection"] = response.json()
                    st.session_state["last_filename"] = uploaded.name

            data = st.session_state.get("last_detection")

            if data and st.session_state.get("last_filename") == uploaded.name:
                detections = data.get("detections", [])
                result_image = draw_detections(original_image, detections)
                st.image(result_image, use_container_width=True)

                if detections:
                    result_df = pd.DataFrame(detections)
                    result_df["confidence"] = (
                        result_df["confidence"] * 100
                    ).round(1).astype(str) + "%"
                    result_df["bbox"] = result_df["bbox"].apply(
                        lambda box: ", ".join(f"{float(v):.1f}" for v in box)
                    )
                    st.dataframe(
                        result_df[["class_name", "confidence", "bbox"]],
                        use_container_width=True,
                        hide_index=True,
                    )
                    st.success(f"{len(detections)}개 객체 탐지")
                else:
                    st.info("탐지된 객체가 없습니다.")

                download_buffer = io.BytesIO()
                result_image.save(download_buffer, format="JPEG", quality=90)
                st.download_button(
                    "⬇️ 결과 이미지 저장",
                    data=download_buffer.getvalue(),
                    file_name=f"detected_{uploaded.name.rsplit('.', 1)[0]}.jpg",
                    mime="image/jpeg",
                    use_container_width=True,
                )
            else:
                st.info("탐지 실행 버튼을 눌러주세요.")

with tab_dashboard:
    st.subheader("API 운영 대시보드")
    metrics, error = get_json("/metrics")

    if error:
        st.error(f"운영 지표를 불러오지 못했습니다: {error}")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("총 요청", f"{metrics.get('total_requests', 0):,}")
        c2.metric("총 탐지 객체", f"{metrics.get('total_detections', 0):,}")
        c3.metric("평균 Confidence", f"{metrics.get('avg_confidence', 0):.3f}")
        c4.metric("평균 추론 시간", f"{metrics.get('avg_inference_time_ms', 0):.1f} ms")

        st.divider()
        endpoint_counts = metrics.get("requests_by_endpoint", {})

        if endpoint_counts:
            col1, col2 = st.columns([1.3, 1])
            endpoint_df = pd.DataFrame(
                [{"endpoint": endpoint, "requests": count} for endpoint, count in endpoint_counts.items()]
            )

            with col1:
                st.markdown("#### 엔드포인트별 요청")
                chart = (
                    alt.Chart(endpoint_df)
                    .mark_bar()
                    .encode(
                        x=alt.X("requests:Q", title="요청 수"),
                        y=alt.Y("endpoint:N", sort="-x", title=None),
                        tooltip=["endpoint:N", "requests:Q"],
                    )
                    .properties(height=280)
                )
                st.altair_chart(chart, use_container_width=True)

            with col2:
                st.markdown("#### 엔드포인트별 비율")
                ratio_df = endpoint_df.copy()
                ratio_df["ratio"] = (
                    ratio_df["requests"] / ratio_df["requests"].sum() * 100
                ).round(1).astype(str) + "%"
                st.dataframe(ratio_df, use_container_width=True, hide_index=True)
        else:
            st.info("아직 기록된 API 요청이 없습니다.")

with tab_training:
    st.subheader("MLflow 학습 이력")
    history, error = get_json("/model/training-history")

    if error:
        st.error(f"학습 이력을 불러오지 못했습니다: {error}")
    else:
        runs = history.get("runs", [])
        finished_count = sum(r.get("status") == "FINISHED" for r in runs)

        c1, c2, c3 = st.columns(3)
        c1.metric("학습 세션", f"{history.get('total_sessions', 0):,}")
        c2.metric("누적 완료 Epoch", f"{history.get('total_epochs', 0):,}")
        c3.metric("완료 세션", f"{finished_count:,}")
        st.divider()

        if runs:
            df = pd.DataFrame(runs)
            display_columns = [
                "run_name", "status", "epochs", "actual_epochs",
                "mAP50", "mAP50_95", "precision", "recall",
            ]
            display_columns = [c for c in display_columns if c in df.columns]
            table_df = df[display_columns].copy()

            for col in ["mAP50", "mAP50_95", "precision", "recall"]:
                if col in table_df.columns:
                    table_df[col] = table_df[col].map(
                        lambda value: f"{value:.3f}" if pd.notna(value) else "-"
                    )
            if "status" in table_df.columns:
                table_df["status"] = table_df["status"].map(status_badge)

            st.dataframe(
                table_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "run_name": "Run",
                    "status": "상태",
                    "epochs": "목표 Epoch",
                    "actual_epochs": "실제 Epoch",
                    "mAP50": "mAP50",
                    "mAP50_95": "mAP50-95",
                    "precision": "Precision",
                    "recall": "Recall",
                },
            )

            chart_df = df.dropna(subset=["mAP50"]).copy()
            if not chart_df.empty:
                st.markdown("#### Run별 mAP50")
                chart = (
                    alt.Chart(chart_df)
                    .mark_bar()
                    .encode(
                        x=alt.X("run_name:N", sort=None, title=None, axis=alt.Axis(labelAngle=-25)),
                        y=alt.Y("mAP50:Q", title="mAP50", scale=alt.Scale(domain=[0, 1])),
                        color=alt.Color("status:N", title="상태"),
                        tooltip=[
                            "run_name:N", "status:N", "mAP50:Q",
                            "precision:Q", "recall:Q",
                        ],
                    )
                    .properties(height=330)
                )
                st.altair_chart(chart, use_container_width=True)
        else:
            st.info("MLflow 학습 기록이 없습니다.")

        st.divider()
        st.markdown("### 📈 종합 학습 결과 (누적)")
        st.caption("여러 학습 세션을 하나로 이어붙인 전체 진행 추이입니다.")

        cumulative_metrics = history.get("cumulative_metrics", {})

        if not cumulative_metrics:
            st.info("종합 학습 결과 데이터가 없습니다.")
        else:
            metric_labels = {
                "mAP50": "mAP50",
                "mAP50_95": "mAP50-95",
                "precision": "Precision",
                "recall": "Recall",
            }
            available_metrics = [m for m in metric_labels if m in cumulative_metrics]

            selected = st.multiselect(
                "표시할 지표",
                options=available_metrics,
                default=[m for m in ["mAP50"] if m in available_metrics] or available_metrics[:1],
                format_func=lambda m: metric_labels.get(m, m),
            )

            frames = []
            for metric_key in selected:
                for point in cumulative_metrics.get(metric_key, []):
                    frames.append({
                        "metric": metric_labels.get(metric_key, metric_key),
                        "step": point["step"],
                        "value": point["value"],
                    })

            if frames:
                cum_df = pd.DataFrame(frames)
                chart = (
                    alt.Chart(cum_df)
                    .mark_line(point=True)
                    .encode(
                        x=alt.X("step:Q", title="누적 Epoch"),
                        y=alt.Y("value:Q", title=None, scale=alt.Scale(domain=[0, 1])),
                        color=alt.Color("metric:N", title="지표"),
                        tooltip=["metric:N", "step:Q", "value:Q"],
                    )
                    .properties(height=350)
                )
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("선택된 지표의 데이터가 없습니다.")
with tab_model:
    st.subheader("현재 서빙 모델")
    info, error = get_json("/model/info")

    if error:
        st.error(f"모델 정보를 불러오지 못했습니다: {error}")
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.metric("클래스 수", info.get("num_classes", 0))
            st.markdown("#### 모델 경로")
            st.code(info.get("model_path", "-"))
        with c2:
            st.markdown("#### 탐지 클래스")
            classes = info.get("classes", {})
            if classes:
                class_df = pd.DataFrame(
                    [{"ID": class_id, "Class": class_name} for class_id, class_name in classes.items()]
                )
                st.dataframe(class_df, use_container_width=True, hide_index=True)
            else:
                st.info("클래스 정보가 없습니다.")