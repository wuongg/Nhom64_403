# Đánh giá RAG với tập `ragas_dataset_20.json`

Tập `ragas_dataset_20.json` gồm 20 mẫu: `user_input`, `retrieved_contexts` (top‑k từ KB), `reference` (đáp án chuẩn). Dùng để chạy Ragas **không** cần sinh lại dataset mỗi lần.

## Chuẩn bị

1. Python 3.10+ và cài dependency:

```bash
pip install -r requirements.txt
```

2. Tạo file `.env` ở thư mục gốc project (không commit file này) với API key OpenAI:

```env
OPENAI_API_KEY=sk-...
```

## Chạy đánh giá trên tập 20 câu

Từ thư mục gốc `Nhom64_403`:

```bash
python eval_ragas_dataset.py --dataset ragas_dataset_20.json --out ragas_eval_20.json
```

### Tham số thường dùng

| Tham số | Mặc định | Ý nghĩa |
|--------|----------|---------|
| `--dataset` | `ragas_dataset_20.json` | Đường dẫn file JSON dataset |
| `--evaluator-model` | `gpt-4o-mini` | Model dùng để chấm Ragas |
| `--out` | `ragas_eval_20.json` | File kết quả (metrics + runtime + usage) |
| `--limit` | 0 (đủ 20) | Chỉ lấy N mẫu đầu (ví dụ `--limit 5` để thử nhanh) |
| `--timeout` | 90 | Timeout mỗi request (giây) |
| `--max-retries` | 2 | Số lần thử lại khi lỗi |
| `--max-workers` | 8 | Số worker song song |

Ví dụ chạy thử 5 mẫu:

```bash
python eval_ragas_dataset.py --dataset ragas_dataset_20.json --limit 5 --out ragas_eval_5.json
```

### Ước tính chi phí (USD)

Nếu biết giá theo **1 triệu token** (input / output), truyền thêm:

```bash
python eval_ragas_dataset.py --dataset ragas_dataset_20.json --out ragas_eval_20.json ^
  --price-in-per-1m 0.15 --price-out-per-1m 0.60
```

(Thay số theo bảng giá model bạn dùng.) Trong file output sẽ có thêm `cost_usd_estimate` nếu cả hai giá đều lớn hơn 0.

## Kết quả trong file output

- **`metrics`**: trung bình các chỉ số Ragas (ví dụ `context_recall`, `faithfulness`, `factual_correctness`).
- **`runtime`**: tổng thời gian, giây/mẫu, mẫu/giây.
- **`usage`**: token (nếu API trả về `usage` trong response).
- **`per_sample_scores`**: điểm từng mẫu (nếu có).

## Tạo lại tập 20 mẫu (tùy chọn)

Nếu đổi KB trong `raw/` và muốn sinh lại dataset:

```bash
python make_eval_samples.py --n 20 --k 5 --seed 7 --out ragas_dataset_20.json
```

`--seed` khác nhau sẽ chọn bộ câu hỏi khác nhau (random trong pool câu có trong KB).
