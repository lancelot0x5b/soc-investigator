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
- DS-006 chờ người chủ duyệt (ghim `pytest>=8.0,<9` do plugin `libtmux` cài sẵn trong môi trường xung đột pytest 9.x — nếu không ghim, mọi lệnh pytest trong repo này bị INTERNALERROR).
- Không tự commit (AGENTS.md §3.4) — quyền Git thuộc người chủ.

**Task tiếp theo (chỉ đề xuất, chưa triển khai):** Task 1 — Schema miền dữ liệu và NDJSON replay tất định.
