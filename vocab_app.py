import os
import json
import sqlite3
import csv
import random
from datetime import datetime
from openai import OpenAI
import streamlit as st

# ========== 配置部分 ==========
DB_PATH = "vocab.db"

# 初始化 OpenAI 客户端
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ========== 数据库相关函数 ==========

def init_db():
    """初始化数据库，没有表就创建；旧库自动补上 difficulty 字段。"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS vocab (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL,
            meaning_en TEXT,
            meaning_zh TEXT,
            example TEXT,
            topic TEXT,
            tag TEXT,
            difficulty INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    # 旧库可能没有 difficulty 字段，这里尝试加一列
    try:
        c.execute("ALTER TABLE vocab ADD COLUMN difficulty INTEGER;")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()


def insert_vocab_items(items, topic=None, tag=None, difficulty=None):
    """
    items: 列表，每个元素是 dict:
        {
            "word": ...,
            "meaning_en": ...,
            "meaning_zh": ...,
            "example": ...
        }
    difficulty: 1~5 或 None
    """
    if not items:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for it in items:
        c.execute(
            """
            INSERT INTO vocab (word, meaning_en, meaning_zh, example, topic, tag, difficulty)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                it.get("word"),
                it.get("meaning_en"),
                it.get("meaning_zh"),
                it.get("example"),
                topic,
                tag,
                difficulty,
            ),
        )
    conn.commit()
    conn.close()


def get_random_items(limit=10, difficulty=None):
    """随机抽词；如果传 difficulty，就按生僻程度筛选。"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if difficulty is None:
        c.execute(
            """
            SELECT id, word, meaning_en, meaning_zh, example, topic, tag, difficulty, created_at
            FROM vocab
            ORDER BY RANDOM()
            LIMIT ?;
            """,
            (limit,),
        )
    else:
        c.execute(
            """
            SELECT id, word, meaning_en, meaning_zh, example, topic, tag, difficulty, created_at
            FROM vocab
            WHERE difficulty = ?
            ORDER BY RANDOM()
            LIMIT ?;
            """,
            (difficulty, limit),
        )
    rows = c.fetchall()
    conn.close()
    return rows


def get_recent_items(limit=50):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        SELECT id, word, meaning_en, meaning_zh, example, topic, tag, difficulty, created_at
        FROM vocab
        ORDER BY id DESC
        LIMIT ?;
        """,
        (limit,),
    )
    rows = c.fetchall()
    conn.close()
    return rows


def export_to_csv(filename="vocab_export.csv"):
    """导出所有词汇到 CSV，包含 difficulty。"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        SELECT word, meaning_en, meaning_zh, example, topic, tag, difficulty, created_at
        FROM vocab
        ORDER BY id;
        """
    )
    rows = c.fetchall()
    conn.close()

    headers = [
        "word",
        "meaning_en",
        "meaning_zh",
        "example",
        "topic",
        "tag",
        "difficulty",
        "created_at",
    ]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    return filename

# ========== GPT 生成部分 ==========

