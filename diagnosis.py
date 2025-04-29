import streamlit as st
import sqlite3
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

# 페이지 설정
st.set_page_config(layout="wide")

# 언어 선택 (모든 탭에 적용)
_, lang_col = st.columns([10, 1])
with lang_col:
    language = st.selectbox(
        label="🌐 Language",
        options=["Eng", "Viet", "Kor"],
        index=0,
        key="language_selector"
    )

# 언어별 타이틀 및 라벨 설정
titles = {
    "Eng": "CJ Pig Disease Diagnosis Tool",
    "Kor": "CJ 돼지 질병 원격 진단 Tool",
    "Viet": "Công cụ chẩn đoán bệnh ở heo từ xa của CJ"
}

tab_titles = {
    "Eng": ["Disease Diagnosis", "Disease Description", "Antibiotics & Disinfectants"],
    "Kor": ["질병 진단", "질병 설명", "항생제 및 소독제"],
    "Viet": ["Chẩn đoán bệnh", "Mô tả bệnh", "Kháng sinh & Chất khử trùng"]
}

labels = {
    "Kor": {
        "step3": "3️⃣ 의심 증상 선택",
        "click": "🩺 증상을 클릭해 선택/해제",
        "selected": "🧾 선택한 증상",
        "no_sig": "선택된 증상이 없습니다.",
        "step4": "4️⃣ 유력한 질병 추천 결과",
        "match_count": "매칭 수",
        "match_rate": "일치율(%)"
    },
    "Eng": {
        "step3": "3️⃣ Select Suspected Signals",
        "click": "🩺 Click to select/deselect",
        "selected": "🧾 Selected Signals",
        "no_sig": "No signals selected.",
        "step4": "4️⃣ Suspected Diseases",
        "match_count": "Match Count",
        "match_rate": "Match Rate (%)"
    },
    "Viet": {
        "step3": "3️⃣ Chọn triệu chứng nghi ngờ",
        "click": "🩺 Nhấp để chọn/hủy chọn",
        "selected": "🧾 Triệu chứng đã chọn",
        "no_sig": "Chưa có triệu chứng nào được chọn.",
        "step4": "4️⃣ Bệnh nghi ngờ hàng đầu",
        "match_count": "Số lần khớp",
        "match_rate": "Tỷ lệ khớp (%)"
    }
}[language]

# 탭 생성
tab1, tab2, tab3 = st.tabs(tab_titles[language])

