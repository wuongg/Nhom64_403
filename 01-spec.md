# SPEC — AI Product Hackathon

**Nhóm:** Nhom064-E403

**Track:** ☐ VinFast · ☐ Vinmec · ☐ VinUni-VinSchool · ☑ XanhSM · ☐ Open

**Problem statement (1 câu):** Khách hàng XanhSM gặp khó khăn khi tìm kiếm quy trình hỗ trợ qua danh sách FAQ dài và phải lặp lại thông tin khi gọi tổng đài; AI tóm tắt nhanh quy trình chuẩn và tự động điều phối, gom ngữ cảnh chuyển nhân viên CSKH ngay khi cần.

---

## 1. AI Product Canvas

|   | Value | Trust | Feasibility |
|---|-------|-------|-------------|
| **Câu hỏi** | User nào? Pain gì? AI giải gì? | Khi AI sai thì sao? User sửa bằng cách nào? | Cost/latency bao nhiêu? Risk chính? |
| **Trả lời** | **User:** Khách XanhSM gặp sự cố chuyến đi, thanh toán, thất lạc đồ.<br>**Pain:** Tìm FAQ khó, gọi tổng đài lâu, phải kể lại vấn đề từ đầu.<br>**AI giải quyết:** Đóng vai trò trợ lý điều phối; phân loại intent, trích RAG hướng dẫn, tóm tắt ngữ cảnh & chuyển CSKH. | **Khi sai:** Trả lời nhầm (ném FAQ khi khách hoảng loạn).<br>**Cách sửa:** Rào trước "Do bảo mật, em chỉ tra cứu...". User có thể bấm "Gặp nhân viên ngay". AI tự sửa sai: chuyển thẳng CSKH nếu không tìm được hướng dẫn trên Knowledge Base, hoặc khách yêu cầu gặp nhân viên. | **Cost:** ~100đ-300đ/req.<br>**Latency:** <2-3s/phản hồi.<br>**Risk:** Intent mismatch (từ lóng teencode), đặt ngưỡng handoff sai, KB bị lỗi thời. |

**Automation hay augmentation?** ☐ Automation · ☑ Augmentation
Justify: AI tuyệt đối không can thiệp tự động (do không được truy cập Dữ liệu Khách hàng PII/hành trình thực). AI chỉ sàng lọc bước đầu (Tier 1). Mọi quyết định đền bù, nhạy cảm đều do CSKH chốt. Khi có rủi ro, hệ thống nhường quyền tự động cho CSKH.

**Learning signal:**

1. User correction đi vào đâu? Đi vào chat logs, gắn cờ ưu tiên. CSKH thay AI xem lại ca chuyển tiếp (fail handoff), cập nhật Knowledge Base hoặc rule threshold.
2. Product thu signal gì để biết tốt lên hay tệ đi?
   - Tốt: Deflection rate (tự xử lý xong) tăng; Thời gian chốt ticket giảm.
   - Tệ: Lượt bấm "Gặp nhân viên ngay" ngay từ đầu quá lớn; rơi vào ngắt và handoff do thiếu dữ liệu Knowledge Base nhiều; drop-off cao.
3. Data thuộc loại nào? ☐ User-specific · ☑ Domain-specific · ☐ Real-time · ☑ Human-judgment · ☑ Khác: Log hội thoại (Chat logs)
   Có marginal value không? (Model đã biết cái này chưa?) Chắc chắn Có (Moat/Hào kinh tế). Kho từ lóng phàn nàn của người Việt (app lag trừ tiền 2 chập, xe hôi, đi láo) mà không LLM mở nào tự hiểu đúng. Data này giúp map chuẩn intent vào bài policy.

---

## 2. User Stories — 4 paths

Mỗi feature chính = 1 bảng. AI trả lời xong → chuyện gì xảy ra?

### Feature: Trợ lý điều phối tra cứu Hỗ Trợ (RAG Chatbot)

**Trigger:** Khách hàng gặp sự cố, mở Trung tâm hỗ trợ nhắn tin hoặc chọn vào 1 chủ đề bất kỳ.

| Path | Câu hỏi thiết kế | Mô tả |
|------|-------------------|-------|
| Happy — AI đúng, tự tin | User thấy gì? Flow kết thúc ra sao? | User hỏi "Xin VAT", AI nhận đúng vấn đề → hiển thị luồng bước 1-2-3 (checklist) kèm nút chuyển chức năng. User làm theo và kết thúc nhanh gọn. |
| Low-confidence — AI không chắc | System báo "không chắc" bằng cách nào? User quyết thế nào? | User nhắn "Bị trừ tiền". AI không phán đoán bừa, đưa ra tối đa 2 câu hỏi ngắn/nút click (VD: "Bị trừ đúp" hay "Huỷ xe nhưng vẫn trừ tiền?"). User bấm chọn đúng luồng. |
| Failure — AI sai | User biết AI sai bằng cách nào? Recover ra sao? | AI đưa nhầm FAQ (xin cách đặt xe thay vì phản ánh bác tài sai biển số). Recovery: Nút "Câu trả lời không đúng" luôn thường trực. Chuyển fallback sang CSKH. |
| Correction — user sửa | User sửa bằng cách nào? Data đó đi vào đâu? | User bấm phàn nàn hoặc "Gặp nhân viên hỗ trợ". Ngữ cảnh chat được đẩy thẳng vào log để nhãn viên CSKH check & system cải thiện embeddings (nhận biết từ lóng). |

---

## 3. Eval metrics + threshold

