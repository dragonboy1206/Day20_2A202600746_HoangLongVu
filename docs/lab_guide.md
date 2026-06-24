# Hướng dẫn lab: Hệ thống nghiên cứu Multi-Agent với Ollama

## Bối cảnh

Bạn cần xây dựng một research assistant (trợ lý nghiên cứu - chương trình nhận câu hỏi, tìm thông tin, phân tích và viết câu trả lời). Lab yêu cầu so sánh hai cách làm:

1. **Single-agent baseline** (một tác tử làm toàn bộ): một agent tự xử lý từ đầu đến cuối.
2. **Multi-agent workflow** (luồng nhiều tác tử): Supervisor điều phối Researcher, Analyst và Writer.

Repo đã cấu hình mặc định để dùng **Ollama** (công cụ chạy mô hình AI cục bộ trên máy). Bạn không cần OpenAI API key.

## Cấu hình cần có

File `.env`:

```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:latest
```

Giải thích thuật ngữ:

- `LLM` (mô hình ngôn ngữ lớn): mô hình AI sinh văn bản.
- `Provider` (nhà cung cấp mô hình): nơi app gửi yêu cầu sinh câu trả lời. Ở đây là Ollama.
- `Base URL` (địa chỉ gốc): địa chỉ HTTP để app kết nối tới Ollama.
- `Model` (mô hình): tên mô hình cụ thể được Ollama chạy.

## Quy tắc quan trọng

- Không thêm agent nếu không có lý do rõ ràng.
- Mỗi agent phải có trách nhiệm riêng.
- Shared state (trạng thái dùng chung) phải đủ rõ để debug.
- Phải có log hoặc trace cho từng bước.
- Phải benchmark, không chỉ đánh giá output bằng cảm tính.

## Milestone 1: Baseline

File gợi ý:

- `src/multi_agent_research_lab/cli.py`
- `src/multi_agent_research_lab/services/llm_client.py`

Việc cần làm: thay baseline placeholder bằng một lần gọi `LLMClient`.

## Milestone 2: Supervisor

File gợi ý:

- `src/multi_agent_research_lab/agents/supervisor.py`
- `src/multi_agent_research_lab/graph/workflow.py`

Việc cần làm: triển khai routing policy (chính sách điều phối - quy tắc quyết định agent nào chạy tiếp).

Câu hỏi thiết kế:

- Khi nào gọi Researcher?
- Khi nào gọi Analyst?
- Khi nào gọi Writer?
- Khi nào dừng?
- Nếu agent lỗi thì retry (thử lại) hay fallback (chuyển sang phương án dự phòng)?

## Milestone 3: Worker agents

File gợi ý:

- `src/multi_agent_research_lab/agents/researcher.py`
- `src/multi_agent_research_lab/agents/analyst.py`
- `src/multi_agent_research_lab/agents/writer.py`

Việc cần làm: triển khai từng worker agent.

## Milestone 4: Trace và benchmark

File gợi ý:

- `src/multi_agent_research_lab/observability/tracing.py`
- `src/multi_agent_research_lab/evaluation/benchmark.py`
- `src/multi_agent_research_lab/evaluation/report.py`

Benchmark tối thiểu:

| Metric | Nghĩa | Cách đo gợi ý |
|---|---|---|
| Latency | độ trễ | đo thời gian chạy thực tế |
| Cost | chi phí | với Ollama local có thể ghi `0`, nhưng vẫn đo token |
| Quality | chất lượng | chấm theo rubric 0-10 |
| Citation coverage | độ phủ trích dẫn | số claim có nguồn / tổng claim chính |
| Failure rate | tỷ lệ lỗi | số query lỗi / tổng query |

## Exit ticket

Mỗi nhóm trả lời 2 câu:

1. Trường hợp nào nên dùng multi-agent? Vì sao?
2. Trường hợp nào không nên dùng multi-agent? Vì sao?