# 탭 1: 질병 진단 (기존 코드 포함)
with tab1:
    st.title(titles[language])
    
    # DB 유틸리티 함수
    def fetch_unique_values(col_base, table="total"):
        col = f"{col_base} ({language})"
        try:
            conn = sqlite3.connect("Diagnosis.db")
            cur = conn.cursor()
            cur.execute(f"SELECT DISTINCT [{col}] FROM {table} WHERE [{col}] IS NOT NULL")
            vals = [r[0] for r in cur.fetchall()]
            conn.close()
            return vals
        except Exception as e:
            st.error(f"DB Error: {e}")
            return []

    def fetch_filtered_categories(sel_type):
        type_col = f"Type ({language})"
        cat_col = f"Category ({language})"
        try:
            conn = sqlite3.connect("Diagnosis.db")
            cur = conn.cursor()
            cur.execute(f"""
                SELECT DISTINCT [{cat_col}]
                FROM total
                WHERE [{type_col}] = ? AND [{cat_col}] IS NOT NULL
            """, (sel_type,))
            cats = [r[0] for r in cur.fetchall()]
            conn.close()
            return cats
        except Exception as e:
            st.error(f"DB Error: {e}")
            return []

    def fetch_signals_grouped(sel_type, sel_cat):
        type_col = f"Type ({language})"
        cat_col = f"Category ({language})"
        sig_col = f"Signal ({language})"
        other_lbl = {
            "Kor": "기타 관련 증상",
            "Eng": "Other related symptoms",
            "Viet": "Triệu chứng khác liên quan"
        }[language]
        try:
            conn = sqlite3.connect("Diagnosis.db")
            cur = conn.cursor()
            cur.execute(f"""
                SELECT DISTINCT [{sig_col}]
                FROM total
                WHERE [{type_col}] = ? AND [{cat_col}] = ? AND [{sig_col}] IS NOT NULL
            """, (sel_type, sel_cat))
            rows = cur.fetchall()
            conn.close()
            grouped = {}
            for (cell,) in rows:
                if not cell:
                    continue
                for part in cell.split(','):
                    part = part.strip()
                    if ':' in part:
                        grp, sig = [x.strip() for x in part.split(':', 1)]
                    else:
                        grp, sig = other_lbl, part
                    grouped.setdefault(grp, []).append(sig)
            for g in grouped:
                grouped[g] = sorted(set(grouped[g]))
            return grouped
        except Exception as e:
            st.error(f"Signal Load Error: {e}")
            return {}

    def remove_signal(sig):
        if sig in st.session_state.selected_signals:
            st.session_state.selected_signals.remove(sig)

    # 1️⃣ 질병 타입 선택
    st.subheader("1️⃣ Select Disease Type")
    type_options = fetch_unique_values("Type")
    selected_type = st.selectbox("Type", type_options)

    # 2️⃣ 카테고리 선택
    st.subheader("2️⃣ Select Category")
    category_options = fetch_filtered_categories(selected_type)
    selected_category = st.selectbox("Category", category_options)

    # 3️⃣ 증상 선택 및 삭제
    st.subheader(labels["step3"])
    if "selected_signals" not in st.session_state:
        st.session_state.selected_signals = []

    grouped = fetch_signals_grouped(selected_type, selected_category)
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(labels["click"])
        for grp, sigs in grouped.items():
            with st.expander(f"📂 {grp}", expanded=False):
                for sig in sigs:
                    sel = sig in st.session_state.selected_signals
                    btn_lbl = f"✅ {sig}" if sel else sig
                    if st.button(btn_lbl, key=f"sel_{grp}_{sig}"):
                        if sel:
                            st.session_state.selected_signals.remove(sig)
                        else:
                            st.session_state.selected_signals.append(sig)

    with col2:
        st.markdown(labels["selected"])
        if st.session_state.selected_signals:
            for i, sig in enumerate(st.session_state.selected_signals.copy(), 1):
                lc, bc = st.columns([8, 1])
                lc.markdown(f"{i}. {sig}")
                bc.button(
                    "❌", key=f"rm_{sig}_{i}",
                    on_click=remove_signal, args=(sig,)
                )
        else:
            st.info(labels["no_sig"])

    # 4️⃣ 질병 추천 + 클릭 시 √된 증상 보기
    st.subheader(labels["step4"])
    if st.session_state.selected_signals:
        conn = sqlite3.connect("Diagnosis.db")
        df = pd.read_sql("SELECT * FROM total", conn)
        conn.close()

        sig_idx = df.columns.get_loc(f"Signal ({language})")
        disease_cols = df.columns[sig_idx + 1:]

        # 매칭 수 집계
        counter = {d: 0 for d in disease_cols}
        for _, row in df.iterrows():
            field = row[f"Signal ({language})"]
            if not field:
                continue
            row_sigs = [s.strip() for s in field.split(',')]
            if set(row_sigs) & set(st.session_state.selected_signals):
                for d in disease_cols:
                    if str(row[d]).strip() == "√":
                        counter[d] += 1

        results = [
            {"Disease": d, labels["match_count"]: c}
            for d, c in counter.items() if c > 0
        ]
        if results:
            res_df = pd.DataFrame(results).sort_values(
                by=labels["match_count"], ascending=False
            )
            total = res_df[labels["match_count"]].sum()
            res_df[labels["match_rate"]] = (res_df[labels["match_count"]] / total * 100).round(1)

            main_col, detail_col = st.columns([2, 1])

            # AgGrid 설정
            gb = GridOptionsBuilder.from_dataframe(res_df)
            gb.configure_selection("single", use_checkbox=False)
            grid_opts = gb.build()

            with main_col:
                grid_resp = AgGrid(
                    res_df,
                    gridOptions=grid_opts,
                    update_mode="SELECTION_CHANGED",
                    theme="streamlit",
                    height=350,
                    allow_unsafe_jscode=True
                )

            with detail_col:
                selected = grid_resp.get("selected_rows", [])
                if isinstance(selected, pd.DataFrame):
                    sel_records = selected.to_dict("records")
                elif isinstance(selected, list):
                    sel_records = selected
                else:
                    sel_records = []

                if len(sel_records) > 0:
                    sel_disease = sel_records[0]["Disease"]
                    checked = []
                    for _, row in df.iterrows():
                        if str(row[sel_disease]).strip() == "√":
                            fld = row[f"Signal ({language})"]
                            if fld:
                                checked += [s.strip() for s in fld.split(',')]
                    checked = sorted(set(checked))
                    st.markdown(f"**{sel_disease}**")
                    st.markdown("#### √ Checked Signals")
                    for s in checked:
                        st.markdown(f"- {s}")
                else:
                    st.info("Click a disease to see its checked signals.")
        else:
            st.warning("❗ No matching disease found.")
    else:
        st.info("Please select signals first.")

