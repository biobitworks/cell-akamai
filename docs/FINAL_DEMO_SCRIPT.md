# Cell-Akamai — approximately three-minute walkthrough

Read at roughly 145 words/minute. Show only sanitized aggregates and source code. Confirm actual screen status before recording. No GPU traffic starts during this walkthrough.

## 0:00–0:30 — The problem
Show: dashboard “What we added to the workshop”, Problem card.

Cell-Akamai asks whether challenging an AI agent’s answer helps, and what that process costs. Scientific users need more than fluent responses: they need reproducible inputs, honest comparisons and evidence someone else can check. We extended the Akamai workshop into a framework for recording those comparisons, including negative results and missing measurements.

## 0:30–1:00 — Tech stack
Show: Tech stack card, then Strands bridge source.

We use Strands to separate actor, challenger, randomized control and adjudicator roles. Akamai provides GPU inference through vLLM serving Qwen3-4B. Python notebooks, tests and an OpenAI-compatible client connect the experiments to our evidence dashboard. A tool-free Strands call to Akamai succeeded. The full deployed agent workflow is not yet verified, and the measured comparison pilots used the plain client.

## 1:00–1:35 — What we added
Show: deterministic reconstruction, local/cloud and evidence-custody bullets.

Beyond the modules, we ran local Ollama Llama 3.2 3B and Akamai Qwen3-4B pilots using our evaluation harness. Because the models and hardware differ, these are observed comparisons, not proof of a platform advantage. We froze 32 synthetic cellular-automaton tasks and verified exact reconstruction across original records, content-addressed objects and graphs. Deterministic means those data transformations reproduce exactly; it does not mean the model answers are deterministic. These are paired representations, not independent biological datasets.

## 1:35–2:15 — First experiment: rate and rate change
Show: “First experiment · tokens/second/second” table. Highlight the formula, requests 2–4 and their reproduced values; then show throughput/latency axes.

Our first recorded experiment measured throughput and its change between sequential requests. Tokens per second is completion tokens divided by request duration. Tokens per second squared is the change in that rate divided by the time between request midpoints. We reproduced three recorded calculations exactly: approximately 0.1900, 0.00769 and 0.00554 tokens per second squared. These describe rate variation, not learning or individual-token acceleration. Separately, Module 7 reached about 269 output tokens per second at concurrency eight in a short run. The small scored agent panels returned zero correct answers; tokens per correct answer is therefore undefined.

## 2:15–2:45 — Code and controls
Show: strict parser, commitment checks, then module status.

Our tests cover strict answer parsing, commitment and coverage checks, and accounting for partial failures. Answers are committed before scoring; changed evidence must be refused. Some recovered archive answers currently fail that check and remain under reconciliation. Module 8 completed a short before-and-after tuning pilot with no demonstrated benefit. Module 9’s deployment failed at readiness; that is separate from its ECA execution. Software tests and infrastructure successes do not establish model improvement.

## 2:45–3:10 — Close
Show: contribution list and limits.

Our contribution is the combination: frozen records that reconstruct exactly across original, object and graph formats; role-separated agent comparisons; real local and Akamai inference; reproduced token-rate calculations; and evidence checked before scoring. The framework keeps successful measurements, nulls and negative findings inspectable. Next we extend these verified foundations with independent repeats, longer runs and complete checkpoint coverage.

## Recording rule

Anticube and ΔG* are omitted from the spoken demo because their numerical calculations have not yet been reconciled to this project’s experiment receipts. Do not imply they were never computed in other project work. The first experiment is EXP-AKAMAI-TOKEN-001; its derivative is sequential, not a concurrent-workload acceleration claim.
