# SPEC draft — Nhom064-403

## Track: XanhSM

## Problem statement
Trung tâm hỗ trợ của XanhSM đang gặp tình trạng quá tải khi xử lý các yêu cầu lặp lại (như hỏi về chuyến đi, thanh toán, thất lạc đồ), dẫn đến thời gian phản hồi chậm và trải nghiệm khách hàng giảm.

## Canvas draft

| | Value | Trust | Feasibility |
|---|-------|-------|-------------|
| Trả lời + Hướng dẫn | Người dùng cần “giải quyết nhanh” các câu hỏi thường gặp trong Trung tâm hỗ trợ: **An toàn**, **đặt/chỉnh/hủy chuyến**, **thất lạc đồ**, **thanh toán & hoá đơn/VAT**, **khuyến mãi/VPoint**, **tài khoản & bảo mật**, **lỗi ứng dụng**. Pain: tìm mục đúng khó, phải đọc dài, chờ tổng đài, phải kể lại nhiều lần. AI giúp: tóm tắt đúng vấn đề + đưa đúng bước thao tác theo ngữ cảnh. | Người dùng kỳ vọng: **không bịa**, nói rõ khi “không chắc”, và luôn có đường lui “gặp nhân viên”. Nội dung liên quan **an toàn/tai nạn/quấy rối** phải ưu tiên hướng dẫn khẩn cấp + hotline. Với thanh toán/PII: hỏi tối thiểu và giải thích vì sao cần thông tin. | Người dùng chấp nhận: trả lời ngắn gọn, theo “bước 1-2-3”, có nút chọn nhanh thay vì phải gõ nhiều; nếu vấn đề phức tạp thì chuyển nhân viên và **không bắt kể lại từ đầu**. |

**Auto hay aug?** Augmentation — AI hỗ trợ định hướng/giải thích/hướng dẫn; quyết định cuối cùng (đặc biệt ca nhạy cảm) thuộc về người dùng và/hoặc nhân viên hỗ trợ.

**Learning signal (từ góc nhìn user):** user bấm “Hữu ích/Không hữu ích”, chọn lại mục đúng, hoặc phải bấm “gặp nhân viên” → phản ánh AI đang hướng dẫn đúng hay chưa.

## Hướng đi chính
- Prototype: chatbot hỏi 2–4 câu làm rõ → đưa người dùng vào đúng nhóm nhu cầu (An toàn / Chuyến đi / Thanh toán / Khuyến mãi / Tài khoản / Ứng dụng) → trả lời dạng checklist “làm ngay” + link tới bài liên quan, hoặc tạo yêu cầu để gặp nhân viên
- Eval (user-centric): thời gian “tìm được câu trả lời” giảm; số bước thao tác giảm; tỉ lệ “đọc xong vẫn không biết làm gì” giảm; người dùng cảm thấy minh bạch và an tâm hơn
- Main failure mode: người dùng mô tả quá chung chung (“bị trừ tiền”, “không an toàn”) → AI hỏi lan man hoặc đưa sai bài; cần nút chọn nhanh + câu hỏi làm rõ thật ngắn + ưu tiên đường lui gặp nhân viên

## Phân công
- Anh: Canvas + failure modes
- Tú: User stories 4 paths
- Phước: Eval metrics + ROI
- Trung: Prototype research + prompt test
- Vương: Tổng hợp tài liệu + chỉnh sửa final spec
