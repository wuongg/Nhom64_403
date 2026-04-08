# SPEC draft — Nhom064-403

## Track: XanhSM

## Problem statement
Trung tâm hỗ trợ của XanhSM đang gặp tình trạng quá tải khi xử lý các yêu cầu lặp lại (như hỏi về chuyến đi, thanh toán, thất lạc đồ), dẫn đến thời gian phản hồi chậm và trải nghiệm khách hàng giảm.

## Canvas draft

| | Value | Trust | Feasibility |
|---|-------|-------|-------------|
| Trả lời + Tra cứu | Khách hàng hỏi lặp lại (trạng thái chuyến, hoá đơn, mã khuyến mãi, thất lạc đồ). Pain: chờ lâu, phải mô tả lại nhiều lần. AI trả lời ngay + hướng dẫn bước tiếp theo + (nếu cần) tra cứu theo mã chuyến/SĐT. | Nếu trả lời sai → mất niềm tin, khiếu nại, rủi ro “bịa” thông tin. Phải luôn có nút **chuyển nhân viên** và hiển thị rõ **AI có thể sai** khi thiếu dữ liệu. Chỉ tra cứu khi user cung cấp định danh hợp lệ. | Tích hợp kênh chat + intent routing + KB. Latency mục tiêu <3s cho FAQ; tra cứu có thể 3–6s. Cost LLM ~\$0.003–0.01/lượt tuỳ model. Risk: câu hỏi mơ hồ (“tôi bị trừ tiền”), dữ liệu phân tán, yêu cầu bảo mật/PII. |

**Auto hay aug?** Augmentation/Hybrid — AI xử lý FAQ/flow đơn giản; các case nhạy cảm (tranh chấp thanh toán, sự cố an toàn, hoàn tiền) luôn **handoff** sang nhân viên.

**Learning signal:** user bấm “Hữu ích/Không hữu ích”, chọn intent đúng sau khi AI gợi ý, tỉ lệ handoff, thời gian giải quyết ticket, nhãn của nhân viên (đúng/sai/thiếu thông tin) → dùng làm correction signal cho KB + prompt + routing.

## Hướng đi chính
- Prototype: chatbot hỗ trợ hỏi 2–4 câu làm rõ → phân loại intent (chuyến đi / thanh toán / thất lạc / khuyến mãi / khác) → trả lời từ KB + link hướng dẫn, hoặc tạo yêu cầu và chuyển nhân viên
- Eval: containment rate (không cần nhân viên) ≥ 30–50% cho FAQ; CSAT không giảm; thời gian phản hồi ban đầu < 10s; tỉ lệ “AI trả lời sai” (user downvote/escalation vì sai) giảm theo tuần
- Main failure mode: user mô tả chung chung (“bị trừ tiền”, “không thấy chuyến”) + thiếu định danh → AI trả lời lan man; cần hỏi lại ngắn gọn + fallback sang nhân viên

## Phân công
- An: Canvas + failure modes
- Bình: User stories 4 paths
- Châu: Eval metrics + ROI
- Dũng: Prototype research + prompt test