"""DERK Content Intelligence: exploratory, data-driven topic discovery.

Run: python content_intelligence/thematic_analysis.py article_corpus.csv
Requires: pandas scikit-learn

Topics are learned from the corpus, not predefined. Top words are *descriptors*,
not validated semantic labels. A researcher must inspect sample articles.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import pandas as pd
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfVectorizer

STOPWORDS = set("и в во не что он на я с со как а то все она так его но да ты к у же вы за бы по только ее мне было вот от меня еще нет о из ему теперь когда даже ну вдруг ли если уже или ни быть был него до вас нибудь опять уж вам ведь там потом себя ничего ей может они тут где есть надо ней для мы тебя их чем была сам чтоб без будто чего раз тоже себе под будет ж тогда кто этот того потому этого какой совсем ним здесь этом один почти мой тем чтобы нее сейчас были куда зачем всех никогда можно при об над под про между также это эти этих этой который которая которые которых которое которым которых которого данный данных года году лет сайт сайте статья статьи материал материалы казахстан казахстана немец немцы немцев немецкий немецкого возрождение".split())


def analyze(input_csv: str, output_dir: str = "topic_results", n_topics: int = 4) -> None:
    data = pd.read_csv(input_csv).fillna("")
    if "text" not in data.columns:
        raise ValueError("CSV должен содержать колонку 'text'")
    if "classification" in data.columns:
        data = data[data["classification"].eq("article")].copy()
    data = data[data["text"].astype(str).str.strip().ne("")].copy()
    data = data.drop_duplicates(subset=["url"] if "url" in data.columns else ["text"])
    if len(data) < 5:
        raise ValueError("Для пробного выделения тем необходимо хотя бы 5 текстов")

    vectorizer = TfidfVectorizer(
        lowercase=True,
        token_pattern=r"(?u)\b[а-яёa-z]{4,}\b",
        stop_words=list(STOPWORDS),
        min_df=2,
        max_df=0.85,
        max_features=2500,
        ngram_range=(1, 2),
        sublinear_tf=True,
    )
    matrix = vectorizer.fit_transform(data["text"].astype(str))
    count = min(n_topics, len(data) - 1, matrix.shape[1])
    if count < 2:
        raise ValueError("Недостаточно повторяющейся лексики для выделения тем")
    model = NMF(n_components=count, init="nndsvda", random_state=42, max_iter=700)
    weights = model.fit_transform(matrix)
    terms = vectorizer.get_feature_names_out()
    topic_names = []
    topic_rows = []
    for i, component in enumerate(model.components_):
        keywords = [terms[j] for j in component.argsort()[-10:][::-1]]
        name = f"Тема {i+1} (требует интерпретации)"
        topic_names.append(name)
        topic_rows.append({"topic_id": i+1, "topic": name, "keywords": ", ".join(keywords)})

    # Assign one leading topic to each article to make percentages sum to 100%.
    # Multi-topic interpretation remains possible after human review.
    leading = weights.argmax(axis=1)
    data["topic_id"] = leading + 1
    data["topic"] = [topic_names[i] for i in leading]
    data["topic_strength"] = [round(float(weights[i, t] / max(weights[i].sum(), 1e-12)), 3) for i, t in enumerate(leading)]
    counts = data.groupby(["topic_id", "topic"]).size().reset_index(name="articles")
    counts["share_percent"] = (counts["articles"] / len(data) * 100).round(1)
    summary = pd.DataFrame(topic_rows).merge(counts, on=["topic_id", "topic"], how="left").fillna({"articles": 0, "share_percent": 0})

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    data.to_csv(output / "articles_with_topics.csv", index=False, encoding="utf-8-sig")
    summary.to_csv(output / "topic_summary.csv", index=False, encoding="utf-8-sig")
    print(f"Проанализировано статей: {len(data)}; предварительных тем: {count}")
    print(summary.to_string(index=False))
    print("Результаты:", output.resolve())
    print("ВНИМАНИЕ: это пробные статистические кластеры, а не подтверждённые темы.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv", help="Путь к article_corpus.csv")
    parser.add_argument("--output-dir", default="topic_results")
    parser.add_argument("--topics", type=int, default=4)
    args = parser.parse_args()
    analyze(args.input_csv, args.output_dir, args.topics)
