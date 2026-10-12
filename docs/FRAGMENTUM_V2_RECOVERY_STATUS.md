# Fragmentum v2 recovery status

**Status: blocked for real VCC target binding.** The local consumer contract and a separate Substrata builder are identifiable, but the governed Fragmentum v2 source manifest/data and an admitted target list are not present in this integration checkout. Synthetic fixtures must not be substituted for biological source data.

## Builder and source provenance

- The Substrata v2 core builder is `scripts/ftc_generate_core_universe.py` in the `substrata` repository. It streams exact-contiguous fragments and writes per-shard records to `partition_manifest.jsonl` and `SHA_MANIFEST.json`; final certification remains a separate closeout step. It reads canonical sequences from ProtHub through its read-only AQL API (default local endpoint `localhost:8529`) and checks lengths against `fragmentum/results/proteinome_canonical_lengths_full_store_20260602.json`. That pinned length-table file is missing from the inspected checkout, so its source hash/provenance cannot currently be checked here.
- This builder has no dry-run mode. `--validation` still queries ProtHub and writes a local generated dataset; it is not a preview. Do not use it until a separate validation run is authorized and a fresh scratch destination is specified.
- The other v2 entrypoint, `fragmentum/v2/release/panel61_release.py`, reconstructs sequences from the existing local v1 substrate. Its source explicitly says it does not fetch UniProt sequences. It is a bounded Panel61 release flow, not an internet dataset acquisition path.
- Direct UniProt REST access appears in the older v1 remediation script `fragmentum/experiments/exp009_v1_sequence_record_remediation.py`; this must not be described as the v2 builder.
- Cloudmer's `FragmentumV2Panel61Provider` is a read-only consumer for a separately provisioned `fragmentum/v2_panel61/manifest.json` and optional parquet partitions. The recovered provider validation is `SOURCE_UNAVAILABLE`; no provider manifest/data was found in the inspected roots. It does not download or generate data.

Safe interface previews only print help and perform no data acquisition or writes:

```sh
PYTHONPATH=. python3 scripts/ftc_generate_core_universe.py --help
PYTHONPATH=. python3 -m fragmentum.v2.release.panel61_release --help
```

## Scientific target semantics

The DAISY simulation Anticube target is a five-class label: `SELF_SAFE`, `SELF_UNSAFE`, `NONSELF_SAFE`, `NONSELF_UNSAFE`, or `UNKNOWN`. It describes a governed simulation/evidence classification, not a biological-cell phenotype or clinical label. The available public ECA construction explicitly limits its claim to a simulation evaluation distribution and says it is not biological or independently calibrated.

The DAISY `delta_g_star` target is the versioned `DAISY-PFCO-004-dg_score-v1` observed transition score: a weighted composite of changes in evidence, claims, prediction, contradiction, uncertainty, topology, context, and reproducibility. It is a dimensionless project score with no physical units. It is distinct from current-state `G*`, and it is not thermodynamic Gibbs free energy, a measured biological free-energy change, or a validated biological endpoint. Rows where it is not computed must remain null/status-bearing rather than be imputed.

These definitions describe the recovered DAISY fixture/training lineage only. They do not authorize interpreting those values as VCC outcomes. The R4 checkpoint is identified as custom `DAISY-0-vita-1/MSM-Tiny` and was evaluated on its recorded validation split; its test set and VCC adapter/submission were not evaluated/executed. No evidence currently binds this checkpoint to a licensed, identified biological dataset or VCC target panel.

## Requirements before real VCC integration

1. Recover the exact source dataset and its upstream manifest: source/version or revision, source-file hashes, organism/assay/population scope, row identity, license/DUA and permitted processing/training use.
2. Provide a non-synthetic, admitted target list with stable target identifiers and mapping provenance. Record exclusions, ambiguity, and missing coverage explicitly.
3. Provision the Fragmentum v2 provider manifest plus its source commit, certification class, coverage scope, license-use state, and byte hashes. Verify those against the acquired partitions before binding predictors.
4. Establish that the MSM checkpoint's training and evaluation inputs, tokenizer/model identity, labels, and split are compatible with the real source and targets. Preserve training/evaluation separation and prohibit source identifiers or target-derived leakage in predictive inputs.
5. Keep `NOT_TESTED`, `NOT_COMPUTED`, `UNKNOWN`, `NOT_RECOVERED`, and `FAILED` distinct. A successful manifest/hash check establishes custody only; it does not establish predictive validity or biological truth.

**Next safe action:** recover and review the approved source manifest/license and Fragmentum v2 provider package, then run a manifest-only/read-only verification. Keep real-target predictor binding blocked until that verification and target mapping are complete. No training, SeedGraph mutation, or external publication is authorized by this status note.

## Recovery update

The exact full-store length table was recovered privately from Substrata Git commit `71f49cb5f6aa8527e69febd3d38f4af59f5fc180`: 20,493 positive integer accession lengths, SHA-256 `8e4caacd1f22628beb6a0d6e7734546e4572e0529688f282d0826403b0d425fc`. This resolves the missing table input; it does not establish availability of protein sequences, generated v2 partitions or the Cloudmer provider manifest. The three-entry seed table is insufficient. Earlier missing-path findings above describe the working checkout before this recovery.
