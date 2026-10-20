## AI coach latency baseline (pre-streaming)

Date: 2026-10-19  
Model: `llama3.2:3b`  
Mode: non-streaming (`/api/chat`)  
Requests: 20 (first request = cold, remaining = warm)

### Results
- **Cold total** (n=1): median **8.054s**, p95 **8.054s**, min **8.054s**, max **8.054s**
- **Warm total** (n=19): median **26.950s**, p95 **35.120s**, min **3.968s**, max **35.120s**

### TTFT interpretation
In non-streaming mode, **TTFT equals total response time** because the UI displays text only after the full reply arrives.

### Notes
- Measured locally on developer machine with Ollama.
- This baseline is the “before” snapshot for comparison after streaming is implemented.