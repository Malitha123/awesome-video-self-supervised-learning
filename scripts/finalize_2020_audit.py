#!/usr/bin/env python3
"""Finalize the original 2020 cohort and reconcile its later versions."""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path


ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
PAPERS_PATH = ROOT / "data" / "papers.json"
AUDITS_DIR = ROOT / "data" / "audits"
VERIFIED_AS_OF = "2026-08-11"


def unique(items):
    return list(dict.fromkeys(item for item in items if item))


def split(value):
    return [item.strip() for item in value.split(";") if item.strip()]


def normalize_title(value):
    return " ".join("".join(ch.lower() if ch.isalnum() else " " for ch in value).split())


def spec(method, family, description, pretraining, evaluation, venue, venue_normalized,
         *, year=2020, status="peer_reviewed", url="", doi="", arxiv="", notes="", new_title=""):
    return {
        "method": method, "method_family": family, "method_description": description,
        "pretraining_datasets": split(pretraining), "evaluation_datasets": split(evaluation),
        "dataset_notes": notes, "venue": venue, "venue_normalized": venue_normalized,
        "year": year, "publication_status": status, "paper_url": url, "doi": doi,
        "arxiv_id": arxiv, "new_title": new_title,
    }


SPECS = {
    "Self-Supervised Learning to Detect Key Frames in Videos": spec(
        "Automatic Key-Frame Detection", "Other / Hybrid",
        "LDA-derived pseudo-labels supervise a two-stream RGB and optical-flow ConvNet initialized from ImageNet VGG-16 features.",
        "UCF101; ImageNet-1K", "UCF101; VSUMM", "Sensors 2020", "Sensors",
        url="https://www.mdpi.com/1424-8220/20/23/6941", doi="10.3390/s20236941",
        notes="ImageNet-1K is supervised VGG-16 initialization; UCF101 supplies the unlabeled key-frame training videos.",
    ),
    "Self-supervised motion representation via scattering local motion cues": spec(
        "Scattering Local Motion Cues", "Pretext / Predictive",
        "A coarse-to-fine network scatters local motion regions and uses context-guided semantic upsampling to learn explicit motion maps.",
        "UCF101; Kinetics-400", "UCF101; UCF-Flow; UCF-Pred; Kinetics-400; Kinetics-600; HMDB51", "ECCV 2020", "ECCV",
        url="https://www.ecva.net/papers/eccv_2020/papers_ECCV/papers/123590069.pdf", doi="10.1007/978-3-030-58568-6_5",
    ),
    "Self-supervised video representation learning using inter-intra contrastive framework": spec(
        "Inter-Intra Contrastive Learning (IIC)", "Contrastive",
        "RGB, residual, and optical-flow views provide positives, while other videos and shuffled or repeated clips provide inter- and intra-video negatives.",
        "UCF101", "UCF101; HMDB51", "ACM Multimedia 2020", "ACM Multimedia",
        url="https://doi.org/10.1145/3394171.3413694", doi="10.1145/3394171.3413694", arxiv="2008.02531",
    ),
    "Video representation learning with visual tempo consistency": spec(
        "Visual Tempo Hierarchical Contrastive Learning (VTHCL)", "Contrastive",
        "Slow and fast clips form tempo views whose shared information is contrasted hierarchically across network stages.",
        "Kinetics-400", "UCF101; HMDB51; AVA; EPIC-KITCHENS-55", "arXiv / Preprint", "arXiv / Preprint",
        status="preprint", url="https://arxiv.org/abs/2006.15489", arxiv="2006.15489",
    ),
    "Self-supervised temporal discriminative learning for video representation learning": spec(
        "Video-Based Temporal-Discriminative Learning (VTDL)", "Contrastive",
        "Temporally consistent augmentations form metric-learning triplets that distinguish clips within a video and across videos.",
        "UCF101; HMDB51; Kinetics-400", "UCF101; HMDB51", "arXiv / Preprint", "arXiv / Preprint",
        status="preprint", url="https://arxiv.org/abs/2008.02129", arxiv="2008.02129",
    ),
    "Self-supervised learning by cross-modal audio-video clustering": spec(
        "Cross-Modal Deep Clustering (XDC)", "Multimodal / Audio-Visual",
        "Audio and video are alternately clustered, and cluster assignments from one modality supervise the representation of the other.",
        "Kinetics-400; AudioSet; AudioSet-240K; Instagram-65M", "UCF101; HMDB51; ESC-50", "NeurIPS 2020", "NeurIPS",
        url="https://proceedings.neurips.cc/paper/2020/hash/6f2268bd1d3d3ebaabb04d6b5d099425-Abstract.html", arxiv="1911.12667",
        notes="The paper reports AudioSet-240K and Instagram variants, including random and Kinetics-filtered Instagram subsets.",
    ),
    "Self-supervised video representation learning by pace prediction": spec(
        "Pace Prediction", "Other / Hybrid",
        "Playback pace classification is coupled with a same-content contrastive objective to learn motion-sensitive representations.",
        "UCF101; Kinetics-400", "UCF101; HMDB51", "ECCV 2020", "ECCV",
        url="https://www.robots.ox.ac.uk/~vgg/publications/2020/Wang20/", doi="10.1007/978-3-030-58568-6_31", arxiv="2008.05861",
    ),
    "Unsupervised learning from video with deep neural embeddings": spec(
        "Video Instance Embedding (VIE)", "Contrastive",
        "Video instance recognition and local aggregation learn persistent embeddings with single-stream, 3D, SlowFast, and two-pathway variants.",
        "Kinetics-400", "Kinetics-400; ImageNet-1K; UCF101; HMDB51", "CVPR 2020", "CVPR",
        url="https://openaccess.thecvf.com/content_CVPR_2020/html/Zhuang_Unsupervised_Learning_From_Video_With_Deep_Neural_Embeddings_CVPR_2020_paper.html", arxiv="1905.11954",
    ),
    "Unsupervised learning of video representations via dense trajectory clustering": spec(
        "IDT-Guided Video Local Aggregation", "Clustering / Prototypes",
        "Video instance recognition and local aggregation use improved-dense-trajectory Fisher vectors to seed motion-aware clusters.",
        "Kinetics-400", "UCF101; HMDB51", "ECCV Workshops 2020", "ECCV Workshops",
        url="https://doi.org/10.1007/978-3-030-66096-3_28", doi="10.1007/978-3-030-66096-3_28", arxiv="2006.15731",
        notes="The workshop proceedings appeared online in 2021, but the archival event is ECCV Workshops 2020.",
    ),
    "Video representation learning by recognizing temporal transformations": spec(
        "Recognizing Temporal Transformations (RTT)", "Pretext / Predictive",
        "The encoder classifies speed changes, random skips, periodic frame warps, and forward or backward playback.",
        "UCF101; Kinetics-600", "UCF101; HMDB51", "ECCV 2020", "ECCV",
        url="https://doi.org/10.1007/978-3-030-58604-1_26", doi="10.1007/978-3-030-58604-1_26", arxiv="2007.10730",
    ),
    "Video playback rate perception for self-supervised spatio-temporal representation learning": spec(
        "Playback Rate Perception (PRP)", "Other / Hybrid",
        "Dilated sampling-rate classification is combined with reconstructive decoding and motion attention in a discriminative-generative objective.",
        "UCF101; HMDB51", "UCF101; HMDB51", "CVPR 2020", "CVPR",
        url="https://openaccess.thecvf.com/content_CVPR_2020/html/Yao_Video_Playback_Rate_Perception_for_Self-Supervised_Spatio-Temporal_Representation_Learning_CVPR_2020_paper.html", doi="10.1109/CVPR42600.2020.00658", arxiv="2006.11476",
    ),
    "Self-supervised co-training for video representation learning": spec(
        "CoCLR", "Contrastive",
        "RGB and optical-flow encoders alternate training, using one view to mine hard semantic positives for the other.",
        "UCF101; Kinetics-400", "UCF101; HMDB51; Kinetics-400", "NeurIPS 2020", "NeurIPS",
        url="https://proceedings.neurips.cc/paper/2020/hash/3def184ad8f4755ff269862ea77393dd-Abstract.html", arxiv="2010.09709",
    ),
    "Video cloze procedure for self-supervised spatio-temporal learning": spec(
        "Video Cloze Procedure (VCP)", "Pretext / Predictive",
        "Spatial and temporal cloze transformations create missing clips, and the network classifies the operation needed to complete them.",
        "UCF101; HMDB51", "UCF101; HMDB51", "AAAI 2020", "AAAI",
        url="https://ojs.aaai.org/index.php/AAAI/article/view/6840", doi="10.1609/aaai.v34i07.6840", arxiv="2001.00294",
    ),
    "End-to-end learning of visual representations from uncurated instructional videos": spec(
        "Multiple-Instance Noise-Contrastive Estimation (MIL-NCE)", "Multimodal / Video-Language",
        "Multiple-instance video-text contrastive learning treats nearby narrations as candidate positives to tolerate temporal misalignment.",
        "HowTo100M", "HMDB51; UCF101; Kinetics-700; YouCook2; MSR-VTT; YouTube-8M Segments; CrossTask; COIN", "CVPR 2020", "CVPR",
        url="https://openaccess.thecvf.com/content_CVPR_2020/html/Miech_End-to-End_Learning_of_Visual_Representations_From_Uncurated_Instructional_Videos_CVPR_2020_paper.html", arxiv="1912.06430",
    ),
    "Speednet: Learning the speediness in videos": spec(
        "SpeedNet", "Pretext / Predictive",
        "A dynamic-frame network predicts whether a clip plays at its natural rate or has been artificially sped up.",
        "Kinetics-400", "Kinetics-400; Need for Speed; UCF101; HMDB51", "CVPR 2020", "CVPR",
        url="https://openaccess.thecvf.com/content_CVPR_2020/html/Benaim_SpeedNet_Learning_the_Speediness_in_Videos_CVPR_2020_paper.html", arxiv="2004.06130", new_title="SpeedNet: Learning the Speediness in Videos",
    ),
    "Contrastive multiview coding": spec(
        "Contrastive Multiview Coding (CMC)", "Contrastive",
        "A view-agnostic contrastive objective maximizes shared information across sensory views, including video RGB frames and optical flow.",
        "ImageNet-1K; UCF101; NYU Depth V2", "ImageNet-1K; ImageNet-100; STL-10; UCF101; HMDB51; NYU Depth V2", "ECCV 2020", "ECCV",
        url="https://link.springer.com/chapter/10.1007/978-3-030-58621-8_45", doi="10.1007/978-3-030-58621-8_45", arxiv="1906.05849",
    ),
    "Self-supervised video representation learning by maximizing mutual information": spec(
        "Deep Video InfoMax (DVIM)", "Contrastive",
        "Clip-level mutual information links clips from one video, while motion-level mutual information links clip features to salient local motion regions.",
        "UCF101", "UCF101; HMDB51; ASLAN", "Signal Processing: Image Communication 2020", "Signal Processing: Image Communication",
        url="https://www.sciencedirect.com/science/article/pii/S0923596520301417", doi="10.1016/j.image.2020.115967",
    ),
    "Memory-augmented dense predictive coding for video representation learning": spec(
        "Memory-Augmented Dense Predictive Coding (MemDPC)", "Pretext / Predictive",
        "Predictive attention over a compressed memory bank constructs multiple hypotheses for future latent states in RGB or optical flow.",
        "UCF101; Kinetics-400; Oops", "UCF101; HMDB51; Kinetics-400; Oops", "ECCV 2020", "ECCV",
        url="https://www.robots.ox.ac.uk/~vgg/research/DPC/", doi="10.1007/978-3-030-58580-8_19", arxiv="2008.01065",
        notes="Oops is used for additional self-supervised adaptation and downstream evaluation in the failure-recognition experiment.",
    ),
    "Evolving losses for unsupervised video representation learning": spec(
        "Evolving Losses (ELo)", "Other / Hybrid",
        "Evolutionary search composes ordering, reconstruction, cross-modal alignment, and contrastive losses using an unsupervised distribution-matching fitness score.",
        "YouTube-8M", "HMDB51; UCF101; Kinetics-400", "CVPR 2020", "CVPR",
        url="https://openaccess.thecvf.com/content_CVPR_2020/html/Piergiovanni_Evolving_Losses_for_Unsupervised_Video_Representation_Learning_CVPR_2020_paper.html", doi="10.1109/CVPR42600.2020.00021",
        notes="Pretraining uses a random two-million-video subset sampled from YouTube-8M.",
    ),
    "Audiovisual slowfast networks for video recognition": spec(
        "AudioVisual SlowFast (AVSlowFast)", "Multimodal / Audio-Visual",
        "Slow and Fast visual pathways are joined by a faster audio pathway with hierarchical fusion, DropPathway, and audio-video synchronization supervision.",
        "Kinetics-400; Kinetics-600", "EPIC-KITCHENS-55; Kinetics-400; Kinetics-600; Kinetics-Sounds; Charades; AVA; UCF101; HMDB51", "arXiv / Preprint", "arXiv / Preprint",
        status="preprint", url="https://arxiv.org/abs/2001.08740", arxiv="2001.08740", new_title="AudioVisual SlowFast Networks for Video Recognition",
    ),
    "Cycle-contrast for self-supervised video representation learning": spec(
        "Cycle-Contrastive Learning (CCL)", "Contrastive",
        "Cycle consistency aligns frame and video embeddings, while contrastive discrimination and a diversity regularizer prevent degenerate correspondences.",
        "UCF101; Kinetics-400", "UCF101; HMDB51; MMAct", "NeurIPS 2020", "NeurIPS",
        url="https://proceedings.neurips.cc/paper_files/paper/2020/hash/5c9452254bccd24b8ad0bb1ab4408ad1-Abstract.html", arxiv="2010.14810", new_title="Cycle-Contrast for Self-Supervised Video Representation Learning",
    ),
    "Can temporal information help with contrastive self-supervised learning?": spec(
        "Temporal-Aware Contrastive Learning (TaCo)", "Other / Hybrid",
        "Temporal transformations augment contrastive positives and also define auxiliary rotation, reversal, shuffling, and speed-prediction tasks.",
        "Kinetics-400", "UCF101; HMDB51", "arXiv / Preprint", "arXiv / Preprint",
        status="preprint", url="https://arxiv.org/abs/2011.13046", arxiv="2011.13046",
    ),
    "Self-supervised multimodal versatile networks": spec(
        "Multimodal Versatile Networks (MMV)", "Multimodal / Audio-Visual",
        "Fine-and-coarse video, audio, and text contrastive learning produces one representation transferable across modalities and tasks.",
        "HowTo100M; AudioSet", "UCF101; HMDB51; Kinetics-600; ESC-50; AudioSet; MSR-VTT; YouCook2; PASCAL VOC 2007; ImageNet-1K", "NeurIPS 2020", "NeurIPS",
        url="https://proceedings.neurips.cc/paper/2020/hash/0060ef47b12160b9198302ebdb144dcf-Abstract.html", arxiv="2006.16228",
    ),
    "Watching the world go by: Representation learning from unlabeled videos": spec(
        "Video Noise-Contrastive Estimation (VINCE)", "Contrastive",
        "Multi-frame, multi-positive noise-contrastive learning uses temporally related natural video views and a momentum memory bank.",
        "R2V2; YouTube-8M URL collection; Kinetics-400 URL collection", "ImageNet-1K; SUN397; Kinetics-400; GOT-10k; OTB-2015", "ICLR 2021", "ICLR",
        year=2021, url="https://openreview.net/forum?id=iktA2PtTRsK", arxiv="2003.07990", new_title="Watching the World Go By: Representation Learning from Unlabeled Videos",
        notes="R2V2 is the authors' Random Related Video Views collection; URL-based YouTube-8M and Kinetics-400 collections are reported as variants.",
    ),
    "Pretext-contrastive learning: Toward good practices in self-supervised video representation leaning": spec(
        "Pretext-Contrastive Learning (PCL)", "Other / Hybrid",
        "Contrastive learning is jointly optimized with video cloze, clip-order, or rotation pretext branches using residual clips and strong augmentation.",
        "UCF101; Kinetics-400", "UCF101; HMDB51", "arXiv / Preprint", "arXiv / Preprint",
        status="preprint", url="https://arxiv.org/abs/2010.15464", arxiv="2010.15464", new_title="Pretext-Contrastive Learning: Toward Good Practices in Self-Supervised Video Representation Learning",
    ),
    "Univl: A unified video and language pre-training model for multimodal understanding and generation": spec(
        "UniVL", "Multimodal / Video-Language",
        "Unimodal encoders, a cross encoder, and a decoder learn five video-language alignment, masking, and reconstruction objectives in staged training.",
        "HowTo100M", "YouCook2; MSR-VTT; COIN; CrossTask; CMU-MOSI", "arXiv / Preprint", "arXiv / Preprint",
        status="preprint", url="https://arxiv.org/abs/2002.06353", arxiv="2002.06353", new_title="UniVL: A Unified Video and Language Pre-Training Model for Multimodal Understanding and Generation",
    ),
    "Self-supervised learning of audio-visual objects from video": spec(
        "Audio-Visual Object Discovery", "Multimodal / Audio-Visual",
        "Attention localizes discrete sound sources, optical flow aggregates and tracks them, and synchronization plus mix-and-separate provide supervision.",
        "LRS2; The Simpsons raw footage; Sesame Street raw footage", "LRS2; LRS3; Columbia Active Speaker; The Simpsons; Sesame Street", "ECCV 2020", "ECCV",
        url="https://doi.org/10.1007/978-3-030-58523-5_13", doi="10.1007/978-3-030-58523-5_13", arxiv="2008.04237",
        notes="The Simpsons and Sesame Street footage are private or program-specific collections rather than released benchmarks.",
    ),
    "Parameter efficient multimodal transformers for video representation learning": spec(
        "Audio-Visual BERT (AVBERT)", "Multimodal / Audio-Visual",
        "Modality-specific and shared low-rank Transformers learn masked embedding prediction and cross-modal pair prediction with content-aware negatives.",
        "Kinetics-700; AudioSet", "UCF101; ESC-50; Charades; Kinetics-Sounds", "ICLR 2021", "ICLR",
        year=2021, url="https://openreview.net/forum?id=6UdQLhqJyFD", arxiv="2012.04124", new_title="Parameter Efficient Multimodal Transformers for Video Representation Learning",
    ),
    "Active contrastive learning of audio-visual video representations": spec(
        "Cross-Modal Active Contrastive Coding (CM-ACC)", "Multimodal / Audio-Visual",
        "Active gradient-embedding selection builds diverse and informative audio and video negative dictionaries for cross-modal contrastive learning.",
        "Kinetics-Sounds; Kinetics-700; AudioSet; UCF101", "UCF101; HMDB51; ESC-50", "ICLR 2021", "ICLR",
        year=2021, url="https://openreview.net/forum?id=OMizHuea_HB", arxiv="2009.09805", new_title="Active Contrastive Learning of Audio-Visual Video Representations",
        notes="UCF101 is used in the paper's small-scale active-selection analysis in addition to the large pretraining collections.",
    ),
    "Speech2action: Cross-modal supervision for action recognition": spec(
        "Speech2Action", "Multimodal / Video-Language",
        "BERT learns speech-to-action correlations from screenplays, mines weak action labels in movies, and supervises an S3D-G action model.",
        "IMSDb Screenplays; Speech2Action-mined Movies", "HMDB51; AVA; UCF101", "CVPR 2020", "CVPR",
        url="https://openaccess.thecvf.com/content_CVPR_2020/html/Nagrani_Speech2Action_Cross-Modal_Supervision_for_Action_Recognition_CVPR_2020_paper.html", new_title="Speech2Action: Cross-Modal Supervision for Action Recognition",
        notes="The mined pretraining collection contains clips drawn from a large private movie and speech corpus; IMSDb provides screenplay text for the speech-action model.",
    ),
    "Look, listen, and attend: Co-attention network for self-supervised audio-visual representation learning": spec(
        "Look, Listen, and Attend (LLA)", "Multimodal / Audio-Visual",
        "Visual-guided, audio-guided, and cross-modal co-attention learn audio-video correspondence and synchronization.",
        "AudioSet-240K", "AudioSet-240K; AudioSet-750K; Kinetics-400; Kinetics-Sounds; UCF101; HMDB51", "ACM Multimedia 2020", "ACM Multimedia",
        url="https://dl.acm.org/doi/10.1145/3394171.3413869", doi="10.1145/3394171.3413869", arxiv="2008.05789", new_title="Look, Listen, and Attend: Co-Attention Network for Self-Supervised Audio-Visual Representation Learning",
        notes="AudioSet-240K is resegmented without constraining the clips to the original label ontology.",
    ),
}


