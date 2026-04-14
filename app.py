import json
import random
from datetime import datetime
import streamlit as st
from pathlib import Path

# --- 設定 ---
QUESTIONS_PATH = Path(__file__).parent / "questions.json"

# --- 画面設定 ---
st.set_page_config(
    page_title="トランス知識クイズ",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- カスタムCSS ---
st.markdown("""
<style>
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans JP", sans-serif;
    }

    .stApp {
        background: #F9F9F8;
        color: #1A1A1A;
    }

    section[data-testid="stSidebar"] {
        background: #F5F5F4;
    }

    .main-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1A1A1A;
        margin-bottom: 0.1rem;
    }

    .sub-title {
        color: #6B7280;
        font-size: 0.85rem;
        margin-bottom: 2rem;
    }

    .question-card {
        background: #FFFFFF;
        border: 1px solid #E5E5E5;
        border-left: 3px solid #D97706;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }

    .question-number {
        color: #D97706;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }

    .question-text {
        font-size: 1.05rem;
        font-weight: 500;
        color: #1A1A1A;
        line-height: 1.7;
    }

    .answer-correct {
        background: #F0FDF4;
        border: 1px solid #BBF7D0;
        border-radius: 6px;
        padding: 0.8rem 1rem;
        color: #166534;
        margin: 0.4rem 0;
    }

    .answer-wrong {
        background: #FEF2F2;
        border: 1px solid #FECACA;
        border-radius: 6px;
        padding: 0.8rem 1rem;
        color: #991B1B;
        margin: 0.4rem 0;
    }

    .answer-neutral {
        background: #F9F9F9;
        border: 1px solid #E5E5E5;
        border-radius: 6px;
        padding: 0.8rem 1rem;
        color: #374151;
        margin: 0.4rem 0;
    }

    .score-display {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1A1A1A;
        text-align: center;
    }

    .score-label {
        text-align: center;
        color: #6B7280;
        font-size: 0.85rem;
    }

    .explanation-box {
        background: #FFFBEB;
        border: 1px solid #FDE68A;
        border-radius: 6px;
        padding: 1rem;
        margin-top: 0.8rem;
        color: #92400E;
        font-size: 0.9rem;
        line-height: 1.6;
    }

    .stButton > button {
        background: #FFFFFF;
        border: 1px solid #D1D5DB;
        color: #374151;
        font-size: 0.85rem;
        transition: all 0.15s;
    }

    .stButton > button:hover {
        background: #F3F4F6;
        border-color: #9CA3AF;
        color: #1A1A1A;
    }

    div[data-testid="stRadio"] label {
        color: #1A1A1A !important;
    }

    div[data-testid="stRadio"] label:hover {
        background: #F3F4F6;
        border-radius: 4px;
    }

    .stProgress > div > div {
        background: #D97706;
    }
</style>
""", unsafe_allow_html=True)


# --- データ読み込み ---
@st.cache_data
def load_questions():
    with open(QUESTIONS_PATH, encoding="utf-8") as f:
        return json.load(f)


def build_report(questions: list, answers: dict) -> str:
    """誤答レポートをMarkdown文字列で返す"""
    wrong_items = []
    for i, q in enumerate(questions):
        user_ans = answers.get(i, "（未回答）")
        correct_key = q.get("correct", "")
        if not user_ans.startswith(correct_key):
            correct_choice = next(
                (c for c in q.get("choices", []) if c.startswith(correct_key)),
                correct_key,
            )
            wrong_items.append((i + 1, q, user_ans, correct_choice))

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# トランス知識クイズ 誤答レポート",
        f"",
        f"実施日時：{now}",
        f"結果：{len(questions) - len(wrong_items)} / {len(questions)} 正解　（誤答 {len(wrong_items)} 問）",
        f"",
        f"---",
        f"",
    ]

    if not wrong_items:
        lines.append("誤答なし。全問正解です！")
    else:
        for num, q, user_ans, correct_choice in wrong_items:
            type_label = (
                q.get("type", "")
                .replace("multiple_choice", "4択")
                .replace("true_false", "○×")
                .replace("fill_blank", "穴埋め")
            )
            diff_label = {"basic": "入門", "standard": "標準", "advanced": "応用"}.get(
                q.get("difficulty", ""), q.get("difficulty", "")
            )
            lines += [
                f"## Q{num}　{q.get('category', '')} ／ {type_label} ／ {diff_label}",
                f"",
                f"**問題：** {q['question']}",
                f"",
                f"- あなたの回答：{user_ans}",
                f"- 正解：{correct_choice}",
                f"",
                f"> **解説：** {q.get('explanation', '')}",
                f"",
                f"---",
                f"",
            ]

    return "\n".join(lines)


