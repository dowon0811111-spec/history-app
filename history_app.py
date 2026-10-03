import streamlit as st
import re
from ai_helper import ask_ai, get_person_image, save_history, load_history

# 페이지 설정
st.set_page_config(
    page_title="비슷한 위인 찾기",
    page_icon="🎭",
    layout="wide"
)

# 세션 상태 초기화 (맨 처음에 실행)
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "result_shown" not in st.session_state:
    st.session_state.result_shown = False
if "view_history_index" not in st.session_state:
    st.session_state.view_history_index = None

st.title("🎭 나와 비슷한 위인 찾기")

# 통계 정보 표시
histories = load_history()
total_people = sum(len(h.get('records', [])) for h in histories)
total_analyses = len(histories)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📊 분석 횟수", total_analyses, delta=None)
with col2:
    st.metric("👥 분석된 위인", total_people, delta=None)
with col3:
    if total_analyses > 0:
        st.metric("📈 평균 위인/분석", f"{total_people/total_analyses:.1f}", delta=None)
    else:
        st.metric("📈 평균 위인/분석", "0", delta=None)

st.markdown("---")

# 사이드바에 기록 조회 메뉴
with st.sidebar:
    st.subheader("📚 저장된 기록")
    histories = load_history()

    if histories:
        st.info(f"총 {len(histories)}개의 기록이 있습니다.")

        # 기록 리스트
        for idx, history in enumerate(histories):
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{history['user_name']}**")
                    st.caption(history['timestamp'])
                with col2:
                    if st.button("보기", key=f"view_{idx}", use_container_width=True):
                        st.session_state.view_history_index = idx

        st.divider()
    else:
        st.info("아직 저장된 기록이 없습니다.")

# 기록 상세 보기
if st.session_state.view_history_index is not None:
    histories = load_history()
    if st.session_state.view_history_index < len(histories):
        history = histories[st.session_state.view_history_index]

        st.subheader("📖 기록 상세")
        st.markdown(f"**{history['title']}**")
        st.markdown("---")

        # 위인 정보 표시
        for record in history['records']:
            with st.container(border=True):
                col1, col2 = st.columns([1, 2])

                # 이미지 표시
                with col1:
                    if record.get('image_url'):
                        st.image(record['image_url'], caption=record['name'], use_column_width=True)
                    else:
                        st.info(f"📷 {record['name']}")

                # 정보 표시
                with col2:
                    st.markdown(f"**위인 {record['rank']}: {record['name']}**")
                    st.markdown(f"*({record['english_name']})*")
                    st.markdown(f"**주요 업적:** {record['achievement']}")
                    st.markdown("**나와의 유사점:**")
                    for similarity in record['similarities']:
                        st.markdown(f"- {similarity}")

        # 뒤로가기 버튼
        if st.button("◀ 돌아가기"):
            st.session_state.view_history_index = None
            st.rerun()
        st.stop()

# 이름 입력 페이지
if not st.session_state.user_name:
    st.subheader("👋 시작하기")
    st.info("먼저 당신의 이름을 알려주세요!")

    col1, col2 = st.columns([3, 1])
    with col1:
        name_input = st.text_input("이름을 입력하세요", placeholder="예: 김철수")
    with col2:
        if st.button("시작", use_container_width=True, type="primary"):
            if name_input.strip():
                st.session_state.user_name = name_input.strip()
                st.rerun()
            else:
                st.error("이름을 입력해주세요!")
    st.stop()

# 이름 표시
st.write(f"👤 **{st.session_state.user_name}님의 성향 진단**")
st.markdown("---")

# 12개의 이지선다 질문 정의
questions = [
    {
        "id": 1,
        "question": "새로운 상황에서 당신은?",
        "option_a": "신중하게 계획을 세운다",
        "option_b": "직관적으로 행동한다"
    },
    {
        "id": 2,
        "question": "문제 해결 시 주로?",
        "option_a": "분석적이고 논리적으로 접근한다",
        "option_b": "창의적인 아이디어를 먼저 생각한다"
    },
    {
        "id": 3,
        "question": "팀에서의 역할은?",
        "option_a": "리더로서 방향을 제시한다",
        "option_b": "팀원을 지원하고 조화를 맞춘다"
    },
    {
        "id": 4,
        "question": "실패했을 때 반응은?",
        "option_a": "원인을 분석하고 다시 도전한다",
        "option_b": "기분을 전환하고 다른 방법을 시도한다"
    },
    {
        "id": 5,
        "question": "사람들과의 관계에서?",
        "option_a": "넓고 얕은 관계를 유지한다",
        "option_b": "깊고 의미있는 관계를 추구한다"
    },
    {
        "id": 6,
        "question": "변화에 대해?",
        "option_a": "안정성을 중시하고 현상을 유지하려 한다",
        "option_b": "혁신을 추구하고 새로움을 좋아한다"
    },
    {
        "id": 7,
        "question": "학습 시 선호하는 방식은?",
        "option_a": "이론과 원칙을 체계적으로 배운다",
        "option_b": "경험을 통해 자연스럽게 배운다"
    },
    {
        "id": 8,
        "question": "사회적 책임에 대해?",
        "option_a": "개인의 역할에 충실한다",
        "option_b": "사회 전체의 발전을 추구한다"
    },
    {
        "id": 9,
        "question": "의사결정 시 주로?",
        "option_a": "논리와 사실을 중시한다",
        "option_b": "가치관과 감정을 중시한다"
    },
    {
        "id": 10,
        "question": "목표 달성을 위해?",
        "option_a": "체계적인 계획을 따른다",
        "option_b": "유연하게 상황에 맞춰 조정한다"
    },
    {
        "id": 11,
        "question": "갈등 상황에서는?",
        "option_a": "원칙과 신념을 지킨다",
        "option_b": "합의점을 찾으려 노력한다"
    },
    {
        "id": 12,
        "question": "영향력 행사 시?",
        "option_a": "설득과 논리로 설명한다",
        "option_b": "행동과 본보기로 보여준다"
    }
]

