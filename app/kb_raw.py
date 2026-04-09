from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RawKBEntry:
    id: str
    text: str
    metadata: dict

    @property
    def category(self) -> str:
        return str(self.metadata.get("category", ""))

    @property
    def topic(self) -> str:
        return str(self.metadata.get("topic", ""))

    @property
    def question(self) -> str:
        return str(self.metadata.get("question", ""))


def _infer_category_from_filename(name: str) -> str:
    n = name.lower()
    if "restaurant" in n:
        return "Dành cho Nhà hàng"
    if "driver-bike" in n:
        return "Dành cho tài xế Bike"
    if "driver-taxi" in n:
        return "Dành cho tài xế Taxi"
    if "user" in n:
        return "Dành cho người dùng"
    return "Unknown"


def _stable_id(*parts: str) -> str:
    h = hashlib.md5()
    for p in parts:
        h.update(p.encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()


def load_raw_folder(raw_dir: str | Path) -> list[RawKBEntry]:
    raw_path = Path(raw_dir)
    files = sorted(raw_path.glob("*.md"))
    entries: list[RawKBEntry] = []

    for fp in files:
        category = _infer_category_from_filename(fp.name)
        content = fp.read_text(encoding="utf-8")
        lines = content.splitlines()

        current_topic: str | None = None
        current_question: str | None = None
        answer_lines: list[str] = []

        def flush() -> None:
            nonlocal current_question, answer_lines
            if not current_question:
                answer_lines = []
                return
            answer = "\n".join(answer_lines).strip()
            if not answer:
                answer_lines = []
                return
            q = current_question.strip()
            t = (current_topic or "").strip()
            eid = _stable_id(fp.name, category, t, q, answer[:2000])
            text = (
                f"Đối tượng: {category}\n"
                f"Chủ đề: {t}\n"
                f"Câu hỏi: {q}\n"
                f"Trả lời: {answer}"
            )
            entries.append(
                RawKBEntry(
                    id=eid,
                    text=text,
                    metadata={
                        "category": category,
                        "topic": t,
                        "question": q,
                        "source": str(fp),
                    },
                )
            )
            answer_lines = []

        for line in lines:
            # Topic lines start with "## "
            if line.startswith("## "):
                flush()
                current_question = None
                current_topic = line[3:].strip()
                continue

            # Question lines start with "### "
            if line.startswith("### "):
                flush()
                current_question = line[4:].strip()
                answer_lines = []
                continue

            # Ignore top metadata & main title
            if line.startswith("# "):
                continue
            if line.startswith("- Nguồn:") or line.startswith("- Ngày crawl:") or line.startswith("- Tổng số"):
                continue

            if current_question is not None:
                answer_lines.append(line)

        flush()

    return entries

