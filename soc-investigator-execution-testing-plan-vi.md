# soc-investigator v0.2.6 — Kế hoạch triển khai và kiểm thử

> **Dành cho AI coding agent:** Triển khai lần lượt từng task. Tuân thủ Phát triển hướng kiểm thử (Test-Driven Development — TDD): viết một test đang thất bại, chạy để xác nhận nó thất bại đúng như dự kiến, viết thay đổi nhỏ nhất để đáp ứng test, chạy lại test, sau đó chạy bộ test liên quan. Không triển khai nhiều task trong một lượt lớn.
>
> **Tài liệu đặc tả nguồn:** `soc-investigator-spec-final.md` (v0.2.6). Kế hoạch này chuyển đặc tả thành trình tự triển khai; không cho phép mở rộng phạm vi v0.2.

**Mục tiêu:** Xây dựng một trợ lý điều tra SOC độc lập với SIEM trong phạm vi v0.2.6: một Wazuh connector, một replay connector, một scenario pack về ứng dụng Office tạo tiến trình thông dịch lệnh, nhà cung cấp mô hình Ollama chạy cục bộ và Anthropic tùy chọn, báo cáo có bằng chứng truy nguyên được, cùng bộ kiểm thử có thể tái lập.

**Kiến trúc:** Xây dựng luồng replay ngoại tuyến trước. Giữ phần Investigation Brain mang tính tất định (deterministic) trong phạm vi có thể: correlator tạo Evidence Bundle mà không dùng LLM; LLM chỉ nhìn thấy bundle đã cô đọng và che dữ liệu; validator kiểm tra schema, tham chiếu bằng chứng và thực thể có thể kiểm tra bằng máy; report writer lưu bản chụp, ledger và mã băm. Chỉ bổ sung Wazuh connector chạy trực tiếp và lab vật lý sau khi replay hoạt động ổn định.

**Công nghệ:** Python 3.12, Typer, Pydantic, PyYAML, opensearch-py, requests, Ollama, Anthropic SDK, Jinja2, pytest, ruff, Docker Compose, Sysmon và Atomic Red Team.

---

## 1. Phạm vi và các ranh giới bắt buộc

### Nằm trong phạm vi v0.2.6

- Các lệnh CLI: `install`, `config`, `doctor`, `investigate` (chế độ live và `--replay`), `smoke`, `verify`, `eval`, `export` (`--public`).
- `WazuhConnector` đọc `wazuh-alerts-*` và `wazuh-archives-*`; chỉ ghi vào `ai-investigations-*`.
- `FileConnector` replay một bản xuất NDJSON có tính tất định (deterministic), không cần lab đang chạy.
- Một scenario pack: `office-interpreter-execution-v1`, lấy Wazuh rule `100110` làm điểm neo.
- Tương quan từ Sysmon EID 1, 3 và 11; DNS EID 22 tùy chọn và được khai báo rõ là khoảng trống dữ liệu (Declared Data Gap) trong lab tham chiếu.
- `qwen2.5:3b-instruct` Q4_K_M chạy cục bộ qua Ollama; Anthropic Claude API là tùy chọn. Khi dùng nhà cung cấp từ xa, bắt buộc bật che dữ liệu và không được phép tắt.
- Tập con ATT&CK cục bộ và playbook do scenario pack khai báo.
- Evidence snapshot, kiểm tra citation, đối chiếu thực thể mức 1, investigation ledger, xác minh SHA-256, đầu ra Markdown/HTML/JSON và xuất bản công khai an toàn.
- CI sử dụng `FakeProvider`; smoke với mô hình thật chỉ chạy thủ công hoặc trước khi phát hành.

### Nằm ngoài phạm vi

Không bổ sung SIEM khác, scenario pack khác, nhà cung cấp LLM khác, vector database, Kafka, TheHive, chức năng tạo Sigma/YARA, phản ứng tự động, quy trình SOAR, agent tự trị nhiều bước hoặc trình cài đặt doanh nghiệp hoàn chỉnh. Ghi các ý tưởng này vào sổ quyết định; không triển khai trong phiên bản này.

### Các ràng buộc toàn cục (áp dụng cho mọi task)

1. Python **3.12**.
2. LLM không bao giờ nhận sự kiện SIEM thô (raw events). LLM chỉ nhận Evidence Bundle đã được cô đọng.
3. Correlation và dựng cây tiến trình là mã Python tất định; correlator không sử dụng LLM.
4. Dựng cây tiến trình bằng tổ hợp host + `ProcessGuid` / `ParentProcessGuid`, tuyệt đối không dùng PID/PPID.
5. Phân trang OpenSearch sử dụng `search_after`; không dùng `from/size` cho tập kết quả lớn hoặc phân trang sâu.
6. Các chỉ mục cảnh báo/log nguồn chỉ có quyền đọc. Chỉ ghi vào `ai-investigations-*`.
7. Không được có hành động phản ứng tự động. Các khuyến nghị chỉ dành cho nhà phân tích con người xem xét và quyết định.
8. Thiếu telemetry không bao giờ được làm gián đoạn điều tra. Phải phân biệt `Declared Data Gap` với `Anomalous Data Absence`.
9. Mọi dữ kiện, IoC và phát biểu trong timeline phải có citation tới bằng chứng; `checklist_results`, `facts` và `hypotheses` phải là các mảng riêng biệt.
10. Che dữ liệu với Anthropic là bắt buộc. Với Ollama, che dữ liệu mặc định được bật và chỉ có thể tắt bằng cấu hình cục bộ được chỉ định rõ.
11. Bản đồ đối chiếu dữ liệu đã che (redaction map) phải nằm riêng, không nằm trong báo cáo, và được ghi với quyền `0600`; `.env` và `reports/` phải nằm trong `.gitignore`.
12. Render HTML sử dụng Jinja2 autoescape và chính sách CSP trong meta. Coi mọi giá trị hiển thị có nguồn gốc từ log là dữ liệu do kẻ tấn công kiểm soát.
13. Tuyệt đối không sao chép nguyên văn cấu hình Docker của Wazuh từ `wazuh-docker` vào repository Apache-2.0 này. Hãy tự viết các file compose/cấu hình và ghi nhận nguồn gốc trong `NOTICE.md`.
14. Ghim phiên bản các thành phần lab và nguồn/checksum của model trong `lab/versions.yml`.
15. CI phải chạy được mà không cần GPU, Ollama, thông tin xác thực Anthropic hoặc dịch vụ Wazuh đang hoạt động.

---

## 2. Trình tự triển khai được khuyến nghị

Thứ tự phụ thuộc được lựa chọn có chủ đích:

`domain contracts → FileConnector/replay → scenario loader → correlator → knowledge → prompt/redaction → providers → validator → report/ledger/hash → CLI/smoke/eval → Wazuh/doctor → physical lab/release`

Không đảo ngược trình tự này. Đặc biệt, không bắt đầu bằng Docker lab hoặc mô hình thật.

### Task 0 — Nền tảng repository và các hợp đồng triển khai

**Các file:** `pyproject.toml`, `.gitignore`, `README.md`, `soc_investigator/__init__.py`, `soc_investigator/errors.py`, `soc_investigator/config.py`, `tests/test_project_baseline.py`.

