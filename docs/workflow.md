# Workflow & Chức năng dự án — XanhSM Help Center AI (prototype)

## Mục tiêu
Dự án là prototype chatbot Trung tâm trợ giúp Xanh SM theo hướng **RAG (Retrieval-Augmented Generation)**:

- **Phân loại vai trò (role)** người hỏi: `user` / `driver` / `merchant` (kèm nhánh **safety**).
- **Truy xuất Knowledge Base (KB)** từ dữ liệu trong `raw/` theo role và lấy **top-k** đoạn liên quan.
- **Ghép prompt** (system + user) và **gọi OpenAI** để sinh câu trả lời.
- Nếu **thiếu `OPENAI_API_KEY`** hoặc lỗi gọi LLM thì chạy **preview mode**: vẫn phân role + retrieve KB + build prompt nhưng **không gọi LLM**.
- Backend có REST API + SSE streaming để frontend có thể hiển thị trả lời theo thời gian thực.

---

## Kiến trúc tổng quan
### Thành phần
- **Frontend**: trang tĩnh trong `frontend/` (chạy bằng `python -m http.server ...`).
- **Backend API**: `app/api/*` (routing + schema + container), expose REST + SSE streaming.
- **Core pipeline (services)**: `app/services/*` (role → kb → handoff → prompt → llm/websearch/memory).

### Dữ liệu & lưu trữ
- **KB**: markdown trong `raw/*.md` (mỗi entry có metadata như `category/topic/question`).
- **DB**: SQLite theo `DB_URL` (mặc định `sqlite:///./xanhsm_helpcenter.db`) lưu session/messages/feedback.

---

## Workflow khởi động backend (lifecycle)
Khi backend start (entrypoint `app/api/main.py`):

1. Load cấu hình từ `.env`/env qua `Settings.load()` (`app/settings.py`).
2. Build `AppContainer` (`app/api/container.py`):
   - Build `CoreServices` (`app/services/bootstrap.py`): tạo `RoleService`, `KnowledgeBaseService.load(raw_dir)`, `ChatService`, `MemoryService`, `WebSearchService`, `WebRouterService`, `HandoffService`.
   - Tạo `SqlAlchemyChatStore`, tạo schema DB.
3. Expose endpoints:
   - `GET /` thông tin service
   - `GET /health` báo `kb_loaded` và `openai_configured`
   - Router `/api/v1/*`

---

## Workflow chính của chatbot (pipeline RAG)
Luồng xử lý 1 câu hỏi (dùng chung cho API và CLI) nằm ở `ChatService` (`app/services/chat_service.py`).

### 1) Role classification
`RoleService.decide()` (`app/services/role_service.py`):

- `role_mode="auto"`: có `OPENAI_API_KEY` thì dùng LLM classifier; không có thì dùng rule-based.
- Có thể ép role bằng `role_override`.

Kết quả là `RoleDecision` gồm:

- `role`: `user|driver|merchant`
- `safety`: true/false
- `reason`, `driver_type` (nếu có)

### 2) KB retrieval (top-k theo role)
`KnowledgeBaseService.search()` (`app/services/kb_service.py`) gọi `retrieve_scored()` (`app/kb.py`):

- Lọc KB theo role → map sang category:
  - `user` → `Dành cho người dùng`
  - `driver` → `Dành cho tài xế Taxi` + `Dành cho tài xế Bike`
  - `merchant` → `Dành cho Nhà hàng`
- Scoring là **overlap keyword** (ưu tiên `question` > `topic` > `text`).
- Nếu không có hit score > 0 vẫn trả fallback top-k trong bucket role.

### 3) Handoff decision (khuyến nghị chuyển người thật)
`HandoffService.evaluate()` (`app/services/handoff_service.py`):

- Nếu `safety=true` → **handoff recommended**
- Nếu query có ý định escalation (vd “hotline”, “khiếu nại”, …) → **handoff recommended**
- Nếu KB “không có hit score > 0” → **handoff recommended**
- Ngược lại → không cần handoff

### 4) (Tuỳ chọn) Web Search router + Web Search
Trong `ChatService.prepare()`:

- Nếu bật `ENABLE_WEB_SEARCH=true` và có cấu hình provider:
  - `WebRouterService.decide()` (`app/services/web_router_service.py`) dùng LLM để quyết định:
    - có dùng web search không
    - `prefer_web` cho câu hỏi “cập nhật theo thời gian”
    - tạo `search_query` (guardrail: luôn gắn “Xanh SM …”)
  - `WebSearchService.search_sync()` (`app/services/web_search_service.py`) gọi:
    - Serper.dev (`SERPER_API_KEY`) hoặc SerpAPI (`SERPAPI_API_KEY`)

Ghi chú:
- Mặc định `ENABLE_WEB_SEARCH` đang là `False` trong `Settings`.
- Kể cả khi bật web search, prompt vẫn có nguyên tắc “ưu tiên KB”, chỉ dùng web khi liên quan trực tiếp.

