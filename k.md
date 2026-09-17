# Interview-Related AI Model Benchmark

## 1. Interview Criteria Generation

This functionality generates the six most important interview evaluation criteria from the job title, company introduction, job description, responsibilities, and requirements. Production requires exactly six criteria, each with a concise 1–5 word name and a percentage weight, with all weights summing to 100%. :contentReference[oaicite:0]{index=0}

For this benchmark, a fixed **Senior Software Engineer** job was used. The role emphasized scalable/distributed backend systems, Java/Python, cloud platforms, APIs/databases, production reliability, technical leadership, mentoring, and cross-functional collaboration. :contentReference[oaicite:1]{index=1}

A high-capability reference model (`GPT-6 Astra + High`) first generated a reference criteria set. The result was manually reviewed and approved before the benchmark, then frozen as the ground truth for this test case. :contentReference[oaicite:2]{index=2}

The approved ground truth was:

| Ground-Truth Criterion | Weight |
|---|---:|
| Distributed System Design | 25% |
| Java or Python Proficiency | 20% |
| Production Reliability and Performance | 20% |
| Technical Leadership and Delivery | 15% |
| Cloud and Backend Engineering | 10% |
| Mentorship and Cross-Functional Collaboration | 10% |

:contentReference[oaicite:3]{index=3}

Each model configuration was run 10 times. In addition to the production-format checks, candidate criteria were semantically matched against the approved ground truth using the same fixed high-capability judge.

The primary metrics were:

- **API / Parse Success:** whether a usable model response was returned and parsed correctly.
- **Exactly 6 Rate:** percentage of runs containing exactly six criteria.
- **Weight Sum = 100 Rate:** percentage of runs whose criterion weights summed to exactly 100%.
- **Concise Name Rate:** percentage of criteria satisfying the 1–5 word requirement.
- **Duplicate Rate:** duplicate criteria within the same generated set.
- **Ground Truth Coverage:** percentage of the six approved ground-truth concepts semantically represented by the generated criteria.
- **Ground Truth Weight MAE:** mean absolute difference between candidate weights and the corresponding ground-truth weights. Lower is better.
- **Pairwise Criteria Similarity:** lexical consistency between repeated runs. Higher indicates more stable naming, but does not measure semantic correctness. :contentReference[oaicite:4]{index=4}
- **Unique Normalized Names:** number of distinct criterion names produced across the 10 runs. Lower generally indicates more stable wording.
- **Latency / Reasoning Tokens / Cost:** operational efficiency.

### Results

| Model | Reasoning | API | Parse | Exactly 6 | Sum 100 | GT Coverage ↑ | Min GT Coverage ↑ | Weight MAE ↓ | Criteria Similarity ↑ | Unique Names ↓ | Avg Latency ↓ | P95 Latency ↓ | Avg Reasoning Tokens | Cost / 1K ↓ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| GPT-4o mini | N/A | 100% | 100% | 100% | 100% | 58.3% | 50.0% | 3.75 | 0.615 | 20 | 1.64s | 2.23s | 0 | $0.10 |
| GPT-5 | Low | 100% | 100% | 100% | 100% | 91.7% | 83.3% | **2.33** | 0.630 | 24 | 5.80s | 8.77s | 390 | $5.41 |
| **GPT-5** | **Medium (Baseline)** | **100%** | **100%** | **100%** | **100%** | **95.0%** | **83.3%** | **2.61** | **0.675** | **24** | **14.48s** | **21.09s** | **1,030** | **$11.69** |
| GPT-5 | High | 100% | 100% | 100% | 100% | **100.0%** | **100.0%** | 2.63 | 0.670 | 23 | 29.44s | 56.12s | 2,746 | $28.87 |
| GPT-5.6 Luna | Low | 100% | 100% | 100% | 100% | 80.0% | 66.7% | 2.60 | 0.561 | 24 | 5.26s | 6.37s | 50 | $0.22 |
| GPT-5.6 Luna | Medium | 100% | 100% | 100% | 100% | 78.3% | 66.7% | **2.23** | 0.599 | 27 | 4.73s | 5.53s | 86 | $0.26 |
| GPT-5.6 Luna | High | 100% | 100% | 100% | 100% | 85.0% | 66.7% | 2.93 | 0.622 | 23 | 5.30s | 7.61s | 128 | $0.31 |
| GPT-5.6 Terra | Low | 100% | 100% | 100% | 100% | 83.3% | 83.3% | 3.00 | **0.961** | 8 | **1.54s** | **1.94s** | 0 | $1.52 |
| GPT-5.6 Terra | Medium | 100% | 100% | 100% | 100% | 83.3% | 83.3% | 3.20 | 0.893 | 11 | 1.61s | 2.52s | 0 | $1.53 |
| GPT-5.6 Terra | High | 100% | 100% | 100% | 100% | 83.3% | 83.3% | 3.00 | 0.922 | 10 | 1.63s | 2.94s | 0 | $1.53 |
| GPT-5.6 Sol | Low | 100% | 100% | 100% | 100% | 83.3% | 83.3% | 2.96 | 0.941 | **7** | 1.80s | 2.30s | 0 | $2.81 |
| GPT-5.6 Sol | Medium | 100% | 100% | 100% | 100% | 88.3% | 83.3% | 2.49 | 0.746 | 15 | 2.97s | 4.13s | 48 | $3.82 |
| GPT-5.6 Sol | High | 100% | 100% | 100% | 100% | 90.0% | 83.3% | 2.67 | 0.726 | 16 | 3.21s | 3.70s | 70 | $4.26 |

### Result

All configurations satisfied the hard production requirements in all 10 runs: API success, parsing, six-criterion count, 100% weight sum, concise naming, and absence of duplicate criteria were all perfect. Therefore, the main differentiators were semantic coverage of the approved ground truth, consistency, latency, and cost.

`GPT-5 + High` achieved the strongest semantic quality, reaching **100% Ground Truth Coverage in every run**. However, this required approximately **29.4 seconds average latency**, **2,746 reasoning tokens**, and approximately **$28.87 per 1,000 requests**, making it substantially slower and more expensive than the current production configuration.

The current `GPT-5 + Medium` baseline remained strong, with **95.0% average Ground Truth Coverage**, but required approximately **14.5 seconds per request** and **$11.69 per 1,000 requests**.

`GPT-5 + Low` preserved most of the semantic quality at **91.7% average coverage**, while reducing average latency from **14.48s to 5.80s** and estimated cost from **$11.69 to $5.41 per 1,000 requests**. It also produced the lowest average ground-truth weight error among the GPT-5 configurations.

`GPT-5.6 Sol + High` achieved **90.0% average Ground Truth Coverage**, while reducing latency to approximately **3.21 seconds** and cost to approximately **$4.26 per 1,000 requests**. Its minimum coverage remained at 83.3%, meaning that at most one of the six approved criteria was missing in its weaker runs.

The Terra configurations were the most lexically stable: `GPT-5.6 Terra + Low` achieved a pairwise criteria similarity of **0.961** and generated only eight unique normalized criterion names. However, this high wording consistency did not translate into the highest semantic coverage; all Terra configurations remained at **83.3% Ground Truth Coverage**.

For production selection, **GPT-5 + Low is currently the strongest quality/cost compromise**. It preserves substantially more of the approved ground-truth criteria than Luna or Terra while cutting both latency and cost by more than half relative to the current GPT-5 + Medium baseline.

If maximum semantic coverage is the only priority, **GPT-5 + High** provides the strongest result. If lower latency and cost are given greater weight, **GPT-5.6 Sol + High** is a viable alternative with somewhat lower semantic coverage.
