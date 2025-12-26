import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
import hashlib

# ==========================================
# 🔐 0. 비밀번호 보호 기능
# ==========================================
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.title("🔒 자금 집행 관리 시스템 (Demo)")
        st.write("시연용 버전입니다. 비밀번호를 입력하세요.")
        
        pwd = st.text_input("비밀번호", type="password")
        
        if st.button("로그인"):
            if pwd == "1234":  # 비밀번호
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("비밀번호가 틀렸습니다.")
        return False
    return True

if not check_password():
    st.stop()

# =========================================================
# 1. 설정 및 스타일 (여백 최적화 및 80% 축소 적용)
# =========================================================
st.set_page_config(page_title="자금 집행 대시보드(Demo)", layout="wide")

st.markdown("""
<style>
    /* 전체 화면 배율을 80%로 조정 */
    body {
        zoom: 80%;
    }
    
    /* [수정] 상단/하단 여백을 줄여서 리스트를 더 많이 보여줌 */
    div.block-container {
        padding-top: 2rem;
        padding-bottom: 0.01rem;
    }
    
    /* 버튼 스타일 */
    div.stButton > button[kind="primary"] {
        background-color: #198754 !important;
        border-color: #198754 !important;
        color: white !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #157347 !important;
        border-color: #146c43 !important;
        color: white !important;
    }
    div.stButton > button[kind="primary"]:focus {
        box-shadow: 0 0 0 0.25rem rgba(25, 135, 84, 0.5) !important;
        border-color: #198754 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2. [핵심] 가짜 데이터 생성 및 상태 관리
# =========================================================

# ★ 시연을 위해 날짜를 2025-12-17로 고정하는 함수
def get_fixed_today():
    return datetime(2025, 12, 17)

def init_mock_data():
    """시연용 데이터 생성 (최초 1회만 실행됨)"""
    if "master_df" not in st.session_state:
        # ★ 날짜 기준점 (고정된 날짜 사용: 2025-12-17 수요일)
        today = get_fixed_today()
        
        # [수정] 날짜를 다양하게 분산
        d_prev = (today - timedelta(days=1)).strftime("%Y-%m-%d") # 12/18 (목) - 금주
        d_this = today.strftime("%Y-%m-%d")                       # 12/19 (금) - 금주
        
        d_next_mon = (today + timedelta(days=5)).strftime("%Y-%m-%d") # 12/22 (월) - 차주
        d_next_wed = (today + timedelta(days=7)).strftime("%Y-%m-%d") # 12/24 (수) - 차주
        d_next_fri = (today + timedelta(days=9)).strftime("%Y-%m-%d") # 12/26 (금) - 차주
        
        d_past = (today - timedelta(days=10)).strftime("%Y-%m-%d") # 12/07 (과거)
        
        # 가짜 데이터 리스트
        data = [
            # [금주 지급] - 12/18(목), 12/19(금)으로 분산
            {"No": 1, "기안자": "김대리", "기안일자": d_prev, "제목": "연구소 모니터 구매 건", "지급요청일(하)": d_this, "거래처명": "삼성전자", "은행명": "우리은행", "계좌번호": "1002-111-222222", "통화": "KRW", "이체금액": "1,500,000", "결재완료": "O", "지급완료": False, "전표완료": False},
            {"No": 2, "기안자": "이과장", "기안일자": d_this, "제목": "12월 시약 구매", "지급요청일(하)": d_this, "거래처명": "LG화학", "은행명": "신한은행", "계좌번호": "110-333-444444", "통화": "KRW", "이체금액": "450,000", "결재완료": "O", "지급완료": False, "전표완료": False},
            
            # [차주 지급] - 월/수/금으로 분산
            {"No": 3, "기안자": "박차장", "기안일자": d_this, "제목": "마케팅 대행비 선금", "지급요청일(하)": d_next_mon, "거래처명": "제일기획", "은행명": "국민은행", "계좌번호": "004-555-666666", "통화": "KRW", "이체금액": "3,000,000", "결재완료": "O", "지급완료": False, "전표완료": False},
            {"No": 4, "기안자": "최대리", "기안일자": d_this, "제목": "서버 호스팅 비용(AWS)", "지급요청일(하)": d_next_wed, "거래처명": "AWS Korea", "은행명": "하나은행", "계좌번호": "222-777-888888", "통화": "KRW", "이체금액": "120,000", "결재완료": "O", "지급완료": False, "전표완료": False},
            {"No": 11, "기안자": "고사원", "기안일자": d_this, "제목": "사무용품(비품) 정기구매", "지급요청일(하)": d_next_fri, "거래처명": "알파문구", "은행명": "-", "계좌번호": "-", "통화": "KRW", "이체금액": "55,000", "결재완료": float('nan'), "지급완료": False, "전표완료": False}, # 차주 금요일
            
            # [내부 규정 - 날짜 없음]
            {"No": 5, "기안자": "정대리", "기안일자": d_past, "제목": "파렛트 구매 대금 결제", "지급요청일(하)": "[V] 회사내부규정", "지급요청일(상)": "[V] 회사내부규정", "거래처명": "현대카드", "은행명": "-", "계좌번호": "-", "통화": "KRW", "이체금액": "5,400,000", "결재완료": "O", "지급완료": False, "전표완료": False},
            
            # [지급 누락 (과거 날짜)]
            {"No": 6, "기안자": "강팀장", "기안일자": d_past, "제목": "퀵서비스 비용", "지급요청일(하)": d_past, "거래처명": "바로고", "은행명": "농협", "계좌번호": "302-1234-5678", "통화": "KRW", "이체금액": "35,000", "결재완료": "O", "지급완료": False, "전표완료": False},
            
            # [기타 - 텍스트 날짜]
            {"No": 7, "기안자": "홍과장", "기안일자": d_this, "제목": "사무실 간식비", "지급요청일(하)": "영수증 확인후", "거래처명": "이마트", "은행명": "-", "계좌번호": "-", "통화": "KRW", "이체금액": "88,000", "결재완료": "O", "지급완료": False, "전표완료": False},

            # [상태별 테스트용 데이터]
            {"No": 8, "기안자": "정부장", "기안일자": d_this, "제목": "지급만 된 건", "지급요청일(하)": d_prev, "거래처명": "테스트업체1", "은행명": "카카오뱅크", "계좌번호": "3333-01-00000", "통화": "KRW", "이체금액": "10,000", "결재완료": "O", "지급완료": True, "전표완료": False},
            {"No": 9, "기안자": "조대리", "기안일자": d_this, "제목": "완료된 건(삭제테스트)", "지급요청일(하)": d_this, "거래처명": "테스트업체2", "은행명": "토스뱅크", "계좌번호": "1000-00-00000", "통화": "KRW", "이체금액": "20,000", "결재완료": "O", "지급완료": True, "전표완료": True},
            
            # [같은 No로 묶인 데이터 (그룹핑 테스트)] - 금요일 지급
            {"No": 10, "기안자": "정사원", "기안일자": d_this, "제목": "행사비 분할 지급(1)", "지급요청일(하)": d_this, "거래처명": "호텔신라", "은행명": "우리", "계좌번호": "111-111", "통화": "KRW", "이체금액": "1,000,000", "결재완료": "O", "지급완료": False, "전표완료": False},
            {"No": 10, "기안자": "정사원", "기안일자": d_this, "제목": "행사비 분할 지급(2)", "지급요청일(하)": d_this, "거래처명": "이벤트사", "은행명": "국민", "계좌번호": "222-222", "통화": "KRW", "이체금액": "500,000", "결재완료": "O", "지급완료": False, "전표완료": False},
        ]
        
        df = pd.DataFrame(data)
        
        # ID 생성 로직
        def temp_make_id(row):
            raw = f"{row.get('기안일자','')}_{row.get('기안자','')}_{row.get('거래처명','')}_{row.get('이체금액','')}"
            return hashlib.md5(raw.encode('utf-8')).hexdigest()[:12]
        
        df['ID'] = df.apply(temp_make_id, axis=1)
        st.session_state["master_df"] = df

# 데이터 초기화 호출
init_mock_data()

# =========================================================
# 3. 데이터 로직 (파일 대신 session_state 사용)
# =========================================================

def load_merged_data():
    """메모리에 있는 데이터프레임을 반환"""
    return st.session_state["master_df"].copy()

def update_status_memory(target_id, col_name, value=None):
    """메모리 상의 상태 업데이트 (토글 또는 지정값)"""
    df = st.session_state["master_df"]
    if target_id in df['ID'].values:
        idx = df[df['ID'] == target_id].index[0]
        if value is not None:
            df.at[idx, col_name] = value
        else:
            # 토글
            current = df.at[idx, col_name]
            df.at[idx, col_name] = not current
    st.session_state["master_df"] = df

def batch_update_status_memory(id_list, col_name, value=True):
    """일괄 업데이트"""
    df = st.session_state["master_df"]
    for tid in id_list:
        if tid in df['ID'].values:
            idx = df[df['ID'] == tid].index[0]
            df.at[idx, col_name] = value
    st.session_state["master_df"] = df

def batch_archive_memory(id_list):
    """삭제(아카이브) - 메모리에서 행 삭제"""
    df = st.session_state["master_df"]
    st.session_state["master_df"] = df[~df['ID'].isin(id_list)]
    return True

# 날짜 파싱 유틸리티
def parse_date(text):
    if pd.isna(text): return None
    if isinstance(text, (datetime, pd.Timestamp)):
        return text.date()
    text = str(text).strip()
    # [V] 포함된 경우에도 날짜가 있으면 추출
    import re
    if '[V]' in text:
        match = re.search(r'(\d{4})[\.-](\d{1,2})[\.-](\d{1,2})', text)
        if match:
            try:
                return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3))).date()
            except:
                return None
    try:
        return pd.to_datetime(text).date()
    except:
        return None

def is_text_type(text):
    if pd.isna(text): return False
    text = str(text).strip()
    if '[V]' in text and parse_date(text) is None: # 내부규정 등
        return True
    if parse_date(text) is None: # 날짜 형식이 아닌 텍스트
        return True
    return False

def parse_amount_str(val):
    try:
        return float(str(val).replace(',', ''))
    except:
        return 0.0

# =========================================================
# 4. 화면 구성 (UI)
# =========================================================

col_title, col_btn = st.columns([7, 3])

with col_title:
    st.title("💰 자금 집행 관리 시스템 (Demo)")
    # ★ 시연 날짜 안내 추가
    st.caption("※ 시연용 고정 날짜: 2025-12-17(수) 기준")

with col_btn:
    st.write("") 
    if st.button("🔄 데이터 초기화 (Reset)", use_container_width=True):
        del st.session_state["master_df"]
        st.rerun()

df = load_merged_data()

# --- [상단 필터 영역] ---
with st.expander("🔍 상세 검색 및 필터 (클릭)", expanded=True):
    f_col1, f_col2, f_col3, f_col4, f_col5, f_col6 = st.columns([0.8, 1.2, 1.2, 0.5, 0.8, 0.8])
    
    all_drafters = sorted(df['기안자'].dropna().unique())
    filter_drafter = f_col1.multiselect("👤 기안자", all_drafters, placeholder="전체")
    search_vendor = f_col2.text_input("🏢 거래처", placeholder="예: 삼성")
    search_title = f_col3.text_input("📋 제목/내용", placeholder="키워드")
    all_currencies = sorted(df['통화'].dropna().unique())
    filter_currency = f_col4.multiselect("💵 통화", all_currencies, placeholder="전체")
    filter_approval = f_col5.radio("📝 결재여부", options=["전체", "승인(O)", "미결(X)"], horizontal=True)
    filter_status = f_col6.radio("📊 진행상태", options=["전체", "대기", "지급됨", "완료"], horizontal=True)

# --- [필터링 로직] ---
if filter_drafter: df = df[df['기안자'].isin(filter_drafter)]
if search_vendor: df = df[df['거래처명'].astype(str).str.contains(search_vendor, case=False, na=False)]
if search_title: df = df[df['제목'].astype(str).str.contains(search_title, case=False, na=False)]
if filter_currency: df = df[df['통화'].isin(filter_currency)]

if filter_approval == "승인(O)": df = df[df['결재완료'].notna() & (df['결재완료'].astype(str) != 'nan')]
elif filter_approval == "미결(X)": df = df[df['결재완료'].isna() | (df['결재완료'].astype(str) == 'nan')]

if filter_status == "대기": df = df[df['지급완료'] == False]
elif filter_status == "지급됨": df = df[(df['지급완료'] == True) & (df['전표완료'] == False)]
elif filter_status == "완료": df = df[(df['지급완료'] == True) & (df['전표완료'] == True)]

# --- [데이터 분류 로직] ---
# ★ [중요] 분류 기준 날짜도 고정된 날짜(12/17)를 사용
today = get_fixed_today().date() # 2025-12-17

start_of_week = today - timedelta(days=today.weekday()) # 월요일
end_of_week = start_of_week + timedelta(days=6) # 일요일
start_of_next = end_of_week + timedelta(days=1)
end_of_next = start_of_next + timedelta(days=6)

# 완료된 항목(지급O, 전표O)
df_completed = df[(df['지급완료'] == True) & (df['전표완료'] == True)].copy()

# 활성 항목
df_active = df[~df.index.isin(df_completed.index)].copy()

# 내부규정 등 텍스트 날짜
df_policy = df_active[ df_active['지급요청일(상)'].astype(str).str.contains(r'\[V\]\s*회사내부규정', na=False) ]

# 그 외 (날짜 파싱)
df_others = df_active[ ~df_active.index.isin(df_policy.index) ].copy()
df_others['date_obj'] = df_others['지급요청일(하)'].apply(parse_date)

df_overdue = df_others[ (df_others['date_obj'].notnull()) & (df_others['date_obj'] < today) & (df_others['지급완료'] == False) ]
df_this = df_others[ (df_others['date_obj'] >= start_of_week) & (df_others['date_obj'] <= end_of_week) ]
df_next = df_others[ (df_others['date_obj'] >= start_of_next) & (df_others['date_obj'] <= end_of_next) ]

# 텍스트 타입 (날짜 파싱 실패 등)
df_others['is_text'] = df_others['지급요청일(하)'].apply(is_text_type)
df_text_type = df_others[ df_others['is_text'] == True ]

df_slip_pending = df_active[ df_active['전표완료'] == False ]

# 탭 생성
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    f"🚨 금주지급 ({len(df_this['No'].unique())}건)",
    f"📅 차주지급 ({len(df_next['No'].unique())}건)",
    f"🏢 내부규정 ({len(df_policy['No'].unique())}건)",
    f"⚠️ 지급누락 ({len(df_overdue['No'].unique())}건)",
    f"🎸 기타지급 ({len(df_text_type['No'].unique())}건)",
    f"📝 전표작성 ({len(df_slip_pending['No'].unique())}건)",
    f"📂 전체 ({len(df['No'].unique())}건)",
    f"✅ 작업완료 ({len(df_completed['No'].unique())}건)"
])

# =========================================================
# 5. 테이블 렌더링 함수 (기존 유지)
# =========================================================
def render_table_grouped(target_df, tab_key):
    if target_df.empty:
        st.info("내역이 없습니다.")
        return

    unique_nos = target_df['No'].unique()
    
    # 선택 로직
    selected_ids = []
    selected_group_count = 0
    
    for no in unique_nos:
        if st.session_state.get(f"check_{tab_key}_{no}", False):
            selected_group_count += 1
            ids_in_no = target_df[target_df['No'] == no]['ID'].tolist()
            selected_ids.extend(ids_in_no)
            
    selected_rows = target_df[target_df['ID'].isin(selected_ids)]
    total_sum = 0
    if not selected_rows.empty:
        total_sum = sum(selected_rows['이체금액'].apply(parse_amount_str))

    if selected_group_count > 0:
        st.info(f"✅ **선택: {selected_group_count}건** ｜ 💰 **합계: {int(total_sum):,}원**")
    else:
        st.caption("항목을 선택하면 일괄 처리 및 합계가 계산됩니다.")

    # 버튼 배치
    b1, b2, b3, b4, b5, b_spacer = st.columns([0.3, 0.4, 0.4, 0.4, 0.6, 4.4], gap="small")
    
    with b1:
        if st.button("전체 선택", key=f"all_{tab_key}"):
            for no in unique_nos:
                st.session_state[f"check_{tab_key}_{no}"] = True
            st.rerun()
    with b2:
        if st.button("전체 해제", key=f"none_{tab_key}"):
            for no in unique_nos:
                st.session_state[f"check_{tab_key}_{no}"] = False
            st.rerun()

    with b3:
        if st.button("일괄 지급처리", key=f"batch_pay_{tab_key}"):
            if selected_ids:
                batch_update_status_memory(selected_ids, '지급완료', True)
                st.success(f"{selected_group_count}건 지급 처리 완료!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.warning("선택된 항목이 없습니다.")

    with b4:
        if st.button("일괄 전표처리", key=f"batch_slip_{tab_key}"):
            if selected_ids:
                batch_update_status_memory(selected_ids, '전표완료', True)
                st.success(f"{selected_group_count}건 전표 처리 완료!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.warning("선택된 항목이 없습니다.")
    
    with b5:
        if tab_key == "completed":
            if st.button("🧹 완료건 정리", key=f"batch_del_{tab_key}", type="primary"):
                if selected_ids:
                    if batch_archive_memory(selected_ids):
                        st.success(f"{selected_group_count}건이 삭제되었습니다.")
                        # 체크박스 초기화
                        for no in unique_nos:
                            if st.session_state.get(f"check_{tab_key}_{no}"):
                                del st.session_state[f"check_{tab_key}_{no}"]
                        time.sleep(1)
                        st.rerun()
                else:
                    st.warning("삭제할 항목을 선택해주세요.")

    st.markdown('<hr style="margin-top: 5px; margin-bottom: 0px; border: 0; border-top: 1px solid #e0e0e0;">', unsafe_allow_html=True)

    # [수정된 코드] 테이블 헤더 및 구분선 (간격 좁히기 적용)
    col_ratios = [0.3, 0.5, 0.3, 0.5, 0.8, 2.8, 0.8, 1.4, 0.8, 1.2, 0.5, 0.8, 0.6, 0.6]
    cols = st.columns(col_ratios)
    headers = ["선택", "상태", "결재", "기안자", "기안일", "제목", "지급요청일", "거래처", "은행", "계좌", "통화", "금액", "지급", "전표"]
    
    # 헤더 글자 출력 (여백 제거)
    for col, h in zip(cols, headers): 
        col.markdown(f"<p style='margin-bottom: 0px; margin-top: 0px; font-weight:bold;'>{h}</p>", unsafe_allow_html=True)
    
    # 헤더 바로 아래 구분선 (st.divider 대신 사용, 위쪽 여백 조절)
    st.markdown('<hr style="margin-top: 0px; margin-bottom: 5px; border: 0; border-top: 2px solid #e0e0e0;">', unsafe_allow_html=True)

    # 데이터 출력
    for no, group in target_df.groupby('No', sort=False):
        first_row = group.iloc[0]
        
        is_paid = first_row['지급완료']
        is_done = first_row['전표완료']
        all_done = is_paid and is_done
        style = "text-decoration: line-through; color: gray;" if all_done else ""
        
        c_list = st.columns(col_ratios)
        
        c_list[0].checkbox("", key=f"check_{tab_key}_{no}")

        if all_done: c_list[1].markdown("✅ 완료")
        elif is_paid: c_list[1].markdown("💰 지급됨")
        else: c_list[1].markdown("⏳ 대기")
        
        approval_val = str(first_row['결재완료']).strip()
        is_approved = "O" if pd.notna(first_row['결재완료']) and approval_val != "" and approval_val != "nan" else "X"
        color = "blue" if is_approved == "O" else "red"
        c_list[2].markdown(f"<span style='color:{color}; font-weight:bold;'>{is_approved}</span>", unsafe_allow_html=True)
        
        c_list[3].markdown(f"<span style='{style}'>{first_row['기안자']}</span>", unsafe_allow_html=True)
        c_list[4].markdown(f"<span style='{style}'>{first_row['기안일자']}</span>", unsafe_allow_html=True)
        
        unique_titles = group['제목'].unique()
        title_str = "<br>".join([str(t) for t in unique_titles])
        c_list[5].markdown(f"<span style='{style}'>{title_str}</span>", unsafe_allow_html=True)
        
        req_date = first_row.get('지급요청일(하)', '')
        c_list[6].markdown(f"<span style='{style}'>{req_date}</span>", unsafe_allow_html=True)
        
        vendor_list = group['거래처명'].fillna('-').astype(str).tolist()
        c_list[7].markdown(f"<span style='{style}'>{'<br>'.join(vendor_list)}</span>", unsafe_allow_html=True)
        
        bank_list = group['은행명'].fillna('-').astype(str).tolist()
        c_list[8].markdown(f"<span style='{style}'>{'<br>'.join(bank_list)}</span>", unsafe_allow_html=True)
        
        acc_list = group['계좌번호'].fillna('-').astype(str).tolist()
        c_list[9].markdown(f"<span style='{style}'>{'<br>'.join(acc_list)}</span>", unsafe_allow_html=True)
        
        curr_list = group['통화'].fillna('').astype(str).tolist()
        c_list[10].markdown(f"<span style='{style}'>{'<br>'.join(curr_list)}</span>", unsafe_allow_html=True)
        
        try:
            amt_list = []
            for x in group['이체금액']:
                val = float(str(x).replace(',', ''))
                amt_list.append(f"{int(val):,}")
            amt_str = "<br>".join(amt_list)
        except:
            amt_str = str(first_row['이체금액'])
        c_list[11].markdown(f"<span style='{style}'>{amt_str}</span>", unsafe_allow_html=True)
        
        current_ids_in_group = group['ID'].tolist()

        btn_key_pay = f"pay_{tab_key}_{no}"
        if c_list[12].button("취소" if is_paid else "지급", key=btn_key_pay, type="secondary" if is_paid else "primary"):
            for uid in current_ids_in_group:
                update_status_memory(uid, '지급완료')
            st.rerun()
            
        btn_key_slip = f"slip_{tab_key}_{no}"
        if c_list[13].button("취소" if is_done else "전표", key=btn_key_slip, type="secondary" if is_done else "primary"):
            for uid in current_ids_in_group:
                update_status_memory(uid, '전표완료')
            st.rerun()
    
    st.markdown("---")

# 탭 렌더링
with tab1: render_table_grouped(df_this, "this")
with tab2: render_table_grouped(df_next, "next")
with tab3: render_table_grouped(df_policy, "policy")
with tab4: render_table_grouped(df_overdue, "overdue")
with tab5: render_table_grouped(df_text_type, "others")
with tab6: render_table_grouped(df_slip_pending, "slip_pending")
with tab7: render_table_grouped(df, "all")
with tab8: render_table_grouped(df_completed, "completed")
