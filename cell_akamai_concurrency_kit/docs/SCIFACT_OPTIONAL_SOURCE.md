# SciFact scientific-evidence dataset: staged, not admitted

Source: Wadden et al. (EMNLP 2020), https://github.com/allenai/scifact
Dataset archive: https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz
Official repo describes claim/evidence annotation licenses as CC BY 4.0 and abstracts as ODC-By 1.0: https://github.com/allenai/scifact/blob/master/LICENSE.md
Hugging Face dataset card currently describes SciFact as CC BY-NC 2.0: https://huggingface.co/datasets/allenai/scifact

**LICENSE CONFLICT / NOT CLEARED for redistributable commercial business use:** do not blend this into the canonical Cell-Akamai dataset or redistribute SciFact corpus text until attribution, terms, and intended use are reviewed. The source URL is a retrieval pointer, not evidence that a download executed; the exact archive hash must be pinned after retrieval. Official test-set labels are not released, so use development labels only for nonconfirmatory calibration; independently blind held-out scientific scoring needs separate governance.

Suggested later evaluation: SUPPORTED / CONTRADICTED / INSUFFICIENT_INFORMATION claims with supplied abstracts and exact cited evidence; score calibrated abstentions, evidence sentence retrieval, rationales, token cost and concurrency under the same served engine. No external SciFact observations are present in this kit.
