# UX analysis — XanhSM Support AI (Nhom064-403)

## Mục tiêu
Giảm quá tải cho trung tâm hỗ trợ XanhSM bằng chatbot AI xử lý các yêu cầu lặp lại (trạng thái chuyến, thanh toán/hoá đơn, khuyến mãi, thất lạc đồ), đồng thời giữ trải nghiệm đáng tin và có đường lui sang nhân viên.

## 4 paths (hành trình người dùng)

### 1) AI đúng (happy path)
- User: “Cho mình hỏi chuyến vừa rồi đã thanh toán chưa?”
- AI: hỏi 1 thông tin định danh (mã chuyến / SĐT / thời gian) → tra cứu → trả lời rõ ràng + bước tiếp theo (ví dụ: “Bạn có thể tải hoá đơn tại …”)
- UI: hiển thị câu trả lời + nút “Hữu ích” + “Chuyển nhân viên”

### 2) AI không chắc (thiếu dữ liệu / intent mơ hồ)
- User: “Mình bị trừ tiền 2 lần”
- AI: không kết luận ngay; hỏi 2–3 câu ngắn để thu hẹp (thời gian, phương thức thanh toán, có mã chuyến không) + đưa 2–3 lựa chọn intent (“Tra soát thanh toán”, “Hoá đơn”, “Khác”)
- UI: hiển thị rõ “Mình cần thêm thông tin để kiểm tra” + CTA “Tạo yêu cầu cho nhân viên” nếu user không muốn trả lời thêm

### 3) AI sai (trả lời nhầm / hướng dẫn sai)
- User: hỏi về hoàn tiền nhưng AI trả lời theo kịch bản khuyến mãi, hoặc “bịa” trạng thái chuyến khi không tra cứu được
- Hậu quả: user làm sai thao tác, mất thời gian, có thể bực bội/khiếu nại
- Recovery tối thiểu:
  - 1 chạm “Câu trả lời không đúng” → AI xin lỗi, hỏi lại intent bằng nút chọn nhanh
  - ưu tiên chuyển nhân viên cho nhóm case nhạy cảm (tranh chấp thanh toán, an toàn)
  - ghi nhận lý do sai (intent sai / thiếu dữ liệu / nội dung KB sai) để sửa hệ thống

### 4) User mất niềm tin (sai lặp lại hoặc thiếu minh bạch)
- Dấu hiệu: user bỏ qua chatbot, liên tục bấm “chuyển nhân viên”, hoặc nói “đừng trả lời nữa”
- Thiếu fallback sẽ làm “AI = rào cản” thay vì trợ lý
- Exit/fallback nên có:
  - nút “Gặp nhân viên ngay” luôn hiện
  - tuỳ chọn “Chỉ tra cứu, không suy đoán” (tránh trả lời dạng phỏng đoán)
  - thông báo minh bạch khi không thể xác minh (“Mình chưa tra cứu được vì thiếu mã chuyến…”)

## Path yếu nhất: 3 + 4 (vì ảnh hưởng trust)
- Khi AI sai, chi phí phục hồi phải thấp (ít bước, không bắt user gõ lại dài)
- Cần feedback loop rõ ràng để người dùng thấy hệ thống “có học” và để team vận hành sửa KB/routing nhanh

## “Gap” kỳ vọng vs thực tế
- Kỳ vọng user: “chatbot trả lời nhanh như người thật”
- Thực tế: nhiều câu hỏi cần định danh/tra cứu; nếu không có dữ liệu, AI dễ suy đoán → rủi ro sai
- Cách giảm gap:
  - định vị: “trợ lý hỗ trợ + tra cứu nhanh”, không hứa chính xác tuyệt đối
  - ưu tiên câu trả lời có căn cứ (KB/tra cứu) và nói rõ khi thiếu căn cứ

## Sketch (mô tả luồng as-is/to-be)
- As-is: user nhắn tổng đài → xếp hàng → nhân viên hỏi lại thông tin → xử lý
- To-be:
  - user nhắn → AI phân loại intent
  - nếu FAQ/KB: trả lời ngay + link hướng dẫn
  - nếu cần tra cứu: xin định danh tối thiểu → trả kết quả
  - nếu confidence thấp / case nhạy cảm: đề xuất handoff + tạo ticket kèm tóm tắt (để user không phải kể lại)