**Kết quả cần bàn giao:**
- Một Python package có thể cài đặt và có entry point Typer `soc-investigator`.
- Các dải phiên bản dependency được ghim phù hợp với Python 3.12; dependency phát triển dành cho pytest và ruff.
- Các kiểu exception ổn định và cơ chế ánh xạ mã thoát CLI. Đặc tả yêu cầu mã thoát riêng cho các trường hợp “không có scenario pack khớp”, “scenario pack không hợp lệ” và lỗi hệ thống ngoài dự kiến, nhưng chưa ấn định con số. Đề xuất ánh xạ: `0=success`, `10=alert/scenario not found`, `11=invalid scenario pack`, `20=configuration/doctor failure`, `30=connector failure`, `40=provider failure after retries`, `50=verification mismatch`, `70=unexpected internal error`. Lỗi cú pháp/cách dùng lệnh giữ mã lỗi mặc định của Typer.
- Một model cấu hình có kiểm tra hợp lệ. Giữ cấu hình nhỏ gọn; không thêm framework khám phá plugin hoặc provider.
- `.gitignore` phải có `.env`, `reports/` và các artifact cấu hình/model cục bộ.

**Kiểm thử:** Kiểm tra metadata phiên bản Python/package; CLI `--help`; ánh xạ mã thoát; config từ chối giá trị bắt buộc bị thiếu/không hợp lệ; `.gitignore` có đủ đường dẫn bắt buộc.

**Cổng nghiệm thu:** Các lệnh `python -m pip install -e '.[dev]'`, `soc-investigator --help`, `ruff check .`, `pytest -q` đều kết thúc với mã thoát 0.

### Task 1 — Schema miền dữ liệu và NDJSON replay tất định

**Các file:** `soc_investigator/models.py`, `soc_investigator/connectors/base.py`, `soc_investigator/connectors/file.py`, `tests/fixtures/ndjson/`, `tests/unit/test_file_connector.py`, `lab-data/sample-mini.ndjson`.

**Các interface cần chốt trước khi phát triển thành phần phụ thuộc:**

```python
class SiemConnector(Protocol):
    def get_alert(self, alert_id: str) -> Alert: ...
    def search_events(self, query: dict, start: datetime, end: datetime,
                      limit: int = 500) -> list[Event]: ...
    def write_investigation(self, report: InvestigationReport) -> str: ...

class FileConnector:
    def __init__(self, path: Path): ...
    def get_alert(self, alert_id: str) -> Alert: ...
    def search_events(self, query: dict, start: datetime, end: datetime,
                      limit: int = 500) -> list[Event]: ...
    def write_investigation(self, report: InvestigationReport) -> str: ...
```

Sử dụng Pydantic model cho `Alert`, `Event` đã chuẩn hóa, `RawRef`, `Evidence`, `EvidenceBundle`, `InvestigationReport` và dữ liệu ledger. Chốt hợp đồng dữ liệu đã chuẩn hóa này trước khi xây correlator:

- `RawRef`: `index: str`, `id: str`.
- `Alert`: `alert_id: str`, `rule_id: str`, `timestamp: datetime`, `host: str | None`, `user: str | None`, `raw_ref: RawRef`, `raw: dict`.
- `Event`: `document_id: str`, `timestamp: datetime`, `host: str`, `source: str`, `event_code: int | str | None`, `process_guid: str | None`, `parent_process_guid: str | None`, `pid: int | None`, `parent_pid: int | None`, `image: str | None`, `parent_image: str | None`, `command_line: str | None`, `destination_ip: str | None`, `destination_hostname: str | None`, `destination_port: int | None`, `target_filename: str | None`, `file_mtime: datetime | None`, `raw_ref: RawRef`, `raw: dict`.
- `Evidence`: `evidence_id: str`, `type: Literal["process_create", "network", "file_change"]`, `timestamp: datetime`, `summary: str`, `raw_ref: RawRef`.
- `EvidenceBundle`: metadata cảnh báo, `scenario_id`, danh sách evidence có thứ tự, các evidence ID trong timeline, IoC đã trích xuất và thống kê (`raw_events`, `distilled_evidence`, `per_type_counts`, `dropped_by_budget`).

Tất cả thuộc tính sự kiện ngoài `document_id`, `timestamp`, `host`, `raw_ref` và `raw` đều là tùy chọn vì telemetry có thể thiếu trường. Giữ toàn bộ sự kiện thô tại ranh giới connector/snapshot; không bao giờ chuyển nó cho prompt builder. Bộ chuẩn hóa (normalizer) là nơi duy nhất biết đường dẫn trường lồng nhau cụ thể của Wazuh.

**Hợp đồng NDJSON đề xuất để không chặn triển khai:** mỗi dòng là một OpenSearch hit, có dạng `{"_index":"...","_id":"...","_source":{...}}`. Phân loại record theo các index pattern cấu hình cho alerts/archive. Fixture tham chiếu phải có đúng một alert không mơ hồ để replay. Xác nhận mapping field bằng một bản xuất Wazuh thật trước khi triển khai `WazuhConnector`; không đoán đường dẫn field Wazuh từ trí nhớ. Nếu JSON sai định dạng hoặc thiếu trường envelope bắt buộc, phải từ chối kèm tên file và số dòng; không âm thầm bỏ qua record lỗi.

**Kiểm thử:**
- Đọc được alert và các archive event từ cùng một file.
- Chọn đúng alert được yêu cầu; alert không tồn tại hoặc có nhiều alert khớp phải trả về lỗi có kiểu (typed error).
- Giữ nguyên `_index` và `_id` trong `raw_ref`.
- Lọc theo time window, host và điều kiện query.
- Xử lý UTF-8 và giá trị JSON chứa chuỗi đã escape.
- Báo số dòng khi NDJSON bị lỗi và không tạo báo cáo một phần.
- Các lần đọc lặp lại tạo ra cùng record đã chuẩn hóa và cùng thứ tự.

**Cổng nghiệm thu:** Có thể replay fixture cục bộ mà không cần Docker, Wazuh hoặc LLM.

### Task 2 — Scenario pack loader và kiểm định bằng máy

**Các file:** `soc_investigator/scenarios/models.py`, `soc_investigator/scenarios/loader.py`, `scenarios/office-interpreter-execution-v1.yaml`, `scenarios/_shared/tier-b-execution-chain.yaml`, `scenarios/_shared/tier-c-tactic-sweep.yaml`, `playbooks/phish-initial-triage.yaml`, `tests/unit/test_scenario_loader.py`, `tests/fixtures/scenario-packs/`.

**Interface:** `load_scenario_pack(path: Path) -> ScenarioPack`.

**Triển khai chính xác các luật kiểm tra sau:**
1. Ghép các file include đã khai báo trước khi kiểm định; giải quyết đường dẫn include tương đối với thư mục gốc repository/scenario và từ chối đường dẫn thoát ra ngoài thư mục gốc đó (path traversal).
2. Bắt buộc có `scenario_id`, entry alert, correlation config, hypothesis checklist và `coverage` gồm đủ ba danh sách: `can_query`, `blind_missing_data`, `out_of_scope`.
3. Mọi câu hỏi checklist phải có `id`, `question` ở dạng khẳng định có thể kiểm chứng và `evidence_types` không rỗng; mọi evidence type phải được tạo ra từ correlation config của pack.
4. Mọi tactic ở tầng C phải có câu hỏi hoặc có `blind` kèm lý do.
5. Mọi đường dẫn playbook được khai báo phải trỏ tới file thực sự tồn tại.
6. Mã runtime không được nạp golden truth.
7. Pack không hợp lệ phải thất bại với exit code `11` và thông báo đúng đường dẫn YAML/trường gây lỗi. Không fallback sang pack rỗng.

**Kiểm thử:** Pack hợp lệ; thiếu coverage; thiếu include; include tạo vòng lặp; include path traversal; evidence type không được correlation tạo ra; câu hỏi mở; thiếu question ID; tactic không có question/blind; thiếu playbook; runtime loader không thể import file golden.

**Cổng nghiệm thu:** Pack hợp lệ được nạp; mọi fixture không hợp lệ đều bị từ chối ngay lúc nạp, trước khi gọi connector/provider.

### Task 3 — Evidence correlator (Python thuần)