def call_gpt_for_vocab(topic, num_items=10, difficulty=2, forbidden_words=None):
    """
    让 GPT 生成 JSON 格式的生活场景词汇。
    difficulty: 1 (非常常用) ~ 5 (比较生僻/高级)
    forbidden_words: 已出现过的词列表，要求 GPT 避免重复。
    """
    random_seed = random.randint(1, 1_000_000)

    forbidden_block = ""
    if forbidden_words:
        unique = sorted({w.strip() for w in forbidden_words if w})
        if unique:
            joined = ", ".join(unique[:200])  # 避免太长
            forbidden_block = f"""
Important:
- Do NOT include any of these previously generated words or phrases (avoid exact matches):
  {joined}
- Prefer new vocabulary rather than repeating the same items.
"""

    prompt = f"""
You are an English tutor for a Chinese ESL student in the United States.

Generate {num_items} daily-life English words or short phrases
for the topic "{topic}", with rarity level {difficulty} on a 1–5 scale:

1 = very common, basic, used every day
2 = common but slightly more specific
3 = moderately uncommon but useful
4 = uncommon but natural in real conversations
5 = rare/advanced but practical and expressive

{forbidden_block}

Additional instructions:
- Every time this request is called, you MUST generate a NEW and DIFFERENT
  set of vocabulary, even if the topic and difficulty are the same.
- Use the random seed below to diversify your choice.
- Avoid only the most obvious textbook examples; explore more natural daily language.

Random seed for this generation: {random_seed}

Return ONLY valid JSON in this exact format (no explanation, no markdown):

[
  {{
    "word": "checkup",
    "meaning_en": "a medical examination to see if you are healthy",
    "meaning_zh": "体检；检查身体",
    "example": "I scheduled a checkup with my doctor for next week."
  }}
]
"""
    resp = client.chat.completions.create(
        model="gpt-4.1",   # 使用更强模型
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
    )
    content = resp.choices[0].message.content.strip()
    return json.loads(content)


def call_gpt_for_phrasal_verbs(num_items=10, difficulty=2, forbidden_words=None):
    """
    让 GPT 生成 JSON 格式的动词短语（phrasal verbs）。
    difficulty: 1 (常用) ~ 5 (生僻/高级)
    forbidden_words: 已出现过的短语列表，要求 GPT 避免重复。
    """
    random_seed = random.randint(1, 1_000_000)

    forbidden_block = ""
    if forbidden_words:
        unique = sorted({w.strip() for w in forbidden_words if w})
        if unique:
            joined = ", ".join(unique[:200])
            forbidden_block = f"""
Important:
- Do NOT include any of these previously generated phrasal verbs (avoid exact matches):
  {joined}
- Prefer new phrasal verbs rather than repeating the same items.
"""

    prompt = f"""
Generate {num_items} useful English phrasal verbs used in daily life,
with rarity level {difficulty} (1 = common/basic, 5 = rare/advanced).

Definitions:
1 = very common and basic (used every day)
2 = common but slightly more advanced
3 = moderately uncommon but helpful for fluency
4 = uncommon but expressive, more nuanced
5 = rare, advanced but still practical phrasal verbs

{forbidden_block}

Additional instructions:
- Every time this request is called, you MUST generate a NEW and DIFFERENT
  set of phrasal verbs, even with the same difficulty level.
- Use the random seed below to diversify your choice.
- Avoid only textbook-style examples; focus on natural spoken English.

Random seed for this generation: {random_seed}

Return ONLY valid JSON in this exact format (no explanation, no markdown):

[
  {{
    "word": "dress up",
    "meaning_en": "to put on nice or formal clothes",
    "meaning_zh": "盛装打扮",
    "example": "We have to dress up for the wedding this weekend."
  }}
]
"""
    resp = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    content = resp.choices[0].message.content.strip()
    return json.loads(content)

# ========== Streamlit 界面部分 ==========

