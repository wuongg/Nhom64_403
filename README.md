# Nhom064-403 — XanhSM Help Center AI (prototype)

## FastAPI backend

This repo now has a backend contract for a FastAPI-style app on top of the existing CLI pipeline. The examples below assume the app is exposed as `app.api.main:create_app`; if the final entrypoint lands elsewhere, keep the same env contract and adjust the import path.

Set the runtime environment:

```powershell
$env:RAW_DIR="$PWD/raw"
$env:DB_URL="sqlite:///./backend.db"
$env:OPENAI_API_KEY="YOUR_KEY"
```

Run the API:

```powershell
uvicorn app.api.main:app --factory --reload
```  

Run the frontend:  
```
.venv\Scripts\python.exe -m http.server 3000 --directory frontend
```  

Run tests:

```powershell
pytest -q
```

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
python eval_ragas.py --n 10 --k 5 --role-mode rule --answer-model gpt-4o-mini --evaluator-model gpt-4o-mini --out ragas_results.json
```

Output:
- In ra metrics tổng hợp (ví dụ `context_recall`, `faithfulness`, `factual_correctness(...)`)
- Lưu file kết quả (mặc định `ragas_results.json`) gồm config + samples + scores theo từng sample

## Cơ chế Retry & Fallback

Hệ thống tích hợp cơ chế tự động thử lại (Retry) và chuyển hướng (Fallback) để đảm bảo độ tin cậy khi các dịch vụ AI gặp sự cố.

### Luồng hoạt động
1. **Lần 1**: Gọi model chính (mặc định `gpt-4o-mini`) với timeout cấu hình.
2. **Retry**: Nếu gặp lỗi transient (Rate Limit, Timeout, Server 5xx), hệ thống tự động thử lại tối đa `LLM_RETRY_MAX` lần với thuật toán Exponential Backoff.
3. **Fallback**: Nếu vẫn thất bại sau các lần retry, hệ thống sẽ chuyển sang gọi `LLM_FALLBACK_MODEL` (mặc định dùng Google Gemini 2.0 Flash Lite qua OpenRouter).
4. **Final Fallback**: Nếu toàn bộ đều lỗi, hệ thống sẽ trả về `preview` mode kèm thông tin lỗi.

### Cấu hình môi trường (.env)

| Biến | Mặc định | Mô tả |
|------|----------|-------|
| `LLM_RETRY_MAX` | `2` | Số lần thử lại tối đa sau lần gọi đầu tiên |
| `LLM_RETRY_BASE_DELAY` | `1.0` | Giây chờ cơ bản cho exponential backoff |
| `LLM_TIMEOUT` | `30.0` | Giây timeout cho mỗi request LLM |
| `LLM_FALLBACK_MODEL` | `google/gemini-2.0-flash-lite...:free` | Model dự phòng (OpenRouter) |
| `OPENROUTER_API_KEY` | `null` | API Key nếu dùng fallback qua OpenRouter |

### Giám sát và Debug
- **Non-stream**: Trường `retry_info` trong response JSON chứa chi tiết các lần thử.
- **Streaming (SSE)**: Hệ thống yield event `type: "retry"` để frontend hiển thị trạng thái chờ cho người dùng trước khi thử lại model mới.

## Tuỳ chọn

- `--role user|driver|merchant`: ép role (bỏ qua decision tree)
- `--k 5`: số đoạn KB đưa vào prompt
- `--role-mode auto|llm|rule`: mặc định `auto` (ưu tiên LLM nếu có `OPENAI_API_KEY`)