**Các file:** `soc_investigator/correlator.py`, `soc_investigator/correlation/`, `tests/unit/test_correlator.py`, `tests/fixtures/ndjson/`.

**Interface:** `build_evidence_bundle(alert: Alert, pack: ScenarioPack, connector: SiemConnector) -> EvidenceBundle`.

**Triển khai:**
- Sử dụng lookback window do pack quy định (pack tham chiếu: 30 phút).
- Dựng cây tiến trình bằng host + `ProcessGuid` và `ParentProcessGuid`; bao gồm tiến trình trong alert và các tiến trình con liên quan theo pack.
- Tương quan sự kiện Sysmon EID 3 (network) của các tiến trình trong cây.
- Tương quan sự kiện Sysmon EID 11 (file creation) trên host.
- Khử trùng lặp file change theo khóa `(host, normalized_path, mtime)`; giữ lại các trường hợp khác path hoặc mtime.
- Dựng timeline theo thứ tự thời gian, evidence ID, `raw_ref`, IoC và số lượng event theo từng loại.
- Áp dụng budget của pack (pack tham chiếu: `max_evidence_items=40`, `max_estimated_tokens=6000`). Giảm tải theo đúng thứ tự quy định; không bao giờ loại bỏ chuỗi tiến trình gốc, bằng chứng IoC hoặc bằng chứng ATT&CK chính. Ghi mọi lần loại bỏ vào `stats.dropped_by_budget`.
- Đếm loại evidence có kết quả bằng 0. Không dừng xử lý chỉ vì một loại evidence không có kết quả.

**Kiểm thử:**
- Tái dựng đúng chuỗi `WINWORD.EXE → powershell.exe → child process`.
- PID reuse: hai tiến trình có cùng PID nhưng khác ProcessGuid không bị nối nhầm.
- Cùng ProcessGuid qua nhiều event vẫn là một process node.
- Loại event ngoài lookback 30 phút hoặc thuộc host khác.
- Loại EID 3 của tiến trình không liên quan.
- Các EID 11 lặp lại cùng host/path/mtime được khử trùng lặp; khác mtime/path phải được giữ.
- Timeline sắp xếp tất định theo timestamp và tiêu chí phụ ổn định.
- Số lượng EID 3 hoặc EID 11 bằng 0 vẫn được ghi nhận là 0; bundle vẫn được trả về.
- Khi vượt budget, loại evidence ưu tiên thấp trước; giữ pivot bắt buộc và ghi lại số lượng/loại đã loại.
- Hơn 10.000 source event không bị cắt im lặng do phân trang ở tầng dưới (Task 9 cũng phải có test ở cấp connector).

**Cổng nghiệm thu:** Fixture tạo ra bundle tất định, evidence ID ổn định và số đếm chính xác.

### Task 4 — Bộ truy xuất tri thức cục bộ

**Các file:** `soc_investigator/knowledge/retriever.py`, `soc_investigator/knowledge/attack.py`, `soc_investigator/knowledge/playbooks.py`, `knowledge/attack-subset/`, `playbooks/phish-initial-triage.yaml`, `tests/unit/test_knowledge_retriever.py`.

**Interface:** `retrieve_knowledge(bundle: EvidenceBundle, pack: ScenarioPack) -> KnowledgeContext`.

**Triển khai:** Nạp tập con ATT&CK STIX đã ghim phiên bản; chỉ ánh xạ chỉ dấu/kỹ thuật được evidence hỗ trợ; chỉ truy xuất playbook được pack hiện tại nêu tên; trả về danh sách kỹ thuật đề xuất làm whitelist cho validator ở bước sau. Ghi mã băm file playbook tại thời điểm chạy. Không dùng vector database và không quét đệ quy toàn bộ thư mục playbook.

**Kiểm thử:** Evidence process/network đã biết truy xuất được candidate technique dự kiến; indicator không biết không tạo ra technique tưởng tượng; technique ID thuộc tập con ATT&CK cục bộ; playbook không liên quan không được nạp; playbook được pack khai báo được nạp; hash provenance của playbook thay đổi khi nội dung file thay đổi.

**Cổng nghiệm thu:** Whitelist của validator lấy từ đầu ra retriever, tuyệt đối không lấy từ `eval/golden/`.

### Task 5 — Che dữ liệu, prompt builder và prompt guard

**Các file:** `soc_investigator/redact.py`, `soc_investigator/prompts/builder.py`, `soc_investigator/prompts/templates/`, `soc_investigator/security/prompt_guard.py`, `tests/unit/test_redaction.py`, `tests/unit/test_prompt_builder.py`, `tests/security/test_prompt_guard.py`.

**Các interface:**

```python
redact_evidence(bundle: EvidenceBundle, *, redact_hostname: bool = False) -> RedactionResult
build_prompt(bundle: EvidenceBundle, pack: ScenarioPack,
             knowledge: KnowledgeContext, provider_name: str) -> PromptPackage
check_prompt_safety(prompt: PromptPackage) -> None  # raises PromptSafetyError
```

**Triển khai:**
- Dùng placeholder ổn định cho username, username nằm trong đường dẫn `C:\Users\<name>\`, IP private và địa chỉ email; che hostname là tùy chọn riêng.
- Giữ giá trị gốc trong nội bộ; redaction map là artifact riêng, không bao giờ nằm trong report hoặc prompt.
- Bắt buộc che dữ liệu với provider từ xa; không được có cấu hình hoặc CLI flag để tắt. Ollama cục bộ mặc định bật; chỉ cấu hình cục bộ mới có thể tắt.
- Tách system instruction khỏi dữ liệu evidence. Đánh dấu evidence là nội dung không đáng tin cậy. Đưa checklist, methodology và chỉ nội dung playbook đã được Task 4 lựa chọn vào prompt.
- Prompt guard từ chối raw event payload và chuỗi bí mật khớp pattern cố định trước khi gọi provider. Guard phải chạy với cả Ollama và Anthropic.
- Ledger chỉ lưu prompt text sau khi đã che dữ liệu.

**Kiểm thử:** Username, username trong path, IPv4 nội bộ và email được thay bằng placeholder; cùng giá trị lặp lại dùng cùng placeholder; giá trị khác nhau dùng placeholder khác nhau; hostname được giữ lại trừ khi có yêu cầu che; public IP không bị nhận nhầm thành IP nội bộ; provider từ xa không thể tắt redaction; mặc định local là bật; có thể chủ động tắt ở local; prompt chứa summary nhưng không có raw JSON; prompt không chứa giá trị bí mật gốc; log độc hại như `ignore prior instructions` vẫn chỉ là dữ liệu và không thể thay thế system instruction; guard chặn chuỗi giống API key/password với cả hai provider.

**Cổng nghiệm thu:** Kiểm tra fixture prompt và chứng minh không có raw event object hoặc giá trị gốc đã che xuất hiện trước khi gọi provider.

### Task 6 — Các bộ điều hợp LLM provider

**Các file:** `soc_investigator/providers/base.py`, `soc_investigator/providers/ollama.py`, `soc_investigator/providers/anthropic.py`, `soc_investigator/providers/fake.py`, `tests/unit/test_providers.py`, `tests/integration/test_anthropic_adapter.py`.

**Interface:**

```python
class LlmProvider(Protocol):
    def generate(self, system: str, user: str, schema: dict,
                 temperature: float = 0.0) -> dict: ...
