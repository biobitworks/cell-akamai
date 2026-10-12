# Vita/DAISY longevity and virtual-cell evaluation: starting tracks

Status: Hugging Face tracks remain SOURCES_PINNED_DESIGN_ONLY. Separately, recovered Kaggle Vita DAISY R4 checkpoints have now completed an Akamai CPU validation replay: [receipt](../evidence/20261012/AKAMAI_VITA_R4_CPU_REPLAY.json). This is a structured three-head model evaluation, separate from longevity text generation or official VCC scoring. See hf_longevity_source_registry.json for pinned Hugging Face revisions.

## First experiment: structured answer revision

Use LongevityBench mini as development/adapter validation only; its728rows are a subsample of the main benchmark, not an independent holdout. Inspect actual schema and separate target/assistant messages from actor-visible inputs before use. Select task families whose actual model-tokenizer lengths fit8192 without silently truncating biological features. Pin sources, deduplicate subjects/cohorts and source pointers, and keep development examples out of final reported evaluation. Benchmark canary prohibits inclusion in training corpora.

Primary comparisons: Qwen/Qwen3-0.6B versus insilicomedicine/Qwen3-0.6B-Longevity; Qwen/Qwen3-1.7B versus insilicomedicine/Qwen3-1.7B-Longevity. Each model is a separate hosted serving epoch requiring explicit deployment authorization. Current Qwen3-4B is a plumbing/reference model, not a same-size adaptation control. The linked models are Qwen transformers; an LFM-specific experiment needs an exact LFM repository/revision.

Within each model compare B0fixed, B1Genesis-proxy, B2Genesis+DAISYchallenge and B3randomizedchallenge. Freeze call/token budgets and include a token-matched useful-information-free extra-inference control. Commit actor/challenger/adjudicator outputs before independent scoring. Track correction vs harmful reversal, task-specific deterministic accuracy/error, abstention, coverage, parse/truncation failures, calibration when actual confidence is collected, tokens/correct and stage-level latency. Subject/cohort/task-block bootstrap, not repeated-request pseudo-replication. No training claim.

Genesis policy code/hash must be bound. MSM semantics/schema must be bound to the existing project contract before adding features; do not invent an acronym expansion or composite scientific score. Antigence may provide operational admission predicates only after freezing tests for schema, provenance, budget, leakage and unsafe admission. Its gate must not read evaluation truth. For this proposed longevity actor experiment, Anticube operational predicates and ΔG* need a bound implementation and tests. The separate recovered Vita MSMTiny model already computes five-class Anticube accuracy/cross-entropy and ΔG* target MSE; its Akamai replay receipt records those values. These task-specific metrics must not be substituted for physical Gibbs energy, biological VCC scores or the proposed actor experiment.

## Second independent track: URSA plausibility

Use the1000reaction plausibility set (500/500 expert labels). Hide expert_score, chemcensor_score and derived label from actors. Compare deterministic parser validity, balanced accuracy, false-admission rate and DAISY harmful/corrected reversals. Chemistry expertise/tool validation is required; plausible output is not experimental synthesis proof. Retrosynthesis target-only files require external reference reactants and a route/chemistry scorer before accuracy claims.

## Virtual Cell Challenge track

2026task: predict CRISPRi perturbation expression profiles in unseen cell contexts from controls plus knockdown identities. Build a numerical predictor using appropriately split public perturbation data; compare a matched baseline with and without LLM-derived biological priors. Use Genesis for orchestration and Vita/DAISY for bounded data/QC/error review. Final numerical predictions must come from the declared predictor; free-text biomedical answers are not submission matrices.

Use the current official2026scoring configuration (six-metric aggregate), not a hardcoded2025three-metric profile. Preserve gene order, contexts, perturbation IDs, counts and normalization. Validate real prediction h5ad with vcc prep, then one team submission at a time. Local vcc0.1.0 is installed; authentication/data/predictions/submission NOT_VERIFIED. Final test release October22; final submission November5,23:59UTC per Arc announcement. No submission was made by this preparation.

## Resource and provenance limits

The9B longevity-llm card reports~18.8GB BF16 weights and H10094GB validation. The current20GBworkshop GPU offers little serving/KV headroom; start with smaller checkpoints after existing workload finishes. Model cards label checkpoints CC-BY-ND-4.0; LongevityBench CC-BY-NC-4.0 with underlying-source conditions; URSA Apache2.0. Keep evaluation data out of training and check derivative permissions before tuning/quantizing redistributed checkpoints.

Merkle roots establish checkpoint custody, not biological correctness. Tokens/s² measures throughput change, not learning or scientific progress. Keep GPU capacity experiments separate from held-out task quality comparisons.

Sources: https://huggingface.co/datasets/insilicomedicine/longebench ; https://huggingface.co/insilicomedicine/Qwen3-0.6B-Longevity ; https://huggingface.co/insilicomedicine/Qwen3-1.7B-Longevity ; https://huggingface.co/insilicomedicine/longevity-llm ; https://huggingface.co/datasets/insilicomedicine/URSA-benchmarking-sets ; https://arcinstitute.org/news/virtual-cell-challenge-2026 .
