# soc-investigator — Đặc tả kỹ thuật v0.2.6

> Tên dự án: **soc-investigator** · Giao diện dòng lệnh: `soc-investigator` . 
> Giấy phép: **Apache-2.0** (kèm quy tắc không sao chép cấu hình từ wazuh-docker, xem mục 13 và mục 14).
> Mô tả nhanh: soc-investigator là trợ lý điều tra sự cố an ninh **độc lập SIEM**
---
## 0. Tóm tắt đặc tả.

| Khía cạnh                | Tóm tắt                                                                                                                                                                                                                                                                                                                                            | Đọc sâu ở mục |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- |
| Vấn đề cần giải quyết    | Cảnh báo đổ về với số lượng lớn gây quá tải cho SOC (Trung Tâm Vận Hành An Ninh Mạng) dẫn tới chất lượng điều tra cảnh báo kém. SOC cần một công cụ tạo ra bản thảo điều tra đầu tiên, có bằng chứng kiểm chứng được cho mỗi cảnh báo nhằm giúp tăng tốc và chất lượng điều ra.                                                                    | Mục 1, 2      |
| Công cụ là gì            | Trợ lý điều tra chạy trên giao diện dòng lệnh: nhận một cảnh báo từ SIEM, tự thu thập và tương quan các sự kiện liên quan, tạo báo cáo điều tra ban đầu                                                                                                                                                                                            | Mục 2, 6      |
| Công cụ không phải là gì | - Không phải là  SIEM/SOAR. <br>- Không tự thực thi hành động phản ứng. <br>- Mô hình ngôn ngữ lớn (LLM model) không bao giờ nhìn dữ liệu sự kiện thô.                                                                                                                                                                                             | Mục 2, 4, 11  |
| Ai dùng                  | Đội SOC (trung tâm vận hành an ninh) thiếu nhân lực để sàn lọc và điều tra cảnh báo trên hệ thống SIEM đã có.                                                                                                                                                                                                                                      | Mục 1, 3      |
| Đầu vào                  | Một cảnh báo (trực tiếp từ chỉ mục  ví dụ như: `wazuh-alerts-*`) hoặc một bản xuất dữ liệu NDJSON (chế độ `--replay`, không cần phòng thí nghiệm)                                                                                                                                                                                                  | Mục 3, 6      |
| Khối điều tra trung tâm  | Sáu thành phần xử lý nối tiếp nhau, mô tả chi tiết ngay sau bảng này                                                                                                                                                                                                                                                                               | Mục 4, 6      |
| Cam kết kiểm chứng       | Mọi kết luận đều có trích dẫn về một mục chứng cứ cụ thể; dữ liệu chứng cứ được đóng băng trong bản chụp kèm mã băm SHA-256; nhật ký điều tra lưu toàn bộ quá trình trao đổi với mô hình để xem lại; lệnh verify đối chiếu mã băm giữa báo cáo và bản ghi lưu ở nơi độc lập; lệnh smoke chạy toàn bộ dây chuyền rồi tự kiểm chứng từng khâu đầu ra | Mục 6, 9, 11  |
| Triết lý gói kịch bản    | Mỗi gói khai báo đúng một điểm phát hiện và phần dữ liệu theo dõi được từ điểm đó, không phải bộ bách khoa về một lớp tấn công; khối coverage công khai ba danh sách: hỏi được gì, không quan sát được gì vì thiếu loại dữ liệu, gì thuộc gói khác                                                                                                 | Mục 7         |
| Với dữ liệu thiếu        | Không bao giờ chặn vì thiếu dữ liệu: khoảng trống dữ liệu đã khai báo (tổ chức chưa triển khai nguồn) được chấp nhận; sự thiếu vắng dữ liệu bất thường (nguồn đã có nhưng không thu được sự kiện nào) được ghi rõ kèm nghi vấn lỗi thu thập; khuyến nghị nêu nguồn cần bổ sung và nguồn đó giúp phát hiện được gì                                  | Mục 2.1, 9    |
| Mô hình ngôn ngữ         | Một mô hình duy nhất chạy tại chỗ (qwen2.5:3b) và API Claude của Anthropic (tùy chọn).                                                                                                                                                                                                                                                             | Mục 5, 10     |

**Sáu thành phần của khối điều tra trung tâm.** Khối điều tra trung tâm (Investigation Brain) là phần lõi không phụ thuộc nhà cung cấp của công cụ, gồm sáu thành phần xử lý nối tiếp nhau trong mỗi lần điều tra:

1. **Bộ nạp gói kịch bản (scenario pack loader):** đọc file YAML mô tả kịch bản điều tra, ghép các tầng câu hỏi chung từ file include, kiểm tra tính hợp lệ của gói bằng luật máy ngay lúc nạp.
2. **Bộ tương quan (correlator):** từ cảnh báo đầu vào, thu thập các sự kiện liên quan, dựng cây tiến trình và dòng thời gian, trích xuất chỉ dấu xâm nhập. Thành phần này viết bằng code thuần, không dùng mô hình ngôn ngữ lớn.
3. **Bộ truy xuất tri thức (knowledge retriever):** tra cứu cơ sở tri thức cục bộ gồm tập con MITRE ATT&CK và các playbook nội bộ, tìm các kỹ thuật và playbook liên quan đến bằng chứng vừa thu thập.
4. **Bộ dựng câu lệnh cho mô hình (prompt builder):** ghép bằng chứng đã cô đọng, bộ câu hỏi giả thuyết và khung phương pháp của gói kịch bản vào khuôn mẫu prompt, áp dụng che dữ liệu nhạy cảm trước khi gửi.
5. **Bộ kiểm định kết quả (output validator):** kiểm tra kết quả trả về của mô hình theo schema dữ liệu, xác nhận mọi kết luận đều có trích dẫn về mục chứng cứ trực tiếp tồn tại trong gói chứng cứ.
6. **Bộ ghi báo cáo (report writer):** kết xuất báo cáo JSON, HTML, Markdown; nhúng bản chụp dữ liệu chứng cứ kèm mã băm; ghi nhật ký điều tra; ghi bản ghi vào chỉ mục lưu trữ.

## 1. Mục tiêu

**A.** Chứng minh năng lực làm chủ công nghệ tích hợp AI vào vận hành SOC (trung tâm vận hành an ninh) trên đủ các khâu cài đặt, triển khai, cấu hình và vận hành, xây dựng trên nền kinh nghiệm SOC thực chiến.

**B:** Phát hành mã nguồn mở trên GitHub một giải pháp giúp doanh nghiệp kết nối SIEM với năng lực AI, theo ba kịch bản:

| Ký hiệu | Tình trạng doanh nghiệp | Giải pháp của soc-investigator |
|---|---|---|
| A | Đã có SIEM (Wazuh, ELK hoặc Splunk) và đã mua AI thương mại (OpenAI, Claude) hoặc có mô hình ngôn ngữ chạy tại chỗ | Cấu hình connector tới SIEM sẵn có (chỉ đọc) và provider tới mô hình sẵn có |
| B | Chưa có SIEM, chưa có mô hình ngôn ngữ | Hướng dẫn và script cài Wazuh cùng Ollama (mô hình ngôn ngữ chạy tại chỗ) rồi kết nối |
| C | Doanh nghiệp nhỏ đã mua ChatGPT hoặc Claude, muốn có SIEM nhỏ nhẹ | Dựng Wazuh tối thiểu với cấu hình tối cần thiết để làm việc với AI thương mại |

Ba kịch bản chỉ khác nhau ở **hai điểm kết nối thay thế được**: bộ kết nối SIEM và bộ cung cấp mô hình ngôn ngữ. Khối điều tra trung tâm là một và chung cho mọi kịch bản.

Mỗi kịch bản được phát hành thành một **hướng dẫn triển khai (deployment recipe)** trong `docs/deployment/`, gồm compose file, script và tài liệu tích hợp LLM model (v0.2 phát hành recipe kịch bản B: `wazuh-ollama.md` — chính là lab, xem mục 13; recipe cho kịch bản A và C, ví dụ `wazuh-openai.md`, nằm ngoài phạm vi v0.2 — xem mục 3). Recipe **không phải trình cài đặt hoàn chỉnh**, vì mỗi môi trường thật tế đều có chỗ lệch riêng so với môi trường chuẩn.



### Bối cảnh thị trường (v0.2.6)

Khảo sát nhanh ba tên tuổi đại diện để trả lời câu hỏi "thị trường đã có gì và định vị soc-investigator ở đâu":

| Nhà cung cấp   | Trợ lý AI đang có                                                                                                                                                                                                                                                                                                              | Gắn với nền tảng nào                                                         |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------- |
| Splunk (Cisco) | Splunk AI Assistant for Security: hỗ trợ điều tra, sinh truy vấn, tóm tắt cảnh báo; theo hướng agentic AI từ 2025                                                                                                                                                                                                              | Nền tảng Splunk (Enterprise Security, Cloud), giấy phép thương mại theo hạng |
| Elastic        | Elastic AI Assistant for Security: điều tra cảnh báo, sinh phản hồi, trò chuyện với dữ liệu Elastic Security; Elastic AI Agent chạy các kỹ năng phân tích                                                                                                                                                                      | Elastic Security (trả phí hoặc tự vận hành với giấy phép Elastic)            |
| Wazuh          | Dòng 4.x (bản ổn định đang phát hành): không có trợ lý AI tích hợp sẵn, năng lực AI do người dùng tự ghép. Wazuh 5.0 (chưa phát hành chính thức, đã tới bản ứng viên phát hành): có mô đun trợ lý AI trong bảng điều khiển, dùng theo mô hình tự mang khóa — quản trị viên khai báo nhà cung cấp và tên mô hình trước khi dùng | Hệ sinh thái mã nguồn mở, cộng đồng tự vận hành lớn                          |

Nhận định: trợ lý AI điều tra không phải đề tài mới, các hãng lớn đều đã có sản phẩm, nhưng sản phẩm nào cũng là một phần của nền tảng thương mại giá cao của chính hãng đó. Nhóm chưa được phục vụ là các đội **tự vận hành SIEM mã nguồn mở**: họ có dữ liệu, có cảnh báo, không đủ người để điều tra từng cảnh báo, và không có trợ lý AI nào đi kèm bộ SIEM họ đang giữ. soc-investigator bắt đầu từ nhóm đó — với bộ kết nối Wazuh chạy trước  — và mang tới năng lực "bản thảo điều tra đầu tiên có bằng chứng truy nguyên được", kèm lựa chọn mô hình chạy tại chỗ (dữ liệu không rời hạ tầng) hoặc API thương mại (dữ liệu đã được che trước khi gửi).

### Định vị trung lập với nhà cung cấp.

Câu định vị rút gọn, dùng thống nhất trong README và bài viết công khai: **soc-investigator là trợ lý điều tra (investigation assistant), làm việc trên dữ liệu tổ chức đang có, và khách thật của nó là đội SOC thiếu người.** Ba mệnh đề này kéo theo nhau. Làm việc trên dữ liệu đang có nghĩa là công cụ không yêu cầu tổ chức phải có đủ một danh sách nguồn dữ liệu tối thiểu: thiếu nguồn nào thì báo cáo khai báo khoảng trống dữ liệu ở nguồn đó kèm khuyến nghị thu thập thêm, chứ không từ chối chạy (quy định tại phần 2.1 bên dưới). Khách thật là đội thiếu người, nghĩa là giá trị đem ra đo không phải "độ thông minh của mô hình" mà là "một cảnh báo tốn bao nhiêu phút của nhà phân tích trước và sau khi có bản thảo điều tra". Trung lập với nhà cung cấp nghĩa là không gắn giá trị vào một nhà cung cấp nào: khối điều tra trung tâm là của công cụ, còn bộ kết nối SIEM và bộ cung cấp mô hình là hai điểm kết nối thay thế được (mục 1, kịch bản A, B, C). Chữ Wazuh trong đặc tả này xuất hiện vì v0.2 chọn dựng bộ triển khai tham chiếu trên Wazuh, không phải vì thiết kế chỉ sống được với Wazuh.

## 2. Bài toán

Giúp nhà phân tích nhanh chóng hiểu một cảnh báo: tự động thu thập và tương quan các sự kiện liên quan, rồi tạo báo cáo điều tra ban đầu có bằng chứng kiểm chứng được. Công cụ bổ sung năng lực phân tích cho SIEM hiện có, **không thay thế SIEM/SOAR**.

### 2.1. Yêu cầu chính thức về phạm vi dữ liệu, độ phủ và lỗ hổng dữ liệu.

Bộ yêu cầu này là xương sống nối ba nơi trong đặc tả: thiết kế gói kịch bản, luồng xử lý của lệnh investigate và định dạng báo cáo . Xuất phát điểm là tinh thần khoa học pháp y: hiện vật được lưu giữ tới đâu thì kết luận chỉ tới đó, không hơn; điều tra tra viên còn có nghĩa vụ chuyên môn là khuyến nghị thu thập thêm hiện vật gì để hiểu rõ hơn. Mỗi yêu cầu dưới đây đều kiểm chứng được bằng máy hoặc rà soát được trong pull request. 
*(Ký hiệu RQ là viết tắt của requirement (yêu cầu), dùng làm mã định danh để tham chiếu xuyên suốt tài liệu.)*

- **RQ1: công cụ điều tra trên chính dữ liệu mà tổ chức đang có.** Công cụ nhận dữ liệu thế nào thì phân tích và kết luận trên dữ liệu đó; không đặt điều kiện tổ chức phải có đủ một danh sách nguồn dữ liệu tối thiểu mới cho phép chạy. Lý do: nhiều tổ chức vì hiện trạng hạ tầng không thể triển khai đủ các nguồn (chưa bật ghi log truy vấn DNS, không có dữ liệu từ cổng thư điện tử hoặc proxy).
- **RQ2: mọi gói kịch bản phải khai báo độ phủ dữ liệu.** Mỗi gói kịch bản khai báo khối coverage gồm ba danh sách: những gì gói có thể hỏi được; những gì không quan sát được do thiếu loại dữ liệu; những gì thuộc gói kịch bản khác. Gói không khai báo khối coverage bị từ chối nạp.
- **RQ3: Định danh dữ liệu thiếu.** Mọi dữ liệu thiếu trong báo cáo phải được gắn đúng 1 trong 2 nhãn có ý nghĩa riêng biệt, tuyệt đối không đánh đồng:
        - **Nhãn 1 – Khoảng trống dữ liệu đã khai báo (Declared Data Gap):** Xảy ra khi gói kịch bản xác nhận tổ chức không có nguồn dữ liệu này (thuộc danh sách khoảng trống của khối _coverage_). Đây là trạng thái bình thường và được hiển thị dưới dạng văn bản mô tả trong báo cáo.
        - **Nhãn 2 – Sự thiếu vắng dữ liệu bất thường (Anomalous Data Absence):** Xảy ra khi gói kịch bản có yêu cầu loại dữ liệu này nhưng kết quả đếm thực tế lại trả về 0 sự kiện. Đây là sự mâu thuẫn giữa khai báo và thực tế.
                - _Cách xử lý:_ Công cụ sẽ ghi nhận nguyên văn mâu thuẫn này vào trường `evidence_state` (rõ ràng về nguồn dữ liệu, yêu cầu truy vấn và số lượng đếm được). Đồng thời, báo cáo liệt kê các giả thuyết có thể xảy ra (ví dụ: trích xuất sai khung thời gian, hoặc hoạt động thực tế không phát sinh) để người đọc tự kiểm chứng.
                - _Nguyên tắc:_ Công cụ không tự ý đưa ra kết luận hoặc chọn lựa giả thuyết, vì nó không có đủ căn cứ và đó cũng không phải chức năng của hệ thống.
        - **Mục tiêu cốt lõi:** Báo cáo phải đảm bảo tính tường minh, giúp người đọc nhận biết ngay lập tức mỗi dữ liệu thiếu đang thuộc nhãn nào mà không bị nhầm lẫn.
