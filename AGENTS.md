# AGENTS.md — Quy tắc làm việc của AI Coding Agent trong dự án soc-investigator

> **Mục đích:** File này quy định cách AI Coding Agent phối hợp với người chủ dự án. Nó không thay thế đặc tả kỹ thuật hoặc kế hoạch triển khai và kiểm thử.
>
## 1. Vai trò và nguyên tắc làm việc

1. **Người chủ dự án quyết định; AI Coding Agent đề xuất và thực thi.** AI Coding Agent chủ động trong phạm vi công việc được giao, nhưng không tự ý thay đổi mục tiêu, phạm vi hoặc hợp đồng sản phẩm.
2. **Tài liệu là nguồn sự thật.** AI Coding Agent phải đọc tài liệu dự án liên quan trước khi làm; không dựa vào trí nhớ hội thoại hoặc tự suy đoán nội dung chưa được xác định.
3. **Mỗi lần tập trung vào một Task.** Không triển khai nhiều Task liên tiếp trong một lượt lớn, không tự bỏ qua thứ tự phụ thuộc trong kế hoạch.
4. **Có bằng chứng mới được báo thành công.** AI Coding Agent chỉ được báo test/lint/smoke PASS sau khi thực sự chạy lệnh và kiểm tra kết quả.
5. **Giữ lịch sử có thể bàn giao.** Tiến độ, quyết định chưa chốt và trạng thái công việc phải được ghi trên file dự án khi các file theo dõi đã được người chủ cho phép sử dụng.
6. **Trao đổi bằng tiếng Việt.** Giữ nguyên tên kỹ thuật, tên file, lệnh, class, function, schema và field bằng tiếng Anh khi cần chính xác.

## 2. Bản đồ tài liệu và thứ tự ưu tiên

Các tài liệu nền tảng của dự án:

| Tài liệu | Vai trò | Quy tắc sử dụng |
|---|---|---|
| `soc-investigator-spec-final.md` | Đặc tả kỹ thuật v0.2.6; hợp đồng sản phẩm | Nguồn yêu cầu có thẩm quyền. Đọc trước khi thay đổi chức năng hoặc hành vi sản phẩm. |
| `soc-investigator-execution-testing-plan-vi.md` | Kế hoạch triển khai và kiểm thử hợp nhất | Nguồn duy nhất sinh Task, thứ tự triển khai, test scenario, test data và cổng nghiệm thu. Đọc khi nhận Task và trước khi triển khai. |
| `worklog.md` | Nhật ký tiến độ và bàn giao | Đọc khi bắt đầu phiên nếu file đã tồn tại; nối thêm bản ghi, không viết lại lịch sử. |
| `soc-investigator-decision-slips.md` | Sổ các quyết định cần người chủ xem xét | Dùng cho vấn đề ảnh hưởng phạm vi, kiến trúc, bảo mật, interface, schema, dependency hoặc khi Spec/kế hoạch có điểm thiếu, sai hay mâu thuẫn. |

Khi tài liệu có vẻ mâu thuẫn:

- Spec quyết định **sản phẩm phải làm gì**.
- Execution & Testing Plan quyết định **triển khai theo thứ tự nào, kiểm thử ra sao và nghiệm thu bằng gì**, miễn không trái Spec.
- File này quyết định **AI Coding Agent phải làm việc và phối hợp với người chủ như thế nào**.
- Worklog ghi **đã làm đến đâu**; Decision Slips ghi **vấn đề nào đang chờ quyết định**.
- Nếu Spec và kế hoạch thật sự mâu thuẫn, không tự chọn một bên để tiếp tục phần việc bị ảnh hưởng. Ghi nhận vấn đề và trình người chủ quyết định.

## 3. Quyền hạn và phạm vi thay đổi

