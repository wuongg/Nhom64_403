# UX analysis — XanhSM Help Center AI (user-focused) (Nhom064-403)

## Mục tiêu (từ góc nhìn người dùng)
Giúp người dùng giải quyết nhanh các vấn đề thường gặp trong Trung tâm hỗ trợ XanhSM: **An toàn**, **đặt/chỉnh/hủy chuyến**, **thất lạc đồ**, **thanh toán/hoá đơn/VAT**, **khuyến mãi/VPoint**, **tài khoản & bảo mật**, **lỗi ứng dụng** — với câu trả lời ngắn gọn, đúng ngữ cảnh và có đường lui rõ ràng.

## 4 paths (hành trình người dùng)

### 1) AI đúng (happy path)
- User: “Mình muốn xuất hoá đơn VAT cho chuyến hôm qua”
- AI: nhận đúng vấn đề → hướng dẫn dạng “bước 1-2-3” + chỉ rõ vị trí thao tác trong app + link tới bài liên quan
- Người dùng: làm được ngay, không cần đọc dài/không cần gọi tổng đài

### 2) AI không chắc (thiếu dữ liệu / intent mơ hồ)
- User: “Mình bị trừ tiền 2 lần”
- AI: không phán đoán; hỏi tối thiểu 2–3 câu để thu hẹp (thời gian, phương thức thanh toán, có mã chuyến không) và đưa nút chọn nhanh:
  - “Chuyến bị huỷ nhưng vẫn bị trừ tiền”
  - “Bị trừ tiền 2 lần”
  - “Đã trả tiền mặt nhưng app vẫn báo trừ thẻ”
- Người dùng: chọn đúng nhánh → nhận hướng dẫn phù hợp, hoặc tạo yêu cầu hỗ trợ nếu không có đủ thông tin

### 3) AI sai (trả lời nhầm / hướng dẫn sai)
- Tình huống: user báo “thông tin tài xế/xe không giống trên ứng dụng” nhưng AI lại đưa bài “cách đặt chuyến”
- Hậu quả với user: cảm giác không được lắng nghe, tốn thời gian, rủi ro an toàn nếu không biết làm gì ngay
- Recovery (trọng tâm user):
  - nút “Câu trả lời không đúng” luôn thấy → AI chuyển sang câu hỏi phân loại 1 bước (An toàn / Chuyến đi / Thanh toán / Khác)
  - với nhóm **An toàn**: ưu tiên hiển thị hành động ngay (đảm bảo an toàn, liên hệ khẩn cấp/hotline) rồi mới hỏi thêm

### 4) User mất niềm tin (sai lặp lại hoặc thiếu minh bạch)
- Dấu hiệu: user bỏ qua chatbot, liên tục bấm “chuyển nhân viên”, hoặc nói “đừng trả lời nữa”
- Thiếu fallback sẽ làm “AI = rào cản” thay vì trợ lý
- Exit/fallback nên có:
  - nút “Gặp nhân viên ngay” luôn hiện
  - tuỳ chọn “Chỉ đưa bài hướng dẫn chính thức” (tránh trả lời suy đoán)
  - thông báo minh bạch khi chưa đủ thông tin (“Mình cần mã chuyến hoặc thời gian chuyến để kiểm tra…”)

## Path yếu nhất: 3 + 4 (vì ảnh hưởng trust)
- Khi AI sai, chi phí phục hồi phải thấp (ít bước, không bắt user gõ lại dài)
- Cần feedback loop đơn giản cho user: bấm “Không hữu ích” → chọn lý do (Sai nội dung / Sai mục / Thiếu thông tin) → chuyển nhân viên nếu cần

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
  - nếu cần thêm thông tin: hỏi ít câu nhất có thể + nút chọn nhanh
  - nếu thuộc nhóm an toàn/nhạy cảm hoặc user không muốn trả lời thêm: gặp nhân viên + kèm tóm tắt để user không phải kể lại