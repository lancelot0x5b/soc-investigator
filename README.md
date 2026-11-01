# SOC Investigator

Trợ lý điều tra an ninh mạng (SOC) theo đặc tả **v0.2.6**: pipeline tất định
evidence-first, replay NDJSON offline, LLM chỉ nhận Evidence Bundle đã cô đọng
và redaction.

> Dự án đang ở **Task 0** (nền tảng repository và hợp đồng triển khai).
> CLI hiện là stub: mọi lệnh trả lời "not implemented" với exit code 70.

## Cài đặt (yêu cầu Python 3.12)

```bash
python -m pip install -e '.[dev]'
```

## Sử dụng

```bash
soc-investigator --help
soc-investigator --version
```

## Bảng mã thoát CLI (DS-001)

| Code | Ý nghĩa |
|---|---|
| 0  | success |
| 10 | alert / scenario pack not found |
| 11 | invalid scenario pack |
| 20 | configuration / doctor failure |
| 30 | connector failure |
| 40 | provider failure after retries |
| 50 | verification mismatch |
| 70 | unexpected internal error |

Lỗi cú pháp/cách dùng lệnh giữ mã mặc định của Typer (2).

## Kiểm thử & lint

```bash
pytest -q
ruff check .
ruff format --check .
```

## Tài liệu dự án

- `soc-investigator-spec-final.md` — đặc tả sản phẩm (nguồn yêu cầu có thẩm quyền)
- `soc-investigator-execution-testing-plan-vi.md` — kế hoạch triển khai & kiểm thử (Task 0–11)
- `AGENTS.md` — quy tắc làm việc của AI Coding Agent
- `worklog.md` / `soc-investigator-decision-slips.md` — nhật ký tiến độ / sổ quyết định
