# Recovery signature

Self-issued local Ed25519 key signs ../recovery_audit/package_manifest.json in namespace cell-akamai-recovery. Verification passed and repeated signing of identical bytes with the same key produced identical signatures. This verifies manifest integrity under this key, not external identity, trusted time, complete server coverage or scientific correctness. Private signing key and full archives stay private.
