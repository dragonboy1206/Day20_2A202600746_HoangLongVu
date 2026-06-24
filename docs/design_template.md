# Design Template

## Problem

Hệ thống research assistant cần trả lời câu hỏi nghiên cứu bằng cách phối hợp nhiều agent. Mỗi agent có vai trò riêng: tìm kiếm thông tin, phân tích, và viết câu trả lời. Single-agent không đủ vì prompt quá dài khi gộp tất cả responsibilities, dễ mất chất lượng output.

## Why multi-agent?

Single-agent phải vừa tìm kiếm vừa phân tích vừa viết trong một prompt duy nhất. Điều này dẫn đến:
- Prompt quá dài → LLM mất tập trung, giảm chất lượng
- Khó debug khi có lỗi → không biết bước nào sai
- Không thể retry từng bước riêng biệt

Multi-agent tách rõ trách nhiệm, mỗi agent tập trung vào một việc, dễ debug, dễ test, và có thể retry riêng từng bước.

## Agent roles

| Agent | Responsibility | Input | Output | Failure mode |
|---|---|---|---|---|
| Supervisor | Điều phối, chọn agent tiếp theo | State hiện tại | Route quyết định | Max iterations → stop |
| Researcher | Tìm kiếm, tạo research notes | Query | research_notes + sources | Retry 1 lần → skip, log error |
| Analyst | Phân tích research notes | research_notes | analysis_notes | Retry 1 lần → skip, log error |
| Writer | Viết câu trả lời cuối cùng | research + analysis | final_answer | Retry 1 lần → dùng raw output |

## Shared state

| Field | Type | Mục đích |
|---|---|---|
| request | ResearchQuery | Câu hỏi gốc + metadata (max_sources, audience) |
| iteration | int | Số lần supervisor đã chạy (limit: 6) |
| route_history | list[str] | Lịch sử routing để debug |
| sources | list[SourceDocument] | Nguồn tham khảo từ researcher |
| research_notes | str \| None | Ghi chú nghiên cứu từ researcher |
| analysis_notes | str \| None | Phân tích từ analyst |
| final_answer | str \| None | Câu trả lời cuối từ writer |
| agent_results | list[AgentResult] | Kết quả từng agent để trace |
| trace | list[dict] | Chi tiết trace: duration, tokens, errors |
| errors | list[str] | Danh sách lỗi xảy ra |

## Routing policy

```text
Câu hỏi người dùng
    │
    v
Supervisor (kiểm tra state)
    │
    ├─ research_notes is None? ──→ Researcher
    ├─ analysis_notes is None? ──→ Analyst
    ├─ final_answer is None? ──→ Writer
    └─ tất cả có rồi ──→ Done
```

Max iterations: 6 (3 vòng lặp hoàn chỉnh)

## Guardrails

- **Max iterations:** 6 (tránh vòng lặp vô hạn)
- **Timeout:** 60s per LLM call
- **Retry:** 1 lần khi LLM timeout/error
- **Fallback:** Skip agent nếu retry fail, log error, tiếp tục workflow
- **Validation:** Kiểm tra output không rỗng trước khi lưu vào state

## Benchmark plan

| Query | Metric | Expected |
|---|---|---|
| "Tóm tắt GraphRAG và viết câu trả lời ngắn gọn" | Latency | Multi-agent > Baseline (3-4x) |
| "Tóm tắt GraphRAG và viết câu trả lời ngắn gọn" | Tokens | Multi-agent > Baseline (3-4x) |
| "Tóm tắt GraphRAG và viết câu trả lời ngắn gọn" | Quality | Multi-agent ≥ Baseline |
| "Tóm tắt GraphRAG và viết câu trả lời ngắn gọn" | Citation coverage | Multi-agent > 0% |
