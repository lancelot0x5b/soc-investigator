# soc-investigator — Sổ quyết định (Decision Slips)

> File theo dõi các quyết định cần người chủ dự án xem xét, theo AGENTS.md mục 9.4.
> Mỗi phiếu: bối cảnh, phương án & đánh đổi, khuyến nghị của AI Coding Agent, quyết định của người chủ, ngày quyết định.

---

## DS-001 — Bảng mã thoát CLI cho Task 0

**Bối cảnh:** Spec v0.2.6 yêu cầu mã thoát riêng cho "không có scenario pack khớp", "scenario pack không hợp lệ" và lỗi hệ thống ngoài dự kiến, nhưng chưa ấn định con số (kế hoạch, Task 0). Execution Plan đề xuất một ánh xạ làm mặc định.

**Phương án:**
- A) Dùng ánh xạ đề xuất trong kế hoạch: `0=success`, `10=alert/scenario not found`, `11=invalid scenario pack`, `20=configuration/doctor failure`, `30=connector failure`, `40=provider failure after retries`, `50=verification mismatch`, `70=unexpected internal error`. Lỗi cú pháp/dùng lệnh giữ mã mặc định của Typer (2).
- B) Người chủ đề xuất bảng số khác.

**Khuyến nghị:** Phương án A — đã được kế hoạch nêu làm mặc định, phân biệt đủ ba nhóm lỗi bắt buộc theo Spec.

**Quyết định của người chủ:** DS-001: dùng bảng exit code đề xuất của kế hoạch (`0/10/11/20/30/40/50/70`, Typer giữ mã 2 cho lỗi cú pháp).
**Ngày:** 2026-11-01

---

## DS-002 — Hành vi của CLI stub trong Task 0

**Bối cảnh:** Task 0 chỉ yêu cầu package cài được với entry point Typer `soc-investigator` và test `--help`; các lệnh thật (`install`, `config`, `doctor`, `investigate`, `smoke`, `verify`, `eval`, `export`) thuộc Task 2–10.

**Phương án:**
- A) Task 0 đăng ký app Typer rỗng (chỉ có `--help`/`--version`). Test `--help` PASS; gọi lệnh chưa triển khai sẽ bị Typer báo "unknown command" (exit code mặc định của Typer).
- B) Khai báo sẵn toàn bộ lệnh ở Task 0, mỗi lệnh in thông báo "not implemented" và thoát bằng exit code lỗi hệ thống (70).

**Khuyến nghị:** Phương án A — tối thiểu, không tạo hành vi sản phẩm giả; tránh phải sửa contract sau này. Nếu người chủ muốn người dùng cuối phân biệt "lệnh tồn tại nhưng chưa build", chọn B với exit code 70.

**Quyết định của người chủ:** DS-002: phương án B — khai báo sẵn toàn bộ lệnh ở Task 0, mỗi lệnh in "not implemented" và thoát bằng exit code 70.
**Ngày:** 2026-11-01

---

## DS-003 — Schema config tối thiểu cho Task 0

**Bối cảnh:** Task 0 yêu cầu "một model cấu hình có kiểm tra hợp lệ, giữ cấu hình nhỏ gọn". Spec đề cập các nhóm cấu hình rải rác: Opensearch/Wazuh endpoint + credentials (qua `.env`), provider mặc định (`ollama`|`anthropic`), model name (`qwen2.5:3b-instruct`), index patterns (`wazuh-alerts-*`, `wazuh-archives-*`, `ai-investigations-*`), redaction policy (bắt buộc bật với remote, mặc định bật với local), output dir `reports/`.

**Phương án:**
- A) Pydantic model nhỏ gọn với các field: `opensearch_url`, `opensearch_username`, `opensearch_password`, `provider` (Literal["ollama","anthropic"], mặc định "ollama"), `model` (mặc định "qwen2.5:3b-instruct"), `alert_index_pattern`, `archive_index_pattern`, `investigation_index_pattern`, `redact_hostname` (bool, mặc định False), `reports_dir` (mặc định "reports"). Load từ dict/env; thiếu/b sai giá trị bắt buộc → raise typed error ánh xạ exit code 20. Không dùng pydantic-settings hay plugin framework.
- B) Chỉ vài field tối đa cho tới khi Task liên quan cần thêm.