# 탭 2: 질병 설명 (disease 테이블 데이터 표시)
with tab2:
    st.title(titles[language])

    try:
        # DB 연결 및 disease 테이블 불러오기
        conn = sqlite3.connect("Diagnosis.db")
        df_disease = pd.read_sql_query("SELECT * FROM disease", conn)
        conn.close()

        # 실제 컬럼 이름 확인 (화면에는 표시하지 않음)
        available_columns = df_disease.columns.tolist()

        # 언어별 컬럼 동적 선택 (컬럼 이름에 언어 포함 여부로 필터링)
        disease_col = next((col for col in available_columns if "Disease" in col and language in col), None)
        if not disease_col:
            disease_col = next((col for col in available_columns if "Disease" in col), available_columns[0] if available_columns else None)

        fullname_col = next((col for col in available_columns if "Full name" in col and language in col), None)
        if not fullname_col:
            fullname_col = next((col for col in available_columns if "Full name" in col), available_columns[1] if len(available_columns) > 1 else None)

        explanation_col = next((col for col in available_columns if "explanation" in col and language in col), None)
        if not explanation_col:
            explanation_col = next((col for col in available_columns if "explanation" in col), available_columns[2] if len(available_columns) > 2 else None)

        # 컬럼이 제대로 선택되었는지 확인
        if disease_col and fullname_col:
            # 질병 리스트 (Disease, Full name)
            disease_list_df = df_disease[[disease_col, fullname_col]].drop_duplicates().reset_index(drop=True)
            # AgGrid로 질병 리스트 표시 및 더블 클릭 이벤트 처리
            gb = GridOptionsBuilder.from_dataframe(disease_list_df)
            gb.configure_selection("single", use_checkbox=False)
            gb.configure_column(disease_col, flex=1)  # 첫 번째 열 폭을 반절 차지
            gb.configure_column(fullname_col, flex=1)  # 두 번째 열 폭을 반절 차지
            gb.configure_grid_options(onCellDoubleClicked=JsCode("""
                function(event) {
                    // 더블 클릭 시 이벤트 처리 (세션 상태 업데이트는 Streamlit에서 처리)
                }
            """))
            grid_options = gb.build()

            grid_response = AgGrid(
                disease_list_df,
                gridOptions=grid_options,
                height=300,
                update_mode="SELECTION_CHANGED",
                fit_columns_on_grid_load=True,
                allow_unsafe_jscode=True
            )

            # 더블 클릭으로 선택된 행 처리
            selected_rows = grid_response.get("selected_rows", [])
            if isinstance(selected_rows, pd.DataFrame):
                sel_records = selected_rows.to_dict("records")
            elif isinstance(selected_rows, list):
                sel_records = selected_rows
            else:
                sel_records = []

            if sel_records and explanation_col:
                selected_disease = sel_records[0][disease_col]
                st.markdown(f"#### {selected_disease}")

                # 선택된 질병의 설명만 추출
                explanation_df = df_disease[df_disease[disease_col] == selected_disease][[explanation_col]].rename(
                    columns={explanation_col: {
                        "Eng": "Explanation",
                        "Kor": "설명",
                        "Viet": "Giải thích"
                    }[language]}
                )

                # AgGrid로 explanation 보여주기
                gb_exp = GridOptionsBuilder.from_dataframe(explanation_df)
                gb_exp.configure_default_column(autoHeight=True, wrapText=True)
                grid_options_exp = gb_exp.build()

                AgGrid(
                    explanation_df,
                    gridOptions=grid_options_exp,
                    height=200,
                    fit_columns_on_grid_load=True,
                    allow_unsafe_jscode=True
                )
            elif not explanation_col:
                st.error("Explanation column not found in the database.")
            else:
                st.info("Double-click a disease to see its explanation.")
        else:
            st.error("Required columns (Disease or Full name) not found in the database.")
    except Exception as e:
        st.error(f"Error loading data from disease table: {e}")

# 탭 3: 항생제 및 소독제 (예시 콘텐츠)
with tab3:
    st.title(titles[language])
    st.header("Antibiotics & Disinfectants" if language == "Eng" else "항생제 및 소독제" if language == "Kor" else "Kháng sinh & Chất khử trùng")
    st.write("This tab can provide information on antibiotics and disinfectants used in pig disease management.")
    st.write("Content will adapt to the selected language.")
