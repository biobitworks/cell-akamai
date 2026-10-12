# Cell-Akamai — three-minute walkthrough

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

## 1:35–2:10 — Results and units
Show: actual scored panels, then throughput and latency.

The four arms compare a single answer, a voting proxy, a challenge and a randomized challenge control. Their call budgets differ. The small scored panels returned zero correct answers, so tokens per correct answer is undefined. That is a recorded negative result, not missing data. Separately, the original Module 7 short concurrency-eight run measured about 269 output tokens per second and 1,262 milliseconds p95 latency. We count tokens from usage, not streaming chunks. Tokens per second squared would measure throughput change over time; it is not ordinary throughput or a new unit.

## 2:10–2:40 — Code and controls
Show: strict parser, commitment checks, then module status.

Our tests cover strict answer parsing, commitment and coverage checks, and accounting for partial failures. Answers are committed before scoring; changed evidence must be refused. Some recovered archive answers currently fail that check and remain under reconciliation. Module 8 completed a short before-and-after tuning pilot with no demonstrated benefit. Module 9’s deployment failed at readiness; that is separate from its ECA execution. Software tests and infrastructure successes do not establish model improvement.

## 2:40–3:00 — Close
Show: contribution list and limits.

Our success is a working foundation for accountable scientific agents: owned inference, local and cloud pilots, reproducible data and inspectable evidence. We preserve nulls and negative findings. We have not established training, quality improvement, a Strands speedup or a completed hour-scale study. Next are sufficient answer budgets, independent repeats and complete checkpoint coverage.
