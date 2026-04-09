from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import time

from .services.faq_service import FAQService
from .agents.router_agent import RouterAgent
from .agents.qa_agent import QAAgent

app = FastAPI(title="XanhSM FAQ API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for evolution
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup services
RAW_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "raw")
faq_service = FAQService(RAW_DATA_PATH)
qa_agent = QAAgent()

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []

# GPT-4o-mini pricing (USD per 1M tokens)
GPT4O_MINI_INPUT_PRICE  = 0.150  # $0.150 per 1M input tokens
GPT4O_MINI_OUTPUT_PRICE = 0.600  # $0.600 per 1M output tokens

def calculate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    """Calculate API call cost in USD based on GPT-4o-mini pricing."""
    input_cost  = (prompt_tokens     / 1_000_000) * GPT4O_MINI_INPUT_PRICE
    output_cost = (completion_tokens / 1_000_000) * GPT4O_MINI_OUTPUT_PRICE
    return round(input_cost + output_cost, 8)

class ChatResponse(BaseModel):
    answer: str
    file_key: Optional[str] = None
    category: Optional[str] = None
    is_urgent: bool = False
    latency_ms: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0

@app.get("/")
async def root():
    return {"message": "XanhSM FAQ Agent API is running"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    start_time = time.perf_counter()
    total_prompt_tokens = 0
    total_completion_tokens = 0

    # 1. Get FAQ structure for routing
    structure = faq_service.get_structure_summary()
    router = RouterAgent(structure)
    
    # 2. Identify target file and category
    route_info, router_usage = router.route(request.message)
    total_prompt_tokens += router_usage.get("prompt_tokens", 0)
    total_completion_tokens += router_usage.get("completion_tokens", 0)

    file_key = route_info.get("file_key")
    category = route_info.get("category")
    is_urgent = route_info.get("is_urgent", False)
    
    # 3. Retrieve context
    context = faq_service.get_context(file_key, category)
    
    if not context:
        latency_ms = (time.perf_counter() - start_time) * 1000
        return ChatResponse(
            answer="Xin lỗi, tôi không tìm thấy thông tin phù hợp. Bạn có muốn kết nối với nhân viên không?",
            file_key=file_key,
            category=category,
            is_urgent=is_urgent,
            latency_ms=latency_ms,
            prompt_tokens=total_prompt_tokens,
            completion_tokens=total_completion_tokens,
            cost_usd=calculate_cost(total_prompt_tokens, total_completion_tokens)
        )
    
    # 4. Generate answer
    answer, qa_usage = qa_agent.generate_answer(request.message, context)
    total_prompt_tokens += qa_usage.get("prompt_tokens", 0)
    total_completion_tokens += qa_usage.get("completion_tokens", 0)

    latency_ms = (time.perf_counter() - start_time) * 1000
    
    return ChatResponse(
        answer=answer,
        file_key=file_key,
        category=category,
        is_urgent=is_urgent,
        latency_ms=latency_ms,
        prompt_tokens=total_prompt_tokens,
        completion_tokens=total_completion_tokens,
        cost_usd=calculate_cost(total_prompt_tokens, total_completion_tokens)
    )