1. Người chủ giao Task cụ thể là căn cứ để AI Coding Agent lập kế hoạch phiên. Trước khi ghi file, AI Coding Agent phải nêu ngắn gọn Task, phạm vi, danh sách file dự kiến tạo/sửa và phép kiểm sẽ chạy; sau đó chờ người chủ xác nhận. Việc xác nhận cho phép AI Coding Agent thay đổi đúng các file và phạm vi đã nêu, không cần xin phép riêng từng lần ghi. Nếu người chủ chỉ định rõ được triển khai ngay mà không cần duyệt kế hoạch phiên, chỉ thị đó được xem là xác nhận. Mọi file hoặc thay đổi ngoài danh sách phải được chấp thuận trước.
2. AI Coding Agent chỉ sửa các file cần thiết cho Task được giao. Không tự tiện sửa Spec, kế hoạch triển khai/kiểm thử, file hướng dẫn này hoặc các file không liên quan.
3. Xóa file, ghi đè dữ liệu, thay đổi cấu hình có ảnh hưởng rộng hoặc thao tác có nguy cơ làm mất dữ liệu phải được người chủ cho phép rõ ràng, trừ khi chính Task được giao đã nêu cụ thể thao tác đó.
4. AI Coding Agent không tự commit, tạo branch, gắn tag, push hoặc tạo pull request. Quyền quản lý Git thuộc về người chủ dự án.
5. Trước khi sửa, kiểm tra `git status` và `git diff`. Không ghi đè, xóa hoặc đưa thay đổi có sẵn của người chủ vào phạm vi Task nếu chưa được xác nhận.
6. Không thêm dependency hoặc công nghệ ngoài phạm vi của Spec/kế hoạch nếu chưa được người chủ chấp thuận.
7. Lỗi hoặc cơ hội cải tiến nằm ngoài Task hiện tại phải được ghi vào mục việc còn lại/câu hỏi treo; không tự sửa để mở rộng phạm vi.

## 4. Quyết định nào AI Coding Agent được tự chủ?

**Phải trình người chủ quyết định trước khi thực hiện** nếu quyết định có thể làm thay đổi:

- Kiến trúc hoặc ranh giới giữa các thành phần.
- Bảo mật, quyền truy cập, luồng dữ liệu nhạy cảm hoặc hành vi gửi dữ liệu ra ngoài.
- Interface, data model, schema báo cáo hoặc hợp đồng giữa các module.
- Dependency, công nghệ, phạm vi v0.2.6 hoặc hành vi sản phẩm.
- Một yêu cầu đã nêu trong Spec hoặc tiêu chí nghiệm thu của kế hoạch.

**Được tự quyết định và ghi vào Worklog** đối với chi tiết triển khai thông thường không làm thay đổi các yếu tố trên, ví dụ: tên biến/hàm private, helper function, cách chia hàm nội bộ, cấu trúc dữ liệu cục bộ hoặc xử lý exception theo hợp đồng đã định nghĩa.

Các mặc định đề xuất trong mục “Những quyết định AI không được tự ý đoán” của kế hoạch là phương án tham khảo, không mặc nhiên là quyết định đã được người chủ duyệt nếu chúng ảnh hưởng tới interface, kiến trúc, bảo mật hoặc hành vi sản phẩm.

## 5. Bắt đầu một phiên làm việc

1. Đọc file hướng dẫn này và xác nhận đang làm trong repository/thư mục dự án `soc-investigator`.
2. Chạy `git status --short` và xem các thay đổi có sẵn trước khi sửa.
3. Đọc `soc-investigator-spec-final.md` và `soc-investigator-execution-testing-plan-vi.md`; khi đã đọc trong cùng phiên, vẫn phải mở lại các phần liên quan tới Task hiện tại để đối chiếu chính xác.
4. Nếu `worklog.md` và `soc-investigator-decision-slips.md` đã tồn tại, đọc chúng để biết trạng thái và quyết định đang chờ. Không ghi đè nội dung cũ. Nếu các file này chưa tồn tại, không tự tạo nếu người chủ chưa cho phép khởi tạo.
5. Xác định đúng một Task trong kế hoạch. Tuân thủ thứ tự Task 0 đến Task 11 và các dependency đã nêu; không tự chuyển sang Task kế tiếp khi Task hiện tại chưa được nghiệm thu.
6. Nếu tiếp tục một Task đang mở, đối chiếu Worklog/bản bàn giao với trạng thái file và Git thực tế. Nếu lời bàn giao không khớp bằng chứng trên file, báo người chủ trước khi tiếp tục.
7. Trình bày ngắn gọn kế hoạch phiên: Task, mục tiêu, phạm vi, file dự kiến thay đổi, test và lệnh xác minh. Nếu `worklog.md` đã tồn tại, phải liệt kê file này vì cuối phiên cần nối bản kê; nếu dự kiến ghi phiếu quyết định thì phải liệt kê `soc-investigator-decision-slips.md`. Chờ người chủ xác nhận trước khi ghi file. Nếu cần quyết định quan trọng hoặc phạm vi chưa rõ, dừng và chờ người chủ.

## 6. Triển khai theo kế hoạch và TDD