### 5) Build Prompt
`build_prompt()` (`app/prompting.py`):

- System prompt theo role (user/driver/merchant) + rules “ưu tiên KB”, không bịa, không xin OTP…
- Nếu `safety=true` thêm safety rules.
- User message gồm: câu hỏi + (memory nếu có) + KB hits + (web hits nếu có).

### 6) LLM call / Preview mode
`ChatService.process()`:

- Nếu `preview_only=True` hoặc thiếu `OPENAI_API_KEY` → trả `mode="preview"` (không gọi OpenAI).
- Nếu đủ điều kiện → gọi OpenAI (`app/llm.py`) và trả:
  - `answer.text`
  - metrics (latency, token usage, ước tính cost)

---

## Workflow theo Session (API)
Backend lưu hội thoại theo session trong DB.

### 1) Tạo session
`POST /api/v1/sessions` → tạo `session_id`.

### 2) Gửi message (non-stream)
`POST /api/v1/sessions/{session_id}/messages` (`app/api/routes.py`):

1. Lấy **memory** bằng `MemoryService.build()`:
   - giữ 10 message gần nhất (user/assistant)
   - tóm tắt phần cũ hơn (nếu có OpenAI key) và lưu summary như message ẩn actor=`memory`
2. Chạy `chat_service.process()`.
3. Lưu DB:
   - message user luôn được lưu
   - message assistant chỉ lưu khi có `answer`
4. Trả response: `answer|mode|role_decision|kb_hits|web_hits|handoff|metrics`.

### 3) Gửi message (streaming SSE)
`POST /api/v1/sessions/{session_id}/messages/stream`:

- SSE event types:
  - `meta`: trả ngay (role/kb/handoff/mode) để UI render trước
  - `chunk`: text stream từ OpenAI
  - `done`: kết thúc, kèm metrics + `assistant_message_id`
  - `error`: nếu lỗi giữa chừng

### 4) Feedback
`POST /api/v1/sessions/{session_id}/feedback`:

- Lưu đánh giá `helpful|not_helpful` + reason + note gắn với message.

---

## Workflow CLI
Chạy `python -m app "câu hỏi..."` (`app/__main__.py`):

- Load settings, build services.
- Chạy `chat_service.process()`.
- `--show-prompt` hoặc không có key → in prompt/KB (preview).
- Có key → in answer + metrics.

---

## Chức năng theo thư mục/module
### `app/api/`
- **`main.py`**: tạo app, CORS, health/index, lifespan build/close container.
- **`routes.py`**: REST API + SSE streaming; quản lý session/messages/feedback; persist DB.
- **`schemas.py`**: Pydantic schema cho request/response.
- **`container.py`**: build container (core services + DB store).
- **`framework.py`**: “mini FastAPI” (router, request/response, CORS) dùng nội bộ.

### `app/services/`
- **`chat_service.py`**: orchestration pipeline (role → kb → handoff → web router/search → prompt → llm).
- **`role_service.py`**: quyết định role (auto/llm/rule) + override.
- **`kb_service.py`**: load/search KB từ `raw/`.
- **`handoff_service.py`**: rule khuyến nghị chuyển người thật.
- **`memory_service.py`**: tóm tắt hội thoại + lấy turns gần nhất cho prompt.
- **`web_router_service.py`**: LLM router quyết định dùng web search không.
- **`web_search_service.py`**: gọi Serper/SerpAPI lấy kết quả web.
- **`bootstrap.py`**: dựng `CoreServices`.

### `app/` (core)
- **`settings.py`**: đọc env, default model/top_k/cors/websearch keys…
- **`prompting.py`**: build prompt chuẩn hoá theo role + safety + KB/Web/Memory.
- **`kb.py`**: load KB + scoring/retrieval theo token overlap.
- **`llm.py`**: wrapper gọi OpenAI + streaming + metrics + ước tính cost.
- **`db/`**: SQLAlchemy store, models, contracts (session/message/feedback).

### `raw/`
- Dữ liệu KB dạng markdown theo nhóm đối tượng (user/driver/merchant).

### `docs/`
- Tài liệu chạy backend, API contract, kế hoạch/thiết kế, eval ragas…

---

## Cấu hình quan trọng (env)
Các biến chính (xem `app/settings.py`):

- `OPENAI_API_KEY`: có thì `mode="answer"` mới hoạt động
- `MODEL`: mặc định `gpt-4o-mini`
- `RAW_DIR`: trỏ tới thư mục KB `raw/`
- `DB_URL`: SQLite URL, mặc định `sqlite:///./xanhsm_helpcenter.db`
- `TOP_K`: số KB hits (default 5)
- `ENABLE_WEB_SEARCH`, `SERPER_API_KEY`, `SERPAPI_API_KEY`: bật/tắt & cấu hình web search
- `CORS_ORIGINS`: origins cho frontend local