AUDIT_UPDATE_FIELDS = [
    "year", "date_label", "venue", "venue_normalized", "publication_status", "method",
    "method_family", "method_description", "pretraining_datasets", "evaluation_datasets",
    "datasets", "benchmarks", "benchmark_suites", "benchmark_text", "dataset_notes",
    "paper_url", "code_url", "project_url", "doi", "arxiv_id", "published_date",
    "verification_urls", "venue_evidence", "audit_notes", "previous_titles",
]


def audit_updates(paper):
    return {key: paper[key] for key in AUDIT_UPDATE_FIELDS if key in paper}


def write_audit(year, papers):
    records = [{"normalized_title": p["normalized_title"], "updates": audit_updates(p)} for p in papers]
    payload = {
        "schema_version": 1, "year": year, "status": "complete", "verified_as_of": VERIFIED_AS_OF,
        "paper_count": len(records),
        "source_policy": "Use exact-title scholarly discovery, then verify venue and metadata against an official conference, publisher, DOI, or preprint record. Do not promote a search-result venue without primary-source confirmation.",
        "dataset_policy": "Record separately the datasets used for self-supervised or backbone pretraining and the datasets used for downstream evaluation. Preserve named benchmark suites and explicitly label unnamed private collections.",
        "records": records,
    }
    (AUDITS_DIR / f"{year}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    fields = ["Title", "Method", "Method family", "Pretraining datasets", "Evaluation datasets", "Year", "Venue", "Publication status", "DOI", "Verified as of"]
    with (AUDITS_DIR / f"{year}.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for p in papers:
            writer.writerow({
                "Title": p["title"], "Method": p["method"], "Method family": p["method_family"],
                "Pretraining datasets": "; ".join(p["pretraining_datasets"]),
                "Evaluation datasets": "; ".join(p["evaluation_datasets"]),
                "Year": p["year"], "Venue": p["venue"], "Publication status": p["publication_status"],
                "DOI": p.get("doi", ""), "Verified as of": VERIFIED_AS_OF,
            })


def status_block(year, papers):
    return {
        "status": "complete", "paper_count": len(papers),
        "peer_reviewed_count": sum(p["publication_status"] == "peer_reviewed" for p in papers),
        "preprint_count": sum(p["publication_status"] == "preprint" for p in papers),
        "audit_file": f"data/audits/{year}.json", "summary_file": f"data/audits/{year}.csv",
        "verified_as_of": VERIFIED_AS_OF,
    }


def apply_spec(paper, data):
    old_title = paper["title"]
    new_title = data.get("new_title") or old_title
    if new_title != old_title:
        paper["previous_titles"] = unique(paper.get("previous_titles", []) + [old_title])
        paper["title"] = new_title
        paper["normalized_title"] = normalize_title(new_title)
    for field in ("method", "method_family", "method_description", "pretraining_datasets", "evaluation_datasets", "dataset_notes", "venue", "venue_normalized", "year", "publication_status"):
        paper[field] = data[field]
    paper["date_label"] = str(data["year"])
    paper["published_date"] = str(data["year"])
    paper["datasets"] = unique(data["pretraining_datasets"] + data["evaluation_datasets"])
    paper["benchmarks"] = data["evaluation_datasets"]
    paper["benchmark_text"] = ", ".join(data["evaluation_datasets"])
    if data.get("paper_url"):
        paper["paper_url"] = data["paper_url"]
    paper["doi"] = data.get("doi", "")
    paper["arxiv_id"] = data.get("arxiv_id", "") or paper.get("arxiv_id", "")
    if not paper["arxiv_id"]:
        match = re.search(r"(?:abs/|pdf/|arXiv:)(\d{4}\.\d{4,5})", paper.get("paper_url", "") + " " + paper.get("venue", ""), re.I)
        paper["arxiv_id"] = match.group(1) if match else ""
    verification = [paper.get("paper_url", "")]
    if paper["doi"]:
        verification.append("https://doi.org/" + paper["doi"])
    if paper["arxiv_id"]:
        verification.append("https://arxiv.org/abs/" + paper["arxiv_id"])
    paper["verification_urls"] = unique(verification)
    paper["venue_evidence"] = "arxiv_record_and_exact_title_publication_search" if data["publication_status"] == "preprint" else "official_proceedings_or_publisher_record"
    if data["publication_status"] == "preprint":
        paper["audit_notes"] = "Exact-title and author-record searches found no peer-reviewed version through the verification date."
    elif data["year"] != 2020:
        paper["audit_notes"] = "The initial 2020 preprint record was reconciled to the accepted archival conference version."
    else:
        paper.pop("audit_notes", None)
    paper["audited_at"] = VERIFIED_AS_OF
    paper["discovery_source"] = "exact_title_scholarly_search_then_primary_source"


def main():
    papers = json.loads(PAPERS_PATH.read_text())
    initial = [p for p in papers if p.get("year") == 2020]
    initial_titles = {p["title"] for p in initial}
    if initial_titles != set(SPECS):
        raise SystemExit(f"2020 mapping mismatch: missing={sorted(initial_titles-set(SPECS))}, extra={sorted(set(SPECS)-initial_titles)}")
    for paper in initial:
        apply_spec(paper, SPECS[paper["title"]])

    completed = {}
    years = (2026, 2025, 2024, 2023, 2022, 2021, 2020)
    for year in years:
        year_papers = [p for p in papers if p.get("year") == year]
        for paper in year_papers:
            paper["audit_status"] = "verified"
            paper["audit_year"] = year
            paper["audited_at"] = VERIFIED_AS_OF
        completed[year] = year_papers
    PAPERS_PATH.write_text(json.dumps(papers, indent=2, ensure_ascii=False) + "\n")
    for year in years:
        write_audit(year, completed[year])

    verified = sum(len(completed[year]) for year in years)
    progress_path = ROOT / "data" / "audit_progress.json"
    progress = json.loads(progress_path.read_text())
    progress.update({
        "last_checkpoint_at": VERIFIED_AS_OF, "completed_years": list(years), "next_year": 2019,
        "verified_paper_count": verified, "remaining_paper_count": len(papers) - verified,
        "resume_instruction": "Start with 2019. Verify exact-title publication history, fill method and split pretraining/evaluation datasets, rebuild the site, validate the catalog, and save the 2019 checkpoint.",
    })
    progress["year_status"] = {str(year): status_block(year, completed[year]) for year in years}
    progress_path.write_text(json.dumps(progress, indent=2, ensure_ascii=False) + "\n")
    print("Finalized original 2020 cohort and reconciled completed years: " + ", ".join(f"{year}={len(completed[year])}" for year in years))


if __name__ == "__main__":
    main()