def page_generate_vocab():
    st.header("🔤 生成生活场景词汇")

    topic = st.text_input("生活场景（中文或英文都可以）：", value="看病 / 去医院")
    num_items = st.slider("生成多少个词/短语？", min_value=5, max_value=30, value=12, step=1)
    difficulty = st.slider("生僻程度 (1 = 非常常用, 5 = 比较生僻)", 1, 5, 2)

    # 准备历史单词，用于禁止重复（按主题区分）
    normalized_topic = topic.strip().lower()
    vocab_history = st.session_state.setdefault("vocab_history", {})
    forbidden_words = sorted(vocab_history.get(normalized_topic, set()))

    if st.button("✨ 用 GPT 生成新词汇"):
        if not os.getenv("OPENAI_API_KEY"):
            st.error("没有找到 OPENAI_API_KEY 环境变量，请先配置 API Key。")
            return

        with st.spinner("正在向 GPT 请求词汇，请稍等..."):
            try:
                items = call_gpt_for_vocab(
                    topic,
                    num_items=num_items,
                    difficulty=difficulty,
                    forbidden_words=forbidden_words,
                )
            except Exception as e:
                st.error(f"调用 GPT 出错：{e}")
                return

        # 更新 session_state 历史 & 本次结果
        st.session_state["last_vocab_items"] = items
        st.session_state["last_vocab_topic"] = topic
        st.session_state["last_vocab_difficulty"] = difficulty

        # 更新历史禁止词列表
        hist_set = vocab_history.get(normalized_topic, set())
        for it in items:
            w = (it.get("word") or "").strip().lower()
            if w:
                hist_set.add(w)
        vocab_history[normalized_topic] = hist_set
        st.session_state["vocab_history"] = vocab_history

    # 如果有历史生成结果，就展示出来
    items = st.session_state.get("last_vocab_items", None)
    if items:
        topic = st.session_state.get("last_vocab_topic", topic)
        difficulty = st.session_state.get("last_vocab_difficulty", difficulty)

        st.success(f"已生成 {len(items)} 个词汇（主题: {topic}，难度 Level {difficulty}）")
        save_all_clicked = st.button("💾 将这批词汇全部保存到词库")

        for i, it in enumerate(items, start=1):
            st.markdown(f"### {i}. {it['word']}")
            st.write(f"- **英文释义**: {it['meaning_en']}")
            st.write(f"- **中文释义**: {it['meaning_zh']}")
            st.write(f"- **例句**: {it['example']}")

            # 单独保存按钮
            if st.button("添加到我的词库", key=f"add_vocab_{i}"):
                insert_vocab_items(
                    [it],
                    topic=topic,
                    tag=f"daily_vocab_{difficulty}",
                    difficulty=difficulty,
                )
                st.success(f"✅ 已添加：{it['word']}")

            st.write("---")

        # 一键保存全部
        if save_all_clicked:
            insert_vocab_items(
                items,
                topic=topic,
                tag=f"daily_vocab_{difficulty}",
                difficulty=difficulty,
            )
            st.success("✅ 当前这一批词汇已全部保存到词库。")


def page_generate_phrasal_verbs():
    st.header("🧩 生成动词短语（phrasal verbs）")

    num_items = st.slider("生成多少个动词短语？", min_value=5, max_value=30, value=10, step=1)
    difficulty = st.slider("生僻程度 (1 = 常用, 5 = 生僻/高级)", 1, 5, 2)

    # 准备历史短语，用于禁止重复（按难度区分）
    phrasal_history = st.session_state.setdefault("phrasal_history", {})
    forbidden_words = sorted(phrasal_history.get(difficulty, set()))

    if st.button("✨ 用 GPT 生成新短语"):
        if not os.getenv("OPENAI_API_KEY"):
            st.error("没有找到 OPENAI_API_KEY 环境变量，请先配置 API Key。")
            return

        with st.spinner("正在生成动词短语，请稍等..."):
            try:
                items = call_gpt_for_phrasal_verbs(
                    num_items=num_items,
                    difficulty=difficulty,
                    forbidden_words=forbidden_words,
                )
            except Exception as e:
                st.error(f"调用 GPT 出错：{e}")
                return

        st.session_state["last_phrasal_items"] = items
        st.session_state["last_phrasal_difficulty"] = difficulty

        # 更新 phrasal 历史
        hist_set = phrasal_history.get(difficulty, set())
        for it in items:
            w = (it.get("word") or "").strip().lower()
            if w:
                hist_set.add(w)
        phrasal_history[difficulty] = hist_set
        st.session_state["phrasal_history"] = phrasal_history

    items = st.session_state.get("last_phrasal_items", None)
    if items:
        difficulty = st.session_state.get("last_phrasal_difficulty", difficulty)
        st.success(f"已生成 {len(items)} 个动词短语（难度 Level {difficulty}）")
        save_all_clicked = st.button("💾 将这批短语全部保存到词库")

        for i, it in enumerate(items, start=1):
            st.markdown(f"### {i}. {it['word']}")
            st.write(f"- **英文释义**: {it['meaning_en']}")
            st.write(f"- **中文释义**: {it['meaning_zh']}")
            st.write(f"- **例句**: {it['example']}")

            if st.button("添加到我的词库", key=f"add_phrasal_{i}"):
                insert_vocab_items(
                    [it],
                    topic="phrasal_verbs",
                    tag=f"phrasal_{difficulty}",
                    difficulty=difficulty,
                )
                st.success(f"✅ 已添加：{it['word']}")

            st.write("---")

        if save_all_clicked:
            insert_vocab_items(
                items,
                topic="phrasal_verbs",
                tag=f"phrasal_{difficulty}",
                difficulty=difficulty,
            )
            st.success("✅ 当前这一批动词短语已全部保存到词库。")


