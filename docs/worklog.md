# SOC Investigator — Worklog

> Nhật ký tiến độ và bàn giao theo AGENTS.md mục 9. Nối thêm bản ghi, không viết lại lịch sử.
> File được tạo ngày 2026-11-01 theo phê duyệt DS-004.

---

## 2026-11-01 — Task 0: Nền tảng repository và các hợp đồng triển khai

**Trạng thái:** chờ người chủ nghiệm thu.

**Việc đã làm (TDD):**
1. Viết `tests/test_project_baseline.py` (26 test) trước; chạy pytest xác nhận **26 failed** đúng nguyên nhân dự kiến (module chưa tồn tại).
2. Viết implementation tối thiểu: `soc_investigator/__init__.py`, `errors.py` (exception types + exit-code mapping theo DS-001), `config.py` (Pydantic model theo DS-003-A, message lỗi không lộ giá trị secret), `cli.py` (Typer stub theo DS-002-B: 8 lệnh đăng ký sẵn, "not implemented" → exit 70).
3. Tạo `pyproject.toml` (package cài được, entry point `soc-investigator`, requires-python >=3.12, dev extras pytest+ruff), `.gitignore` (có `.env`, `reports/` + artifact cục bộ), `README.md`.
4. Cập nhật DS-001..DS-005 (quyết định người chủ, ngày 2026-11-01); mở DS-006 (ghim pytest <9 — xem bên dưới).

**File thay đổi:** `pyproject.toml`, `.gitignore`, `README.md`, `soc_investigator/__init__.py`, `soc_investigator/errors.py`, `soc_investigator/config.py`, `soc_investigator/cli.py`, `tests/test_project_baseline.py`, `soc-investigator-decision-slips.md`, `worklog.md` (tạo mới).

**Lệnh & kết quả (bằng chứng):**
| Lệnh | Kết quả | Exit code |
|---|---|---|
| `python -m pip install -e '.[dev]'` | thành công | 0 |
| `soc-investigator --help` | in đủ 8 lệnh stub | 0 |
| `soc-investigator smoke` | "'smoke' is not implemented yet..." | 70 |
| `ruff check .` | All checks passed! | 0 |
| `ruff format --check .` | 5 files already formatted | 0 |
| `pytest -q` | **26 passed** | 0 |

**Acceptance Criteria (Task 0):** `pip install -e '.[dev]'` ✅ · `soc-investigator --help` exit 0 ✅ · `ruff check .` exit 0 ✅ · `pytest -q` exit 0 ✅.

**Rà soát bảo mật (§7.9):** `.gitignore` chứa `.env` và `reports/` (có test kiểm tra); `load_config` render lỗi ValidationError chỉ kèm field path + lý do, không kèm value — có test chống rò rỉ secret. Task 0 chưa đụng đường dẫn gửi dữ liệu ra ngoài.

**Ghi chú kỹ thuật:**
- `ruff format --check .` ban đầu FAIL vì ruff format cả code block Python trong 2 file `.md` tài liệu nguồn sự thật (không được sửa — AGENTS.md §3.2). Đã khắc phục bằng `extend-exclude = ["*.md"]` trong `[tool.ruff]` (chi tiết triển khai, không đổi hành vi sản phẩm).
- `soc-investigator smoke` của cổng CI §8 sẽ không chạy PASS cho tới Task 8 (pipeline FakeProvider); ở Task 0 đây là hành vi stub exit 70 đã duyệt qua DS-002-B.

**Việc còn lại / câu hỏi treo:**
- DS-006 đã đóng (2026-11-01): nguyên nhân gốc là plugin `libtmux` cài sẵn trong môi trường xung đột pytest 9.x; đã gỡ `libtmux`, xác nhận pytest 9.2.0 chạy OK (26 passed), bỏ trần `<9` — dev extras trở về `pytest>=8.0`. Không cần quyết định của người chủ.
- Không tự commit (AGENTS.md §3.4) — quyền Git thuộc người chủ.

**Task tiếp theo (chỉ đề xuất, chưa triển khai):** Task 1 — Schema miền dữ liệu và NDJSON replay tất định.

---

## 2026-11-01 — Bổ sung: dọn dẹp theo yêu cầu người chủ (sau nghiệm thu Task 0)

**Việc đã làm:**
1. Gỡ `libtmux` khỏi môi trường (không liên quan dự án, gây xung đột plugin với pytest). pytest 9.2.0 chạy sạch; dev extras giữ `pytest>=8.0`, không cần ghim trần. DS-006 đóng.
2. Ruff không đụng file `.md`: `[tool.ruff] extend-exclude = ["*.md"]` đã cấu hình từ trước; xác nhận lại bằng `ruff check .` và `ruff format --check .`.
3. Chuyển toàn bộ file `.md` vào `docs/` theo phê duyệt của người chủ: `AGENTS.md`, `SKILL.md`, spec, execution plan, decision slips, worklog (dùng `git mv`). `README.md` giữ ở gốc theo layout Task 0; cập nhật tham chiếu trong README sang đường dẫn `docs/...`.

**Lệnh & kết quả (bằng chứng):**
| Lệnh | Kết quả | Exit code |
|---|---|---|
| `python -m pytest -q` | 26 passed | 0 |
| `ruff check .` | All checks passed! | 0 |
| `ruff format --check .` | pass (bỏ qua *.md) | 0 |
| `soc-investigator --help` | in đủ 8 lệnh stub | 0 |

**Lưu ý cho người chủ:** repo local hiện **không có remote git nào** (`git remote -v` trống), vì vậy các thay đổi chưa thể đẩy lên GitHub. Cần người chủ cung cấp URL remote hoặc tự push từ branch cục bộ `qwen-code-5ee4a145-...`.

---

## 2026-11-02 — Phiên tiếp theo: chuẩn bị Task 1 (chưa code)

**Việc đã làm:**
1. Tiếp tục phiên sau khi tạm dừng; rà soát trạng thái repo (Task 0 đã commit, working tree sạch).
2. Phân tích yêu cầu Task 1 (Schema miền dữ liệu + NDJSON replay tất định) từ Spec và Execution Plan.
3. Giải đáp chất vấn của người chủ về fixture tự dựng: thống nhất chiến lược 2 tầng (fixture synthetic cho unit test tất định; độ khớp thực tế do smoke/golden live Task 8–10 đảm nhiệm).
4. Ghi 4 phiếu quyết định mới DS-007..DS-010 vào `docs/soc-investigator-decision-slips.md` (đang chờ người chủ duyệt).

**File thay đổi:** `docs/soc-investigator-decision-slips.md` (thêm DS-007..DS-010), `docs/worklog.md` (bản ghi này).

**Việc còn treo:** Chờ quyết định DS-007 (kích thước/nguồn fixture ~100 record synthetic), DS-008 (định nghĩa đầy đủ InvestigationReport ngay), DS-009 (fail-fast khi NDJSON lỗi), DS-010 (không ghi file ở Task 1). Sau khi duyệt → viết test trước (TDD) rồi implementation.

**Task tiếp theo (chỉ đề xuất, chưa triển khai):** Task 1 — bắt đầu code ngay sau khi DS-007..DS-010 được duyệt.