# --- セッション状態の初期化 ---
def init_session():
    defaults = {
        "questions": [],
        "current_q": 0,
        "answers": {},
        "quiz_started": False,
        "quiz_finished": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_session()

# --- questions.json 存在確認 ---
if not QUESTIONS_PATH.exists():
    st.error(f"⚠️ 問題ファイルが見つかりません: {QUESTIONS_PATH}")
    st.stop()

all_questions = load_questions()

# --- サイドバー ---
with st.sidebar:
    st.markdown("### ⚙️ クイズ設定")

    # カテゴリ（動的生成）
    categories = ["すべて"] + sorted(set(q["category"] for q in all_questions))
    selected_category = st.selectbox("カテゴリ", categories)

    # 問題形式
    selected_type = st.selectbox("問題形式", ["すべて", "4択", "○×", "穴埋め"])

    # 難易度（動的生成）
    difficulties = ["すべて"] + sorted(
        set(q.get("difficulty", "") for q in all_questions if q.get("difficulty")),
        key=lambda x: {"basic": 0, "standard": 1, "advanced": 2}.get(x, 9)
    )
    diff_labels = {
        "すべて": "すべて",
        "basic": "入門",
        "standard": "標準",
        "advanced": "応用",
    }
    difficulty_display = [diff_labels.get(d, d) for d in difficulties]
    selected_difficulty_label = st.selectbox("難易度", difficulty_display)
    selected_difficulty = difficulties[difficulty_display.index(selected_difficulty_label)]

    # フィルタリング
    filtered = all_questions

    if selected_category != "すべて":
        filtered = [q for q in filtered if q["category"] == selected_category]

    if selected_type != "すべて":
        type_map = {"4択": "multiple_choice", "○×": "true_false", "穴埋め": "fill_blank"}
        filtered = [q for q in filtered if q["type"] == type_map[selected_type]]

    if selected_difficulty != "すべて":
        diff_map = {"入門": "basic", "標準": "standard", "応用": "advanced"}
        filtered = [q for q in filtered if q.get("difficulty") == diff_map.get(selected_difficulty_label, selected_difficulty)]

    # 問題数スライダー（フィルタ後の数に応じて上限調整）
    max_q = max(1, len(filtered))
    default_q = min(10, max_q)
    num_q = st.slider("問題数", min_value=5, max_value=min(30, max_q), value=default_q) if max_q >= 5 else st.slider("問題数", min_value=1, max_value=max_q, value=default_q)

    st.caption(f"対象問題数：{len(filtered)} 問")

    generate_btn = st.button("🎲 問題をランダムに選ぶ", use_container_width=True)


# --- メインエリア ---
st.markdown('<div class="main-title">⚡ トランス知識クイズ</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">変圧器の理論・設計知識を確認するクイズアプリ（全{len(all_questions)}問）</div>', unsafe_allow_html=True)

# --- 問題抽出 ---
if generate_btn:
    if len(filtered) == 0:
        st.error("⚠️ 条件に合う問題がありません。フィルタを変更してください。")
    else:
        actual_num = min(num_q, len(filtered))
        if actual_num < num_q:
            st.warning(f"⚠️ 条件に合う問題が {len(filtered)} 問しかありません。全件表示します。")
        questions = random.sample(filtered, actual_num)
        st.session_state.questions = questions
        st.session_state.current_q = 0
        st.session_state.answers = {}
        st.session_state.quiz_started = True
        st.session_state.quiz_finished = False
        st.rerun()


# --- クイズ表示 ---
if st.session_state.quiz_started and st.session_state.questions:
    questions = st.session_state.questions
    total = len(questions)

    if not st.session_state.quiz_finished:
        current = st.session_state.current_q

        # プログレスバー
        progress = current / total
        st.progress(progress)
        st.caption(f"問題 {current + 1} / {total}")

        q = questions[current]

        # 問題カード
        type_label = q.get("type", "").replace("multiple_choice", "4択").replace("true_false", "○×").replace("fill_blank", "穴埋め")
        st.markdown(f"""
        <div class="question-card">
            <div class="question-number">Q{current + 1} &nbsp;·&nbsp; {type_label} &nbsp;·&nbsp; {q.get('category', '')}</div>
            <div class="question-text">{q['question']}</div>
        </div>
        """, unsafe_allow_html=True)

        # 選択肢
        choices = q.get("choices", [])
        already_answered = current in st.session_state.answers

        if not already_answered:
            selected = st.radio(
                "回答を選んでください",
                choices,
                key=f"q_{current}",
                label_visibility="collapsed"
            )

            col1, col2, col3 = st.columns([2, 1, 2])
            with col2:
                if st.button("✅ 回答する", use_container_width=True):
                    st.session_state.answers[current] = selected
                    st.rerun()

        else:
            user_answer = st.session_state.answers[current]
            correct_key = q.get("correct", "")

            for choice in choices:
                is_correct_choice = choice.startswith(correct_key)
                is_user_choice = (choice == user_answer)

                if is_correct_choice and is_user_choice:
                    st.markdown(f'<div class="answer-correct">✅ {choice}（あなたの回答・正解）</div>', unsafe_allow_html=True)
                elif is_correct_choice:
                    st.markdown(f'<div class="answer-correct">✅ {choice}（正解）</div>', unsafe_allow_html=True)
                elif is_user_choice:
                    st.markdown(f'<div class="answer-wrong">❌ {choice}（あなたの回答）</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="answer-neutral">{choice}</div>', unsafe_allow_html=True)

            # 解説
            if "explanation" in q:
                st.markdown(f'<div class="explanation-box">💡 <strong>解説：</strong>{q["explanation"]}</div>', unsafe_allow_html=True)

            # 次へボタン
            st.markdown("")
            col1, col2, col3 = st.columns([2, 1, 2])
            with col2:
                if current < total - 1:
                    if st.button("次の問題 →", use_container_width=True):
                        st.session_state.current_q += 1
                        st.rerun()
                else:
                    if st.button("📊 結果を見る", use_container_width=True):
                        st.session_state.quiz_finished = True
                        st.rerun()

    else:
        # --- 結果画面 ---
        st.markdown("## 🏆 クイズ結果")

        correct_count = 0
        for i, q in enumerate(questions):
            if i in st.session_state.answers:
                user_ans = st.session_state.answers[i]
                correct_key = q.get("correct", "")
                if user_ans.startswith(correct_key):
                    correct_count += 1

        score_pct = int(correct_count / total * 100)

        # スコア表示
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f'<div class="score-display">{correct_count}/{total}</div>', unsafe_allow_html=True)
            st.markdown('<div class="score-label">正解数</div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="score-display">{score_pct}%</div>', unsafe_allow_html=True)
            st.markdown('<div class="score-label">正答率</div>', unsafe_allow_html=True)
        with col3:
            if score_pct >= 80:
                grade, color = "優秀", "#166534"
            elif score_pct >= 60:
                grade, color = "合格", "#D97706"
            else:
                grade, color = "要復習", "#991B1B"
            st.markdown(f'<div class="score-display" style="color:{color};font-size:1.6rem">{grade}</div>', unsafe_allow_html=True)
            st.markdown('<div class="score-label">評価</div>', unsafe_allow_html=True)

        st.divider()

        # 問題ごとの振り返り
        st.markdown("### 📝 振り返り")
        for i, q in enumerate(questions):
            user_ans = st.session_state.answers.get(i, "（未回答）")
            correct_key = q.get("correct", "")
            is_correct = user_ans.startswith(correct_key)

            icon = "✅" if is_correct else "❌"
            with st.expander(f"{icon} Q{i+1}: {q['question'][:50]}..."):
                st.markdown(f"**あなたの回答:** {user_ans}")
                correct_choice = next((c for c in q.get("choices", []) if c.startswith(correct_key)), correct_key)
                st.markdown(f"**正解:** {correct_choice}")
                if "explanation" in q:
                    st.markdown(f"**解説:** {q['explanation']}")

        st.divider()

        # 誤答レポートダウンロード
        wrong_count = total - correct_count
        if wrong_count > 0:
            report_md = build_report(questions, st.session_state.answers)
            filename = f"trans_quiz_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
            st.download_button(
                label=f"📥 誤答レポートをダウンロード（{wrong_count} 問）",
                data=report_md.encode("utf-8"),
                file_name=filename,
                mime="text/markdown",
                use_container_width=True,
            )
        else:
            st.info("全問正解です！誤答レポートはありません。")

        st.markdown("")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 もう一度同じ問題", use_container_width=True):
                st.session_state.current_q = 0
                st.session_state.answers = {}
                st.session_state.quiz_finished = False
                st.rerun()
        with col2:
            if st.button("🎲 新しい問題を選ぶ", use_container_width=True):
                st.session_state.quiz_started = False
                st.session_state.questions = []
                st.rerun()

elif not st.session_state.quiz_started:
    # --- ウェルカム画面 ---
    st.markdown(f"""
    <div style="text-align:center; padding: 3rem 0; color: #6B7280;">
        <div style="font-size: 3rem; margin-bottom: 1rem;">⚡</div>
        <div style="font-size: 1.05rem; margin-bottom: 0.5rem; color: #1A1A1A; font-weight: 500;">使い方</div>
        <ol style="text-align: left; display: inline-block; line-height: 2.2; font-size: 0.9rem; color: #374151;">
            <li>サイドバーで <strong style="color:#D97706">カテゴリ・問題形式・難易度</strong> を絞り込む</li>
            <li>問題数を選んで <strong style="color:#D97706">「問題をランダムに選ぶ」</strong> を押す</li>
            <li>問題に答えて変圧器の理解度を確認</li>
        </ol>
        <br>
        <div style="font-size: 0.8rem; color: #9CA3AF;">
            カテゴリ・難易度はフィルタを「すべて」にすると全{len(all_questions)}問から出題されます
        </div>
    </div>
    """, unsafe_allow_html=True)