**Optimize precision hay recall?** ☑ Precision · ☐ Recall
Tại sao? Đối với ngành gọi xe & giao dịch, thà chatbot báo "Vấn đề này em không tra cứu được, anh chị vui lòng gặp CSKH" còn hơn bịa thông tin sai lầm về đền bù, cách huỷ thẻ hoặc hướng dẫn an toàn, dẫn đến hậu quả nghiêm trọng hơn. Yêu cầu đúng thông tin là tối thiết.

| Metric | Threshold | Red flag (dừng khi) |
|--------|-----------|---------------------|
| Mức độ chính xác truy xuất (Context Rel/Accuracy)| ≥ 85% | < 70% trong vòng 1 tuần |
| Deflection Rate (Trả lời tự động thành công) | ≥ 30% | < 10% (Coi như AI không có tác dụng) |
| Latency P95 | < 3 giây | > 5 giây |

---

## 4. Top 3 failure modes

*“Failure mode nào user KHÔNG BIẾT bị sai? Đó là cái nguy hiểm nhất.”*

| # | Trigger | Hậu quả | Mitigation |
|---|---------|---------|------------|
| 1 | Dùng từ lóng rành rẽ hoặc tiếng lóng địa phương ("xe hôi", "trừ đúp") | AI suy diễn sai intent và nhiệt tình hướng dẫn sai (vd: đưa FAQ cách huỷ chuyến, user tự làm sai hỏng việc) | Bắt buộc có nút "Không đúng" ở mỗi câu; cập nhật thủ công các intent lóng phổ biến vào vector DB. |
| 2 | Truy vấn ở nhóm An toàn Khẩn cấp ("Nguy hiểm", "sao chém nhau") | AI tốn thời gian cố tra cứu RAG thay vì đưa Hotline cảnh sát / ứng trực | Bắt Keyword regex (hardcode). Nếu dính keyword nhóm "Sinh mạng/An toàn", bypass LLM và quăng ngay thẻ Hotline khẩn cấp. |
| 3 | Chính sách trên app thay đổi nhưng KB chưa cập nhật | AI tự tin hướng dẫn user bấm vào một nút không tồn tại. User thử mãi không được. | Đồng bộ auto từ CMS lên VectorDB định kì. Thiết lập logic tự động handover sang CSKH nếu duyệt search engine luôn trả về 0 kết quả (hit score = 0). |

---

## 5. ROI 3 kịch bản

|   | Conservative | Realistic | Optimistic |
|---|-------------|-----------|------------|
| **Assumption** | 5,000 tick/ngày. Giảm 15% tải | 10,000 tick/ngày. Giảm 30% tải | 20,000 tick/ngày. Giảm 45% tải |
| **Cost** | ~$15 / ngày (Inference RAG) | ~$30 / ngày | ~$60 / ngày |
| **Benefit** | Giảm tương đương 15 CSKH ngồi chat | Giảm tương đương 60 CSKH | Giảm tương đương 180 CSKH |
| **Net** | ROI dương, test thị trường ổn | Cắt giảm OPEX cực tốt | Giảm cực mạnh thời gian chờ, CSAT tăng 15% |

**Kill criteria:** Chỉ số CSAT/NPS của hạng mục Hỗ trợ giảm mạnh > 10% trong tháng đầu ra mắt chatbot; Số lượt user bấm "Không hữu ích" chiếm > 50%.

---

## 6. Mini AI spec (1 trang)

**Tên sản phẩm:** XanhSM Help Center AI (AI Trợ lý điều phối)
**Khách hàng mục tiêu:** Khách dùng app XanhSM đang cần hỗ trợ (FAQ, tra cứu chính sách, báo lỗi app, quên đồ, xử lý khẩn cấp).

**Vấn đề giải quyết:**  
Hiện tại, người dùng lúng túng khi dò tìm danh sách FAQ dài lê thê và chán nản khi phải nhấc máy / chat với tổng đàiên để diễn giải lại vụ việc từ đầu. Hệ thống hiện tại tốn kém nhân sự CSKH để xử lý hàng ngàn query dạng hỏi lặp đi lặp lại.

**Giải pháp (AI Augmentation):**  
Xây dựng một chatbot đệm (Tier 1) có chức năng truy xuất Knowledge Base (FAQ) dựa vào Intent của người dùng (RAG pipeline). 
- AI làm nhiệm vụ "trích xuất hướng dẫn" (đưa bullet point nhanh gọn, có link đến nút thao tác).
- AI KHÔNG truy cập dữ liệu PII/hành trình, KHÔNG tự quyết định đền bù. 
- Giới hạn: Khi AI không tìm được thông tin trên KB, khách hàng yêu cầu khiếu nại (intent triggers), hoặc đụng từ khóa sự cố tai nạn (safety triggers) → Lập tức pass nguyên block tóm tắt bối cảnh chat sang Human CSKH.

**Giá trị cạnh tranh (Data Flywheel):**  
Thay vì dùng FAQ tĩnh, hệ thống hấp thụ kho ngôn ngữ đặc thù của mảng gọi xe Việt Nam ("bị trừ đúp", "xe bốc mùi", "tài xế nói bậy"). Hành vi CSKH bóc tách và sửa sai cho AI sẽ tạo ra bản đồ "từ điển người Việt" mà đối thủ không thể học mót từ mô hình thuần túy.

**Quy chuẩn rủi ro:**  
Ưu tiên Precision. Mọi thông tin xuất ra phải có Reference từ nguồn XanhSM ban hành. Đường lui cực kỳ nhẹ nhàng, hỗ trợ người dùng khiếu nại hiệu quả (intent phrases), chống "Bot loop" nhờ fallback khi KB không phản hồi. Lỗi nguy hiểm nhất là hướng dẫn user sai quy trình khẩn cấp, do đó bypass bằng hardcode keywords luôn được bật.
