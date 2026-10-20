## AI coach latency benchmark

Model: `llama3.2:3b`  
Requests: 20 (first request = cold, remaining = warm)

### Non-streaming baseline (before streaming)
- **Cold total** (n=1): median **8.054s**, p95 **8.054s**, min **8.054s**, max **8.054s**
- **Warm total** (n=19): median **26.950s**, p95 **35.120s**, min **3.968s**, max **35.120s**
- In non-streaming mode, TTFT equals total response time (text appears only after full reply).

### Streaming (after)
- **Cold TTFT** (n=1): median **11.241s**, p95 **11.241s**, min **11.241s**, max **11.241s**
- **Warm TTFT** (n=19): median **0.784s**, p95 **1.073s**, min **0.659s**, max **1.073s**
- **Cold total** (n=1): median **14.152s**, p95 **14.152s**, min **14.152s**, max **14.152s**
- **Warm total** (n=19): median **24.609s**, p95 **36.680s**, min **4.970s**, max **36.680s**

### Summary
- Warm **TTFT improved from ~26.950s to ~0.784s** (about **97% faster** first visible output).
- Warm total response time stayed in a similar range; streaming mainly improves perceived responsiveness.