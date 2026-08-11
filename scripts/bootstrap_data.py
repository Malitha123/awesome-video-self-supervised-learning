from pathlib import Path
from repo_tools import README_PATH, DATA_DIR, CONFIG_PATH, parse_main_representation, save_papers, TARGET_BENCHMARKS
import json

readme = README_PATH.read_text()
papers = parse_main_representation(readme)
save_papers(papers)
DATA_DIR.mkdir(exist_ok=True)
if not CONFIG_PATH.exists():
    CONFIG_PATH.write_text(json.dumps({
        "lookback_days": 10,
        "max_candidates": 40,
        "copilot_model": "",
        "copilot_batch_size": 8,
        "target_benchmarks": TARGET_BENCHMARKS,
        "search_queries": [
            '"self-supervised" AND video',
            '"self supervised" AND video',
            '"masked video modeling"',
            '"video representation learning" AND self-supervised',
            '"video masked autoencoder"',
            '"VideoSSL"'
        ]
    }, indent=2) + "\n")
print(f"Wrote {len(papers)} canonical representation-learning papers to {DATA_DIR / 'papers.json'}")