# 질문 폼 표시
st.subheader("📋 성향 진단 질문")
st.info("아래 12개의 질문에 답변하세요. 각 질문에서 더 공감되는 선택지를 선택하면 됩니다.")

# 각 질문을 컨테이너로 표시
for q in questions:
    with st.container(border=True):
        st.markdown(f"**Q{q['id']}: {q['question']}**")

        col1, col2 = st.columns(2)
        with col1:
            if st.button(
                f"A. {q['option_a']}",
                key=f"q{q['id']}_a",
                use_container_width=True
            ):
                st.session_state.answers[q['id']] = ("A", q['option_a'])

        with col2:
            if st.button(
                f"B. {q['option_b']}",
                key=f"q{q['id']}_b",
                use_container_width=True
            ):
                st.session_state.answers[q['id']] = ("B", q['option_b'])

        # 선택된 답변 표시
        if q['id'] in st.session_state.answers:
            choice, text = st.session_state.answers[q['id']]
            st.success(f"✓ 선택: {choice}번 - {text}")

st.markdown("---")

# 진행 상태 표시
progress = len(st.session_state.answers) / len(questions)
st.progress(progress, text=f"진행률: {len(st.session_state.answers)}/{len(questions)}")

# 모든 질문에 답변했을 때만 분석 버튼 활성화
if len(st.session_state.answers) == len(questions):
    if st.button("🔍 위인 분석 시작", use_container_width=True, type="primary"):
        st.session_state.result_shown = True

# 분석 결과 표시
if st.session_state.result_shown and len(st.session_state.answers) == len(questions):
    st.markdown("---")

    # 프롬프트 구성
    answers_text = "\n".join([
        f"Q{i}: {st.session_state.answers[i][1]}"
        for i in sorted(st.session_state.answers.keys())
    ])

    prompt = f"""사용자 이름: {st.session_state.user_name}

다음은 이 사람의 성향 진단 결과입니다:

{answers_text}

{st.session_state.user_name}의 성향 진단 결과를 바탕으로 역사 속에서 가장 비슷한 특징을 가진 위인 3명을 찾아주세요.

각 위인에 대해 다음 형식으로 답변해주세요 (반드시 영어 이름도 포함):

**위인 1: [한국 이름] (English Name)**
- 주요 업적: [업적 설명]
- 나와의 유사점: [구체적인 유사한 성향 3가지]

**위인 2: [한국 이름] (English Name)**
- 주요 업적: [업적 설명]
- 나와의 유사점: [구체적인 유사한 성향 3가지]

**위인 3: [한국 이름] (English Name)**
- 주요 업적: [업적 설명]
- 나와의 유사점: [구체적인 유사한 성향 3가지]
"""

    with st.spinner("Claude가 당신과 비슷한 위인을 찾고 있습니다..."):
        result = ask_ai(prompt)

    st.subheader(f"🌟 {st.session_state.user_name}님의 분석 결과")

    # 결과를 JSON 파일에 저장
    save_history(st.session_state.user_name, result)
    st.success("✅ 결과가 history.json에 저장되었습니다.")

    # 위인 정보와 이미지 표시
    sections = re.split(r'\*\*위인 \d+:', result)

    for i, section in enumerate(sections[1:], 1):
        # 위인 이름과 영어 이름 추출
        name_match = re.search(r'^([^(]+)\s*\(([^)]+)\)', section)
        if name_match:
            person_name = name_match.group(1).strip()
            english_name = name_match.group(2).strip()

            with st.container(border=True):
                col1, col2 = st.columns([1, 2])

                # 이미지 표시 (영어 이름으로 검색)
                with col1:
                    image_url = get_person_image(english_name)
                    if image_url:
                        st.image(image_url, caption=person_name, use_column_width=True)
                    else:
                        st.info(f"📷 {person_name}")

                # 정보 표시
                with col2:
                    st.markdown(f"**위인 {i}: {person_name}**")
                    content = section.split('\n', 1)[1] if '\n' in section else ""
                    st.markdown(content)

    # 초기화 버튼
    if st.button("↺ 다시 시작", use_container_width=True):
        st.session_state.user_name = ""
        st.session_state.answers = {}
        st.session_state.result_shown = False
        st.rerun()