- **RQ4: Đảm bảo tính liên tục của công cụ và cơ chế phân định trách nhiệm.** Sự thiếu hụt dữ liệu chỉ làm thay đổi phạm vi kết luận của báo cáo chứ không bao giờ được làm gián đoạn quá trình vận hành của công cụ.
        - **Tính liên tục của hệ thống:** Bất kể gói chứng cứ ở trạng thái nào, công cụ vẫn phải thực hiện trọn vẹn quy trình để tạo ra kết quả điều tra. Hệ thống tuyệt đối không trả về mã lỗi hay tự ý phán quyết gói chứng cứ là "đạt" hay "không đạt" do thiếu dữ liệu.
        - **Phân chia trách nhiệm một chiều:** Công cụ đóng vai trò mô tả sự thật, còn người đọc đóng vai trò phán quyết. Dựa trên hai nhãn của RQ3 và số đếm trong trường `evidence_state`, người đọc sẽ tự đánh giá được giới hạn của kết luận tương ứng với lượng dữ liệu đầu vào.
- **RQ5: giới hạn kết luận và khuyến nghị chuyên gia là thành phần bắt buộc của báo cáo.** Mọi báo cáo phải phát biểu rõ giới hạn của kết luận và kèm khuyến nghị về các nguồn dữ liệu cụ thể cần thu thập thêm. Mỗi khuyến nghị nêu rõ nguồn cần bổ sung và nguồn đó cho phép phát hiện được gì. Người đọc từ đó tự kết luận được phải cung cấp thêm gì để nâng chất lượng điều tra.
- **RQ6: mọi phát biểu về dữ liệu phải dựa trên phép đếm máy thực hiện được.** Mọi phát biểu về trạng thái chứng cứ trong báo cáo đều xuất phát từ phép đếm sự kiện theo loại, không dựa trên phán đoán chủ quan.
- **Ghi chú về mối quan hệ giữa RQ3 và RQ4:**  RQ3 và RQ4 là hai mặt của một cam kết vận hành thống nhất, không thể tách rời:
        - **RQ4** cấp quyền cho công cụ luôn hoạt động bất chấp dữ liệu thiếu (tương tự một điều tra viên độc lập không trả lại hồ sơ chỉ vì hồ sơ mỏng).
        - **RQ3** buộc công cụ phải trung thực về những gì mình có và thiếu (điều tra viên không được im lặng về những tài liệu chưa tiếp cận).
        - _Hệ quả nếu tách rời:_ Nếu chỉ áp dụng RQ4 mà bỏ RQ3, công cụ sẽ tạo ra một báo cáo "giả tạo về sự đầy đủ", khiến người đọc lầm tưởng hệ thống an toàn ("không có bất thường") trên những vùng dữ liệu thực chất chưa từng được kiểm tra. Ngược lại, nếu cho phép công cụ dừng hoạt động khi thiếu dữ liệu, nó sẽ từ chối phục vụ chính những tổ chức đang gặp khuyết điểm về nguồn lực mà nó có trách nhiệm hỗ trợ.

## 3. Phạm vi của phiên bản v0.2

**Nguyên tắc xuyên suốt** 
1. Không tham vọng bao phủ mọi SIEM hay mọi mô hình; chỉ nhắm vào các lựa chọn phổ biến hiện tại.
2. **Wazuh chỉ là bộ SIEM đầu tiên dùng để hiện thực ý tưởng.** soc-investigator là trợ lý điều tra độc lập SIEM. Thiết kế không gắn với nhà cung cấp nào.

**Lưu ý**: Những tham chiếu hay đề cập tới wazuh trong nội bộ tài liệu này chỉ mang một trong ba vai trò:
1. **Bộ kết nối đầu tiên.** v0.2 triển khai đúng một `SiemConnector` chạy trực tiếp: WazuhConnector, đọc từ Wazuh Indexer qua giao diện OpenSearch API. Mọi chi tiết `wazuh-alerts-*`, `wazuh-archives-*` trong tài liệu thuộc vai trò này.
2. **Phòng thí nghiệm tham chiếu.** Dữ liệu demo và kiểm thử được sản xuất từ một phòng thí nghiệm Wazuh cùng Sysmon và Atomic Red Team.
3. **Kịch bản triển khai cho khách chưa có SIEM.** Trong trường hợp, khách hàng muốn bắt đầu từ số không được hướng dẫn dựng Wazuh cùng Ollama.

**Nội dung:**
- Một bộ kết nối SIEM: **Wazuh Indexer** (giao diện OpenSearch API), quyền chỉ đọc trên dữ liệu nguồn.
- Một kịch bản điều tra: **tình huống ứng dụng Office sinh tiến trình thông dịch lệnh trên máy Windows**. Gói kịch bản `office-interpreter-execution-v1` điều tra ứng dụng Office sinh tiến trình thông dịch lệnh, theo dõi qua giai đoạn thực thi payload tới giai đoạn kết nối ra bên ngoài.
- Hai nhà cung cấp mô hình ngôn ngữ chạy được: **Ollama** (chạy tại chỗ, mặc định, kịch bản B) và **Anthropic Claude API** (từ xa, kịch bản A và C, che dữ liệu bắt buộc bật), kèm interface cho nhà cung cấp khác.
- Tập tri thức cục bộ: **MITRE ATT&CK (tập con)** cùng playbook nội bộ.
- **Giao diện dòng lệnh là điểm vào duy nhất**: `install`, `config`, `doctor` (kiểm tra vận hành và sinh cấu hình), `investigate` (trực tiếp hoặc `--replay`), `smoke` (kiểm tra bốc khói toàn dây chuyền), `verify` (đối chiếu mã băm báo cáo với bản ghi lưu trong chỉ mục), `eval`, `export` (kèm `--public` để tạo bản chia sẻ đã bỏ dữ liệu thô).
- **Chế độ replay** qua `FileConnector` (bộ triển khai thứ hai của `SiemConnector`): chạy lại điều tra từ bản xuất NDJSON sẵn trong `lab-data/`, phục vụ người dùng không có phòng thí nghiệm, đánh giá trên cùng đầu vào, và demo dự phòng.
- **Investigation ledger (nhật ký điều tra)** ghi kèm mỗi báo cáo tại `reports/<alert_id>.ledger.json`: prompt đã qua che dữ liệu, câu trả lời thô của mô hình, từng hành động của validator. Toàn bộ quá trình trao đổi với mô hình xem lại được sau này.
- **Wazuh archives là yêu cầu của phòng thí nghiệm**: cảnh báo đầu vào đọc từ `wazuh-alerts-*`, sự kiện cho bộ tương quan đọc từ `wazuh-archives-*` . Lưu ý: bật archives làm tăng đáng kể dung lượng lưu trữ, tài liệu deployment phải cảnh báo rõ khi bật ở môi trường thật.
- Kết quả: ghi báo cáo vào **chỉ mục riêng `ai-investigations-*`**, xem được trong Wazuh Dashboard qua file import, kèm xuất báo cáo HTML và Markdown độc lập.
- Bộ dữ liệu kiểm thử tái hiện được bằng **Atomic Red Team**.
- **Eval harness** (bộ khung đánh giá) cùng ghi chú mô hình: đúng một mô hình chạy tại chỗ.

### Ngoài phạm vi v0.2

Đây là những yếu tố đã có sự cân nhắc tuy nhiên chưa triển khai trong phiên bản v0.2:
- Đa SIEM (connector ELK, Splunk).
- Splunk App hoặc plugin Wazuh thật.
- Tích hợp với Kafka, TheHive.
- Công cụ tự tạo quy tắc Sigma/YARA.
- Công cụ tự đóng cảnh báo, tự động hóa phản ứng.
- Agent tự trị nhiều bước, đa agent. 
- Trình cài đặt tự động hoàn chỉnh cho doanh nghiệp, deployment recipe đầy đủ cho kịch bản A và C. 
- Chế độ mở rộng phạm vi điều tra sau vòng đầu (theo hướng do chính kết quả vòng một gợi ý, kèm bước duyệt của người).
## 4. Kiến trúc tổng thể

```
                 ┌──────────────────────────────────────────────────┐
                 │                   CLI (typer)                    │
                 │ install · config · doctor · investigate · smoke  │
                 │ eval · export · verify                           │
                 └───────────────────┬──────────────────────────────┘
                                     │
        ┌────────────────────────────┼─────────────────────────────┐
        │                            ▼                             │
        │  ┌──────────────────────────────────────────────────┐    │
        │  │              Investigation Brain                 │    │
        │  │                                                  │    │
        │  │  1. ScenarioPack loader (YAML)                   │    │
        │  │  2. Evidence Correlator (code thuần, KHÔNG LLM)  │    │
        │  │  3. Knowledge retriever (ATT&CK + playbooks)     │    │
        │  │  4. Prompt builder (evidence đã cô đọng)         │    │
        │  │  5. Output validator                             │    │
        │  │  6. Report writer                                │    │
        │  └───────▲──────────────────────────────▲──────────┘    │
        │          │                              │               │
        │  ┌───────┴────────┐            ┌────────┴───────┐       │
        │  │ SiemConnector  │            │  LlmProvider   │       │
        │  │  (interface)   │            │  (interface)   │       │
        │  │  ├─ Wazuh live │            │  ├─ Ollama thật│       │
        │  │  └─ File replay│            │  ├─ Claude API │       │
        │  │                │            │  └─ Fake smoke │       │
        │  └───────┬────────┘            └────────┬───────┘       │
        └──────────┼──────────────────────────────┼───────────────┘
                   ▼                              ▼
            Wazuh Indexer                  Ollama (local — mặc định)
            - alerts (read-only)           - qwen2.5:3b-instruct-q4_K_M
            - ai-investigations-* (write)
                                            Anthropic API (từ xa — Claude)
```

### Mô tả từng thành phần