def page_review_quiz():
    st.header("📚 复习 / 小测验")

    num_items = st.slider("抽多少个词来复习？", min_value=5, max_value=30, value=10, step=1)
    difficulty_choice = st.selectbox(
        "按生僻程度筛选（可选）：",
        ["全部", "1", "2", "3", "4", "5"],
        index=0,
    )

    if st.button("🎯 抽题开始复习"):
        if difficulty_choice == "全部":
            diff = None
        else:
            diff = int(difficulty_choice)

        rows = get_random_items(limit=num_items, difficulty=diff)
        if not rows:
            st.warning("数据库里还没有符合条件的词汇，先去“生成词汇”页面添加一些吧。")
            return

        for row in rows:
            _id, word, meaning_en, meaning_zh, example, topic, tag, difficulty, created_at = row
            st.markdown(f"### {word}")
            st.caption(
                f"主题: {topic or '-'} | 标签: {tag or '-'} | "
                f"难度: {difficulty if difficulty is not None else '-'} | 添加时间: {created_at}"
            )

            with st.expander("👉 显示释义和中文"):
                st.write(f"**英文释义**: {meaning_en}")
                st.write(f"**中文释义**: {meaning_zh}")
            with st.expander("👉 显示例句"):
                st.write(example)
            st.write("---")


def page_recent_and_export():
    st.header("🗃 最近添加的词汇 & 导出 CSV")

    limit = st.slider("显示最近多少条词汇？", min_value=20, max_value=1000, value=100, step=20)
    rows = get_recent_items(limit=limit)

    if not rows:
        st.info("还没有任何词汇，先去添加一些吧～")
    else:
        st.subheader(f"最近添加的词汇（最多 {limit} 条）")
        for row in rows:
            _id, word, meaning_en, meaning_zh, example, topic, tag, difficulty, created_at = row
            st.markdown(
                f"**{word}**  （主题: {topic or '-'} / 标签: {tag or '-'} / "
                f"难度: {difficulty if difficulty is not None else '-'}）"
            )
            st.caption(f"添加时间: {created_at}")
            st.write(f"- 英文释义: {meaning_en}")
            st.write(f"- 中文释义: {meaning_zh}")
            st.write(f"- 例句: {example}")
            st.write("---")

    st.subheader("📤 导出为 CSV 文件")
    if st.button("导出 vocab_export.csv"):
        filename = export_to_csv()
        st.success(f"已导出为 {filename}，在当前目录下可以找到这个文件。")


def main():
    st.set_page_config(page_title="我的英语背单词小助手", page_icon="📘", layout="wide")
    init_db()

    st.sidebar.title("📘 背单词 App")
    page = st.sidebar.radio(
        "选择页面：",
        (
            "生成生活场景词汇",
            "生成动词短语",
            "复习 / 小测验",
            "查看最近 & 导出 CSV",
        ),
    )

    if page == "生成生活场景词汇":
        page_generate_vocab()
    elif page == "生成动词短语":
        page_generate_phrasal_verbs()
    elif page == "复习 / 小测验":
        page_review_quiz()
    elif page == "查看最近 & 导出 CSV":
        page_recent_and_export()


if __name__ == "__main__":
    main()
