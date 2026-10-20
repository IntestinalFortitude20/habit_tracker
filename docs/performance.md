# AI coach response-time baseline

## Reproducing the measurement

The benchmark sends 20 sequential, fixed prompts through the same configured
OpenAI-compatible chat completions endpoint used by the backend. It measures
the complete `call_llm` duration, from before the HTTP request until the full
reply has arrived. On this non-streaming implementation, TTFT (first visible
text) is therefore the same as total response time.

From `backend/`, configure the endpoint and model in `.env` (or as environment
variables), then run:

```bash
python -m scripts.benchmark_chat
```

For an Ollama baseline, pull `llama3.2:3b`, set
`LLM_BASE_URL=http://localhost:11434/v1`, `LLM_API_KEY=ollama`, and
`LLM_MODEL=llama3.2:3b`, then make sure the model is not already loaded before
starting the script. The first request is reported as cold (including model
loading if needed); the remaining requests are warm. Use
`python -m scripts.benchmark_chat --requests 20` to make the sample count
explicit. Percentiles use the nearest-rank method. Run with no competing
workloads and record whether the model was loaded before the benchmark.

## Results

| Model | Hardware / runtime | Cold median | Cold p95 | Warm median | Warm p95 | Requests |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| llama3.2:3b | Not measured: benchmark environment has no Ollama service/model | — | — | — | — | — |

The available task runner is a virtualized AMD EPYC 9V74 host (4 vCPUs,
approximately 15.6 GiB RAM); no Ollama service or GPU is available in this
environment. These are host details, not model benchmark results. No latency
values are reported because a real `llama3.2:3b` run could not be performed
here. Run the command above on the target hardware and replace this row with
the reported cold and warm values before making a before/after performance
claim.

## Streaming (after)

The coach reply is now streamed token by token from `POST /api/chat/stream`
(`text/event-stream`; `data: {"token": ...}` events, then `event: done`, or
`event: error` on a mid-stream failure). The non-streaming `POST /api/chat`
endpoint is unchanged. The chat modal can cancel a reply with the Stop button.

Measure TTFT and total time with the same prompts:

```bash
python -m scripts.benchmark_chat --stream --requests 20
```

| Mode | Cold TTFT | Warm TTFT median / p95 | Warm total median / p95 |
| --- | ---: | ---: | ---: |
| Before (non-streaming, baseline) | 8.054s | 26.950s / 35.120s | 26.950s / 35.120s |
| After (streaming) | Not measured | Not measured | Not measured |

The streaming numbers could not be recorded here because no Ollama service or
model is available in this environment. Run the command above on the baseline
hardware and fill in the "After" row.
