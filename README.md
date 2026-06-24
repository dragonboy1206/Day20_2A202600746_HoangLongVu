# Lab 20: Hệ thống nghiên cứu Multi-Agent chạy Ollama

Đây là repo starter cho bài lab **Multi-Agent Systems** (hệ thống nhiều tác tử - nhiều thành phần AI cùng phối hợp để giải quyết một nhiệm vụ). Dự án đã được cấu hình mặc định để dùng **Ollama** (công cụ chạy mô hình AI cục bộ trên máy), không cần OpenAI API key.

## Kiến trúc mục tiêu

```text
Câu hỏi người dùng
   |
   v
Supervisor / Router
   |------> Researcher Agent  -> research_notes
   |------> Analyst Agent     -> analysis_notes
   |------> Writer Agent      -> final_answer
   |
   v
Trace + Benchmark Report
```

Giải thích thuật ngữ:

- `Agent` (tác tử): một khối xử lý có vai trò riêng, ví dụ tìm kiếm, phân tích hoặc viết câu trả lời.
- `LLM` (mô hình ngôn ngữ lớn): mô hình AI có khả năng đọc, hiểu và sinh văn bản.
- `Ollama`: công cụ giúp tải và chạy LLM cục bộ trên máy của bạn.
- `Provider` (nhà cung cấp mô hình): nơi cung cấp mô hình AI. Trong repo này provider mặc định là `ollama`.
- `Editable install` (cài đặt dạng chỉnh sửa trực tiếp): cài project sao cho khi bạn sửa code trong thư mục này, Python dùng ngay code mới.

## Cài đặt

### 1. Cài Ollama

Tải Ollama tại:

```text
https://ollama.com/download
```

Sau khi cài xong, mở terminal và kiểm tra:

```bash
ollama --version
```

### 2. Tải model cục bộ

Model mặc định của dự án là `llama3.1:latest`, vì model này đang có sẵn trên máy hiện tại.

```bash
ollama pull llama3.1
```

Nếu máy yếu hoặc thiếu RAM, có thể đổi sang model nhẹ hơn trong `.env`, ví dụ:

```bash
OLLAMA_MODEL=llama3.2:1b
```

### 3. Bật server Ollama

Thông thường Ollama tự chạy nền. Nếu cần bật thủ công:

```bash
ollama serve
```

Kiểm tra server:

```bash
curl http://localhost:11434/api/tags
```

Nếu có JSON trả về là Ollama đã chạy.

### 4. Tạo môi trường Python

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

### 5. Cài project

```bash
python -m pip install -e ".[dev]"
```

Nếu cần cài thêm nhóm thư viện workflow:

```bash
python -m pip install -e ".[dev,llm]"
```

## Cấu hình Ollama

File `.env` đã được cấu hình sẵn:

```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:latest
```

Giải thích:

- `LLM_PROVIDER` (nhà cung cấp mô hình): chọn backend AI. Giá trị hiện tại là `ollama`.
- `OLLAMA_BASE_URL` (địa chỉ gốc Ollama): nơi app gửi request tới Ollama.
- `OLLAMA_MODEL` (tên mô hình Ollama): model sẽ được dùng khi gọi LLM.

## Chạy kiểm tra

```bash
pytest
ruff check src tests
mypy src
```

Hoặc dùng Makefile:

```bash
make test
make lint
make typecheck
```

## Chạy CLI

CLI (command-line interface - giao diện dòng lệnh) là cách chạy chương trình bằng terminal.

```bash
python -m multi_agent_research_lab.cli --help
```

Chạy baseline:

```bash
python -m multi_agent_research_lab.cli baseline \
  --query "Tóm tắt GraphRAG và viết câu trả lời ngắn gọn"
```

Chạy multi-agent skeleton:

```bash
python -m multi_agent_research_lab.cli multi-agent \
  --query "Tóm tắt GraphRAG và viết câu trả lời ngắn gọn"
```

Lưu ý: các agent chính vẫn là skeleton (khung bài tập). Nghĩa là workflow multi-agent vẫn có các `TODO(student)` để bạn tự triển khai logic.

## Gọi Ollama trong code

Client đã sẵn sàng tại:

```text
src/multi_agent_research_lab/services/llm_client.py
```

Ví dụ dùng nhanh:

```python
from multi_agent_research_lab.services.llm_client import LLMClient

client = LLMClient()
response = client.complete(
    system_prompt="Bạn là trợ lý AI trả lời bằng tiếng Việt.",
    user_prompt="Giải thích ngắn gọn Ollama là gì.",
)
print(response.content)
```

## Chạy bằng Docker

Khi chạy trong Docker, `localhost` là container chứ không phải máy host. Vì vậy Dockerfile dùng:

```bash
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

Build image:

```bash
docker build -t multi-agent-research-lab .
```

Chạy:

```bash
docker run --rm multi-agent-research-lab --help
```

## Cấu trúc repo

```text
src/multi_agent_research_lab/
  agents/              # Agent interfaces + skeletons
  core/                # Config, state, schemas, errors
  graph/               # Workflow skeleton
  services/            # LLM, search, storage clients
  evaluation/          # Benchmark/evaluation skeleton
  observability/       # Logging/tracing hooks
  cli.py               # CLI entrypoint
configs/               # Cấu hình YAML
docs/                  # Tài liệu lab
tests/                 # Unit tests
```

## TODO chính cho người học

1. Dùng `LLMClient` trong baseline hoặc agent.
2. Triển khai `ResearcherAgent`.
3. Triển khai `AnalystAgent`.
4. Triển khai `WriterAgent`.
5. Triển khai `MultiAgentWorkflow`.
6. Thêm benchmark report.