```

**Triển khai:**
- Mọi adapter phải trả về object đã parse và thỏa schema yêu cầu hoặc raise `SchemaError`/provider error có kiểu.
- Thử lại (retry) khi response sai định dạng/schema tối đa **hai lần retry** (tối đa ba lần gọi tổng cộng). Mỗi lần retry phải kèm yêu cầu có cấu trúc và chẩn đoán cụ thể lỗi của lần trước.
- Ghi số lần thử, lỗi, token usage và thời gian vào ledger.
- `FakeProvider` đọc response fixture cố định; không truy cập mạng.
- Anthropic adapter tuyệt đối không chấp nhận request từ xa nếu trạng thái redaction đang tắt.

**Kiểm thử:** JSON hợp lệ; JSON sai; thiếu trường trong schema; retry lần 1 thành công; retry lần 2 thành công; cả ba lần đều thất bại; error response chỉ rõ trường/citation còn thiếu; timeout/API error được biểu diễn thành lỗi có kiểu; usage được ghi nhận; API key không bao giờ được in; FakeProvider không tạo request mạng; không thể bypass redaction khi gọi provider từ xa.

**Cổng nghiệm thu:** Test mặc định chạy với FakeProvider; unit test provider dùng HTTP/client stub tất định; CI không cần API key.

### Task 7 — Bộ kiểm định đầu ra

**Các file:** `soc_investigator/validator.py`, `soc_investigator/validation/entity_checks.py`, `tests/unit/test_validator.py`, `tests/security/test_validator_adversarial.py`.

**Interface:** `validate_report_draft(draft: dict, bundle: EvidenceBundle, pack: ScenarioPack, allowed_techniques: set[str]) -> ValidationResult`.

**Triển khai năm phép kiểm:** schema; technique whitelist; evidence citation; trạng thái checklist; đối chiếu thực thể mức 1.

- Facts, timeline entry, IoC và hypothesis chứa khẳng định thực tế phải có evidence ID hợp lệ.
- Technique ID phải thuộc whitelist từ retriever, không phải golden truth.
- Trạng thái checklist chỉ được là một trong `confirmed`, `refuted`, `inconclusive`. `confirmed`/`refuted` cần citation hợp lệ; `inconclusive` cần lý do và liên kết tới missing data.
- Phép đối chiếu thực thể trích xuất domain, IP, tên tiến trình, path, hash, timestamp và số; chuẩn hóa các khác biệt an toàn (chữ hoa/thường của process name Windows/domain, đường dẫn/thời gian đã chuẩn hóa) trước khi so với evidence được trích dẫn. Gắn nhãn mỗi phát biểu là `machine_checked`, `citation_only` hoặc `interpretation`; thực thể không được hỗ trợ phải bị đánh dấu `unverified` hoặc loại bỏ và ghi số lượng.
- Giữ `facts`, `checklist_results` và `hypotheses` thành các mảng riêng.
- Giữ các bước playbook tách khỏi claim về evidence; playbook là quy trình, không phải chứng cứ. `unanswered` và `out_of_scope` bắt buộc có lý do.

**Kiểm thử:** Report hợp lệ; schema lỗi; evidence ID không tồn tại; ATT&CK ID không biết; claim trích citation hợp lệ nhưng khẳng định domain/IP/process/path/hash/timestamp/number mâu thuẫn; thực thể đúng với khác biệt chữ hoa/thường/path đã chuẩn hóa; claim không có thực thể kiểm tra bằng máy được gắn nhãn interpretation; quy tắc confirmed/refuted/inconclusive; checklist state không hợp lệ; checklist item trùng lặp; trạng thái playbook và lý do bắt buộc; claim không được hỗ trợ được ghi nhận là dropped/unverified; test từ chối sai đối với tên tiến trình viết tắt so với đường dẫn đầy đủ.

**Cổng nghiệm thu:** Các ca đối kháng trong đó citation tồn tại nhưng nội dung được trích dẫn mâu thuẫn với claim phải bị từ chối. Ghi nhận số lần từ chối sai (false-positive rejection) vào MODEL_SELECTION.md; không mô tả phép đối chiếu mức 1 là xác minh chân lý/ngữ nghĩa.

### Task 8 — Report writer, ledger, snapshot và mã băm

**Các file:** `soc_investigator/report/writer.py`, `soc_investigator/report/schema.py`, `soc_investigator/report/render_markdown.py`, `soc_investigator/report/render_html.py`, `soc_investigator/report/ledger.py`, `soc_investigator/report/integrity.py`, `tests/unit/test_report_writer.py`, `tests/security/test_report_rendering.py`.

**Các interface:**

```python
write_report(result: ValidationResult, bundle: EvidenceBundle,
             pack: ScenarioPack, ledger: InvestigationLedger,
             output_dir: Path) -> ReportArtifacts
