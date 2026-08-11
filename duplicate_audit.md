# Duplicate audit

The canonical statistics and automation now use only the main year-by-year `Representation Learning` bibliography between `# Representation Learning` and `# Challenges`. Papers repeated later in the Challenges / Contrastive / Generative / Cross-Modal taxonomy are intentionally not counted a second time.

## Pre-existing duplicates removed from the canonical list

1. **Static and Dynamic Concepts for Self-supervised Video Representation Learning** appeared twice under 2022. Both entries pointed to arXiv `2207.12795`. The complete ECCV-formatted entry was retained.
2. **Self-Supervised Video Representation Learning by Video Incoherence Detection** appeared as a 2021 arXiv entry and a later 2023 IEEE Transactions on Cybernetics entry. The later journal entry was retained and linked internally to arXiv `2109.12493` for duplicate detection.
3. **Composable Augmentation Encoding for Video Representation Learning** appeared twice under 2021. The official ICCV/CVF entry was retained and linked internally to arXiv `2104.00616`.

## Current automated checks

- Canonical papers: **282**
- Duplicate normalized titles: **0**
- Duplicate arXiv IDs: **0**
- Fuzzy title pairs with similarity ≥ 0.94: **0**

The weekly curation agent repeats exact arXiv ID, DOI, normalized-title and fuzzy-title checks before using the model verifier. The verifier is also shown the closest existing titles and is instructed to reject renamed versions, conference/journal extensions, and other aliases of papers already represented in the repository.
