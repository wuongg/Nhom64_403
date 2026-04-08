# AI Product Canvas — XanhSM Help Center AI (Nhom064-403)

## Canvas

| | Value | Trust | Feasibility |
|---|-------|-------|-------------|
| **Trả lời** | **User:** Khách hàng dùng XanhSM đang gặp vấn đề cần hỗ trợ (thất lạc đồ, lỗi thanh toán, chuyến đi có vấn đề).<br><br>**Pain:** Tìm mục hỗ trợ thủ công quá khó; phải đọc bài FAQ dài dòng; gọi tổng đài thì xếp hàng lâu; bực mình nhất là phải lặp lại thông tin (mã chuyến, sđt) nhiều lần với nhiều người.<br><br>**AI giải quyết:** Tự động phân loại intent (ý định) qua vài câu chat ngắn $\rightarrow$ tóm tắt vấn đề $\rightarrow$ đưa ra hướng dẫn dạng checklist (bước 1-2-3) ứng với đúng ngữ cảnh chuyến đi của user. Có nút chuyển thẳng nhân viên kèm theo *toàn bộ context*, không bắt user kể lại từ đầu. | **Ảnh hưởng khi sai:** User ức chế tột độ vì cảm giác "nói chuyện với cái máy ngu ngốc", tốn thời gian. Rủi ro cực lớn nếu AI tư vấn sai các ca nhạy cảm (tai nạn, an toàn, quấy rối).<br><br>**Cách user nhận biết sai:** AI trả lời không khớp với tình trạng thực tế (VD: bị trừ tiền 2 lần nhưng AI báo hệ thống bình thường); AI đưa ra chính sách đền bù/mã Vpoint ảo (hallucination).<br><br>**Cách user sửa:** Luôn có sẵn nút "Không hữu ích" / "Câu trả lời không đúng" $\rightarrow$ Hiển thị popup chọn lý do nhanh $\rightarrow$ Nút "Gặp nhân viên ngay" để escape (thoát) khỏi luồng AI. | **Cost:** Khoảng 100đ - 300đ/request (ước tính dùng API LLM phổ thông + hệ thống RAG nội bộ để truy xuất KB).<br><br>**Latency:** Cần tối ưu dưới 2-3 giây/phản hồi. Chậm hơn user sẽ bỏ đi.<br><br>**Risk chính:**<br>1. *Hallucination:* AI tự bịa chính sách hoặc hứa hẹn đền bù bậy bạ.<br>2. *Intent mismatch:* User dùng teencode, viết tắt, nóng giận $\rightarrow$ AI hiểu nhầm ý và vướng vào vòng lặp (infinite loop) hỏi đi hỏi lại.<br>3. *Thiếu dữ liệu RAG:* FAQ cập nhật chậm hơn các lỗi app thực tế. |

-----

## Automation hay augmentation?

☐ Automation — AI làm thay, user không can thiệp
☑ Augmentation — AI gợi ý, user quyết định cuối cùng

**Justify:** Hệ thống này tuyệt đối không được phép là Automation hoàn toàn. AI chỉ đóng vai trò "Trợ lý sơ lọc" (Tier 1 Support). Nó giúp định hướng, tóm tắt và đưa ra các bài viết FAQ chuẩn xác. Đối với các quyết định liên quan đến tiền bạc (hoàn tiền) hoặc an toàn, AI bắt buộc phải "aug" (tăng cường) thông tin cho nhân viên CSKH (gửi kèm bản tóm tắt tình huống) để con người đưa ra quyết định cuối cùng. Nếu AI tự ý xử lý (auto) mà sai, XanhSM sẽ đối mặt với khủng hoảng truyền thông ngay lập tức.

-----

## Learning signal

| \# | Câu hỏi | Trả lời |
|---|---------|---------|
| 1 | User correction đi vào đâu? | Đi vào log lịch sử chat, gắn flag (cờ) ưu tiên để nhân viên CSKH con người review lại xem AI đã trả lời sai ở turn nào. Đồng thời log lại thành dataset để team Product cập nhật/tinh chỉnh lại Knowledge Base (KB). |
| 2 | Product thu signal gì để biết tốt lên hay tệ đi? | **Tốt lên:** Tỉ lệ user giải quyết xong vấn đề mà không cần gọi nhân viên (Deflection rate) tăng; CSAT (chỉ số hài lòng) ở các ticket do AI xử lý cao.<br>**Tệ đi:** Số lượt user bấm nút "Gặp nhân viên ngay" tăng vọt; Tỉ lệ thoát ngang (drop-off) khi AI đang hỏi dở dang tăng; Thời gian trung bình của một phiên chat dài ra (do AI hỏi lan man). |
| 3 | Data thuộc loại nào? | ☐ User-specific (Lịch sử chuyến đi, giao dịch của user đó)<br>☑ Domain-specific (Chính sách, FAQ đặc thù của XanhSM)<br>☐ Real-time<br>☐ Human-judgment (Nhân viên CSKH dán nhãn/đánh giá lại câu trả lời của AI)<br>☐ Khác: \_\_\_ |

**Có marginal value không?** Có, và giá trị biên (marginal value) cực kỳ lớn\! Dữ liệu (data) này là độc quyền của XanhSM. Không một model Foundation nào (như GPT-4, Gemini) có sẵn cách người dùng Việt Nam phàn nàn về "xe có mùi", "tài xế lạng lách", hay dữ liệu định giá cuốc xe thực tế của hãng. Càng nhiều user chat, XanhSM càng có bộ dataset CSKH khổng lồ để fine-tune AI trở nên thông minh và "đậm chất" XanhSM hơn, tạo ra con hào kinh tế (moat) mà các đối thủ khó copy.

-----
