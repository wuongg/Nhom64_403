# Nhom064-403 — XanhSM Help Center AI (prototype)

Prototype tối thiểu cho luồng:

- **LLM role classifier (tool-like)** để chọn **role** (user / driver / merchant) + nhánh **safety**
- Lọc Knowledge Base từ `raw/*.md` theo role và **trích top-k** đoạn liên quan
- Ghép **prompt** và gọi LLM (OpenAI). Nếu chưa có API key thì chạy chế độ preview prompt.

## Quickstart (Windows / PowerShell)

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Chạy CLI (không cần API key, chỉ xem prompt + KB)

```bash
python -m app "Mình bị trừ tiền 2 lần" --show-prompt
```

### Chạy CLI có gọi OpenAI

Set biến môi trường:

```powershell
$env:OPENAI_API_KEY="YOUR_KEY"
```

Chạy:

```bash
python -m app "Mình muốn xuất hóa đơn VAT cho chuyến hôm qua"
```

## RAG Evaluation (Ragas)

Dự án có sẵn script `eval_ragas.py` để đánh giá pipeline RAG theo hướng dẫn của Ragas: `https://docs.ragas.io/en/stable/getstarted/rag_eval/`.

Cài dependencies:

```bash
pip install -r requirements.txt
```

Chạy đánh giá (ví dụ 10 câu hỏi ngẫu nhiên trong KB, top-k=5):

```bash
python eval_ragas.py --n 10 --k 5 --role-mode rule --answer-model gpt-4.1-mini --evaluator-model gpt-4.1-mini --out ragas_results.json
```

Output:
- In ra metrics tổng hợp (ví dụ `context_recall`, `faithfulness`, `factual_correctness(...)`)
- Lưu file kết quả (mặc định `ragas_results.json`) gồm config + samples + scores theo từng sample

## Tuỳ chọn

- `--role user|driver|merchant`: ép role (bỏ qua decision tree)
- `--k 5`: số đoạn KB đưa vào prompt
- `--role-mode auto|llm|rule`: mặc định `auto` (ưu tiên LLM nếu có `OPENAI_API_KEY`)