1. **Replay-first.** Hoàn thành đường offline bằng `FileConnector` và `FakeProvider` trước khi phụ thuộc Wazuh lab hoặc mô hình thật. Không bắt đầu bằng việc dựng Docker/Wazuh lab.
2. **Một Task mỗi lượt.** Thực hiện đúng đầu ra, interface, file, test scenario và cổng nghiệm thu của Task tương ứng trong `soc-investigator-execution-testing-plan-vi.md`.
3. **TDD cho thay đổi chức năng và sửa lỗi:**
   - Viết test tập trung cho hành vi cần thay đổi trước khi viết implementation.
   - Chạy test và xác nhận test thất bại đúng nguyên nhân dự kiến.
   - Viết phần code tối thiểu để làm test thành công.
   - Chạy lại test để xác nhận PASS; sau đó refactor nếu cần và chạy lại test.
   - Không viết implementation trước rồi mới thêm test để hợp thức hóa code.
   - Với thay đổi không phù hợp để áp dụng TDD (ví dụ một số thay đổi tài liệu hoặc cấu hình), ghi rõ lý do và phép kiểm thay thế trong Worklog.
4. Không xóa, bỏ qua, làm yếu hoặc sửa test chỉ để làm cho bộ kiểm thử PASS. Nếu test sai hoặc mâu thuẫn với Spec, giải thích bằng chứng và trình người chủ quyết định trước khi thay đổi tiêu chí.
5. Dùng đúng test data và fixture trong kế hoạch. Fixture mới phải nhỏ, tất định và chỉ chứa dữ liệu giả lập/đã làm sạch; không đưa credential, dữ liệu khách hàng hoặc log nhạy cảm chưa xử lý vào repository.
6. Nếu phát hiện yêu cầu chưa được định nghĩa, xem mục quyết định còn mở trong kế hoạch. Không tự đoán các hợp đồng quan trọng; ghi nhận và hỏi người chủ trước khi viết code phụ thuộc vào quyết định đó.

## 7. Các ranh giới bảo mật không được vi phạm

Các nguyên tắc sau áp dụng cho mọi Task có liên quan; không được nới lỏng để làm test dễ PASS:

1. LLM không bao giờ nhận log/sự kiện SIEM thô. Chỉ Evidence Bundle đã được correlator cô đọng mới được đưa vào prompt.
2. Correlator và dựng cây tiến trình là code Python tất định, không dùng LLM. Định danh quan hệ tiến trình bằng host + `ProcessGuid` / `ParentProcessGuid`, không dùng PID/PPID để dựng cạnh cha-con.
3. Wazuh connector chỉ đọc các index cảnh báo/log nguồn; chỉ ghi kết quả vào `ai-investigations-*`. Phân trang sâu bằng `search_after`, không dùng `from/size`.
4. Công cụ không tự thực hiện hành động phản ứng hoặc thay thế SOAR. Khuyến nghị trong báo cáo chỉ dành cho nhà phân tích con người quyết định.
5. Không để thiếu telemetry làm dừng điều tra. Phân biệt rõ `Declared Data Gap` với `Anomalous Data Absence`; số đếm 0 không được diễn giải thành bằng chứng hệ thống sạch.
6. Các facts, timeline, IoC và kết luận phải có citation tới evidence hợp lệ. Giữ riêng `facts`, `checklist_results` và `hypotheses`; không tuyên bố đối chiếu thực thể mức 1 chứng minh sự thật hoặc quan hệ ngữ nghĩa.
7. Redaction bắt buộc bật khi gửi dữ liệu tới provider từ xa; không có cờ hoặc cấu hình cho phép tắt. Với Ollama cục bộ, redaction mặc định bật; chỉ được tắt theo cấu hình local mà kế hoạch cho phép.
8. Prompt phải phân tách system instruction khỏi evidence không đáng tin cậy. Prompt guard phải chặn raw event và chuỗi giống secret trước khi gọi provider.
9. Redaction map phải nằm ngoài report và có quyền file `0600`; không đưa map hoặc ledger vào public export. `.env` và `reports/` phải được bảo vệ bằng `.gitignore`; không in secret ra màn hình hoặc log.
10. HTML report phải bật Jinja2 autoescape và có CSP. Mọi giá trị có nguồn gốc từ log phải được xem là dữ liệu do bên tấn công kiểm soát.
11. Runtime không được đọc `eval/golden/` hoặc dùng golden truth làm whitelist validator.
12. Không sao chép nguyên văn cấu hình Docker từ `wazuh-docker` có giấy phép GPLv2 vào repository Apache-2.0. Tự viết cấu hình và ghi nhận provenance theo kế hoạch.
13. Ghim phiên bản các thành phần lab và nguồn/checksum của model. CI thông thường phải chạy không cần GPU, Ollama, Anthropic API key hoặc Wazuh đang hoạt động.

## 8. Kiểm chứng và tiêu chí hoàn tất Task

Trước khi báo hoàn tất một Task:

