# AI Product Canvas — XanhSM Help Center AI (Nhom064-E403)

## Canvas

| | Value | Trust | Feasibility |
|---|-------|-------|-------------|
| **Trả lời** | **User:** Khách hàng XanhSM đang gặp vấn đề (thất lạc đồ, lỗi thanh toán, sự cố chuyến đi).<br><br>**Pain:** Tìm FAQ khó vì list quá dài; gọi tổng đài chờ lâu; ức chế nhất là phải lặp lại thông tin nhiều lần với nhiều người.<br><br>**AI giải quyết:** Do **không có quyền truy cập dữ liệu chuyến đi cá nhân**, AI đóng vai trò "Trợ lý điều phối thông minh". Phân loại intent -> trích xuất quy trình chuẩn từ FAQ -> đưa ra checklist. **Đặc biệt:** AI có một threshold nhất định, nó sẽ tự động gom toàn bộ ngữ cảnh và chuyển thẳng cho nhân viên CSKH khi chạm ngưỡng giới hạn, khách không cần phải kể lại từ đầu khi nhân viên CSKH xuất hiện. | **Ảnh hưởng khi sai:** Rủi ro về cách ứng xử không đúng với thời điểm, như việc quăng FAQ dài khi khách đang hoảng loạn, hoặc đưa sai quy trình hướng dẫn.<br><br>**Cách user biết sai:** AI trả lời sai ý định, hoặc cứ lải nhải xin lỗi/hỏi lại một vấn đề mãi không xong.<br><br>**Cách user sửa:** AI sẽ rào trước *"Do bảo mật, em chỉ tra cứu được chính sách chung..."*. Luôn hiển thị nút *"Không đúng vấn đề"* -> *"Gặp nhân viên ngay"*. AI cũng **tự động sửa sai** bằng luồng Fallback (chuyển người thật) khi: hỏi quá 3 câu mà không đưa ra được câu trả lời, hoặc dính keyword khẩn cấp (như: "tai nạn", "công an",...), hoặc nhận biết được tone giận dữ từ user. | **Cost:** Khoảng 100đ - 300đ/request (dùng API LLM phổ thông + RAG nội bộ để truy xuất KB).<br><br>**Latency:** Cần tối ưu dưới 2-3 giây/phản hồi.<br><br>**Risk chính:**<br>1. *Intent mismatch:* User dùng teencode, từ lóng -> AI không map được vào bài FAQ.<br>2. *Ngưỡng Handoff sai lệch:* Đặt ngưỡng quá thấp (chuyển CSKH quá nhanh) -> tốn resource tổng đài; đặt quá cao -> khách ức chế.<br>3. *Outdated RAG:* App update tính năng nhưng KB chưa cập nhật. |

-----

## Automation hay augmentation?

☐ Automation — AI làm thay, user không can thiệp

☑ Augmentation — AI gợi ý, user quyết định cuối cùng

**Justify:** Hệ thống này tuyệt đối không được phép Automation toàn phần vì AI không được phép truy cập vào dữ liệu cá nhân. AI này sẽ chỉ được coi là Tier 1 (sàng lọc bước đầu), giúp điều hướng FAQ và tóm tắt vấn đề. Các quyết định liên quan đến PII, hoàn tiền, đền bù bắt buộc phải do nhân viên CSKH thực hiện. Luồng hội thoại được thiết kế có **threshold** để nhường quyền kiểm soát cho nhân viên CSKH ngay khi nhận thấy rủi ro hoặc bế tắc.

-----

## Learning signal

| \# | Câu hỏi | Trả lời |
|---|---------|---------|
| 1 | User correction đi vào đâu? | Đi vào log lịch sử chat, gắn cờ ưu tiên, đặc biệt là các ca chạm ngưỡng Fallback — để nhân viên CSKH thay AI review. Từ đó team Product cập nhật Knowledge Base và tinh chỉnh lại rule của threshold. |
| 2 | Product thu signal gì để biết tốt lên hay tệ đi? | **Tốt lên:** Tỉ lệ Deflection rate (User tự xử lý bằng FAQ thành công) tăng; Thời gian chốt ticket của CSKH giảm (do AI đã được mớm đủ thông tin).<br>**Tệ đi:** Số lượt bấm "Gặp nhân viên ngay" tăng vọt; Tỉ lệ chạm ngưỡng ngắt tự động (hỏi quá 3 turn) quá lớn; Tỉ lệ thoát ngang (drop-off) cao. |
| 3 | Data thuộc loại nào? | ☐ User-specific<br>☑ Domain-specific (FAQ đặc thù XanhSM)<br>☐ Real-time<br>☑ Human-judgment (CSKH dán nhãn lại ca AI hiểu sai)<br>☑ Khác: Lịch sử hội thoại (Chat logs) |

**Có marginal value không?** Có, giá trị biên cực kỳ lớn\! Con hào kinh tế (moat) ở đây chính là **"Từ điển ngôn ngữ tự nhiên của khách hàng XanhSM"**. Không một model mở nào (như GPT-4) hiểu được cách người Việt phàn nàn đặc thù như: "xe hôi", "bác tài đi láo", "app lag trừ tiền 2 chập". Càng thu nhiều chat logs, AI càng học được cách map chuẩn xác những từ lóng bình dân này vào đúng các bài viết chính sách phức tạp. Cục data này đối thủ không thể nào scrap hay copy được\!

-----

*AI Product Canvas — Ngày 5 — VinUni A20 — AI Thực Chiến · 2026*