- Sáu thành phần đầu tiên của khối điều tra trung tâm đã được định nghĩa ngắn ở mục 0 ([[#0. Tóm tắt đặc tả.]]).
- Bảng dưới đây mô tả  từng thành phần và các thành phần hỗ trợ quanh khối.

| Thành phần            | Trách nhiệm                                                                                                                                                                                                                                                                                                                                                                                                             | Ghi chú                                                                                                                                                                                                                        |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `cli`                 | Điểm vào: `install`, `config`, `doctor`, `investigate --alert <id>` hoặc `--replay <file>`, `smoke`, `verify`, `eval`, `export`                                                                                                                                                                                                                                                                                         | Dùng typer                                                                                                                                                                                                                     |
| `connectors.base`     | Interface `SiemConnector`                                                                                                                                                                                                                                                                                                                                                                                               | Chi tiết ở [[#5. Interfaces (phác thảo)]].                                                                                                                                                                                     |
| `connectors.wazuh`    | Đọc cảnh báo, tìm sự kiện, ghi vào chỉ mục `ai-investigations-*`                                                                                                                                                                                                                                                                                                                                                        | Dùng opensearch-py; cảnh báo từ `wazuh-alerts-*`, sự kiện từ `wazuh-archives-*`<br>Chi tiết ở [[#6. Luồng xử lý chi tiết]], [[#7. Scenario Pack — định dạng đầy đủ]].                                                          |
| `connectors.file`     | FileConnector cho chế độ replay: đọc cảnh báo và sự kiện từ bản xuất NDJSON, `write_investigation` ghi cục bộ                                                                                                                                                                                                                                                                                                           | Bộ triển khai thứ hai của `SiemConnector`, phục vụ hướng dẫn nhanh mã nguồn mở và đánh giá trên cùng đầu vào                                                                                                                   |
| `doctor`              | Kiểm tra vận hành: kết nối, vai trò tối thiểu (permissions.md), phát hiện chỉ mục, kiểm tra archives, truy vấn mẫu, kiểm tra nhà cung cấp mô hình (Ollama: server và mô hình; Anthropic: khóa tồn tại, không bao giờ in giá trị khóa); sinh `.env` kèm hướng dẫn và kiểm tra an toàn của `.env`                                                                                                                         | In PASS hoặc FAIL cho từng mục; mã thoát khác 0 khi có FAIL (dùng được trong script và CI)                                                                                                                                     |
| `smoke`               | Chạy `investigate --replay` trên bản NDJSON mẫu sẵn trong repo rồi tự đối chiếu từng khâu đầu ra (báo cáo, schema, trích dẫn, mã băm, nhật ký); in PASS hoặc FAIL cho từng khẳng định                                                                                                                                                                                                                                   | Chống "thành công giả". Mặc định chạy qua **FakeProvider** (không cần mô hình, vài giây); `--live-model` mới gọi nhà cung cấp thật (Ollama, hoặc Claude qua `--provider anthropic`)<br>Chi tiết ở [[#6. Luồng xử lý chi tiết]] |
| `correlator`          | Từ cảnh báo đầu vào: lần ngược cây tiến trình (theo ProcessGuid, mục 6 bước 3b), kết nối mạng, thay đổi file; khử trùng lặp; dựng dòng thời gian; trích chỉ dấu xâm nhập bằng parser và regex; áp dụng ngân sách token.                                                                                                                                                                                                 | **Code thuần, phần khác biệt lớn nhất của công cụ**                                                                                                                                                                            |
| `knowledge`           | Nạp tập con ATT&CK (STIX JSON) và playbook YAML; truy xuất kỹ thuật và playbook liên quan theo bằng chứng                                                                                                                                                                                                                                                                                                               | Không dùng vector DB ở v0.2 vì không cần: tra cứu theo technique id và từ khóa là đủ                                                                                                                                           |
| `providers.base`      | Interface `LlmProvider`                                                                                                                                                                                                                                                                                                                                                                                                 | Chi tiết ở [[#5. Interfaces (phác thảo)]]                                                                                                                                                                                      |
| `providers.ollama`    | Gọi Ollama (chạy tại chỗ, mặc định), ép kết quả có cấu trúc theo JSON schema                                                                                                                                                                                                                                                                                                                                            | format=json hoặc schema; che dữ liệu mặc định bật, tắt được bằng cấu hình                                                                                                                                                                                                        |
| `providers.anthropic` | Gọi Anthropic Messages API (Claude) theo đúng hợp đồng `LlmProvider`: trả JSON khớp schema hoặc raise SchemaError, thử lại tối đa 2 lần kèm phản hồi lỗi có cấu trúc                                                                                                                                                                                                                                                    | Nhà cung cấp từ xa, che dữ liệu bắt buộc bật; chi phí tính từ số liệu usage ghi trong nhật ký                                                                                                                                  |
| `providers.fake`      | **FakeProvider**: đọc câu trả lời mô hình đã ghi sẵn trong `lab-data/`, không gọi mô hình thật                                                                                                                                                                                                                                                                                                                          | Phục vụ tầng smoke nhanh: chạy được trên máy không có mô hình và CI không có GPU.<br>Chi tiết ở [[#6. Luồng xử lý chi tiết]], [[#14. Rủi ro và giảm thiểu]].                                          |
| `prompts`             | Khuôn mẫu prompt; tách rõ phần system (chỉ thị) và phần evidence (dữ liệu, được đánh dấu không tin cậy)                                                                                                                                                                                                                                                                                                                 | Chống prompt injection.<br>Chi tiết ở [[#9. Báo cáo điều tra — định dạng đầu ra]].                                                                                                                                             |
| `validator`           | Kiểm tra kết quả: schema hợp lệ; technique nằm trong whitelist ATT&CK (tập do retriever đề xuất, **không** lấy từ đáp án); mọi dữ kiện có trích dẫn tới evidence_id tồn tại; kiểm thêm `checklist_results`: mỗi mục đúng một trong ba trạng thái confirmed, refuted, inconclusive, trích dẫn hợp lệ khi có, mục inconclusive phải nêu lý do và liên kết tới missing_data.                                               | Kết luận không có trích dẫn thì gắn cờ `unverified` hoặc loại bỏ                                                                                                                                                               |
| `report`              | Kết xuất JSON, ghi vào chỉ mục (document mang kèm mã băm làm mốc đối chiếu, mục 6 bước 8), xuất HTML và Markdown (kèm `--public`), ghi nhật ký điều tra cùng file bảng đối chiếu redaction riêng (quyền 0600); tạo thêm `scope_statement` (phát biểu phạm vi lấy từ khối coverage của gói) và `evidence_state` (trạng thái chứng cứ: đếm theo loại, sự thiếu vắng dữ liệu bất thường, khoảng trống dữ liệu đã khai báo), và `playbook_provenance` (playbook gói khai đã dùng, kèm mã băm nội dung lúc chạy) | Dùng Jinja2 làm định dạng nhật ký.<br>Chi tiết ở [[#9. Báo cáo điều tra — định dạng đầu ra]].                                                                                                                                  |
| `scenarios`           | Nạp gói kịch bản YAML, cung cấp quy tắc khởi điểm, cấu hình truy vết, danh sách câu hỏi giả thuyết ba tầng, khối coverage, khung phương pháp; **kiểm tra gói bằng máy** ngay sau khi ghép include: vi phạm là từ chối nạp với mã thoát riêng                                                                                                                                                                            | Chi tiết ở [[#7. Scenario Pack — định dạng đầy đủ]], [[#10. Eval harness và ghi chú mô hình]].                                                                                                                                 |
| `eval`                | Chạy bộ dữ liệu golden (đọc từ `eval/golden/` tách riêng), chấm điểm, xuất ghi chú mô hình (một mô hình duy nhất)                                                                                                                                                                                                                                                                                                       | Chi tiết ở [[#10. Eval harness và ghi chú mô hình]]                                                                                                                                                                            |

**Quyết định kiến trúc then chốt:** mô hình ngôn ngữ **không bao giờ nhìn log thô**. Correlator làm sạch và cô đọng bằng chứng thành một *evidence bundle* (gói chứng cứ) nhỏ gọn; mô hình chỉ suy luận trên gói đó. Lý do: (1) phần cứng yếu, cửa sổ ngữ cảnh nhỏ nên mô hình nhỏ vẫn chạy được; (2) giảm hallucination; (3) giảm bề mặt prompt injection; (4) kiểm soát chi phí token khi dùng nhà cung cấp thương mại.

## 5. Interfaces (phác thảo)

```python
# connectors/base.py
class SiemConnector(Protocol):
    def get_alert(self, alert_id: str) -> Alert: ...
    def search_events(self, query: dict, start: datetime, end: datetime,
                      limit: int = 500) -> list[Event]: ...
    # Phân trang bằng search_after (con trỏ sort), KHÔNG dùng from/size —
    # vượt max_result_window của OpenSearch là bị cắt im lặng.
    def write_investigation(self, report: InvestigationReport) -> str: ...
    # write_investigation CHỈ ghi vào index riêng của tool,
    # không bao giờ sửa dữ liệu nguồn.
    # Implementations v0.2: WazuhConnector (bộ kết nối Wazuh, chạy trực tiếp),
    # FileConnector (replay NDJSON — đọc lab-data/, ghi report cục bộ).

# providers/base.py
class LlmProvider(Protocol):
    def generate(self, system: str, user: str,
                 schema: dict, temperature: float = 0.0) -> dict: ...
    # HỢP ĐỒNG: luôn trả về JSON khớp schema hoặc raise SchemaError.
    # Cách ép structured output là chuyện của từng provider
    # (Ollama format=json, vLLM guided decoding, OpenAI/Anthropic
    # structured output) — interface ràng buộc KẾT QUẢ, không ràng buộc cơ chế.
    # RETRY: khi output không khớp schema, provider adapter thử lại
    # tối đa 2 lần. Mỗi lần thử lại PHẢI kèm PHẢN HỒI LỖI CÓ CẤU TRÚC
    # gửi cho model, gồm hai phần:
    #   (a) yêu cầu bắt buộc của kết quả — JSON hợp lệ theo schema, mọi
    #       phần tử có citation, mọi câu hỏi checklist có trạng thái
    #       thuộc ba giá trị confirmed/refuted/inconclusive...;
    #   (b) chẩn đoán CỤ THỂ kết quả vừa đưa thiếu gì — lỗi parse ở đâu,
    #       thiếu trường nào, phần tử nào không có citation...
    # Lý do: càng chỉ rõ thiếu sót, xác suất lần sau trả lời đúng càng cao —
    # "thử lại" không kèm chẩn đoán chỉ là cầu may. Số lần thử và lỗi
    # từng lần ghi vào ledger (trường attempts) để xem lại được.

# scenarios/loader.py
class ScenarioPack(BaseModel):
    scenario_id: str
    name: str
    description: str                  # mô tả chính xác nội dung pack điều tra
    entry_alert: EntryAlertConfig
    correlation: CorrelationConfig
    attack_simulation: AttackSimConfig
    hypothesis_checklist: ChecklistConfig   # ba tầng A/B/C
    coverage: CoverageConfig                # hỏi được / không quan sát được / thuộc pack khác
    methodology: list[str]                  # khung hướng dẫn tư duy
    playbooks: list[str]                    # đường dẫn file playbook gói khai —
                                            # nguồn tra của bước 4, nguồn mảnh dữ liệu thứ ba của prompt ở bước 5
    # golden_truth KHÔNG ở đây: đáp án sống ở
    # eval/golden/<scenario_id>.yaml — chỉ eval harness đọc.
    # Runtime không bao giờ thấy đáp án → không có đường rò
    # đáp án vào prompt hay whitelist validator.
```

**Lưu ý:** Thêm SIEM mới nghĩa là viết một `SiemConnector` mới. Thêm mô hình ngôn ngữ mới nghĩa là viết một `LlmProvider` mới. Hai việc này không đụng vào khối điều tra trung tâm.

Kỷ luật triển khai: mỗi interface có **đúng một bộ triển khai chạy được**; interface chứng minh tầm nhìn, một bộ triển khai chạy tốt chứng minh tay nghề. **Ngoại lệ có chủ đích** (mỗi ngoại lệ phải tự trả lời được câu hỏi "tại sao cần nhiều hơn một"): (1) `SiemConnector` có hai (Wazuh chạy trực tiếp và File replay) vì replay phục vụ đồng thời hướng dẫn nhanh mã nguồn mở, đánh giá cùng đầu vào và demo dự phòng; (2) `LlmProvider` có ba nguồn (Ollama là đường cục bộ mặc định cho kịch bản B; Anthropic Claude là đường nhà cung cấp từ xa cho kịch bản A, C và lối thoát rủi ro R1; FakeProvider là tầng smoke nhanh cho CI không GPU). Ba đường phục vụ ba nhu cầu thật khác nhau. Không dùng LiteLLM trong lõi: tự viết adapter mỏng cho từng nhà cung cấp (giữ mục tiêu làm chủ công nghệ, tránh dependency nặng). LiteLLM được nêu trong tài liệu như một lựa chọn cho người dùng muốn thêm nhà cung cấp nhanh.

## 6. Luồng xử lý chi tiết

Mục này mô tả luồng chạy của từng lệnh: `doctor`, `investigate` (trực tiếp hoặc `--replay`), `smoke`, `verify`. Mỗi lệnh ghi đủ ba thứ mà người viết mã cần: dữ liệu vào, dữ liệu ra, và quy tắc bắt buộc kèm lý do của quy tắc. Người đọc không cần nhảy sang mục khác để hiểu một bước.

### 6.1. `doctor` — kiểm tra môi trường trước khi chạy

Lệnh `doctor` trả lời đúng một câu hỏi: máy này đã sẵn sàng chạy điều tra chưa. Lệnh chạy bảy nhóm kiểm tra dưới đây; mỗi nhóm in một dòng PASS hoặc FAIL, FAIL kèm hướng dẫn sửa; tồn tại ít nhất một FAIL thì mã thoát khác 0 để dùng được trong script và tích hợp liên tục.

Mô tả viết theo bộ kết nối Wazuh, bộ kết nối chạy trực tiếp của v0.2. Bộ kết nối khác sẽ có danh sách kiểm riêng theo cùng khuôn mẫu này.

1. **Kết nối tới Wazuh Indexer**: TLS và credential hợp lệ.
2. **Vai trò tối thiểu**: tài khoản của công cụ phải đọc được `wazuh-alerts-*` và `wazuh-archives-*`, ghi được `ai-investigations-*`, và không có quyền nào khác. Định nghĩa vai trò nằm ở `docs/deployment/permissions.md` và `lab/wazuh/roles/`. Quyền rộng hơn mức tối thiểu không làm lệnh FAIL, nhưng in WARN — dấu hiệu tài khoản được cấp quá rộng, cần thu lại.
3. **Phát hiện chỉ mục**: quét xem các pattern có thật tồn tại trên hệ thống (alerts, archives, monitoring) thay vì giả định tên chỉ mục.
4. **Kiểm tra archives**: `wazuh-archives-*` phải tồn tại và có dữ liệu Sysmon gần đây. Thiếu thì in hướng dẫn bật: Filebeat đặt `archives.enabled = true`. Kèm một WARN nếu trường `DestinationHostname` (Sysmon EID 3/22) chưa được decode: correlator truy vấn theo domain sẽ trả về danh sách rỗng mà không báo lỗi khi thiếu trường này — cảnh báo sớm thay vì để nhà phân tích tự truy dò tại sao "không thấy gì".
5. **Truy vấn mẫu**: chạy một truy vấn trên pattern vừa phát hiện, đo độ trễ và đếm tài liệu trong 24 giờ.
6. **Kiểm tra nhà cung cấp mô hình theo cấu hình**: Ollama — server đang chạy và mô hình cấu hình đã được tải; Anthropic — `ANTHROPIC_API_KEY` có mặt trong `.env`. Giá trị khóa không bao giờ được in ra màn hình.
7. **Sinh cấu hình và kiểm tra an toàn của `.env`**: sinh file `.env` từ kết quả phát hiện, in hướng dẫn bước kế tiếp. Vì `.env` chứa mật khẩu dạng văn bản thô (kể cả `ANTHROPIC_API_KEY` khi cấu hình đường Claude), doctor kiểm tra quyền file — khuyến nghị chmod 600, WARN nếu file đọc được rộng hơn chủ sở hữu — và cảnh báo nếu `.env` chưa nằm trong `.gitignore`. Tài liệu đi kèm ghi rõ hai quy tắc xử lý: không bao giờ commit, xóa khi không còn dùng.

### 6.2. `investigate` — điều tra trực tiếp một cảnh báo

```
soc-investigator investigate --alert <alert_id> [--scenario auto] [--provider ollama|anthropic] [--model qwen2.5:3b]
```

Dây chuyền gồm tám bước nối tiếp: hai bước đầu xác định cảnh báo và gói kịch bản, bước ba thu thập bằng chứng, các bước còn lại suy luận, kiểm tra và kết xuất.

**Bước 1 — Đọc cảnh báo.** `Connector.get_alert(alert_id)` trả về cảnh báo gốc qua bộ kết nối đang cấu hình. Với bộ kết nối Wazuh, cảnh báo đọc từ chỉ mục `wazuh-alerts-*`.

**Bước 2 — Nạp gói kịch bản và kiểm tra bằng máy.** Loader khớp `rule_id` của cảnh báo với gói kịch bản tương ứng; cờ `--scenario` chỉ định tường minh khi cần. Không khớp gói nào thì thoát rõ ràng: in thông điệp "alert này không thuộc scenario pack đã cài; xem các pack có sẵn trong thư mục `scenarios/`" và trả mã thoát riêng, phân biệt với lỗi hệ thống — không crash, không trả về báo cáo rỗng.

Gói khớp xong được kiểm bằng máy ngay tại lúc nạp, trước khi bất kỳ thành phần nào sử dụng nó, theo bốn luật. Luật một: mọi câu hỏi trong hypothesis checklist khai `evidence_types` thì loại đó phải có trong correlation config của chính gói. Luật hai: mọi chiến thuật trong tầng C phải có câu hỏi hoặc khai báo khoảng trống dữ liệu kèm lý do. Luật ba: mọi câu hỏi phải là khẳng định kiểm chứng được — có `id`, có `question` phát biểu dưới dạng khẳng định chấm được ba trạng thái, có `evidence_types` không rỗng. Luật bốn: mọi đường dẫn playbook trong khối `playbooks` của gói phải trỏ tới file có thật trên đĩa lúc nạp — khai file không tồn tại là từ chối nạp. Vi phạm bất kỳ luật nào: từ chối nạp gói với mã thoát riêng (phân biệt với cả "cảnh báo không khớp gói" lẫn lỗi hệ thống), kèm thông điệp chỉ đúng mục vi phạm. Mục đích của phép kiểm này là bắt lỗi của người viết gói từ lúc nạp, không đợi tới báo cáo sai xuất hiện trước người dùng cuối.

**Bước 3 — Correlator thu thập và cô đọng.** Correlator chạy theo correlation config của gói. Với bộ kết nối Wazuh: cảnh báo đọc từ `wazuh-alerts-*`, sự kiện đọc từ `wazuh-archives-*`. Bảy việc nối tiếp nhau:

- **(a) Khung thời gian.** Lấy sự kiện trong `lookback_window` quanh thời điểm cảnh báo (gói hiện hành: 30 phút).
- **(b) Cây tiến trình.** Sysmon EID 1, dựng cây theo host cộng ProcessGuid/ParentProcessGuid. Không dùng PID/PPID: Windows tái sử dụng PID — một PID từng thuộc tiến trình A có thể được cấp lại cho tiến trình B sau khi A thoát, nên cây dựng theo PID sẽ nối nhầm quan hệ cha con. Bản NDJSON mẫu trong `lab-data/` kèm một ca PID tái sử dụng làm unit test cho quy tắc này.
- **(c) Kết nối mạng.** Sysmon EID 3: các kết nối ra ngoài của những tiến trình trong cây.
- **(d) Thay đổi file.** Sysmon EID 11: file tạo mới trên máy (payload bị thả xuống). Nguồn dữ liệu là Sysmon; không dùng Wazuh FIM.
- **(e) Dòng thời gian và chỉ dấu.** Khử trùng lặp rồi sắp theo thời gian; trích IoC (domain, IP, hash, đường dẫn) bằng parser. File change khử trùng lặp theo bộ khóa host + đường dẫn + mtime, vì Sysmon EID 11 có thể ghi nhiều bản ghi cho cùng một file (tạo rồi đổi tên); khóa sai thì dòng thời gian lặp đôi.
- **(f) Ngân sách token.** Vượt trần thì siết dần theo thứ tự: siết khung thời gian quanh cảnh báo, bỏ bằng chứng ưu tiên thấp, cắt nhánh lá của cây tiến trình. Mọi lần bỏ dữ liệu phải ghi vào `stats.dropped_by_budget`.
- **(g) Đếm theo loại.** Đếm sự kiện theo loại (process_create, network, file_change...) ghi vào `stats.per_type_counts`. Đây là nguyên liệu cho trường `evidence_state` của báo cáo: loại dữ liệu mà gói khai hỏi được nhưng đếm về 0 là "sự thiếu vắng dữ liệu bất thường" — mâu thuẫn giữa khai báo của gói và phép đếm. Tình huống này được ghi nhận thành chữ trong báo cáo và không bao giờ là lý do từ chối điều tra.

Kết quả của bước này là một EvidenceBundle — gói chứng cứ đã cô đọng. Chỉ gói này đi vào prompt, không phải các sự kiện thô.

**Bước 4 — Truy xuất tri thức.** Knowledge retriever ánh xạ từng indicator sang các kỹ thuật ATT&CK ứng viên và playbook liên quan. Với playbook, retriever chỉ nạp và tra các file trong khối `playbooks` của chính gói đang chạy, không quét toàn thư mục `playbooks/` — gói khai file nào thì chỉ file đó vào vòng. Đầu ra của bước này đồng thời là whitelist cho validator ở bước 7.

**Bước 5 — Dựng prompt.** Prompt gồm hai phần tách bạch: system prompt mang vai trò, luật và schema; phần dữ liệu mang bundle đã cô đọng, đặt trong khối `<evidence>…</evidence>` và được system prompt khai báo rõ là dữ liệu không tin cậy. Prompt mang thêm ba mảnh dữ liệu từ gói kịch bản. Thứ nhất, hypothesis checklist ba tầng: mô hình được chỉ thị trả lời từng câu hỏi với đúng một trong ba trạng thái confirmed, refuted, inconclusive kèm trích dẫn; mục inconclusive phải nêu thiếu dữ liệu gì. Thứ hai, khung phương pháp: các câu hướng dẫn trình tự tư duy riêng của case này, ví dụ đọc timeline trước, kiểm cây tiến trình trước khi kết luận, không bù đắp bằng phỏng đoán khi thiếu bằng chứng. Thứ ba, nội dung các playbook mà bước 4 chọn: quy trình xử lý của tổ chức cho loại sự kiện này. System prompt khai rõ đây là thủ tục, không phải dữ kiện — mô hình bám theo trình tự nhưng không được viện dẫn playbook làm bằng chứng; mọi phát biểu vẫn phải trích dẫn `evidence_id` như luật chung. Từng bước playbook được đánh dấu một trong ba trạng thái vào trường `playbook_results`: `answered` (bằng chứng trong lượt này trả lời được bước), `unanswered` (thuộc phạm vi nhưng chưa trả lời được — phải nêu thiếu dữ liệu gì), `out_of_scope` (ngoài phạm vi lượt điều tra này — phải nêu lý do). Đánh dấu vì playbook viết cho toàn vụ việc, còn gói khai đúng một điểm phát xuất — bản thảo phải nói thẳng bước nào có bằng chứng trả lời, bước nào ngoài lượt này. Checklist là giới hạn dưới chứ không phải giới hạn trên: mô hình được bổ sung giả thuyết ngoài danh sách, miễn mọi giả thuyết có trích dẫn; validator kiểm giả thuyết như kiểm facts.

Trước khi prompt rời khỏi công cụ, che dữ liệu được áp lên phần bằng chứng: username (kể cả trong đoạn đường dẫn `C:\Users\<tên>\`), IP nội bộ, email được thay bằng placeholder dạng `[USR_1]`, `[IP_1]`. Che dữ liệu **bắt buộc bật** khi gửi tới nhà cung cấp mô hình từ xa qua API thương mại (Claude API, ChatGPT/OpenAI) — cấu hình không có cờ tắt; với Ollama cục bộ, che dữ liệu **mặc định bật** và tắt được bằng cấu hình, vì mô hình chạy tại chỗ, dữ liệu không rời hạ tầng. Bundle nội bộ luôn giữ giá trị gốc — che dữ liệu chỉ áp tại biên giới gửi đi và hiển thị. Bảng đối chiếu giữa placeholder và giá trị gốc không bao giờ nằm trong báo cáo: report writer ghi ra file riêng `reports/<alert_id>.redaction-map.json` (chmod 0600, nằm trong .gitignore), để việc gửi báo cáo cho đồng nghiệp không kèm chìa khóa giải mã.

Tại bước này chạy một cơ chế bảo vệ: prompt guard. Đầu ra của prompt builder được kiểm tra trước khi gửi — không chứa sự kiện thô (chỉ summary đã cô đọng), không chứa chuỗi giống key hoặc password theo pattern cố định. Vi phạm là từ chối gửi, không phải che lại sau đó. Guard hoạt động với mọi nhà cung cấp, gồm cả Anthropic. Ngoài guard này không có rào cứng nào khác về nội dung gửi đi: với nhà cung cấp từ xa, che dữ liệu bắt buộc bật, không có cờ tắt; với Ollama cục bộ, người dùng có quyền tắt bằng cấu hình. SECURITY.md ghi thẳng điều cần cân nhắc khi tắt (chỉ khả dụng trên đường Ollama cục bộ): ledger và báo cáo vẫn chứa nội dung nhạy cảm chưa che, phải bảo vệ quyền truy cập tương ứng.

**Bước 6 — Gọi mô hình.** `LlmProvider.generate(...)` trả về bản nháp JSON của báo cáo. Provider chọn theo cấu hình: `ollama` (mặc định, chạy tại chỗ) hoặc `anthropic` (Claude API, che dữ liệu bắt buộc bật, chi phí tính từ số liệu usage ghi trong ledger). Kết quả không khớp schema thì adapter thử lại tối đa 2 lần. Mỗi lần thử lại gửi cho mô hình một phản hồi lỗi có cấu trúc gồm hai phần: yêu cầu bắt buộc của kết quả (JSON hợp lệ theo schema, mọi phần tử có trích dẫn, mọi câu hỏi checklist có trạng thái thuộc ba giá trị), và chẩn đoán cụ thể kết quả vừa trả còn thiếu gì (lỗi parse ở đâu, thiếu trường nào, phần tử nào không có trích dẫn). Càng chỉ rõ thiếu sót, xác suất lần sau trả lời đúng càng cao; thử lại không kèm chẩn đoán chỉ là cầu may. Số lần thử và lỗi từng lần ghi vào ledger, trường `attempts`, để xem lại được.

**Bước 7 — Validator.** Năm phép kiểm nối tiếp:

1. **Schema**: kết quả parse được và khớp schema báo cáo.
2. **Whitelist ATT&CK**: mọi `technique_id` phải nằm trong tập kỹ thuật mà knowledge retriever có thể đề xuất (bộ con của tập ATT&CK trong repo). Whitelist không lấy từ golden truth: dùng đáp án làm whitelist thì validator tự quay vòng với eval.
3. **Trích dẫn**: mọi fact, IoC, timeline entry phải có citation trỏ tới `evidence_id` tồn tại trong bundle.
4. **Checklist**: `checklist_results` là mảng riêng, tách khỏi facts và hypotheses. Mỗi câu hỏi có đúng một trạng thái trong ba giá trị confirmed, refuted, inconclusive; trích dẫn (khi có) phải hợp lệ; mục inconclusive phải nêu lý do và móc vào `missing_data`. Phép kiểm này giữ được ranh giới giữa "hỏi rồi và dữ liệu nói không" (refuted) với "không hỏi được vì thiếu dữ liệu" (inconclusive).
5. **Đối chiếu nội dung mức 1**: với mọi phát biểu chứa thực thể kiểm tra được bằng máy — tên miền, địa chỉ IP, tên tiến trình, đường dẫn tệp, mã băm, dấu thời gian, con số — thực thể, sau khi chuẩn hóa về cùng dạng viết, phải xuất hiện nguyên văn trong ít nhất một mục bằng chứng mà phát biểu trích dẫn. Từng phát biểu của báo cáo mang một trong ba nhãn: **máy đã đối chiếu** (thực thể khớp), **chỉ có trích dẫn tồn tại** (trích dẫn hợp lệ nhưng chưa đối chiếu được nội dung), **diễn giải** (suy luận, không chứa thực thể kiểm tra được); phân bố ba nhãn hiển thị ngay phần mở đầu báo cáo để người đọc biết mình đang tin vào loại phát biểu nào.

Vi phạm: gắn cờ `unverified` hoặc loại bỏ phần tử, ghi lại trong `report.meta.validation`.

**Bước 8 — Report writer.** Tám nhiệm vụ nối tiếp:

1. **Đóng băng bằng chứng**: nhúng JSON đầy đủ của các event được trích dẫn (không phải toàn bộ sự kiện thô) cộng SHA-256 của từng event và của cả bundle vào `evidence_snapshot`. Trường `raw_ref` vẫn giữ để truy vết về SIEM. Giới hạn của cơ chế: mã băm nằm trong cùng file với dữ liệu, nên "mã băm khớp" nghĩa là nội dung nhúng nhất quán với lúc sinh — phát hiện hỏng hóc hoặc sửa vô ý; kẻ có chủ đích sửa event rồi tính lại mã băm thì không bị bắt. Chống sửa có chủ đích cần mã băm lưu ngoài file.
2. **Che dữ liệu hiển thị**: áp redaction lên các field hiển thị; báo cáo chỉ giữ `meta.redaction {enabled, counts}`; bảng map nằm ở file riêng 0600.
3. **Ghi nhật ký điều tra**: `reports/<alert_id>.ledger.json` — prompt đã qua che dữ liệu, câu trả lời thô của mô hình, từng hành động của validator, tên file cùng mã băm SHA-256 của từng playbook đã dùng trong lượt, xem lại được sau này.
4. **Sinh phạm vi, trạng thái chứng cứ và nguồn gốc playbook**: từ khối coverage của gói, sinh `scope_statement` đặt ngay cạnh `missing_data` — gói hỏi được gì, không quan sát được gì vì thiếu loại dữ liệu, gì thuộc gói khác — để người đọc hiểu ranh giới thay vì tự kết luận "công cụ thiếu kiến thức". Từ `stats.per_type_counts`, sinh `evidence_state`: đếm theo loại; danh sách "thiếu vắng dữ liệu bất thường" (gói khai hỏi được nhưng đếm về 0 — mâu thuẫn giữa khai báo và thực tế; báo cáo ghi nguyên văn sự việc kèm các khả năng xảy ra, ví dụ xuất dữ liệu sai khoảng thời gian, để người đọc tự kiểm tra; không chặn, không phán quyết đạt hay không); danh sách "khoảng trống dữ liệu đã khai báo" (thiếu nguồn theo danh sách blind của khối coverage — chấp nhận được). Từ khối `playbooks` của gói, report writer ghi khối `playbook_provenance` của báo cáo: mỗi file playbook đã dùng kèm mã băm SHA-256 nội dung đọc từ đĩa lúc chạy — ai đọc lại biết vụ này vận hành theo quy trình nào, phiên bản nào; dấu trạng thái từng bước lấy nguyên từ `playbook_results` của bản thảo. Khuyến nghị thu thập bổ sung sinh từ bốn nguồn: danh sách khoảng trống của coverage (kèm `would_enable`), lý do các mục inconclusive, và các thiếu vắng bất thường. Nguồn thứ tư là các bước playbook đánh dấu `unanswered` — khuyến nghị nói rõ cần thu thập dữ liệu gì để bước quy trình đó trả lời được; khuyến nghị loại này mang trường `source: "playbook"` thay vì citation, vì playbook là thủ tục, không phải nguồn chứng cứ, không có `evidence_id` để trích. Mỗi khuyến nghị nói rõ nguồn cần thêm và nguồn đó cho thấy gì, để người đọc tự kết luận phải cung cấp thêm gì để nâng chất lượng điều tra.
5. **Ghi mã băm vào nơi độc lập ngoài file**: document ghi vào chỉ mục `ai-investigations-*` mang kèm `bundle_sha256` và `ledger_sha256`; lệnh `verify` đối chiếu hai nơi. LIMITATIONS.md ghi rõ giới hạn còn lại: kẻ có quyền ghi cả báo cáo lẫn chỉ mục vẫn sửa được cả hai; mã băm lưu ngoài file là rào cản nâng cao, không phải biện pháp tuyệt đối.
6. **Ghi vào chỉ mục** `ai-investigations-*`.
7. **Kết xuất** `reports/<alert_id>.md` và `.html`.
8. **Bản chia sẻ an toàn khi chạy `export --public`**: bỏ giá trị thô trong `evidence_snapshot` (giữ `evidence_id` + sha256), áp che dữ liệu lên mọi field hiển thị, không kèm ledger và bảng map — gửi cho người ngoài không kèm dữ liệu gốc lẫn chìa khóa.

### 6.3. Đối chiếu nội dung mức 1

Phép kiểm trích dẫn trả lời được câu hỏi dễ: mục chứng cứ được trích có tồn tại trong gói hay không. Câu hỏi khó hơn — nội dung của mục chứng cứ có ủng hộ phát biểu hay không — do phép đối chiếu nội dung mức 1 trả lời. Mô hình hoàn toàn có thể viết "tiến trình kết nối tới tên miền độc hại cdn-update.example", trích dẫn mục E04, trong khi E04 ghi một truy vấn tới tên miền lành; chỉ kiểm tra trích dẫn tồn tại thì mâu thuẫn này lọt qua.

Hệ quả của lỗ hổng này nguy hiểm hơn cả việc không có kiểm định. Báo cáo trông đầy trích dẫn khiến người đọc hạ cảnh giác và tin vào phát biểu chưa được đối chiếu — niềm tin sai (false confidence). Trong nghiệp vụ điều tra, một báo cáo trông kiểm chứng được mà sai còn nguy hiểm hơn một báo cáo thể hiện rõ mức không chắc chắn, vì người đọc điều chỉnh hành vi theo niềm tin mà báo cáo tạo ra.

Bộ kiểm định thực hiện đối chiếu nội dung theo **mức 1**, gồm bốn phần. Một, trích xuất: với mọi phát biểu chứa thực thể kiểm tra được bằng máy — tên miền, địa chỉ IP, tên tiến trình, đường dẫn tệp, mã băm, dấu thời gian, con số — bộ kiểm định trích thực thể ra khỏi phát biểu. Hai, chuẩn hóa trước khi so sánh: đường dẫn về quy tắc viết thống nhất, dấu thời gian về một định dạng duy nhất, số về đơn vị gốc, không phân biệt hoa thường ở những nơi an toàn (tên miền, tên tiến trình trên Windows). Ba, đối chiếu: thực thể sau chuẩn hóa phải xuất hiện nguyên văn trong ít nhất một mục bằng chứng mà phát biểu trích dẫn. Bốn, gắn nhãn ba mức cho từng phát biểu: **máy đã đối chiếu** (thực thể khớp), **chỉ có trích dẫn tồn tại** (trích dẫn hợp lệ nhưng chưa đối chiếu được nội dung), **diễn giải** (suy luận, không chứa thực thể kiểm tra được); báo cáo hiển thị phân bố ba mức ngay phần mở đầu để người đọc biết mình đang tin vào loại phát biểu nào.

Hai điều kiện bắt buộc kèm theo, để phép đối chiếu không gây tác dụng ngược. Một, bộ kiểm thử đối kháng: gồm các đầu ra cố tình sai — trích dẫn tồn tại nhưng nội dung mâu thuẫn, thực thể không có trong gói chứng cứ — phải bị bộ kiểm định bắt; bộ kiểm thử chạy cùng lệnh smoke trong tích hợp liên tục. Hai, theo dõi tỷ lệ từ chối sai: phát biểu đúng nhưng bị từ chối vì khác dạng viết (mô hình viết tên rút gọn của tiến trình, bằng chứng ghi đường dẫn đầy đủ); tỷ lệ này ghi số thật vào MODEL_SELECTION.md. Lý do bắt buộc: bộ kiểm định hay từ chối sai sẽ bị người dùng tắt, và lúc đó hệ thống tệ hơn cả trường hợp không có kiểm định.

Giới hạn của chính mức 1, ghi thẳng để người đọc không kỳ vọng quá mức: sự hiện diện của một chuỗi, dù đã chuẩn hóa, trong bằng chứng chưa chứng minh vai trò ngữ nghĩa của nó — hai thực thể cùng có mặt trong hai sự kiện khác thời điểm, khác tiến trình vẫn được phép đối chiếu chấp nhận. Mức 1 nâng phát biểu từ truy nguyên được lên có cơ sở văn bản, vẫn chưa phải bảo đảm đúng sự thật.

### 6.4. `investigate --replay` — chạy lại không cần lab

```
soc-investigator investigate --replay <file.ndjson>
```

Bước 1 đến 3 chạy qua `FileConnector`: cảnh báo và sự kiện đọc từ bản xuất NDJSON trong `lab-data/` thay vì từ SIEM; mọi bước còn lại giữ nguyên. `write_investigation` ghi báo cáo ra thư mục cục bộ thay vì chỉ mục. Một bộ đầu vào duy nhất cho mọi lần chạy, phục vụ ba việc: hướng dẫn nhanh cho người dùng mã nguồn mở không có phòng thí nghiệm, ghi chú mô hình trên cùng đầu vào, và demo dự phòng.

Báo cáo — gồm bản chụp chứng cứ kèm SHA-256 và nhật ký điều tra — phải tạo giống hệt chế độ trực tiếp: replay là đầu vào đo lường, nên hai chế độ phải bảo đảm tương đồng tuyệt đối. Chế độ replay không có chỉ mục, vì vậy không có mã băm lưu ở nơi độc lập; lệnh `verify` chạy trên báo cáo replay chỉ kiểm nhất quán nội bộ.

### 6.5. `smoke` — kiểm tra bốc khói

Smoke test (kiểm tra bốc khói) là lệnh chạy nguyên dây chuyền từ đầu đến cuối bằng một đầu vào cố định rồi tự đối chiếu kết quả. Tên gọi bắt nguồn từ nghiệp điện máy: lần đầu cấp điện mà thấy máy bốc khói thì mọi phép đo chi tiết khác đều vô nghĩa — tổng thể không chạy thì đo từng mảnh cũng vô ích. Lệnh này tồn tại để chống "thành công giả", tình huống đáng ngại nhất của một bản demo: dây chuyền báo chạy xong, báo cáo được tạo, file HTML trông đẹp, nhưng bên trong rỗng (ví dụ validator vì một lỗi nhỏ loại bỏ toàn bộ facts) và không ai phát hiện cho tới khi bị chất vấn trực tiếp. doctor kiểm từng mảnh môi trường riêng lẻ; replay tạo báo cáo nhưng không tự kiểm chứng báo cáo đó lành lặn hay không. Smoke lấp đúng khoảng trống giữa hai thứ đó.

```
soc-investigator smoke [--input lab-data/sample-mini.ndjson] [--live-model]
```

Smoke chạy theo hai tầng:

- **Tầng nhanh (mặc định)**: mô hình được thay bằng FakeProvider — một trong ba bộ triển khai của LlmProvider, đọc câu trả lời đã ghi sẵn trong `lab-data/smoke-model-answer.json` (bản chụp từ câu trả lời thô trong ledger của một lần chạy thật). Tầng này kiểm toàn bộ dây chuyền trừ chính con mô hình: schema, trích dẫn, mã băm, ledger — trong vài giây, không cần Ollama, không cần tải mô hình nhiều GB. Lý do tồn tại: runner CI miễn phí của GitHub không có GPU, mỗi commit tải mô hình nặng hàng GB là bất khả thi, và output của mô hình không ổn định giữa các lần chạy làm kết quả CI dao động thất thường (rủi ro R13).
- **Tầng thật (`--live-model`)**: gọi nhà cung cấp thật như bình thường, mặc định Ollama; thêm `--provider anthropic` để kiểm đường Claude mà không cần GPU (tốn vài cent mỗi lần, chỉ chạy tay). Tầng thật chạy tay trước mỗi bản phát hành và trên máy lab, không chạy trong CI.

Quy trình ba bước:

1. Chạy `investigate --replay` trên bản NDJSON mẫu sẵn trong repo; mặc định là `lab-data/sample-mini.ndjson`, đổi được qua `--input` (ví dụ sang bản xuất từ lab thật `phish-case-01.ndjson`). Không cần lab, không cần SIEM; tầng nhanh còn không cần mô hình.
2. Tự đối chứng chuỗi khẳng định về sản phẩm vừa sinh ra — mỗi khẳng định in một dòng PASS/FAIL:
   - Evidence bundle sinh ra và đạt số lượng tối thiểu khai báo?
   - Provider có trả lời không? (tầng nhanh: câu trả lời ghi sẵn đọc được; tầng thật: output không rỗng)
   - Báo cáo parse được và khớp schema_version hiện hành?
   - 100% facts, timeline, IoC, attack_mapping có trích dẫn hợp lệ (đếm bằng validator)? Trạng thái confirmed và refuted của checklist_results phải có trích dẫn hợp lệ; trạng thái inconclusive phải nêu lý do — smoke đếm luôn hai phép này.
   - Validator không loại quá ngưỡng cho phép? Mặc định: quá 50% tổng claim là FAIL — loại gần hết nghĩa là có chỗ đứt ngược dòng.
   - SHA-256 của từng event và của cả bundle trong `evidence_snapshot` khớp khi tính lại từ dữ liệu nhúng?
   - Ledger tồn tại và mã băm prompt trong ledger khớp khi tính lại?
3. Kết thúc bằng mã thoát: 0 khi toàn bộ PASS; khác 0 khi có chỗ đứt, dòng FAIL nói rõ đúng khâu nào đứt.

Smoke không viết logic mới — nó chỉ phủ một lớp khẳng định lên đúng dây chuyền mà replay đã dựng sẵn. Thông điệp nó để lại cho người chạy: nếu lệnh này PASS thì sản phẩm chạy được trên máy bạn.

### 6.6. `verify` — kiểm tra tính toàn vẹn bằng mã băm

Mã băm nhúng trong báo cáo phát hiện được sửa vô ý nhưng không chống sửa có chủ đích, vì người sửa có thể tính lại mã băm. Lệnh `verify` dựa vào mã băm lưu ở nơi độc lập: lúc ghi báo cáo, report writer đã đẩy kèm `bundle_sha256` và `ledger_sha256` vào document trong chỉ mục `ai-investigations-*`. Lệnh verify tính lại mã băm từ dữ liệu trong file rồi so với bản ghi trong chỉ mục:

1. Đọc báo cáo và ledger từ đĩa; tính lại SHA-256 của từng event, của bundle, của prompt trong ledger.
2. Đọc document tương ứng trong `ai-investigations-*` — so hai nơi.
3. Khớp thì PASS: nội dung file nhất quán với lúc ghi (file đổi mà chỉ mục không đổi, hoặc ngược lại, đều bắt được).
4. Không khớp thì mã thoát khác 0, chỉ rõ file nào bị đổi.
5. Chế độ replay (báo cáo ghi cục bộ, không có chỉ mục): chỉ kiểm nhất quán nội bộ — mã băm trong file khớp dữ liệu trong file — và in rõ "không có bản ghi đối chiếu ngoài thư mục cục bộ", không giả vờ có.

Giới hạn ghi vào LIMITATIONS.md: kẻ có quyền ghi cả báo cáo lẫn chỉ mục vẫn sửa được cả hai nơi cho khớp nhau; mã băm lưu ở nơi độc lập là rào cản nâng cao (muốn xóa dấu vết phải đụng vào cả hệ SIEM đang có audit log), không phải biện pháp tuyệt đối.

## 7. Scenario Pack — định dạng đầy đủ

Kịch bản là dữ liệu, không phải code: thêm kịch bản mới nghĩa là thêm một file YAML. Mọi gói mở đầu bằng ghi chú triết lý: gói khai báo đúng **một điểm phát hiện** và phần dữ liệu theo dõi được từ điểm đó, không phải bộ bách khoa về một lớp tấn công. Gói hẹp là chủ đích và hẹp một cách công khai: ranh giới giữa hỏi được, không quan sát được, và thuộc gói khác nằm ngay trong khối coverage, người đọc không phải đoán.

Gói hiện hành của v0.2, nguyên văn:

```yaml
# scenarios/office-interpreter-execution-v1.yaml
#
# TRIẾT LÝ GÓI (ghi chú bắt buộc đầu mọi gói): gói này khai báo đúng một
# điểm phát hiện — rule 100110, ứng dụng Office sinh tiến trình thông dịch
# lệnh — và phần dữ liệu theo dõi được từ điểm đó. Ranh giới hỏi được /
# không quan sát được / thuộc gói khác: xem khối coverage.

scenario_id: office-interpreter-execution-v1
name: "Office-spawned interpreter execution on Windows endpoint"
description: >
  Điều tra tình huống ứng dụng Office sinh tiến trình thông dịch lệnh:
  ứng dụng Office (Word, Excel, PowerPoint) sinh tiến trình thông dịch
  lệnh (powershell, cmd, wscript) — điểm phát hiện của custom rule 100110,
  điểm khởi phát đáng chú ý nhất của chuỗi. Từ điểm đó gói truy vết:
  interpreter chạy dòng lệnh gì, thả file payload nào, mở kết nối ra
  ngoài tới đâu. Giai đoạn trước điểm phát hiện (email đưa tài liệu độc
  hại vào máy) không có telemetry trong lab — khai báo khoảng trống
  trong coverage, không giả vờ hỏi được. Giai đoạn sau xa hơn (mã hóa
  tống tiền) thuộc gói kịch bản khác.

entry_alert:
  # Cảnh báo đầu vào: điểm khởi phát đáng chú ý nhất của chuỗi, quan
  # trọng hơn một phát hiện muộn kiểu "mã hóa hàng loạt"
  wazuh_rule_ids: ["100110"]     # custom rule của phòng thí nghiệm:
                                 # Sysmon EID 1, parent là Office app,
                                 # child là powershell/cmd/wscript
  fallback_query:
    rule.groups: ["sysmon"]

correlation:
  lookback_window: 30m
  sources:                             # cảnh báo và sự kiện đọc từ hai
    alerts_index: "wazuh-alerts-*"     # chỉ mục khác nhau; archives
    events_index: "wazuh-archives-*"   # phải bật (doctor kiểm tra)
  budget:                              # ghi đè trần mặc định của ngân sách token
    max_evidence_items: 40
    max_estimated_tokens: 6000
  pivots:
    - type: process_tree
      source: sysmon
      event_id: 1
      key: processguid               # ProcessGuid/ParentProcessGuid;
                                      # không dùng PID/PPID vì Windows
                                      # tái sử dụng PID
    - type: network_connections
      source: sysmon
      event_id: 3
      scope: processes_in_tree
    - type: file_changes
      source: sysmon_eid11            # nguồn là Sysmon EID 11;
      scope: host                     # không dùng Wazuh FIM

attack_simulation:
  # Tái hiện dữ liệu test bằng Atomic Red Team
  atomic_tests:
    - T1204.002   # user execution: malicious file — mở tài liệu payload
    - T1059       # command/script interpreter: powershell thực thi
    - T1071.001   # web protocols: payload gọi ra ngoài
  notes: >
    Ba test độc lập — chúng không tự sinh chuỗi cha con Word rồi
    PowerShell; lab/simulate.sh thêm script mô phỏng thủ công nối chuỗi
    (mở tài liệu bằng Word, từ đó sinh script interpreter). Chạy trên
    Windows VM có Sysmon + Wazuh agent.

hypothesis_checklist:
  # Câu hỏi giả thuyết viết sẵn trong gói: có phiên bản theo git, review
  # được trong pull request, mã băm ghi vào ledger mỗi lần chạy — sai sót
  # của bộ câu hỏi là loại sai sót kiểm toán được. Mỗi câu hỏi là một
  # khẳng định kiểm chứng được, neo evidence_types có thật trong
  # correlation (loader kiểm máy lúc nạp). Danh sách là giới hạn dưới:
  # mô hình được bổ sung giả thuyết ngoài checklist, miễn có trích dẫn.
  tier_a:   # tầng A — đặc thù kịch bản, neo entry rule + chứng cứ khởi điểm
    - id: A1
      question: "Tiến trình thông dịch lệnh được sinh trực tiếp bởi một ứng dụng Office"
      evidence_types: [process_create]
    - id: A2
      question: "Dòng lệnh của interpreter chứa chỉ dấu tải hoặc giải mã payload (encoded command, URL tải, chuỗi base64)"
      evidence_types: [process_create]
  includes:
    # tầng B + C không viết lại trong từng gói — ghép bằng include
    # (gói là dữ liệu; loader merge xong mới kiểm máy)
    - scenarios/_shared/tier-b-execution-chain.yaml
    - scenarios/_shared/tier-c-tactic-sweep.yaml

coverage:
  # Ba danh sách — nguồn dữ liệu cho scope_statement và evidence_state
  # của báo cáo
  can_query:                    # gói hỏi được — neo evidence type có trong correlation
    - "Chuỗi cha con từ ứng dụng Office, tới interpreter, tới tiến trình con (Sysmon EID 1)"
    - "Dòng lệnh đầy đủ của interpreter và tiến trình con (EID 1)"
    - "File được thả xuống máy trong lookback window (EID 11)"
    - "Kết nối ra ngoài của các tiến trình trong cây (EID 3)"
  blind_missing_data:           # khoảng trống đã khai báo — tổ chức thiếu nguồn
    - data_type: dns_query     # chấp nhận được; hiển thị thành chữ trong báo cáo
      note: "không có Sysmon EID 22 trong lab — không thấy interpreter truy vấn domain nào"
      would_enable: "phân biệt C2 qua domain quen hoặc lạ; phát hiện DGA (thuật toán tự sinh domain)"
    - data_type: mail_gateway
      note: "không có telemetry mail/proxy trong lab"
      would_enable: "truy vết người gửi, tệp đính kèm, các nạn nhân khác của cùng chiến dịch"
  out_of_scope:                 # thuộc gói kịch bản khác
    - "mã hóa tống tiền T1486"
    - "brute force dẫn tới lateral movement"

methodology:
  # Khung hướng dẫn trình tự tư duy — mô hình đọc, suy nghĩ và làm theo;
  # mỗi case một phương pháp, không phải few-shot cố định dùng chung mọi gói
  - "Đọc timeline theo thứ tự thời gian trước khi kết luận bất cứ điều gì"
  - "Kiểm cây tiến trình trước: interpreter do tiến trình nào sinh ra, interpreter sinh ra tiến trình con nào"
  - "Trả lời từng câu hỏi checklist bằng evidence — thiếu dữ liệu thì ghi inconclusive kèm lý do, không bù đắp bằng phỏng đoán"
  - "Hypothesis ngoài checklist được đặt khi có điểm bám trong evidence — luôn kèm citation"

playbooks:
  - playbooks/phish-initial-triage.yaml   # playbook triage ca phishing — tên
                                           # file giữ nguyên vì ca lab vẫn là
                                           # phish-case-01
```

**Ba tầng của hypothesis checklist:**

- **Tầng A, đặc thù kịch bản:** viết riêng trong từng gói, gắn với quy tắc phát hiện khởi điểm và chứng cứ khởi điểm (bản thân cảnh báo cùng các sự kiện quanh nó). Câu hỏi tầng A hỏi đúng nội dung điều tra của gói, ví dụ "interpreter có được sinh trực tiếp bởi ứng dụng Office hay không".
- **Tầng B, chuỗi sau điểm phát hiện:** dùng chung mọi gói kịch bản loại thực thi, gắn với các điểm bám truy vết của gói. Viết một lần ở file chung, mọi gói include; câu hỏi nhất quán giữa các gói, không ai tự chế lại mỗi gói một kiểu.
- **Tầng C, rà soát theo chiến thuật ATT&CK sau khi mã độc đã thực thi:** dùng chung mọi gói. Mỗi chiến thuật hoặc có câu hỏi hoặc khai báo khoảng trống dữ liệu kèm lý do. Nhờ luật "hoặc có câu hỏi hoặc khai báo khoảng trống", tiêu chí "đủ theo phạm vi khai báo" là phép đếm máy thực hiện được ngay lúc nạp gói, và người đọc báo cáo hiểu một chiến thuật vắng mặt là vì thiếu dữ liệu đã khai báo, không phải gói quên hỏi.

Hai file chung có dạng như sau (ví dụ minh họa cấu trúc; danh sách chiến thuật đầy đủ của gói thật do quy trình năm bước viết gói quyết định):

```yaml
# scenarios/_shared/tier-b-execution-chain.yaml
# Tầng B — chuỗi sau điểm phát hiện; dùng chung mọi gói loại thực thi; neo pivots.
tier_b:
  - id: B1
    question: "Interpreter tải hoặc thả file payload xuống máy"
    evidence_types: [file_change]
  - id: B2
    question: "Interpreter mở kết nối ra ngoài tới domain hoặc IP của payload"
    evidence_types: [network]
  - id: B3
    question: "Interpreter sinh tiến trình con tiếp theo (chuỗi không dừng ở một bậc)"
    evidence_types: [process_create]
```

```yaml
# scenarios/_shared/tier-c-tactic-sweep.yaml
# Tầng C — rà soát theo tactic ATT&CK sau thực thi; dùng chung mọi gói.
# Mỗi tactic hoặc có câu hỏi hoặc khai báo khoảng trống dữ liệu — không
# có trạng thái thứ ba.
tier_c:
  - tactic: T1087            # Account Discovery
    questions:
      - id: C1
        question: "Xuất hiện lệnh liệt kê tài khoản người dùng sau điểm phát hiện"
        evidence_types: [process_create]
  - tactic: T1003            # OS Credential Dumping
    questions:
      - id: C2
        question: "Dòng lệnh chứa công cụ dump chứng thực (procdump, mimikatz, comsvcs MiniDump)"
        evidence_types: [process_create]
  - tactic: T1041            # Exfiltration Over C2 Channel
    blind: "không có telemetry proxy/DNS — không thể phân biệt C2 thường với exfiltration qua cùng kênh"
```

Vì sao ghép bằng include thay vì viết chép vào từng gói: tầng B và tầng C là tài sản chung của cả họ gói, không phải của riêng gói này. Sửa một câu hỏi tầng B ở file chung là mọi gói cùng nhận sửa; nếu chép tay thì sau vài gói sẽ lệch nhau, và luật kiểm máy không còn phát hiện được "gói này quên cập nhật tầng B".

**Luật kiểm máy lúc nạp gói.** Loader kiểm gói ngay sau khi ghép include, trước khi gói được dùng, theo bốn luật:

1. Mọi câu hỏi (cả ba tầng) khai `evidence_types`: mỗi loại phải là loại dữ liệu mà correlation config của gói sinh ra được. Câu hỏi neo vào loại không tồn tại là từ chối nạp. Đây là chỗ bắt kiểu lỗi "câu hỏi về nguồn dữ liệu ngoài hệ thống" — ví dụ câu hỏi chỉ trả lời được bằng dịch vụ threat intelligence bên ngoài như VirusTotal — ngay từ lúc nạp, không đợi tới báo cáo.
2. Mọi chiến thuật trong tầng C phải hoặc có câu hỏi hoặc có khai báo khoảng trống `blind` kèm lý do. Chiến thuật "lơ lửng" (không câu hỏi, không khai báo khoảng trống) là từ chối nạp.
3. Mọi câu hỏi phải là khẳng định kiểm chứng được, cấu trúc tối thiểu: có `id`, có `question` phát biểu dưới dạng khẳng định chấm được ba trạng thái, có `evidence_types` không rỗng. Câu hỏi mở kiểu "có gì đáng ngờ không?" không được chấp nhận ở bất kỳ tầng nào.
4. Mọi tên playbook trong khối `playbooks` của gói phải trỏ tới file có thật trong thư mục `playbooks/` lúc nạp. Khai file không tồn tại là từ chối nạp.

Vi phạm bất kỳ luật nào là từ chối nạp gói với mã thoát riêng (phân biệt với cả "cảnh báo không khớp gói" lẫn lỗi hệ thống), kèm thông điệp chỉ đúng mục vi phạm. Mục đích: bắt sai của người viết gói từ đầu, không đợi tới báo cáo sai xuất hiện trước người dùng cuối.

**Golden truth tách khỏi đường chạy.** Golden truth không nằm trong gói mà phần runtime đọc; nó sống ở `eval/golden/<scenario_id>.yaml`, chỉ eval harness dùng:

```yaml
# eval/golden/office-interpreter-execution-v1.yaml — chỉ eval harness đọc
golden_truth:
  techniques:
    # Nhãn đã rà theo trang chính thức ATT&CK: kịch bản là người dùng mở
    # tài liệu đính kèm — đúng nhãn là T1566.001 (T1566.002 là link trong
    # email, không phải kịch bản này). Kỹ thuật có observable: false
    # không tính vào technique recall — chỉ được kỳ vọng xuất hiện trong
    # hypotheses / missing_data.
    - {id: T1566.001, observable: false}   # không có telemetry mail/proxy trong lab
    - {id: T1204.002, observable: true}
    - {id: T1059,     observable: true}
    - {id: T1071.001, observable: true}
  iocs:
    - type: domain
      value: "cdn-update.example"    # domain giả lập trong lab
    - type: filename
      value: "invoice.exe"
  expected_facts:
    - "payload được tải bởi tiến trình browser/office"
    - "script interpreter do Office sinh ra để thực thi payload"
    - "kết nối ra ngoài tới domain của payload"
```

Lý do tách: golden_truth nằm trong ScenarioPack nghĩa là bất kỳ code nào nạp gói cũng đọc được đáp án — một đường rò tiềm ẩn vào prompt hoặc whitelist của validator. Tách ra `eval/golden/` thì ranh giới là vật lý: phần runtime không biết file này tồn tại. Validator lấy whitelist từ đề xuất của knowledge retriever; eval đọc file này để chấm điểm.

### Quy trình năm bước viết gói kịch bản mới

Câu hỏi checklist được **dẫn xuất** từ điểm bám dữ liệu, không phải sáng tác. Quy trình dưới đây ép đúng thứ tự đó, tránh tạo ra "câu hỏi sai tầng dữ liệu" (hỏi thứ không nằm trong dữ liệu) hoặc nhãn kỹ thuật ghi theo trí nhớ rồi sai:

1. **Kể lại câu chuyện tấn công theo giai đoạn và chọn đúng một điểm phát hiện.** Xác định entry rule làm điểm neo (gói này: rule 100110). Giai đoạn trước và sau điểm phát hiện ghi rõ ràng: thuộc khoảng trống dữ liệu của coverage, hay thuộc gói khác.
2. **Rà nhãn kỹ thuật theo trang chính thức ATT&CK (attack.mitre.org).** Tên, số hiệu và mô tả phải khớp trang chính thức tại thời điểm viết, không ghi theo trí nhớ — nhãn ghi theo trí nhớ dễ sai, và sai kiểu này chỉ bị phát hiện khi rà lại theo trang chính thức.
3. **Liệt kê các điểm bám truy vết từ correlation config.** Chỉ ghi loại dữ liệu gói thật sự lấy được (process_create, network, file_change...). Đây chính là tập `evidence_types` hợp lệ cho mọi câu hỏi, và là cái loader kiểm máy lúc nạp.
4. **Dẫn xuất câu hỏi từ các điểm bám.** Mỗi câu hỏi là một khẳng định kiểm chứng được neo vào ít nhất một loại bằng chứng có thật; sắp vào đúng tầng: A nếu đặc thù kịch bản (neo quy tắc khởi điểm và chứng cứ khởi điểm), B nếu thuộc chuỗi sau phát hiện (lấy từ file chung), C nếu là rà soát theo chiến thuật (mỗi chiến thuật có câu hỏi hoặc khai báo khoảng trống).
5. **Điền khối coverage và chạy kiểm nạp.** Ba danh sách: hỏi được, không quan sát được, thuộc gói khác; mỗi mục khoảng trống kèm `would_enable` (nếu có nguồn đó thì thấy được gì). Cuối cùng chạy lệnh nạp gói cho máy kiểm; vi phạm thì sửa **gói**, không phải bỏ kiểm.

## 8. Evidence Bundle — định dạng trung gian

Evidence bundle là đầu ra của correlator và là thứ duy nhất mà mô hình nhìn thấy. Correlator làm sạch, khử trùng lặp và cô đọng hàng trăm sự kiện thô thành một gói chứng cứ nhỏ; mô hình chỉ suy luận trên gói này. Bốn lý do của thiết kế: mô hình nhỏ với cửa sổ ngữ cảnh hẹp vẫn chạy được trên phần cứng yếu; bề mặt sinh hallucination thu hẹp; bề mặt prompt injection thu hẹp; chi phí token kiểm soát được khi dùng nhà cung cấp thương mại.

```json
{
  "alert": {"id": "…", "rule": "…", "timestamp": "…", "host": "WS-014", "user": "an.nguyen"},
  "scenario_id": "office-interpreter-execution-v1",
  "evidence": [
    {"evidence_id": "E01", "type": "process_create",
     "timestamp": "…", "summary": "WINWORD.EXE sinh tiến trình powershell.exe với tham số -enc …",
     "raw_ref": {"index": "wazuh-alerts-*", "id": "…"}},
    {"evidence_id": "E07", "type": "network",
     "timestamp": "…", "summary": "powershell.exe kết nối tới cdn-update.example:443",
     "raw_ref": {"index": "…", "id": "…"}}
  ],
  "timeline": ["E03", "E01", "E07", "E12", "E15"],
  "iocs": [{"type": "domain", "value": "cdn-update.example", "first_seen": "E07"}],
  "stats": {"raw_events": 412, "distilled_evidence": 18,
            "per_type_counts": {"process_create": 9, "network": 6, "file_change": 3},
            "dropped_by_budget": {"count": 0, "by_type": {}}}
}
```

Chỉ gói này (không phải 412 sự kiện thô) đi vào prompt.

### Chính sách ngân sách token

Trần cứng mặc định (ghi đè được trong gói kịch bản qua khối `budget`): `max_evidence_items: 40`, `max_estimated_tokens: 6000` (ước lượng khoảng 4 ký tự cho mỗi token trên phần summary).

Khi vượt ngân sách, siết dần theo thứ tự chứ không cắt đột ngột:

1. Siết khung thời gian quanh cảnh báo, giữ phần gần cảnh báo nhất của chuỗi.
2. Bỏ bằng chứng ưu tiên thấp: file_change phụ, kết nối mạng trùng cặp (tiến trình và đích), nhánh lá của cây tiến trình.
3. Không bao giờ cắt: cây tiến trình gốc tới payload, bằng chứng trích IoC, bằng chứng hỗ trợ ATT&CK mapping chính.

Mọi lần bỏ dữ liệu phải được ghi vào `bundle.stats.dropped_by_budget` và hiển thị trong `report.meta.budget`. Báo cáo phải nói rõ nó đã bỏ gì: sự thật có cấu trúc, không giả vờ đủ. Đây là câu trả lời cho câu hỏi "khi cửa sổ ngữ cảnh đầy thì xử lý thế nào".

## 9. Báo cáo điều tra — định dạng đầu ra

Báo cáo là sản phẩm cuối của dây chuyền và là hợp đồng với hai đối tượng: nhà phân tích đọc nó, các công cụ (verify, eval, dashboard) đọc lại nó. Mọi trường dưới đây là hợp đồng đó — đổi tên trường là phá tính tương thích của cả ba công cụ đọc lại.

```json
{
  "schema_version": "0.2.6",
  "alert_id": "…",
  "scenario_id": "office-interpreter-execution-v1",
  "generated_at": "…",
  "model": {"provider": "ollama", "name": "qwen2.5:3b-instruct-q4_K_M"},
  "summary": "…",
  "facts": [
    {"statement": "…", "citations": ["E01", "E07"]}
  ],
  "timeline": [
    {"timestamp": "…", "event": "…", "citations": ["E03"]}
  ],
  "iocs": [{"type": "domain", "value": "…", "citations": ["E07"]}],
  "attack_mapping": [
    {"technique_id": "T1059", "name": "Command and Scripting Interpreter",
     "confidence": "high", "citations": ["E01"]}
  ],
  "checklist_results": [            # trả lời cho câu hỏi gói khai báo sẵn —
                                     # tách khỏi hypotheses ở dưới
    {"question_id": "A1", "tier": "A",
     "question": "Tiến trình thông dịch lệnh được sinh trực tiếp bởi một ứng dụng Office",
     "status": "confirmed", "citations": ["E01"]},
    {"question_id": "B2", "tier": "B",
     "question": "Interpreter mở kết nối ra ngoài tới domain hoặc IP của payload",
     "status": "confirmed", "citations": ["E07"]},
    {"question_id": "C3", "tier": "C",
     "question": "…",
     "status": "inconclusive", "citations": [],
     "reason": "không có DNS query log — móc vào missing_data và evidence_state.declared_blind"}
  ],
  "playbook_results": [              # dấu trạng thái từng bước quy trình —
                                     # playbook là thủ tục nên không mang citation;
                                     # reason bắt buộc khi unanswered hoặc out_of_scope
    {"step": "truy vết người gửi và tệp đính kèm qua mail gateway",
     "status": "out_of_scope",
     "reason": "giai đoạn mail nằm trước điểm phát xuất — không có telemetry mail_gateway trong gói"},
    {"step": "xác nhận tiến trình thông dịch lệnh do ứng dụng Office sinh ra",
     "status": "answered"},
    {"step": "xác định phạm vi lây lan trên các host khác",
     "status": "unanswered",
     "reason": "gói chỉ thu thập trên host phát cảnh báo — không có dữ liệu host khác"},
    {"step": "phân biệt C2 thường với exfiltration qua cùng kênh",
     "status": "unanswered",
     "reason": "thiếu DNS query log — trùng khoảng trống đã khai báo của tầng C"}
  ],
  "hypotheses": [                   # giả thuyết mô hình tự bổ sung ngoài checklist —
                                     # vẫn qua kiểm trích dẫn như facts
    {"statement": "…", "based_on": ["E01"], "confidence": "medium"}
  ],
  "missing_data": ["DNS query log cho cdn-update.example", "…"],
  "scope_statement": "…",           # phát biểu phạm vi lấy trực tiếp từ khối
                                     # coverage của gói — đặt ngay cạnh
                                     # missing_data: hỏi được gì, không quan sát
                                     # được gì, gì thuộc gói khác
  "evidence_state": {               # trạng thái chứng cứ
    "per_type_counts": {"process_create": 9, "network": 6, "file_change": 3},
    "abnormal_absences": [],        # loại lõi gói khai hỏi được mà đếm về 0 —
                                     # mâu thuẫn giữa khai báo và thực tế, ghi
                                     # kèm các khả năng xảy ra để người đọc kiểm
                                     # tra; rỗng = bình thường
    "declared_blind": ["dns_query", "mail_gateway"]   # khoảng trống dữ liệu đã khai
                                                      # báo (chấp nhận được)
  },
  "playbook_provenance": {           # report writer ghi từ đĩa lúc chạy —
                                     # gói đã dùng playbook nào, phiên bản nội dung nào
    "files": [
      {"file": "playbooks/phish-initial-triage.yaml", "sha256": "…"}
    ]
  },
  "recommendations": [
    {"action": "Cô lập host WS-014 (thủ công, bởi analyst)", "priority": "P1"},
    {"action": "Bật Sysmon EID 22 (DNS query) cho host này", "priority": "P2",
     "would_enable": "phân biệt C2 domain quen hoặc lạ, phát hiện DGA — nguồn này đang nằm trong danh sách khoảng trống của khối coverage"},
    {"action": "Quét các host khác cho IoC của ca này (domain cdn-update.example, tệp invoice.exe) để trả lời bước 'xác định phạm vi lây lan' của quy trình triage", "priority": "P1",
     "source": "playbook"}
  ],
  "meta": {
    "mode": "live",                  # "live" | "replay"
    "ledger_file": "<alert_id>.ledger.json",   # nhật ký điều tra đi kèm báo cáo
    "redaction": {"enabled": true, "counts": {"USR": 2, "IP": 1, "PATH": 1}},
                  # chỉ giữ enabled + số đếm; bảng map không nằm trong báo cáo —
                  # ghi ra reports/<alert_id>.redaction-map.json
                  # (chmod 0600, .gitignore), analyst nội bộ tra cứu
    "validation": {"dropped_claims": 2, "unverified_claims": 1},   # sample công khai dùng dữ liệu lab
    "budget": {"applied": true, "dropped_evidence": 5,
               "dropped_types": {"file_change": 4, "network": 1}},
    "latency_ms": 45000,   # số minh họa — mô hình 3B chạy gọn trong 4GB VRAM,
                           # cỡ 45 giây mỗi cảnh báo là bình thường
    "evidence_stats": {"raw_events": 412, "distilled_evidence": 18}
  },
  "evidence_snapshot": {
    "bundle_sha256": "…",
    "events": [
      {"evidence_id": "E01", "sha256": "…", "raw": {"…event JSON đầy đủ…": null}}
    ]
  }
}
```

**Nguyên tắc:** facts, checklist_results và hypotheses là **ba mảng riêng**, không trộn. Facts là dữ kiện về điều đã xảy ra; checklist_results là câu trả lời cho câu hỏi gói khai báo sẵn (ba trạng thái, mục inconclusive nêu lý do, phân biệt "hỏi rồi và dữ liệu nói không" với "không hỏi được"); hypotheses là giả thuyết mô hình tự bổ sung ngoài danh sách câu hỏi (giới hạn dưới, không phải giới hạn trên). Mọi phần tử đều phải có `citations` trỏ về `evidence_id` trong gói chứng cứ; validator loại bỏ phần tử không có citation và đếm vào `meta.validation`. Evidence snapshot là "bộ nhớ tại chỗ": kể cả khi dữ liệu nguồn đã bị retention xóa, người đọc vẫn tái dựng được timeline từ dữ liệu nhúng và kiểm tra mã băm để biết nội dung nhúng còn khớp với mã băm lúc tạo hay không (giới hạn: chống hỏng hóc hoặc sửa vô ý; chống sửa có chủ đích cần mã băm lưu ở nơi độc lập qua lệnh `verify`). Báo cáo còn đi kèm investigation ledger, "bộ nhớ hội thoại": mọi thứ mô hình nhận được và đáp lại đều xem lại được. `export --public` tạo bản đã bỏ giá trị thô để chia sẻ an toàn.

### Investigation ledger (nhật ký điều tra)

Ledger là thuật ngữ kế toán chỉ sổ cái: thanh tra đòi xem sổ cái đầu tiên vì nó cho thấy từng giao dịch đi đâu, khi nào. Ở đây ledger là bản ghi toàn bộ "cuộc hội thoại" giữa công cụ và mô hình trong **một** lần investigate, ghi thành file riêng `reports/<alert_id>.ledger.json` nằm cạnh báo cáo (chỉ dẫn qua `meta.ledger_file`). Nói đúng giới hạn của nó: công cụ ghi **một lần** mỗi lần chạy rồi không bao giờ tự sửa, nhưng đây là file JSON thường, bất kỳ ai có quyền ghi lên đĩa đều sửa được từ bên ngoài. Ledger chống **mất dấu vết** và **nhầm lẫn** (từng bước nằm nguyên vẹn trong một file), không chống thay đổi có chủ đích; tính chất "chỉ ghi thêm, không xóa sửa" (append-only) là cam kết trong **hành vi** của chính công cụ, không phải thuộc tính vật lý của file.

Vì sao cần: evidence snapshot chứng minh mọi kết luận trỏ về dữ liệu đã đóng băng, nhưng prompt gửi gì cho mô hình và mô hình trả lời thô cái gì thì nằm ngoài snapshot — không có ledger thì khâu đó không để lại dấu vết nào. Người hoài nghi về AI sẽ hỏi thẳng vào đó: "validator bắt được hallucination, nhưng làm sao tôi biết model nhận được gì trước khi validator kịp bắt?". Không có ledger, câu trả lời duy nhất là "tin tôi đi"; có ledger, câu trả lời là mở file cho họ xem. Công dụng phụ không kém giá trị: khi ghi chú mô hình gặp kết quả lạ (mô hình này sao trả lời trống?), ledger cho thấy ngay prompt gửi gì, mô hình đáp gì, không phải đoán.

```json
{
  "schema_version": "0.2.6",
  "alert_id": "…",
  "mode": "replay",                  # "live" | "replay" — khớp report.meta.mode
  "pack": {"scenario_id": "office-interpreter-execution-v1",
           "pack_sha256": "…",           # mã băm gói đã nạp (sau khi ghép include)
           "checklist_sha256": "…"},     # bộ câu hỏi nào đã chạy — sai sót của
                                         # checklist là loại sai sót kiểm toán được
  "model": {"provider": "ollama",
            "name": "qwen2.5:3b-instruct-q4_K_M",
            "runtime": "gpu"},   # gpu / partial / cpu / remote / unknown
                                # remote = nhà cung cấp từ xa (Anthropic)
  "prompt": {"system_sha256": "…",    # template có trong repo — mã băm chứng minh
                                        # phiên bản nào được dùng
             "user_sha256": "…",
             "user_text": "…bản ĐÃ QUA REDACTION…"},   # phần chứa evidence — lưu nguyên văn
  "model_raw_output": "…câu trả lời thô nguyên vẹn, chưa parse…",
  "report_draft": {},                 # report JSON ngay sau parse, TRƯỚC khi validator can thiệp
  "validator_actions": [
    {"action": "dropped", "where": "facts[3]",
     "reason": "citation E99 không tồn tại trong bundle"}
  ],
  "usage": {"prompt_tokens": 4120, "completion_tokens": 580},
  "attempts": {"count": 2,           # tổng số lần gọi mô hình (1 + tối đa 2 lần thử lại)
               "errors": ["lần 1: thiếu trường citations ở facts[2] — đã gửi phản hồi lỗi yêu cầu bổ sung"]},
  "timings_ms": {"correlator": 2100, "retrieval": 350, "prompt_build": 40,
                 "llm_call": 42000, "validation": 90, "report_write": 180}
}
```

Ba nguyên tắc của ledger:

- **Không tạo kẽ hở mới**: prompt lưu trong ledger luôn là bản **đã qua che dữ liệu** (khi redaction bật); giá trị gốc chưa từng rời bộ nhớ nội bộ qua prompt thì cũng không rời qua ledger.
- **Ghi cả thứ dễ bị đọc sai**: trường `runtime` (gpu, partial, cpu, remote, hoặc unknown) nói mô hình đang chạy thực sự ở đâu. Máy lab T500 với 4GB VRAM chạy mô hình 3B là "gpu" (chạy gọn trong card, không offload); dùng đường Claude thì là "remote": mô hình chạy trên hạ tầng Anthropic, công cụ không đo được bên trong đó nên chỉ ghi đúng những gì đo được (latency, tokens lấy từ usage). Không ghi trường này thì ai đọc số latency sẽ kết luận sai "công cụ chậm" thay vì hiểu đúng bối cảnh. Không xác định được thì ghi "unknown", không bịa.
- **Cùng định dạng cho cả hai chế độ trực tiếp lẫn replay**: ledger là một phần của cam kết "báo cáo tạo giống hệt nhau giữa hai chế độ"; smoke cũng kiểm tra sự tồn tại của ledger và mã băm prompt khớp.

## 10. Eval harness và ghi chú mô hình

### Golden dataset — đáp án tách khỏi đường chạy

Golden truth sống ở `eval/golden/<scenario_id>.yaml`, tách khỏi gói kịch bản mà phần runtime đọc. Quy trình tạo dữ liệu: chạy `lab/simulate.sh` (Atomic Red Team) tạo dữ liệu, công cụ điều tra cảnh báo phát sinh, rồi eval so kết quả với golden file. Phần runtime không bao giờ đọc đáp án: không có đường rò vào prompt, whitelist của validator, hay bất kỳ chỗ nào trên đường chạy.

Golden dataset của v0.2 có **đúng một case** (`phish-case-01`) vì ưu tiên của v0.2 là chứng minh toàn mạch chạy được. Harness thiết kế nhận **nhiều** case: đầu vào eval là danh sách cặp (bản xuất NDJSON, golden file); thêm case sau này chỉ là thêm dữ liệu, không sửa code. Hạn chế cỡ mẫu n bằng 1 được ghi thẳng vào LIMITATIONS.md và MODEL_SELECTION.md.

### Các chỉ số đo

| Chỉ số | Cách đo |
|---|---|
| JSON/schema validity | output parse được và khớp schema, tính sau tối đa 2 lần thử lại kèm phản hồi lỗi có cấu trúc |
| Technique precision và recall | so với `golden_truth.techniques` **có `observable: true`**; technique không observable (ví dụ T1566.001: không có telemetry mail/proxy trong lab) không tính vào recall — đó là giới hạn dữ liệu, không phải lỗi mô hình |
| IoC precision | IoC trích đúng chia cho IoC trong output (không bịa) |
| Citation validity (trước validator) | phần trăm phần tử có trích dẫn hợp lệ, tính trên `report_draft` trong ledger; phải đo trước validator vì sau validator tỉ lệ này luôn 100% — validator đã ép hoặc xóa hết phần tử lỗi |
| Hallucination count | số kết luận bị validator loại |
| Latency và tốc độ sinh token | thời gian end-to-end trên máy lab; token mỗi giây tính từ `usage` cộng `timings_ms` trong ledger |

### Ghi chú mô hình: một mô hình duy nhất

Ghi chú này tồn tại để trả lời câu hỏi "vì sao công cụ dùng mô hình này", không phải benchmark khoa học: cỡ mẫu nhỏ (một case) và phần cứng đặc thù đến mức kết quả không tổng quát hóa ra máy khác; MODEL_SELECTION.md ghi rõ điều đó.

- **Mô hình duy nhất: qwen2.5:3b-instruct (Q4_K_M)**, khoảng 1,9GB, chạy gọn trong 4GB VRAM của card T500, không phải trút bớt trọng số sang CPU (offload).
- Phát hành v0.2 không đặt điều kiện đạt ngưỡng chất lượng mô hình. Mô hình yếu ở điểm nào thì ghi thẳng vào MODEL_SELECTION.md "yếu ở điểm X, giảm thiểu bằng Y": sự trung thực về giới hạn là một phần của sản phẩm, che giấu là điểm trừ.
- **Vì sao không chọn mô hình lớn hơn**, câu trả lời chuẩn bị sẵn trong tài liệu cho bất kỳ ai hỏi: card 4GB không chứa nổi mô hình 7B dạng nén Q4 (khoảng 4,7GB), phải offload một phần sang CPU; phần chạy trên CPU chỉ đạt khoảng 3 đến 6 token mỗi giây, nên một báo cáo cỡ 600 token tốn 100 đến 200 giây riêng cuộc gọi mô hình — quá chậm cho demo. Khó khăn phần cứng là thực tế; chọn đúng một mô hình vừa máy và ghi trung thực số đo là quyết đoán hơn kéo thêm mô hình để đo đạc.
- **Chạy `--replay` vài lần** trên cùng gói chứng cứ đã đóng băng (từ bản xuất NDJSON của lần chạy lab đầu): mục đích là xác nhận dây chuyền **ổn định** giữa các lần chạy trên cùng đầu vào.
- Ghi vào MODEL_SELECTION.md mỗi lần chạy: latency, tỉ lệ JSON hợp lệ, tỉ lệ citation hợp lệ **trước validator** (lấy từ `report_draft` trong ledger), số kết luận bị validator loại, token tiêu tốn.
- **Tham chiếu từ xa (tùy chọn, chỉ khi có ANTHROPIC_API_KEY)**: một lần chạy `--provider anthropic` trên cùng đầu vào, ghi chênh lệch chất lượng, latency, chi phí so với đường cục bộ. Đây không phải benchmark: chỉ để MODEL_SELECTION.md trả lời được "chạy mô hình tại chỗ đánh đổi gì so với API thương mại".
- Kỳ vọng phần cứng (T500 4GB VRAM, 16GB RAM, i5-1135G7), ghi ra để đối chiếu: mô hình 3B Q4 chạy gọn trong card thì vài chục giây cho một báo cáo là bình thường; số đo thật mới là chuẩn.

## 11. Nguyên tắc an toàn.

Mười nguyên tắc dưới đây ràng buộc mọi thành phần. Mỗi nguyên tắc là hành vi kiểm được bằng unit test hoặc bằng lệnh doctor, không phải lời hứa trong tài liệu.

1. **Chỉ đọc** dữ liệu cảnh báo và log gốc từ SIEM.
2. **Chỉ ghi** vào chỉ mục riêng `ai-investigations-*` do công cụ sở hữu. Credential của công cụ được cấp vai trò **tối thiểu**: đọc `wazuh-alerts-*`, đọc `wazuh-archives-*`, ghi `ai-investigations-*`, không thêm quyền nào khác. Vai trò chuẩn nằm trong `docs/deployment/permissions.md` cùng `lab/wazuh/roles/`; lệnh `doctor` kiểm đúng vai trò này; quyền rộng hơn mức tối thiểu là cảnh báo.
3. **Không thực thi** hành động phản ứng. Khuyến nghị trong báo cáo dành cho con người quyết định.
4. **Nội dung log là dữ liệu, không phải chỉ thị.** Bằng chứng đặt trong khối phân tách rõ ràng trong prompt; system prompt khai báo bằng chứng là không tin cậy; validator loại output chứa chỉ thị lạ.
5. **Phân biệt dữ kiện và giả thuyết ở cấu trúc dữ liệu**, không chỉ ở lời văn. Ba lớp tách bạch: facts (dữ kiện), checklist_results (câu trả lời cho câu hỏi gói khai báo sẵn, ba trạng thái confirmed, refuted, inconclusive), hypotheses (giả thuyết mô hình tự bổ sung) — ba mảng riêng trong báo cáo, không trộn.
6. **Mọi kết luận quan trọng truy nguyên được** về bằng chứng nguồn (`raw_ref` gồm index và document id), và bằng chứng đã trích dẫn được đóng băng ngay trong báo cáo (bản chụp kèm SHA-256): kể cả khi dữ liệu nguồn bị xóa theo retention, báo cáo vẫn tái dựng được timeline và tự kiểm tra nhất quán nội tại (mã băm khớp dữ liệu là chưa hỏng hóc hoặc sửa vô ý; chống sửa có chủ đích cần mã băm lưu ngoài file, lệnh `verify` đối chiếu chỉ mục). Toàn bộ "cuộc hội thoại" với mô hình nằm trong investigation ledger: prompt đã che dữ liệu, câu trả lời thô, từng hành động của validator — chi tiết đến mức người hoài nghi nhất cũng tự xem lại được từng bước. Trong phạm vi này, "kiểm chứng được" mang nghĩa truy nguyên được, không đồng nghĩa bảo đảm đúng sự thật.
7. **Không gửi dữ liệu ra ngoài** khi chạy chế độ cục bộ. Khi cấu hình nhà cung cấp từ xa (API thương mại, ví dụ Anthropic Claude): che dữ liệu **bắt buộc bật**, không có cờ tắt — username (kể cả trong đường dẫn `C:\Users\<tên>\`), IP nội bộ, email được thay bằng placeholder trước khi rời hạ tầng. Phạm vi che ghi rõ trong tài liệu. Tên máy (hostname) không che mặc định vì host là mảnh ghép quan trọng của phân tích; che qua cờ `--redact-hostname` khi cần chia sẻ rộng. Bảng đối chiếu đặt **ngoài** báo cáo (`reports/<alert_id>.redaction-map.json`, chmod 0600): gửi báo cáo cho người ngoài không kèm chìa khóa giải mã lẫn dữ liệu gốc, qua `export --public`.
8. **Nguồn mô hình tin cậy**: chỉ tải mô hình từ Hugging Face chính thức (`huggingface.co`) hoặc Ollama registry; ghi checksum và nguồn trong tài liệu. Không tải từ mirror lạ.
9. **Mọi đầu ra hiển thị coi bằng chứng là dữ liệu do kẻ tấn công kiểm soát**: báo cáo HTML và Markdown render bằng Jinja2 với autoescape bật mặc định (`select_autoescape`), CSP meta trong template HTML, unit test với payload injection cố định; các trường báo cáo hiển thị trong Wazuh Dashboard cũng phải giả định chứa HTML độc hại. Công cụ bảo mật không được tự trở thành attack vector.
10. **Chính sách an toàn hóa thành hành vi trong code, không dừng ở lời hứa trong tài liệu.** Prompt guard (cơ chế bảo vệ prompt): đầu ra của prompt builder được kiểm tra trước khi gửi — không chứa sự kiện thô (kiến trúc đã đảm bảo bằng việc cô đọng bằng chứng, nhưng viết thành unit test để biến đảm bảo kiến trúc thành lời cam kết kiểm được), không chứa chuỗi giống key hoặc password theo pattern cố định; vi phạm là từ chối gửi, không phải che sau; hoạt động với **mọi** nhà cung cấp (Ollama lẫn Anthropic). Che dữ liệu với nhà cung cấp từ xa là **bắt buộc bật** — cấu hình không có cờ tắt; đường Ollama cục bộ mặc định bật và tắt được bằng cấu hình. SECURITY.md phải ghi thẳng điều cần cân nhắc khi tắt trên đường cục bộ (ledger và báo cáo chứa nội dung nhạy cảm chưa che) thay vì để người dùng tự truy dò; công cụ không giả vờ có rào cứng mà không có.

## 12. Tech stack

- Python 3.12 · typer (CLI) · pydantic (schema và config) · PyYAML
- opensearch-py (bộ kết nối Wazuh) · requests
- Ollama (nhà cung cấp cục bộ) · anthropic SDK (nhà cung cấp Claude, từ xa) · Jinja2 (báo cáo HTML và Markdown)
- Atomic Red Team và Invoke-AtomicRedTeam (mô phỏng lab) · Sysmon cùng Wazuh agent trên Windows VM
- pytest (test) · ruff (lint)

## 13. Cấu trúc repo

Cây dưới đây là toàn bộ kho mã v0.2; ghi chú cạnh từng file nêu vai trò của nó.

```
soc-investigator/
├── README.md                    # tiếng Anh: giới thiệu, quickstart, demo, kiến trúc
├── LICENSE                      # Apache-2.0
├── .gitignore                   # bắt buộc chứa .env và reports/ (báo cáo, ledger, redaction map) — doctor kiểm và cảnh báo
├── NOTICE.md                    # provenance: wazuh-docker (GPLv2) + MITRE ATT&CK (điều khoản yêu cầu giữ thông báo bản quyền khi phân phối dữ liệu)
├── docs/
│   ├── ARCHITECTURE.md          # sơ đồ + quyết định thiết kế + lý do
│   ├── MODEL_SELECTION.md       # ghi chú một mô hình duy nhất: lý do phần cứng + số đo thật + (tùy chọn) một lần chạy tham chiếu Claude
│   ├── SECURITY.md              # nguyên tắc an toàn bằng tiếng Anh; điều cần cân nhắc khi tắt redaction (chỉ với Ollama cục bộ) ghi thẳng
│   ├── LIMITATIONS.md           # giới hạn đã biết, viết thẳng thắn
│   └── deployment/
│       ├── wazuh-ollama.md      # recipe kịch bản B — chính là lab, bản triển khai tham chiếu
│       └── permissions.md       # vai trò tối thiểu cho tài khoản tool: đọc wazuh-alerts-*/wazuh-archives-*, ghi ai-investigations-*
├── soc_investigator/
│   ├── cli.py                   # install, config, doctor, investigate (--provider ollama|anthropic), smoke, verify, eval, export (--public)
│   ├── doctor.py                # bảy nhóm kiểm tra: connectivity, vai trò tối thiểu, index discovery, archives + WARN DestinationHostname, truy vấn mẫu, provider, sinh .env + kiểm an toàn .env
│   ├── smoke.py                 # smoke hai tầng: mặc định FakeProvider (vài giây); --live-model gọi nhà cung cấp thật
│   ├── connectors/
│   │   ├── base.py              # interface SiemConnector
│   │   ├── wazuh.py             # bộ kết nối Wazuh, chạy trực tiếp
│   │   └── file.py              # FileConnector — replay NDJSON
│   ├── providers/
│   │   ├── base.py              # interface LlmProvider (JSON khớp schema hoặc SchemaError; thử lại tối đa 2 kèm phản hồi lỗi có cấu trúc)
│   │   ├── ollama.py            # Ollama, mặc định
│   │   ├── anthropic.py         # Claude API (redaction bắt buộc bật)
│   │   └── fake.py              # FakeProvider — đọc câu trả lời ghi sẵn trong lab-data/, cho smoke tầng nhanh và CI không GPU
│   ├── correlator.py            # process tree theo ProcessGuid (không PID/PPID) — unit test ca PID tái sử dụng
│   ├── knowledge/               # nạp ATT&CK subset + playbook; tra cứu theo technique id và từ khóa
│   ├── prompts/                 # khuôn mẫu prompt: tách phần system và phần evidence
│   ├── redact.py                # redact() + bảng mapping placeholder; che cả C:\Users\<tên>\ trong path; --redact-hostname là cờ riêng; map ghi file riêng 0600
│   ├── validator.py             # năm phép kiểm: schema, whitelist ATT&CK, trích dẫn, checklist, đối chiếu nội dung mức 1
│   └── report/                  # render JSON → index (document kèm mã băm làm mốc đối chiếu) / MD / HTML (+ export --public) + ledger + redaction map
├── scenarios/
│   ├── office-interpreter-execution-v1.yaml   # không chứa golden_truth (đáp án tách ra eval/golden/); chứa hypothesis checklist ba tầng + coverage + methodology; loader kiểm máy lúc nạp
│   └── _shared/                 # tầng B (chuỗi sau điểm phát hiện) + tầng C (rà soát theo tactic), ghép vào gói qua include
├── playbooks/
├── lab/
│   ├── simulate.sh              # Atomic Red Team + script nối chuỗi cha-con (tài liệu → script interpreter)
│   ├── versions.yml             # ghim phiên bản cho cả lab: tag Wazuh compose (nhánh stable), Sysmon, Ollama, digest model, tên model Anthropic khi dùng đường Claude
│   └── wazuh/                   # custom rule 100110 (Office sinh script interpreter), docker-compose lab (TỰ VIẾT — không copy compose wazuh-docker GPLv2; tham khảo thì viết lại + ghi công NOTICE.md), config bật archives, Sysmon config ghim từ 15.0 kèm filter EID 22
│       └── roles/               # manifest vai trò tối thiểu cho tài khoản tool (đọc alerts/archives, ghi ai-investigations-*)
├── lab-data/
│   ├── sample-mini.ndjson       # tự dựng thủ công ~100 events, kèm một ca PID tái sử dụng cho unit test cây tiến trình
│   ├── phish-case-01.ndjson     # dump từ lần chạy lab đầu — đầu vào cho replay và eval
│   └── smoke-model-answer.json  # câu trả lời mô hình ghi sẵn (chụp từ ledger một lần chạy thật) — đầu vào FakeProvider
├── dashboards/
│   └── ai-investigations.ndjson # import vào Wazuh Dashboard
├── eval/
│   ├── run_eval.py              # input: danh sách (NDJSON dump + golden file) — thêm case = thêm dữ liệu, không sửa code
│   └── golden/
│       └── office-interpreter-execution-v1.yaml   # đáp án — eval đọc, runtime không bao giờ đọc; nhãn T1566.001 đã rà theo trang chính thức ATT&CK
├── tests/                       # unit test: redact mapping (kể cả C:\Users\<tên>\), XSS payload injection, prompt guard (không log thô/secret trong prompt), PID tái sử dụng, verify (phát hiện sửa file), adapter Anthropic (parse JSON + retry tối đa 2), pack loader validation (pack xấu — kể cả khai playbook thiếu file — bị từ chối nạp với exit code riêng)
└── docker-compose.yml           # Wazuh + Ollama (lab all-in-one)
```

## 14. Rủi ro và giảm thiểu

| Rủi ro | Giảm thiểu |
|---|---|
| **R1**: mô hình cục bộ lớp 3B có năng lực suy luận yếu hơn lớp 7B (đánh đổi để chạy gọn trong 4GB VRAM), output kém, latency vượt kỳ vọng | Correlator đảm nhận phần việc nặng; prompt nhỏ, structured. Lối thoát: demo bằng `--provider anthropic` (Claude API — che dữ liệu bắt buộc bật, chi phí tính từ usage trong ledger). Ghi số đo thật và giới hạn vào MODEL_SELECTION.md cùng LIMITATIONS.md; phát hành không chặn trên ngưỡng chất lượng mô hình |
| **R2**: Wazuh không có rule sẵn cho "Office sinh script interpreter" (điểm phát hiện của gói demo trong phòng thí nghiệm) | Custom rule 100110 trong `lab/wazuh/`: match Sysmon EID 1, parent Image là Office app, child là script interpreter |
| **R3**: ba Atomic test độc lập không tự sinh chuỗi cha con Word rồi PowerShell | `lab/simulate.sh` thêm script mô phỏng thủ công nối chuỗi (mở tài liệu bằng Word thật, từ đó sinh script interpreter) |
| **R4**: scope creep (muốn thêm SIEM, model, kịch bản) | Danh sách "Ngoài phạm vi" chốt ranh giới; mọi ý tưởng mới ghi vào sổ quyết định `soc-investigator-decision-slips.md`, không làm trong v0.2 |
| **R5**: demo trực tiếp hỏng vào lúc cần trình bày | Video demo quay sẵn, báo cáo mẫu export sẵn, chế độ `--replay` từ NDJSON trong repo (không phụ thuộc hạ tầng live) |
| **R6**: token budget cắt mất bằng chứng quan trọng | Degradation có thứ tự (giữ process tree gốc, IoC, ATT&CK chính); mọi lần bỏ ghi vào `report.meta.budget`; LIMITATIONS.md nêu policy |
| **R7**: bật archives làm phình dung lượng ở môi trường thật | Tài liệu deployment cảnh báo rõ: archives là yêu cầu lab và demo; môi trường thật cần chính sách retention riêng của bộ phận an toàn thông tin |
| **R8**: bốn lỗi telemetry câm lặng: (1) Sysmon dưới 15.0 không filter EID 22 gây tràn log; (2) trường `DestinationHostname` chưa decode khiến query theo domain trả rỗng mà không báo lỗi; (3) Sysmon EID 11 ghi nhiều bản ghi cho cùng một file khiến timeline lặp đôi; (4) kết quả bị cắt qua `max_result_window` | Ghim Sysmon từ 15.0 trong compose; kiểm DestinationHostname có giá trị trước khi chốt dump; khử trùng lặp file change theo khóa host cộng đường dẫn cộng mtime; phân trang `search_after`; doctor WARN DestinationHostname |
| **R9**: mọi việc dồn vào lúc dựng lab sống, lab trễ kéo trượt cả dây chuyền phía sau | Chia hai pha độc lập: dựng đường replay trước (khung repo, FileConnector, NDJSON tự dựng không cần lab), dựng lab thật sau; khối điều tra chỉ cần đường replay xong là tiến hành được, lab trễ không chặn dây chuyền |
| **R10**: copy text cấu hình từ wazuh-docker (GPLv2) làm mất tính permissive của repo Apache-2.0 | Quy tắc không-copy: tự viết compose từ image chính thức Docker Hub; tham khảo thì viết lại và ghi công NOTICE.md; file copy trực tiếp bắt buộc giữ nguyên header GPLv2 |
| **R11**: "thành công giả": dây chuyền chạy xong, báo cáo sinh ra, nhưng bên trong rỗng (ví dụ validator vì một lỗi nhỏ loại bỏ toàn bộ facts) và không ai phát hiện cho tới khi demo bị chất vấn | Lệnh `smoke` chạy nguyên dây chuyền rồi tự đối chứng từng khâu: báo cáo khớp schema, 100% citation, mã băm snapshot khớp, ledger tồn tại; dòng FAIL chỉ đúng chỗ đứt, mã thoát khác 0; CI chạy mỗi commit |
| **R12**: Wazuh (khuyến nghị 4 vCPU + 8 GiB cho 1 đến 25 agent) cộng Windows VM khoảng 4 GiB cộng Ollama cùng lúc vượt RAM laptop 16 GB, máy treo giữa chừng, hỏng cả thu thập lẫn phân tích | Kế hoạch hai pha (chi tiết ở file `soc-investigator-deliverables-plan.md`): Pha A thu thập (Wazuh và VM bật, Ollama tắt) rồi dump NDJSON; Pha B phân tích (tắt cả hai, bật Ollama) rồi replay; cổng quyết định cuối cũng theo đó: demo chạy replay trực tiếp kèm video lần chạy live |
| **R13**: CI mỗi commit gọi model thật: runner GitHub miễn phí không GPU, mỗi lần tải model nhiều GB, output model không ổn định khiến smoke dao động thất thường, người mới không bao giờ thấy PASS | Smoke hai tầng: mặc định FakeProvider đọc câu trả lời ghi sẵn, kiểm schema, citation, mã băm, ledger trong vài giây, không cần model; CI chỉ chạy tầng nhanh; `--live-model` chạy tay trước release |
| **R14**: vận hành mỏng: tài khoản tool quyền rộng hơn cần thiết; phiên bản lab trôi dạt không kiểm soát (tài liệu Wazuh 5.0 đang rc/beta, dựng lab trên nền đó là tự đặt rủi ro); `.env` chứa mật khẩu dạng văn bản thô | `docs/deployment/permissions.md` cùng `lab/wazuh/roles/` định nghĩa vai trò tối thiểu (đọc alerts và archives, ghi ai-investigations-*), doctor kiểm đúng vai trò; `lab/versions.yml` ghim tag Wazuh (nhánh stable, không 5.0-rc/beta), Sysmon, Ollama, digest model; doctor WARN khi `.env` đọc rộng hoặc chưa trong `.gitignore` |
| **R15**: dùng Claude API đưa dữ liệu rời hạ tầng: dữ liệu nhạy cảm nằm ngoài danh sách che, dẫn tới rò lên dịch vụ ngoài | Redaction **bắt buộc bật** với provider từ xa — cấu hình không có cờ tắt; prompt guard vẫn chặn chuỗi giống key hoặc password; danh sách che (username kể cả trong path, IP nội bộ, email) có unit test; usage, model, runtime ghi trong ledger để kiểm toán lại từng lần chạy |
| **R16**: pack viết sai tầng dữ liệu: nhãn technique không khớp trang chính thức ATT&CK, câu hỏi hỏi thứ không nằm trong dữ liệu (kiểu "câu hỏi VirusTotal"), tactic sweep thiếu cả câu hỏi lẫn khai báo khoảng trống; sai sót lọt tới báo cáo trước mắt người dùng cuối | Luật kiểm máy lúc nạp pack: câu hỏi neo evidence type phải có trong correlation, tactic phải có câu hỏi hoặc khai báo khoảng trống, vi phạm là từ chối nạp với mã thoát riêng; quy trình năm bước viết pack gồm bước rà nhãn theo attack.mitre.org và bước **dẫn xuất** câu hỏi từ pivots thay vì sáng tác; luật kiểm thứ tư chặn gói khai playbook mà file không tồn tại ngay tại cửa nạp |
| **R17**: báo cáo trên gói chứng cứ lỗi thu thập (ví dụ xuất dump sai khoảng thời gian) dễ bị đọc như kết luận "máy không có dấu hiệu bất thường": người đọc tưởng mọi thứ đã được kiểm tra đầy đủ | Tool KHÔNG chặn vì thiếu dữ liệu (RQ4: nhiều tổ chức không thể có đủ nguồn), nhưng evidence_state trong báo cáo đối chiếu phần pack khai hỏi được với đếm thực tế: loại lõi có 0 sự kiện được ghi "thiếu vắng dữ liệu bất thường" — mâu thuẫn giữa khai báo và đếm, ghi kèm các khả năng xảy ra (ví dụ xuất dump sai khoảng thời gian) để người đọc kiểm tra — cùng khuyến nghị thu thập kèm would_enable; người đọc tự thấy giới hạn, không bị báo cáo sạch giả |
