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
## 2. Interview Questions Generation

This functionality generates six interview questions from the job information and a predefined set of interview criteria.

To isolate the performance of the question-generation model, the job input and interview criteria will remain fixed across all configurations. The criteria will be generated once and frozen before the benchmark. Only the question-generation model and reasoning level will change.

The production contract requires six concise interview questions and no additional explanatory text.

### Evaluation Metrics

The benchmark will evaluate:

- **API Success Rate**
- **Question Count Compliance:** whether exactly six non-empty questions are returned
- **Duplicate Question Rate:** whether multiple generated questions test substantially the same thing
- **Criteria Coverage:** percentage of the frozen interview criteria addressed by at least one generated question
- **Job Requirement Coverage:** whether the generated question set covers the major requirements of the target role
- **Question Relevance:** whether each question is relevant to the job and the corresponding criteria
- **Question Specificity:** whether questions are sufficiently concrete to obtain meaningful evidence from the candidate
- **Unsupported Assumption Rate:** whether a question incorrectly assumes candidate experience or facts that were not provided
- **Question Diversity:** whether the six questions examine sufficiently different dimensions rather than repeatedly asking similar questions
- **Average / P95 Latency**
- **Reasoning Tokens**
- **Estimated Cost**

### Implementation

A fixed job and fixed human-reviewed interview-criteria set will be used.

A high-capability model will produce a reference evaluation rubric rather than a single mandatory set of six questions. This rubric will define the expected areas that a good question set should cover.

Each candidate model will generate six questions repeatedly using exactly the same input.

A fixed high-capability judge will compare the generated question set against the approved rubric and evaluate criteria coverage, job relevance, specificity, duplication, and unsupported assumptions.

The final model recommendation will prioritize question quality and coverage first, followed by consistency, latency, and cost.


## 3. Resume-Based Interview Question Generation

This functionality generates approximately 2–3 candidate-specific interview questions based on both the job information and the candidate's resume.

Unlike general interview questions, the main purpose of this functionality is to identify valuable areas that require deeper investigation during the interview.

### Evaluation Metrics

- **API Success Rate**
- **2–3 Question Count Compliance**
- **Resume Grounding:** whether each question is supported by information contained in the resume
- **Job Relevance:** whether each question helps assess qualifications relevant to the target job
- **Gap Targeting:** whether questions investigate meaningful gaps, ambiguities, or important evidence in the resume
- **Unsupported Assumption Rate:** whether the question assumes experience or facts that are not present in the resume
- **Duplicate Question Rate**
- **Question Specificity**
- **Average / P95 Latency**
- **Reasoning Tokens**
- **Estimated Cost**

### Implementation

A fixed job and synthetic resume with explicitly known facts will be used.

A human-reviewed reference rubric will identify the most important resume areas that should be investigated during the interview.

Candidate models will generate 2–3 questions using identical job and resume inputs.

The generated questions will be evaluated against the approved reference areas, while unsupported assumptions will be detected separately.


## 4. Interview Evaluation

This functionality evaluates the candidate's actual interview responses using the job information and interview criteria.

The evaluator receives the job title, company information, job description, evaluation criteria, interview questions, follow-up questions, and candidate responses.

Because interview scoring is subjective, a fixed synthetic interview conversation will be created with deliberately strong, average, weak, irrelevant, and incomplete answers.

### Evaluation Metrics

- **API Success Rate**
- **Parse / Schema Success**
- **Ground-Truth Score Agreement**
- **Overall Score Error**
- **Per-Criterion Score Error**
- **Score Standard Deviation**
- **Score Range**
- **Evidence Grounding:** whether evaluation statements can be traced to actual candidate responses
- **Unsupported Evaluation Rate**
- **Cross-Run Evaluation Consistency**
- **Average / P95 Latency**
- **Reasoning Tokens**
- **Estimated Cost**

### Implementation

A high-capability model will first evaluate the fixed interview conversation.

The generated evaluation will then be manually reviewed and corrected where necessary. The human-approved evaluation will be frozen as the benchmark ground truth.

Every candidate model will receive the identical interview conversation and identical evaluation criteria.

Scores will be compared against the approved reference, while repeated runs will measure scoring stability.

This allows both accuracy relative to the approved evaluation and consistency across repeated executions to be measured.


## 5. Real-Time Interview Conversation

This functionality controls the live AI interviewer during the interview.

The model must interpret each candidate response, select the correct conversation state, generate an appropriate interviewer response, ask follow-up questions when necessary, return to the original interview sequence, handle candidate questions, redirect off-topic conversation, and correctly complete the interview.

### Evaluation Metrics

- **API / JSON / Schema Success**
- **Intent Classification Accuracy**
- **Conversation State Accuracy**
- **Question Order Compliance**
- **Follow-Up Decision Accuracy**
- **Return-to-Main-Question Compliance**
- **Candidate Question Handling Accuracy**
- **Off-Topic Recovery Accuracy**
- **Premature Interview Ending Rate**
- **All Questions Asked Rate**
- **Response Relevance**
- **Response Conciseness**
- **Per-Turn Average / P95 Latency**
- **Total Estimated Interview Cost**

### Implementation

A deterministic scripted candidate conversation will be created containing different interaction types, including:

1. Candidate introduction
2. Complete answer
3. Incomplete answer requiring follow-up
4. Irrelevant/off-topic response
5. Candidate asking the interviewer a question
6. Return from a follow-up to the original interview sequence
7. Completion of all required interview questions
8. Final Q&A and interview termination

For each scripted turn, the correct intent and expected conversation state will be manually defined in advance.

Every model configuration will run through the same conversation.

This creates deterministic ground truth for state-transition correctness while separately evaluating the quality of the generated interviewer text.

Model selection will prioritize correct conversation control and interview completion before latency and cost.
