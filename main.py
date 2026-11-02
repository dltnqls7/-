import streamlit as st
import pandas as pd

# ---------------------------------
# 1. 기본 설정
# ---------------------------------
st.set_page_config(
    page_title="결측치와 이상치 확인",
    page_icon="🔎",
    layout="wide"
)

st.title("🔎 데이터 결측치와 이상치 확인")
st.write(
    "운동 강도(MET)와 심박수 분석에 사용하는 데이터에서 "
    "비어 있는 값과 다른 값에 비해 차이가 큰 데이터를 확인합니다."
)

# ---------------------------------
# 2. 데이터 불러오기
# ---------------------------------
DATA_URL = (
    "https://raw.githubusercontent.com/dltnqls7/"
    "dsproject__/refs/heads/main/subject101_preprocessed.csv"
)

@st.cache_data
def load_data():
    return pd.read_csv(DATA_URL)

try:
    df = load_data()
except Exception as e:
    st.error("데이터를 불러오지 못했습니다.")
    st.write("GitHub의 CSV 주소와 파일 공개 설정을 확인해 주세요.")
    st.stop()

# 원본 데이터 보관
original_df = df.copy()

# ---------------------------------
# 3. 데이터 개요
# ---------------------------------
st.header("1. 데이터 개요")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("전체 행 개수", f"{len(original_df):,}개")

with col2:
    st.metric("전체 열 개수", f"{len(original_df.columns):,}개")

with col3:
    st.metric(
        "전체 결측치 개수",
        f"{int(original_df.isna().sum().sum()):,}개"
    )

st.subheader("각 열의 자료형과 결측치 개수")

overview = pd.DataFrame({
    "열 이름": original_df.columns,
    "자료형": original_df.dtypes.astype(str).values,
    "결측치 개수": original_df.isna().sum().values
})

st.dataframe(overview, use_container_width=True)

# ---------------------------------
# 4. 결측치 그래프
# ---------------------------------
st.header("2. 결측치 확인")

missing_counts = original_df.isna().sum()

st.bar_chart(
    missing_counts,
    x_label="열 이름",
    y_label="결측치 개수"
)

total_missing = int(missing_counts.sum())

if total_missing == 0:
    st.success("현재 데이터에서 결측치가 발견되지 않았습니다.")
else:
    st.warning(
        f"현재 데이터에서 결측치 {total_missing:,}개가 발견되었습니다."
    )

st.caption(
    "그래프의 막대가 높을수록 해당 열에 비어 있는 값이 많다는 뜻입니다."
)

# ---------------------------------
# 5. 결측치 처리 전후 비교
# ---------------------------------
st.header("3. 결측치 처리 전후 비교")

before_rows = len(original_df)

# 분석에 꼭 필요한 값이 없는 행만 제외
required_columns = [
    col for col in
    ["time_seconds", "activity_name", "heart_rate_bpm"]
    if col in original_df.columns
]

clean_df = original_df.dropna(subset=required_columns).copy()

after_rows = len(clean_df)
removed_rows = before_rows - after_rows

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("처리 전 행 수", f"{before_rows:,}개")

with col2:
    st.metric("처리 후 행 수", f"{after_rows:,}개")

with col3:
    st.metric("제외한 행 수", f"{removed_rows:,}개")

st.write(
    "처리 방법: 시간, 활동 종류, 심박수 중 하나라도 비어 있는 행을 제외합니다."
)

if removed_rows == 0:
    st.info("필수 항목에 결측치가 없어 제외된 행이 없습니다.")

# ---------------------------------
# 6. 이상치 확인 방법 안내
# ---------------------------------
st.header("4. 이상치 확인")

st.write(
    "이상치는 다른 데이터와 비교했을 때 유난히 크거나 작은 값입니다. "
    "여기서는 사분위수 범위를 이용해 이상치 후보를 찾습니다."
)

st.info(
    "이 방법은 이상치일 가능성이 있는 값을 찾는 방법입니다. "
    "찾아낸 값이 실제 오류라는 뜻은 아니며, 자동으로 삭제하지 않습니다."
)

# 실제 측정값 위주로 확인
measurement_columns = [
    "heart_rate_bpm",
    "MET",
    "hand_acc_x",
    "hand_acc_y",
    "hand_acc_z",
    "chest_acc_x",
    "chest_acc_y",
    "chest_acc_z",
    "ankle_acc_x",
    "ankle_acc_y",
    "ankle_acc_z"
]