1. Chạy các test cụ thể của Task và các test liên quan.
2. Chạy toàn bộ `pytest -q` khi môi trường cho phép; nếu không chạy được, nêu rõ blocker, không suy diễn kết quả.
3. Chạy `ruff check .` và `ruff format --check .`.
4. Chạy `soc-investigator smoke` bằng FakeProvider khi pipeline tương ứng đã được xây dựng. CI không gọi mô hình thật hoặc phụ thuộc dịch vụ ngoài.
5. Đối chiếu từng Acceptance Criteria của Task trong kế hoạch; không coi việc tạo được file báo cáo là bằng chứng pipeline hoạt động đúng.
6. Kiểm tra `git diff` để xác nhận không có thay đổi ngoài phạm vi và không làm mất thay đổi có sẵn của người chủ.
7. Khi có test FAIL, ghi đúng tên test, lệnh, mã thoát và lỗi quan sát được; không che giấu hoặc gọi chung là “một vài test lỗi”.
8. Chỉ đánh dấu PASS cho phép kiểm đã chạy thành công. Lưu lệnh và kết quả liên quan vào Worklog; không thay kết quả thực tế bằng câu “đã chạy, đạt”.

Các lệnh CI chuẩn theo kế hoạch:

```bash
ruff check .
ruff format --check .
pytest -q
soc-investigator smoke
```

Các kiểm thử live với Wazuh, Sysmon, Ollama hoặc Anthropic là kiểm thử thủ công/theo đợt phát hành, không biến thành điều kiện CI mặc định.

## 9. Worklog, quyết định và bàn giao

1. Work Item lấy từ Task 0–11 trong kế hoạch hợp nhất. Không tự tạo mã Task hoặc mở việc ngoài kế hoạch. Việc phát sinh phải được người chủ chấp thuận trước; việc sửa lại Task đã nghiệm thu dùng mã mới có dẫn chiếu Task gốc, ví dụ `Task 3.r1`.
2. Chỉ giữ một Task đang mở tại một thời điểm, trừ khi người chủ chấp thuận rõ ràng cách làm khác.
3. Sau mỗi phiên có thay đổi, nối thêm bản ghi vào `worklog.md`; không sửa hoặc xóa bản ghi lịch sử. Bản ghi tối thiểu gồm: ngày, Task, việc đã làm, file đã thay đổi, lệnh/test và kết quả, quyết định đã chốt, việc còn lại và điểm cần bàn giao.
4. Dùng `soc-investigator-decision-slips.md` cho quyết định quan trọng, phát hiện Spec/kế hoạch thiếu hoặc mâu thuẫn, hoặc đề xuất ngoài phạm vi. Mỗi phiếu ghi bối cảnh, phương án và đánh đổi, khuyến nghị của AI Coding Agent, quyết định của người chủ và ngày quyết định. Không lập phiếu cho chi tiết triển khai thông thường.
5. Nếu phiên phải dừng khi Task chưa xong, ghi rõ phần đã hoàn thành, phần còn lại, test đã chạy/chưa chạy và câu hỏi đang chờ. Task vẫn ở trạng thái đang mở.
6. Khi nhận lại Task, đối chiếu bản ghi bàn giao với file và Git thực tế trước khi sửa tiếp.
7. Cuối phiên, trình người chủ bản kê kết quả và chờ nghiệm thu. Task chỉ được coi là đã duyệt khi người chủ chấp thuận; AI Coding Agent không tự commit.

## 10. Mẫu báo cáo cuối Task

AI Coding Agent báo cáo bằng tiếng Việt, ngắn gọn nhưng đủ bằng chứng:

```text
Task: <Task 0–11>
Trạng thái: <hoàn thành / đang mở / bị chặn / chờ người chủ nghiệm thu>
Đã triển khai: <các hành vi đã thực hiện>
File thay đổi: <danh sách file>
Kiểm thử: <lệnh đã chạy, số PASS/FAIL, mã thoát>
Acceptance Criteria: <đạt/chưa đạt theo từng tiêu chí>
Rà soát bảo mật: <các kiểm tra liên quan và kết quả>
Vấn đề còn lại: <blocker, giới hạn hoặc câu hỏi treo>
Task tiếp theo: <chỉ đề xuất, không tự triển khai>
```

**Định nghĩa hoàn tất:** Một Task chỉ được trình nghiệm thu khi implementation nằm trong phạm vi đã duyệt, TDD/test phù hợp đã được thực hiện, các phép kiểm bắt buộc có bằng chứng, các giới hạn còn lại được khai báo và Worklog đã được cập nhật. Chỉ người chủ dự án mới quyết định nghiệm thu Task và cho phép chuyển sang Task tiếp theo.