verify_local_artifacts(report_path: Path, ledger_path: Path) -> VerifyResult
export_public(report_path: Path, destination: Path) -> Path
```

**Triển khai:**
- Schema đầu ra phiên bản `0.2.6` và các trường được định nghĩa trong đặc tả.
- Evidence snapshot chỉ chứa các event nguồn được trích dẫn, raw reference và SHA-256 của từng event cũng như toàn bundle.
- Dùng canonical JSON tất định để tính hash (UTF-8, thứ tự key ổn định và separator cố định); ghi lại lựa chọn này để `verify` có thể tính lại.
- Ledger chứa hash pack/checklist, hash prompt và prompt text đã che, raw model output, draft trước validator, validator actions, attempts, usage và timings.
- `scope_statement`, `evidence_state`, declared gaps, abnormal absences, recommendations và `playbook_provenance` phải được sinh từ coverage của pack, số liệu đã đo, lý do missing-data và các bước playbook — không để LLM tự bịa. Khuyến nghị phải bao quát đủ bốn nguồn trong đặc tả: khoảng trống đã khai báo, checklist inconclusive, sự thiếu vắng bất thường và bước playbook chưa trả lời được.
- Lưu redaction map ngoài report với POSIX mode `0600`; không bao giờ đưa vào public export.
- Tạo JSON, Markdown và HTML. HTML phải autoescape toàn bộ nội dung có nguồn gốc từ log và có chính sách CSP trong meta.
- `export --public` loại bỏ giá trị thô của snapshot, giữ `evidence_id` + hashes, che các trường hiển thị và loại trừ ledger/redaction map.
- Verify cục bộ kiểm tra tính nhất quán nội bộ; verify live bổ sung đối chiếu `bundle_sha256` và `ledger_sha256` đã lưu với document độc lập trong `ai-investigations-*`.
- Lỗi ghi report phải hiển thị rõ; không trả về thành công nếu artifact bắt buộc hoặc thao tác ghi index thất bại. Khi phù hợp, sử dụng file tạm an toàn và atomic rename ở local.

**Kiểm thử:** Round-trip schema; mọi claim trong report giữ được evidence reference; raw snapshot chỉ chứa event được trích dẫn; tính lại event/bundle hash thành công; sửa event hoặc bundle làm verify thất bại; sửa prompt/ledger làm local verify thất bại; hash index live không khớp làm verify thất bại; verify replay nói rõ không có index độc lập; report chứa chính xác hai nhãn missing-data; evidence type có số lượng 0 là abnormal absence; DNS/mail blind là declared gap; playbook `unanswered` tạo recommendation có `source=playbook` mà không tạo citation evidence giả; redaction map có mode `0600`; public export không có raw source value, ledger hoặc redaction map; payload XSS trong HTML được escape và có CSP; report lỗi định dạng bị từ chối; lỗi ghi index trả về thất bại và không bị báo là đã verify.

**Cổng nghiệm thu:** Có report, HTML, Markdown và ledger được tạo; tất cả hash tính lại được; sửa đổi bị phát hiện; public export không còn dữ liệu thô hoặc key material.

### Task 9 — Wazuh connector và doctor

**Các file:** `soc_investigator/connectors/wazuh.py`, `soc_investigator/doctor.py`, `docs/deployment/permissions.md`, `lab/wazuh/roles/`, `tests/unit/test_wazuh_connector.py`, `tests/integration/test_wazuh_connector.py`, `tests/unit/test_doctor.py`.

**Triển khai:**
- Kết nối OpenSearch qua TLS/auth.
- Tự khám phá index pattern thực tế thay vì giả định chỉ có một tên index cụ thể.
- Chỉ đọc alerts và archives. Chỉ ghi investigation vào `ai-investigations-*`.
- Phân trang bằng `search_after` với stable sort có unique tie-breaker. Không dùng `from/size` để phân trang sâu.
- Ánh xạ field Sysmon thực tế của Wazuh sang hợp đồng `Event` đã chuẩn hóa ở Task 1. Đưa một fixture mẫu thực tế từ archive (đã làm sạch dữ liệu nhạy cảm) vào test.
- Bảy nhóm kiểm tra của doctor: kết nối; role tối thiểu chính xác; khám phá index; archives + dữ liệu Sysmon gần đây + cảnh báo decode `DestinationHostname`; truy vấn mẫu và số lượng/độ trễ trong 24 giờ; kiểm tra provider theo cấu hình; tạo/kiểm tra an toàn `.env` (khuyến nghị `0600` và cảnh báo `.gitignore`).
- Role thiếu quyền là FAIL; quyền vượt mức là WARN; không bao giờ in giá trị bí mật.

**Kiểm thử:** TLS/auth thành công và thất bại; index pattern được khám phá; đọc alert/archive được phép; không thể ghi/cập nhật/xóa source index; ghi được tool-owned index; overprivilege là WARN; thiếu privilege là FAIL; thiếu archives là FAIL kèm hướng dẫn sửa; không có dữ liệu gần đây tạo warning/failure theo chính sách doctor; thiếu `DestinationHostname` phải cảnh báo; cursor `search_after` tiếp tục qua hơn 10.000 record mà không mất/trùng record; `.env` không bị in ra, permission không an toàn thì cảnh báo, thiếu entry `.gitignore` thì cảnh báo.

**Cổng nghiệm thu:** Connector thực hiện được một lượt điều tra live chỉ đọc trong môi trường Wazuh kiểm thử và chỉ ghi vào index do công cụ sở hữu.

### Task 10 — CLI orchestration, smoke và eval

**Các file:** `soc_investigator/cli.py`, `soc_investigator/smoke.py`, `soc_investigator/eval/runner.py`, `eval/run_eval.py`, `eval/golden/office-interpreter-execution-v1.yaml`, `lab-data/smoke-model-answer.json`, `tests/integration/test_cli_replay.py`, `tests/integration/test_smoke.py`, `tests/integration/test_eval.py`.

**Triển khai:**
- Kết nối tám bước của pipeline điều tra, sử dụng typed error và mã thoát đã quy định.
- Hỗ trợ `investigate --alert <id>` và `investigate --replay <file>`; replay đi qua FileConnector nhưng các bước còn lại dùng chung pipeline.
- `smoke` mặc định dùng FakeProvider và kiểm tra từng khẳng định trong đặc tả; `--live-model` là tùy chọn, chạy thủ công.
- `eval` đọc các cặp NDJSON + golden file từ `eval/golden/`; mã runtime không được import hoặc đọc golden truth.
- Chỉ số eval: schema validity; technique precision/recall chỉ tính cho technique `observable: true`; IoC precision; citation validity trước validator lấy từ draft trong ledger; số hallucination/claim bị loại; latency và tokens. Không đặt ngưỡng chất lượng phát hành cho model 3B; phải báo cáo giới hạn đo được và cỡ mẫu n=1.
- `verify` chọn đúng chế độ xác minh local hoặc live.
- `export --public` gọi public exporter.
- Giữ `install` và `config` tối giản, nhất quán với đặc tả hiện tại; không lệnh nào được cài đặt/thay đổi SIEM hoặc âm thầm provision hạ tầng.

**Kiểm thử:** Scenario không xác định trả mã riêng và thông báo rõ; pack không hợp lệ trả mã khác; provider hết retry trả provider code; replay tạo report + ledger; luồng live dùng Wazuh connector; smoke thất bại nếu report rỗng, schema sai, citation sai, số claim bị loại quá nhiều (>50%), snapshot hash sai hoặc thiếu ledger; smoke thành công với fixture FakeProvider hợp lệ; eval loại T1566.001 khỏi observable recall; runtime không đọc golden truth; CLI public export; verify replay nêu rõ không có index độc lập.

**Cổng nghiệm thu:** `soc-investigator smoke` chạy thành công trong CI runner sạch, không cần dịch vụ bên ngoài.

### Task 11 — Lab vật lý, khả năng tái lập và tài liệu phát hành

**Các file:** `docker-compose.yml`, `lab/wazuh/docker-compose.yml`, `lab/wazuh/`, `lab/simulate.sh`, `lab/versions.yml`, `lab-data/phish-case-01.ndjson`, `dashboards/ai-investigations.ndjson`, `docs/ARCHITECTURE.md`, `docs/SECURITY.md`, `docs/LIMITATIONS.md`, `docs/MODEL_SELECTION.md`, `docs/deployment/wazuh-ollama.md`, `NOTICE.md`, `LICENSE`, `README.md`.

**Triển khai theo hai pha sử dụng tài nguyên:**
- **Pha A — thu thập:** Wazuh + Windows VM + Sysmon + Wazuh agent; tắt Ollama. Chạy mô phỏng có kiểm soát; export và làm sạch NDJSON; lưu đầu vào có thể tái lập.
- **Pha B — điều tra:** tắt Wazuh/Windows VM; khởi động Ollama; replay NDJSON đã đóng băng. Cách này tránh để Wazuh, VM và model cùng tranh chấp tài nguyên trên máy RAM 16 GB.

**Phạm vi kiểm thử lab:** Wazuh custom rule `100110` trên Sysmon EID 1 khi ứng dụng Office tạo tiến trình thông dịch script; cấu hình Sysmon 15.0+ bao gồm filter EID 22; bật archives và cảnh báo rõ về lưu trữ/retention; `lab/simulate.sh` nối chuỗi Office → interpreter vì ba Atomic test riêng lẻ không tự tạo quan hệ cha-con này. Ghim phiên bản và checksum model. Tự viết compose/config; không sao chép file Wazuh Docker có giấy phép GPLv2.

**Kiểm thử thủ công trước phát hành:**
- Dựng lại lab từ các phiên bản đã ghim trên một host sạch.
- Chạy mô phỏng và xác nhận alert `100110` xuất hiện trong alerts, evidence EID 1/3/11 kỳ vọng xuất hiện trong archives.
- Export `phish-case-01.ndjson`; replay nhiều hơn một lần và so sánh ngữ nghĩa điều tra giữa các lần chạy.
- Chạy Ollama smoke live. Nếu có Anthropic key, chạy một lượt so sánh đã che dữ liệu theo tùy chọn và ghi usage/chi phí thực tế.
- Import dashboard NDJSON và xác nhận giao diện xem report sử dụng được.
- Kiểm tra toàn bộ tài liệu, license/provenance, không commit `.env`/reports và không commit model file.

**Cổng nghiệm thu:** Demo replay sạch chạy được mà không cần lab live; video/report đã ghi sẵn là phương án dự phòng khi demo live thất bại.

---

## 3. Chiến lược kiểm thử và hợp đồng dữ liệu kiểm thử

### Các tầng kiểm thử

| Tầng | Chứng minh điều gì | Phụ thuộc khi chạy / trong CI |
|---|---|---|
| Unit | Model, kiểm định pack, correlator, redaction, prompt guard, provider adapter, validator, logic hash/report | Chỉ cần Python cục bộ; fixture tất định |
| Integration — replay | Toàn bộ luồng điều tra và đầu ra CLI | Chỉ FileConnector + FakeProvider |
| Security regression | Prompt injection, rò rỉ secret, giả mạo citation, XSS, rò rỉ public export, ranh giới RBAC | Fixture kiểm thử tất định; index Wazuh kiểm thử tách biệt cho RBAC |
| Live integration | Wazuh API, quyền role, Sysmon ingestion, archives, Ollama/Anthropic | Chạy thủ công hoặc trước phát hành; không bao giờ là điều kiện CI thông thường |
| Evaluation | Chất lượng đầu ra model trên golden case cố định | Cùng NDJSON đã đóng băng; ghi metric; không coi n=1 là benchmark |

### Bộ dữ liệu chuẩn

1. **`lab-data/sample-mini.ndjson`** — fixture tất định tự dựng, khoảng 100 OpenSearch hit record. Phải có một alert rule `100110` và chuỗi tối thiểu Office → PowerShell → child-process; Sysmon EID 11 cho `invoice.exe`; EID 3 tới `cdn-update.example` và TEST-NET IP `203.0.113.10`; EID 11 trùng lặp cùng host/path/mtime; một tiến trình không liên quan; một event nằm ngoài lookback window; và một ca PID reuse (cùng PID nhưng khác ProcessGuid). Không đưa domain thật, IP khách hàng công khai hoặc credential vào fixture.
2. **`lab-data/phish-case-01.ndjson`** — bản export đã làm sạch dữ liệu nhạy cảm từ Wazuh lab được kiểm soát. Đây là đầu vào tham chiếu cho replay/eval và phải giữ metadata event/index/document cần thiết để tái tạo `raw_ref`.
3. **`lab-data/smoke-model-answer.json`** — fixture response cố định, hợp lệ, lấy từ một lần chạy model thành công đã được rà soát. Phải có facts, câu trả lời checklist, citations, playbook status và ít nhất một recommendation đại diện. Không được là response rỗng/tối giản khiến pipeline hỏng vẫn vượt qua.
4. **`eval/golden/office-interpreter-execution-v1.yaml`** — tách khỏi runtime. Các technique `T1204.002`, `T1059`, `T1071.001` là observable; `T1566.001` không observable trong lab này; IoC gồm `cdn-update.example` và `invoice.exe`; expected facts phải khớp đặc tả.
5. **`tests/fixtures/`** — các fixture biến thể nhỏ cho trường hợp thiếu network, zero core telemetry, NDJSON lỗi, prompt injection, redaction, budget overflow và model output đối kháng. Không nhân bản toàn bộ fixture 100 event cho từng test; hãy tạo fixture nhỏ theo mục tiêu hoặc fixture builder.

### Ma trận kịch bản kiểm thử

| ID | Kịch bản / đầu vào | Kết quả kỳ vọng (các assertion) |
|---|---|---|
| DATA-01 | Mẫu cơ sở có rule 100110, Office → PowerShell, EID 11 và EID 3 | Chọn đúng alert; evidence bundle có process, file và network evidence với raw reference hợp lệ. |
| DATA-02 | PID được tiến trình mới sử dụng lại nhưng ProcessGuid khác | Tiến trình mới không gắn vào parent cũ; không có cạnh cây sai do dùng PID. |
| DATA-03 | Hai record EID 11 cùng host/path/mtime | Sau khử trùng lặp chỉ còn một file-change evidence item. |
| DATA-04 | EID 11 cùng path nhưng mtime khác, hoặc path khác | Cả hai file change riêng biệt đều được giữ lại. |
| DATA-05 | Event nằm ngoài cửa sổ 30 phút | Bị loại khỏi bundle và số đếm. |
| DATA-06 | Event ở host khác hoặc network event của tiến trình không liên quan | Bị loại khỏi điều tra host/process tree hiện tại. |
| DATA-07 | `DestinationHostname` bị thiếu trong archive mapping | Doctor cảnh báo; correlation không được âm thầm tuyên bố đã quan sát được domain. |
| DATA-08 | Có hơn 10.000 archive record khớp | `search_after` lấy đủ mọi trang, không trùng và không cắt cụt im lặng. |
| GAP-01 | Không có DNS EID 22 và pack khai báo `dns_query` là blind | Điều tra vẫn hoàn thành; `dns_query` nằm trong `declared_blind`, không nằm trong `abnormal_absences`. |
| GAP-02 | Pack yêu cầu network event nhưng EID 3 có số đếm bằng 0 | Điều tra vẫn hoàn thành; `network=0` nằm trong abnormal absence, kèm các khả năng giải thích trung lập. |
| GAP-03 | Tất cả evidence type được query đều trả về 0 | Report và ledger vẫn được tạo; mọi số 0 đều tường minh; không suy diễn thành kết luận “pass/clean”. |
| GAP-04 | Không cấu hình mail gateway data | Hiển thị declared data gap cùng `would_enable`; công cụ không đánh dấu đây là lỗi thu thập. |
| PACK-01 | Pack hợp lệ có include và đủ mọi coverage list | Nạp thành công sau khi ghép include. |
| PACK-02 | Thiếu coverage hoặc thiếu một trong ba list | Pack bị từ chối với exit 11 và chỉ rõ field lỗi. |
| PACK-03 | Checklist hỏi evidence type không có trong correlation pivot | Pack bị từ chối trước khi chạy connector/provider. |
| PACK-04 | Câu hỏi mở, thiếu ID hoặc `evidence_types` rỗng | Pack bị từ chối và chỉ rõ đường dẫn item lỗi. |
| PACK-05 | Tactic tầng C không có question cũng không có blind reason | Pack bị từ chối. |
| PACK-06 | Thiếu playbook, thiếu include, include cycle hoặc include path traversal | Pack bị từ chối; không file nào bên ngoài root được nạp. |
| BUDGET-01 | Có hơn 40 evidence item hoặc token ước lượng vượt 6.000 | Degradation theo thứ tự ưu tiên; giữ root chain, IoC và evidence ATT&CK chính; các phần bị loại được báo cáo. |
| PROMPT-01 | Log field chứa `ignore all previous instructions` | Nội dung vẫn được coi là evidence không đáng tin cậy; system instruction vẫn tách biệt và có hiệu lực. |
| PROMPT-02 | Prompt builder nhận event có field chỉ tồn tại trong raw | Prompt không chứa raw event JSON; guard từ chối nếu raw material lọt vào. |
| REDACT-01 | `alice`, `C:\Users\alice\AppData\Local\Temp\invoice.exe`, `10.10.10.20`, `alice@example.test` | Username/username trong path, private IP và email được thay; raw value không xuất hiện trong prompt gửi từ xa. |
| REDACT-02 | Cùng một định danh xuất hiện trong nhiều evidence record | Cùng placeholder được tái sử dụng nhất quán trong một investigation. |
| REDACT-03 | Anthropic từ xa + redaction bị cấu hình tắt | Cấu hình bị từ chối/ép bật; không có API request nào được gửi kèm giá trị gốc. |
| REDACT-04 | Ollama cục bộ không override / explicit opt-out | Mặc định có che; cho phép opt-out tường minh tại local. |
| PROVIDER-01 | Structured JSON hợp lệ | Trả về object đã parse; attempts count bằng một. |
| PROVIDER-02 | JSON lỗi, sau đó JSON hợp lệ | Retry request kèm chẩn đoán lỗi có cấu trúc; lần gọi thứ hai thành công. |
| PROVIDER-03 | Ba response đều sai định dạng | Đúng ba lần gọi tổng cộng (lần đầu + hai retry), trả lỗi có kiểu và ghi lại đủ mọi lần thử. |
| PROVIDER-04 | Đã cấu hình API key | Key không bao giờ được in trong CLI, doctor output hoặc ledger. |
| VAL-01 | Fact tham chiếu E01 đang tồn tại | Citation được chấp nhận. |
| VAL-02 | Fact tham chiếu E99 không tồn tại | Claim bị loại hoặc đánh dấu unverified; validator action được ghi lại. |
| VAL-03 | Citation tồn tại nhưng ghi `good.example`, model khẳng định `cdn-update.example` | Kiểm tra thực thể mức 1 từ chối/đánh dấu unverified. |
| VAL-04 | Model bịa IP, process, file path, hash, timestamp hoặc số không có trong evidence được trích | Claim bị từ chối/đánh dấu unverified. |
| VAL-05 | Process name đúng nhưng khác chữ hoa/thường hoặc path đã chuẩn hóa | Được chấp nhận sau chuẩn hóa an toàn; trường hợp từ chối sai được đếm. |
| VAL-06 | `technique_id` không nằm trong retriever whitelist | Bị từ chối ngay cả khi tồn tại trong golden truth. |
| VAL-07 | Checklist `confirmed`/`refuted` nhưng không có citation hợp lệ | Bị từ chối. |
| VAL-08 | Checklist `inconclusive` không có reason hoặc missing-data link | Bị từ chối. |
| VAL-09 | Checklist state ngoài ba giá trị cho phép hoặc item bị trùng | Bị từ chối. |
| VAL-10 | Playbook `unanswered` hoặc `out_of_scope` không có reason | Bị từ chối; playbook không bao giờ được coi là citation evidence. |
| REPORT-01 | Đầu ra cơ sở | JSON khớp schema 0.2.6; facts/checklist/hypotheses tách biệt; snapshot chỉ chứa event được trích dẫn. |
| REPORT-02 | Thay đổi một event trong snapshot nhưng không đổi hash | Local verify thất bại và xác định artifact bị hỏng. |
| REPORT-03 | Thay đổi prompt trong ledger nhưng không cập nhật prompt hash | Verify thất bại. |
| REPORT-04 | Live index lưu bundle/ledger hash khác | Live verify thất bại. |
| REPORT-05 | Verify report replay | Kiểm tra hash nội bộ và nói rõ không có index độc lập. |
| REPORT-06 | Có declared gap, abnormal absence và playbook step unanswered | Mỗi loại tạo đúng phần/recommendation source trong report; không tạo citation giả cho recommendation bắt nguồn từ playbook. |
| REPORT-07 | Public export | Không có raw snapshot value, ledger và redaction map; giữ placeholder an toàn cùng event ID/hash. |
| SEC-01 | HTML field chứa `<script>`, thuộc tính event-handler và link độc hại | HTML render escape payload; có CSP meta; không có payload thực thi được. |
| SEC-02 | Alert ID chứa `../` hoặc dấu phân cách đường dẫn | Bị từ chối hoặc ánh xạ an toàn thành tên file không traversal; không thể ghi ra ngoài thư mục reports. |
| RBAC-01 | Tool credential đọc source index và ghi tool index | Được phép. |
| RBAC-02 | Tool credential thử update/delete source index hoặc ghi index không liên quan | Bị từ chối; dữ liệu nguồn không thay đổi. |
| DOCTOR-01 | Có đủ connectivity/index/provider/permission bắt buộc | Bảy nhóm kiểm tra doctor báo PASS. |
| DOCTOR-02 | Tool role thiếu quyền | FAIL và exit code khác 0, chỉ rõ quyền còn thiếu. |
| DOCTOR-03 | Có quyền dư | WARN, không phải FAIL, và chỉ ra đúng loại quyền vượt mức. |
| DOCTOR-04 | `.env` có mode quá rộng hoặc thiếu trong `.gitignore` | WARN; tuyệt đối không in giá trị key. |
| CLI-01 | Alert không khớp scenario pack đã cài | Exit code riêng và thông báo rõ; không crash/không tạo report rỗng. |
| CLI-02 | Pack không hợp lệ | Exit 11; không gọi provider. |
| CLI-03 | Provider thất bại sau retry | Provider exit code; không tạo báo cáo thành công giả. |
| SMOKE-01 | Sample hợp lệ + FakeProvider | Mọi smoke assertion đều PASS; exit 0. |
| SMOKE-02 | Fake response tạo report rỗng hoặc validator loại hơn 50% claim | Smoke FAIL và exit khác 0; xác định khâu gây lỗi. |
| SMOKE-03 | Snapshot/hash/ledger/citation check thất bại | Smoke FAIL; không bao giờ báo thành công chỉ vì file đầu ra tồn tại. |
| EVAL-01 | Golden case `phish-case-01` | Xuất metrics; loại `T1566.001` khỏi observable recall; công bố cỡ mẫu n=1. |
| EVAL-02 | Golden file bị di chuyển/không tồn tại ở runtime path | Điều tra runtime vẫn chạy; chỉ lệnh eval đọc golden truth. |

---

## 4. Cổng nghiệm thu và tiêu chí phát hành

| Cổng | Điều kiện bắt buộc trước khi chuyển tiếp |
|---|---|
| G0 — contracts | Data model chuẩn hóa, cấu trúc NDJSON fixture, đường dẫn config, mô hình lỗi và cách canonicalize hash đã được thống nhất và ghi tài liệu. |
| G1 — nền tảng offline | `FileConnector` đọc được sample tất định; không cần Docker, SIEM hoặc LLM. |
| G2 — lõi điều tra | Pack hợp lệ được nạp; correlator tạo bundle ổn định; data gap và loại dữ liệu có số đếm 0 được biểu diễn chính xác. |
| G3 — ranh giới AI | Prompt chỉ chứa evidence đã cô đọng; redaction từ xa là bắt buộc; retry và usage của provider có thể kiểm toán. |
| G4 — tính toàn vẹn báo cáo | Validator bắt được citation/entity sai; snapshot, ledger, local verify và public export vượt qua security test. |
| G5 — demo CI | `soc-investigator smoke` chạy thành công với FakeProvider trên runner sạch; `ruff` và toàn bộ `pytest` đều PASS. |
| G6 — tích hợp Wazuh | Doctor kiểm tra môi trường thực; live connector chỉ đọc source index và chỉ ghi `ai-investigations-*`; đã test phân trang sâu. |
| G7 — phát hành có thể tái lập | Lab được ghim phiên bản và tái lập được; có NDJSON đã làm sạch, dashboard import, tài liệu, ghi chú model và thông tin nguồn gốc giấy phép. |

### Các lệnh CI

Chạy trong mỗi pull request/commit:

```bash
ruff check .
ruff format --check .
pytest -q
soc-investigator smoke
```

Nếu dự án dùng tên lệnh đã cài khác, hãy cập nhật lệnh một lần trong `pyproject.toml`/README và giữ nhất quán. Không yêu cầu CI tải Ollama model hoặc gọi Anthropic.

### Các lệnh thủ công trước phát hành

```bash
soc-investigator doctor
soc-investigator smoke --live-model
soc-investigator investigate --replay lab-data/phish-case-01.ndjson
soc-investigator verify reports/<alert_id>.json
soc-investigator eval
```

Nếu có Anthropic key, thực hiện một lượt so sánh từ xa tùy chọn trên cùng fixture đã đóng băng; xác nhận redaction trong prompt thực tế gửi đi/ledger và ghi usage/chi phí thực tế. Đây chỉ là số liệu tham chiếu, không phải cổng chất lượng model.

---

## 5. Những quyết định AI không được tự ý đoán

Đặc tả đã chi tiết, nhưng các hợp đồng triển khai sau chưa được chốt hoàn toàn. Hãy giải quyết bằng một ADR ngắn hoặc ghi chú PR tường minh trước khi viết code phụ thuộc vào chúng. Các mặc định đề xuất bên dưới nhằm giảm trao đổi qua lại.

1. **NDJSON envelope và Wazuh field mapping.** Mặc định đề xuất: mỗi dòng là OpenSearch hit (`_index`, `_id`, `_source`); xác nhận field path từ bản export Wazuh thật đã làm sạch và chuẩn hóa trong connector. Không tự nghĩ ra field path.
2. **Chọn alert khi replay.** Mặc định đề xuất: fixture chứa một alert; nếu nhiều alert ứng viên khớp mà không có alert selector thì trả lỗi “ambiguous replay input”, không âm thầm chọn alert đầu tiên.
3. **Cách tuần tự hóa hash chuẩn.** Mặc định đề xuất: canonical UTF-8 JSON, key được sắp xếp và separator cố định; writer và verifier phải dùng chính xác cùng serializer.
4. **Đặt tên/idempotency khi điều tra lặp lại.** Đặc tả đặt tên report/ledger/map theo `alert_id` nhưng cũng cam kết có ledger kiểm toán cho mỗi lần chạy. Cần quyết định lần chạy tiếp theo thay thế artifact cũ hay có run identifier; ghi rõ trước khi triển khai report writer.
5. **Ghi report thất bại một phần.** File local và OpenSearch index không thể dùng chung một transaction. Mặc định đề xuất: ghi local vào file tạm, promote artifact local theo cách atomic, ghi document vào index độc lập, và trả lỗi kèm hướng dẫn khôi phục nếu ghi index thất bại. Không bao giờ in PASS khi thao tác chưa hoàn tất.
6. **Ngữ nghĩa của “live và replay giống hệt nhau”.** Đặc tả đồng thời yêu cầu `meta.mode` khác nhau (`live` và `replay`). Hãy coi nội dung/ngữ nghĩa evidence của hai chế độ là tương đương; test các trường sau khi chuẩn hóa mode, generated time và raw reference phụ thuộc connector. Không yêu cầu toàn bộ report giống nhau từng byte.
7. **Hành vi `install` và `config`.** Các lệnh này được liệt kê nhưng chưa đặc tả đủ. Giữ chúng ở phạm vi bootstrap/config validation cục bộ và tài liệu; không biến thành trình cài SIEM hoặc công cụ provision hạ tầng hoàn chỉnh.
8. **Event lỗi/mapping một phần.** Mặc định đề xuất: từ chối NDJSON envelope sai định dạng; chấp nhận event thiếu các field tùy chọn chưa map nhưng ghi số lượng/cảnh báo. Không bao giờ âm thầm tuyên bố một loại telemetry chưa query/chưa map đã được kiểm tra.
9. **Ngữ nghĩa của anomalous absence.** Suy ra các loại evidence kỳ vọng từ pivot thực tế của pack đang chạy, không dùng danh sách global hard-code. Loại dữ liệu nằm trong declared blind không phải anomalous; pivot đã query nhưng trả 0 phải được báo là anomalous absence, tuyệt đối không coi là bằng chứng hoạt động lành tính.
10. **Giới hạn của đối chiếu thực thể mức 1.** Chỉ gắn nhãn “machine checked” khi thực thể sau chuẩn hóa xuất hiện trong evidence được trích dẫn. Không tuyên bố việc này chứng minh quan hệ ngữ nghĩa hoặc tính độc hại; đặc tả nói rõ đây không phải bằng chứng sự thật.
11. **Ghép include và ID trùng lặp.** Mặc định đề xuất: ghép các file tier dùng chung trước khi kiểm định; từ chối checklist ID trùng và định nghĩa xung đột thay vì âm thầm chọn một bản ghi đè.
12. **Metric expected-facts trong golden.** Golden file mẫu có `expected_facts`, nhưng đặc tả không định nghĩa công thức chấm điểm ngữ nghĩa tự động. Giữ chúng làm mục tiêu để con người rà soát, trừ khi có rubric chấm điểm được con người review; không tự nghĩ ra phép chấm text-match thiếu tin cậy.

---

## 6. Trọng tâm review — năm khoảng trống có rủi ro cao nhất

1. **Sai khác Wazuh field path / thiếu `DestinationHostname`:** xác nhận mapping từ export thật đã làm sạch; cảnh báo phải xuất hiện trước khi diễn giải correlation có kết quả bằng 0.
2. **Sai định danh tiến trình do PID reuse:** test phải chứng minh mọi cạnh trong process tree sử dụng ProcessGuid trên cùng host.
3. **Telemetry thiếu vắng âm thầm:** nguồn blind đã khai báo và nguồn đã query nhưng trả 0 tuyệt đối không được nhập làm một; cả hai trường hợp đều không được chặn tiến trình chạy.
4. **Niềm tin sai do citation:** test các xung đột nội dung thật (evidence ID hợp lệ nhưng sai domain/process/path/IP), không chỉ test evidence ID không tồn tại.
5. **Rò rỉ dữ liệu / render không an toàn:** test remote redaction, loại raw event, secret guard, map riêng mode 0600, public export loại bỏ dữ liệu nhạy cảm và escape XSS.

## 7. Định nghĩa hoàn tất cuối cùng

- Mọi thành phần trong phạm vi đều có unit test và pipeline replay có integration test.
- Có bằng chứng TDD cho các hành vi quan trọng: test đã được quan sát thất bại trước khi triển khai phần code tương ứng.
- Toàn bộ `pytest`, `ruff check`, `ruff format --check` và FakeProvider smoke đều PASS trong môi trường sạch.
- Tất cả test scenario bắt buộc ở trên được tự động hóa hoặc đánh dấu thủ công rõ ràng, kèm bằng chứng đã chạy.
- Credential của tool không thể ghi vào bất kỳ source SIEM index nào; không có hành động phản ứng trong code path.
- Đầu ra live/replay tương đương về ngữ nghĩa trên cùng fixture, chỉ cho phép khác biệt metadata/connector đã khai báo.
- `SECURITY.md`, `LIMITATIONS.md`, `MODEL_SELECTION.md`, `ARCHITECTURE.md`, deployment recipe và `NOTICE.md` mô tả trung thực hành vi và giới hạn.
- Không đưa ra tuyên bố chất lượng model từ một golden case duy nhất; phải ghi nhận latency, số lần retry, citation rate trước validator và false-rejection rate đo được.

---

## 8. Chỉ thị khởi động để sao chép cho coding agent

> Đọc đầy đủ `soc-investigator-spec-final.md` v0.2.6 và kế hoạch triển khai/kiểm thử này trước khi thay đổi file. Coi spec là nguồn yêu cầu có thẩm quyền và tài liệu kế hoạch này là trình tự triển khai. Làm theo hướng replay-first; không bắt đầu dựng Docker/Wazuh lab trước khi pipeline offline đạt trạng thái xanh. Mỗi lần chỉ triển khai một task. Với mỗi hành vi, trước tiên viết một pytest test tập trung, chạy và xác nhận test thất bại đúng nguyên nhân dự kiến, sau đó mới viết code tối thiểu và chạy lại test. Sau mỗi task, chạy test mục tiêu, toàn bộ pytest, ruff và FakeProvider smoke khi có thể. Không bỏ qua, làm yếu đi hoặc xóa test chỉ để build vượt qua. Không thêm tính năng ngoài phạm vi. Không đoán Wazuh field path: kiểm tra một bản export thật đã làm sạch và ghi lại mapping. Không bao giờ chuyển raw SIEM event cho LLM, không bao giờ cho phép tắt redaction từ xa, không bao giờ ghi vào source SIEM index và không bao giờ tuyên bố thành công nếu chưa có output lệnh kiểm chứng mới. Bắt đầu bằng cách chỉ hoàn thành **Task 0**, sau đó báo cáo các file đã thay đổi, lệnh đã chạy, kết quả test chính xác, quyết định còn bỏ ngỏ và task kế tiếp; không âm thầm triển khai toàn bộ kế hoạch trong một lượt.