measurement_columns = [
    col for col in measurement_columns
    if col in clean_df.columns
    and pd.api.types.is_numeric_dtype(clean_df[col])
]

# ---------------------------------
# 7. 이상치 개수 계산
# ---------------------------------
outlier_counts = {}
outlier_details = {}
outlier_masks = {}

for col in measurement_columns:
    values = clean_df[col].dropna()

    if len(values) == 0:
        continue

    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)
    iqr = q3 - q1

    lower_limit = q1 - 1.5 * iqr
    upper_limit = q3 + 1.5 * iqr

    # 원래 데이터 행과 맞춰서 이상치 여부 확인
    mask = (
        (clean_df[col] < lower_limit)
        | (clean_df[col] > upper_limit)
    ).fillna(False)

    outlier_masks[col] = mask
    outlier_counts[col] = int(mask.sum())

    outlier_details[col] = {
        "열 이름": col,
        "정상 범위 하한": round(lower_limit, 3),
        "정상 범위 상한": round(upper_limit, 3),
        "이상치 후보 개수": int(mask.sum())
    }

# ---------------------------------
# 8. 이상치 그래프
# ---------------------------------
st.subheader("이상치 후보 개수 비교")

if outlier_counts:
    outlier_chart = pd.DataFrame({
        "열 이름": list(outlier_counts.keys()),
        "이상치 후보 개수": list(outlier_counts.values())
    }).set_index("열 이름")

    st.bar_chart(
        outlier_chart,
        y="이상치 후보 개수",
        x_label="측정 항목",
        y_label="이상치 후보 개수"
    )

    st.caption(
        "막대가 높을수록 IQR 기준으로 이상치 후보가 많이 발견된 것입니다."
    )
else:
    st.info("이상치를 확인할 숫자형 측정 항목이 없습니다.")

# ---------------------------------
# 9. 이상치 범위 표
# ---------------------------------
st.subheader("이상치 판단 범위")

if outlier_details:
    details_df = pd.DataFrame(list(outlier_details.values()))
    st.dataframe(details_df, use_container_width=True)

    st.write(
        "IQR은 3사분위수에서 1사분위수를 뺀 값입니다. "
        "1사분위수보다 1.5 × IQR 이상 낮거나, "
        "3사분위수보다 1.5 × IQR 이상 높은 값을 이상치 후보로 봅니다."
    )

# ---------------------------------
# 10. 이상치 후보 직접 확인
# ---------------------------------
st.subheader("이상치 후보 데이터 확인")

if measurement_columns:
    selected_column = st.selectbox(
        "확인할 항목을 선택하세요.",
        measurement_columns
    )

    if selected_column in outlier_masks:
        mask = outlier_masks[selected_column]
        candidates = clean_df.loc[mask].copy()

        st.write(f"선택한 항목: **{selected_column}**")
        st.write(f"이상치 후보 개수: **{len(candidates):,}개**")

        if len(candidates) > 0:
            st.dataframe(
                candidates.head(100),
                use_container_width=True
            )

            st.caption(
                "최대 100개를 표시합니다. 실제 오류인지 판단한 후 처리해야 합니다."
            )
        else:
            st.success(
                "선택한 항목에서 IQR 기준 이상치 후보가 발견되지 않았습니다."
            )

# ---------------------------------
# 11. 결론
# ---------------------------------
st.header("5. 분석 결과 요약")

st.write(f"- 원본 데이터: {before_rows:,}행, {len(original_df.columns)}열")
st.write(f"- 결측치 개수: {total_missing:,}개")
st.write(f"- 필수 항목 결측치 처리 후: {after_rows:,}행")
st.write(f"- 제외한 행: {removed_rows:,}개")

if outlier_counts:
    total_outlier_candidates = sum(outlier_counts.values())
    st.write(
        f"- 각 측정 항목에서 발견한 이상치 후보 개수의 합: "
        f"{total_outlier_candidates:,}개"
    )
    st.caption(
        "이 합계는 항목별 개수를 더한 값입니다. "
        "같은 행이 여러 항목에서 이상치로 잡힐 수 있으므로 "
        "고유한 이상치 행의 개수와 같지는 않습니다."
    )

st.warning(
    "이상치 후보는 자동으로 삭제하지 않았습니다. "
    "실제 운동 중 나타날 수 있는 값인지 확인한 뒤 처리해야 합니다."
)