**Khuyến nghị:** Phương án A — chốt sớm hợp đồng config để doctor/providers/connectors sau này không đổi interface; vẫn "nhỏ gọn" theo yêu cầu, không thêm framework khám phá plugin/provider (đúng ràng buộc Task 0). Lưu ý: môi trường hiện có sẵn `pydantic-settings` nhưng ta không dùng để tránh dependency ngoài phạm vi.

**Quyết định của người chủ:** DS-003: phương án A — Pydantic model 10 field như mô tả; thiếu/sai giá trị bắt buộc → ConfigError (exit 20); không dùng pydantic-settings hay plugin framework.
**Ngày:** 2026-11-01

---

## DS-004 — Quyền tạo `worklog.md`

**Bối cảnh:** AGENTS.md mục 5.4: không tự tạo `worklog.md` và `soc-investigator-decision-slips.md` nếu người chủ chưa cho phép khởi tạo. Mục 9.3 yêu cầu nối bản ghi vào worklog sau mỗi phiên có thay đổi.

**Phương án:**
- A) Người chủ cho phép AI tạo mới hai file này ngay đầu Task 0.
- B) AI trình nội dung bản ghi trong báo cáo cuối phiên; người chủ tự tạo file.

**Khuyến nghị:** Phương án A để giữ lịch sử bàn giao trên repository như AGENTS.md yêu cầu. Phiếu này xin phép cho cả `worklog.md`; `soc-investigator-decision-slips.md` đã được tạo kèm các phiếu DS-001..DS-005 (có thể xóa nếu người chủ không duyệt).

**Quyết định của người chủ:** DS-004: cho phép tạo mới `worklog.md`.
**Ngày:** 2026-11-01

---

## DS-005 — Cấu trúc thư mục tests/ cho Task 0

**Bối cảnh:** Task 0 liệt kê `tests/test_project_baseline.py`; Task 1 trở đi liệt kê `tests/unit/...` và `tests/fixtures/...`. Cần chốt cách tổ chức ngay từ đầu.

**Phương án:**
- A) `tests/test_project_baseline.py` nằm trực tiếp dưới `tests/` đúng như Task 0; các task sau dùng `tests/unit/`, `tests/integration/` theo kế hoạch. Không cần `__init__.py` (pytest rootdir discovery).
- B) Đưa mọi test vào `tests/unit/` ngay từ Task 0.

**Khuyến nghị:** Phương án A — bám sát danh sách file trong kế hoạch, tránh xáo trộn về sau.

**Quyết định của người chủ:** DS-005: phương án A — `tests/test_project_baseline.py` nằm trực tiếp dưới `tests/`; task sau dùng `tests/unit/`, `tests/integration/`.
**Ngày:** 2026-11-01

---

## DS-006 — Xung đột plugin `libtmux` với pytest (đã đóng — không cần quyết định nữa)

**Bối cảnh ban đầu:** Môi trường dev có sẵn `libtmux` đăng ký một pytest plugin không tương thích pytest 9.x, khiến mọi lệnh pytest bị INTERNALERROR ("Marks cannot be applied to fixtures"), kể cả test rỗng. Giải pháp tạm thời từng đề xuất: ghim `pytest>=8.0,<9`.

**Điều tra lại (2026-11-01):** Đã kiểm chứng bằng thực nghiệm:
- Gỡ `libtmux` khỏi môi trường → cài pytest 9.2.0 → chạy toàn bộ test suite: **26 passed**, không còn INTERNALERROR.
- Kết luận: lỗi nằm ở package bên thứ ba `libtmux` cài sẵn trong môi trường, không liên quan code dự án và không cần ghim phiên bản pytest.

**Hành động đã thực hiện:** Gỡ `libtmux`; bỏ trần `<9`, dev extras trở về `pytest>=8.0`; xác nhận lại toàn bộ cổng nghiệm thu Task 0 PASS.

**Quyết định của người chủ:** Không còn hiệu lực (phiếu đóng vì không cần thiết). Nếu sau này `libtmux` được cài lại vì lý do khác, mở phiếu mới.
**Ngày:** 2026-11-01
