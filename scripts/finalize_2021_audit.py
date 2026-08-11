#!/usr/bin/env python3
"""Finalize the original 2021 cohort and reconcile its later versions."""

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
         *, year=2021, status="peer_reviewed", url="", doi="", arxiv="", notes="", new_title=""):
    return {
        "method": method, "method_family": family, "method_description": description,
        "pretraining_datasets": split(pretraining), "evaluation_datasets": split(evaluation),
        "dataset_notes": notes, "venue": venue, "venue_normalized": venue_normalized,
        "year": year, "publication_status": status, "paper_url": url, "doi": doi,
        "arxiv_id": arxiv, "new_title": new_title,
    }


SPECS = {
    "Inter-intra Variant Dual Representations for Self-supervised Video Recognition": spec(
        "Inter-Intra Variant Dual Representations (IVDR)", "Contrastive",
        "Dual heads encode variation between videos and complementary variation among clips from the same video.",
        "Kinetics-400; UCF101", "Kinetics-400; UCF101; HMDB51", "BMVC 2021", "BMVC",
        url="https://doi.org/10.5244/C.35.131", doi="10.5244/C.35.131", arxiv="2107.01194",
    ),
    "VIMPAC: Video Pre-Training via Masked Token Prediction and Contrastive Learning": spec(
        "VIMPAC", "Generative / Masked",
        "Blockwise masked prediction over VQ-VAE video tokens is combined with augmentation-free same-video contrastive learning.",
        "HowTo100M", "Something-Something V2; Diving48; UCF101; HMDB51", "NeurIPS 2021", "NeurIPS",
        url="https://openreview.net/forum?id=NP9T_pViXU", arxiv="2106.11250",
    ),
    "Watching too much television is good: Self-supervised audio-visual representation learning from movies and tv shows": spec(
        "Long-form Audio-Visual Contrastive Learning", "Multimodal / Audio-Visual",
        "Audio-visual contrastive learning exploits long-form movies and television, including recurring characters, scenes, and sounds.",
        "Long-form movies and TV shows", "UCF101; HMDB51; ESC-50", "arXiv / Preprint", "arXiv / Preprint",
        status="preprint", url="https://arxiv.org/abs/2106.08513", arxiv="2106.08513",
        notes="The training collection is described by media type rather than released as a named benchmark.",
    ),
    "Temporally coherent embeddings for self-supervised video representation learning": spec(
        "Temporally Coherent Embeddings (TCE)", "Contrastive",
        "A temporal-coherence metric loss keeps nearby frames close and temporally separated frames distinct in embedding space.",
        "UCF101", "UCF101; HMDB51", "ICPR 2020", "ICPR",
        url="https://ieeexplore.ieee.org/document/9412071", arxiv="2004.02753",
        notes="The conference retained the ICPR 2020 name but the IEEE proceedings record was published in 2021.",
    ),
    "Audio-visual instance discrimination with cross-modal agreement": spec(
        "AVID-CMA", "Multimodal / Audio-Visual",
        "Cross-modal instance discrimination is extended with agreement-based mining of additional audio-video positives.",
        "Kinetics-400; AudioSet", "UCF101; HMDB51; ESC-50; DCASE", "CVPR 2021", "CVPR",
        url="https://openaccess.thecvf.com/content/CVPR2021/html/Morgado_Audio-Visual_Instance_Discrimination_With_Cross-Modal_Agreement_CVPR_2021_paper.html", arxiv="2004.12943",
    ),
    "Removing the background by adding the background: Towards background robust self-supervised video representation learning": spec(
        "Background Erasing (BE)", "Contrastive",
        "A static frame is added to every frame of a clip and the original and distracted clips are aligned to suppress background dependence.",
        "Kinetics-400; UCF101; HMDB51", "UCF101; HMDB51; Diving48", "CVPR 2021", "CVPR",
        url="https://openaccess.thecvf.com/content/CVPR2021/html/Wang_Removing_the_Background_by_Adding_the_Background_Towards_Background_Robust_Self-Supervised_CVPR_2021_paper.html", arxiv="2009.05769",
    ),
    "Enhancing unsupervised video representation learning by decoupling the scene and the motion": spec(
        "Decoupling Scene and Motion (DSM)", "Contrastive",
        "Spatial and temporal local disturbances form scene-broken and motion-broken views that explicitly separate appearance from motion.",
        "Kinetics-400; UCF101", "UCF101; HMDB51", "AAAI 2021", "AAAI",
        url="https://ojs.aaai.org/index.php/AAAI/article/view/17215", arxiv="2009.05757",
    ),
    "Self-supervised video representation learning by uncovering spatio-temporal statistics": spec(
        "Spatiotemporal Statistics Prediction", "Pretext / Predictive",
        "The network predicts coarse spatial locations, dominant motion directions, and color-diversity statistics from video clips.",
        "UCF101; Kinetics-400", "UCF101; HMDB51; YUP++; ASLAN", "IEEE Transactions on Pattern Analysis and Machine Intelligence 2022", "IEEE TPAMI",
        year=2022, url="https://ieeexplore.ieee.org/document/9352025", doi="10.1109/TPAMI.2021.3054224", arxiv="2008.13426",
    ),
    "Seco: Exploring sequence supervision for unsupervised representation learning": spec(
        "SeCo", "Contrastive",
        "Frame, clip, and sequence-level contrastive tasks model spatial identity, video identity, and temporal order.",
        "Kinetics-400", "Kinetics-400; ActivityNet; OTB-100; UCF101; HMDB51", "AAAI 2021", "AAAI",
        url="https://ojs.aaai.org/index.php/AAAI/article/view/17274", doi="10.1609/aaai.v35i12.17274", arxiv="2008.00975", new_title="SeCo: Exploring Sequence Supervision for Unsupervised Representation Learning",
    ),
    "Enhancing self-supervised video representation learning via multi-level feature optimization": spec(
        "Multi-Level Feature Optimization (MFO)", "Contrastive",
        "Low-, mid-, and high-level feature objectives combine local contrast, temporal modeling, and global instance discrimination.",
        "Kinetics-400", "Kinetics-400; UCF101; HMDB51; Diving48", "ICCV 2021", "ICCV",
        url="https://openaccess.thecvf.com/content/ICCV2021/html/Qian_Enhancing_Self-Supervised_Video_Representation_Learning_via_Multi-Level_Feature_Optimization_ICCV_2021_paper.html", arxiv="2108.02183",
    ),
    "RSPnet: Relative speed perception for unsupervised video representation learning": spec(
        "RSPNet", "Pretext / Predictive",
        "Relative playback-speed prediction is paired with an appearance-focused task to retain motion and appearance cues.",
        "UCF101; Kinetics-400", "UCF101; HMDB51", "AAAI 2021", "AAAI",
        url="https://ojs.aaai.org/index.php/AAAI/article/view/16189", arxiv="2011.07949", new_title="RSPNet: Relative Speed Perception for Unsupervised Video Representation Learning",
    ),
    "Videomoco: Contrastive video representation learning with temporally adversarial examples": spec(
        "VideoMoCo", "Contrastive",
        "An adversarial frame-drop generator creates temporally robust views and temporal decay reweights stale keys in the memory queue.",
        "Kinetics-400", "UCF101; HMDB51", "CVPR 2021", "CVPR",
        url="https://openaccess.thecvf.com/content/CVPR2021/html/Pan_VideoMoCo_Contrastive_Video_Representation_Learning_With_Temporally_Adversarial_Examples_CVPR_2021_paper.html", arxiv="2103.05905", new_title="VideoMoCo: Contrastive Video Representation Learning with Temporally Adversarial Examples",
    ),
    "On compositions of transformations in contrastive self-supervised learning": spec(
        "Generalized Data Transformations (GDT)", "Contrastive",
        "A generalized transformation framework specifies which spatial, temporal, audio, and text transformations should be invariant or distinctive.",
        "Kinetics-400; AudioSet; HowTo100M", "UCF101; HMDB51; ESC-50; Kinetics-400", "ICCV 2021", "ICCV",
        url="https://openaccess.thecvf.com/content/ICCV2021/html/Patrick_On_Compositions_of_Transformations_in_Contrastive_Self-Supervised_Learning_ICCV_2021_paper.html", arxiv="2003.04298",
    ),
    "Unsupervised visual representation learning by tracking patches in video": spec(
        "Catch-the-Patch (CtP)", "Pretext / Predictive",
        "Synthetic moving patches create a tracking game in which a 3D encoder predicts each patch trajectory and scale.",
        "Kinetics-400", "UCF101; HMDB51; Something-Something V1; Something-Something V2", "CVPR 2021", "CVPR",
        url="https://openaccess.thecvf.com/content/CVPR2021/html/Wang_Unsupervised_Visual_Representation_Learning_by_Tracking_Patches_in_Video_CVPR_2021_paper.html", arxiv="2105.02545",
    ),
    "A large-scale study on unsupervised spatiotemporal representation learning": spec(
        "Space-Time Contrastive Study", "Contrastive",
        "Image contrastive frameworks are generalized to video by encouraging features that persist across long temporal spans.",
        "Kinetics-400; Kinetics-600; Kinetics-700; Instagram-65M", "Kinetics-400; Kinetics-600; Kinetics-700; UCF101; HMDB51; AVA", "CVPR 2021", "CVPR",
        url="https://openaccess.thecvf.com/content/CVPR2021/html/Feichtenhofer_A_Large-Scale_Study_on_Unsupervised_Spatiotemporal_Representation_Learning_CVPR_2021_paper.html", doi="10.1109/CVPR46437.2021.00331", arxiv="2104.14558",
    ),
    "Cocon: Cooperative-contrastive learning": spec(
        "CoCon", "Contrastive",
        "Cooperating encoders exchange complementary positive targets so contrastive training captures both context and motion.",
        "Kinetics-400", "Kinetics-400; UCF101; HMDB51", "CVPR 2021", "CVPR",
        url="https://openaccess.thecvf.com/content/CVPR2021/html/Rai_CoCon_Cooperative-Contrastive_Learning_CVPR_2021_paper.html", arxiv="2104.14764", new_title="CoCon: Cooperative-Contrastive Learning",
    ),
    "VATT: Transformers for multimodal self-supervised learning from raw video, audio and text": spec(
        "VATT", "Multimodal / Audio-Visual",
        "Video, audio, and text transformers are trained end-to-end from raw signals with multimodal contrastive alignment.",
        "HowTo100M; AudioSet", "Kinetics-400; Kinetics-600; Kinetics-700; Moments in Time V1; ImageNet-1K; AudioSet; YouCook2; MSR-VTT", "NeurIPS 2021", "NeurIPS",
        url="https://proceedings.neurips.cc/paper/2021/hash/cb3213ada48302953cb0f166464ab356-Abstract.html", arxiv="2104.11178",
    ),
    "ASCNet: Self-supervised video representation learning with appearance-speed consistency": spec(
        "ASCNet", "Contrastive",
        "Appearance consistency aligns clips played at different speeds, while speed consistency aligns clips with different appearance at one speed.",
        "UCF101; Kinetics-400", "UCF101; HMDB51", "ICCV 2021", "ICCV",
        url="https://openaccess.thecvf.com/content/ICCV2021/html/Huang_ASCNet_Self-Supervised_Video_Representation_Learning_With_Appearance-Speed_Consistency_ICCV_2021_paper.html", arxiv="2106.02342",
    ),
    "Self-supervised visual learning by variable playback speeds prediction of a video": spec(
        "Variable Playback Speed Prediction", "Pretext / Predictive",
        "The model predicts randomized forward, reverse, and mixed playback speeds with temporal group normalization.",
        "UCF101; HMDB51", "UCF101; HMDB51", "IEEE Access 2021", "IEEE Access",
        url="https://ieeexplore.ieee.org/document/9443174", doi="10.1109/ACCESS.2021.3084840", arxiv="2003.02692",
    ),
    "Self-supervised video representation learning with meta-contrastive network": spec(
        "Meta-Contrastive Network (MCN)", "Contrastive",
        "A meta-learning loop adapts the contrastive objective to generate more transferable video representations.",
        "UCF101; Kinetics-400", "UCF101; HMDB51", "ICCV 2021", "ICCV",
        url="https://openaccess.thecvf.com/content/ICCV2021/html/Lin_Self-Supervised_Video_Representation_Learning_With_Meta-Contrastive_Network_ICCV_2021_paper.html", doi="10.1109/ICCV48922.2021.00813",
    ),
    "Long short view feature decomposition via contrastive video representation learning": spec(
        "Long-Short View Feature Decomposition (LSFD)", "Contrastive",
        "Long and short views decompose stationary video attributes from non-stationary temporal attributes.",
        "Kinetics-400", "UCF101; HMDB51; Breakfast; 50Salads", "ICCV 2021", "ICCV",
        url="https://openaccess.thecvf.com/content/ICCV2021/html/Behrmann_Long_Short_View_Feature_Decomposition_via_Contrastive_Video_Representation_Learning_ICCV_2021_paper.html", arxiv="2109.11593",
    ),
    "Time-equivariant contrastive video representation learning": spec(
        "Time-Equivariant Contrastive Learning (TE)", "Contrastive",
        "Representations are trained to transform predictably under temporal shifts while remaining invariant to content-preserving appearance changes.",
        "Kinetics-400", "Kinetics-400; UCF101; HMDB51; FineGym", "ICCV 2021", "ICCV",
        url="https://openaccess.thecvf.com/content/ICCV2021/html/Jenni_Time-Equivariant_Contrastive_Video_Representation_Learning_ICCV_2021_paper.html", arxiv="2112.03624",
    ),
    "Self-supervised video representation learning by context and motion decoupling": spec(
        "Context and Motion Decoupling (CMD)", "Pretext / Predictive",
        "Compressed-video keyframes supervise context matching and motion vectors supervise future-motion prediction.",
        "Kinetics-400", "UCF101; HMDB51", "CVPR 2021", "CVPR",
        url="https://openaccess.thecvf.com/content/CVPR2021/html/Huang_Self-Supervised_Video_Representation_Learning_by_Context_and_Motion_Decoupling_CVPR_2021_paper.html", doi="10.1109/CVPR46437.2021.01367", arxiv="2104.00862",
    ),
    "Unsupervised video representation learning by bidirectional feature prediction": spec(
        "Bidirectional Feature Prediction (BFP)", "Pretext / Predictive",
        "Past and future latent features are predicted jointly, with swapped temporal predictions forming hard negatives.",
        "UCF101; Kinetics-400", "UCF101; HMDB51", "WACV 2021", "WACV",
        url="https://openaccess.thecvf.com/content/WACV2021/html/Behrmann_Unsupervised_Video_Representation_Learning_by_Bidirectional_Feature_Prediction_WACV_2021_paper.html", arxiv="2011.06037",
    ),
    "Self-supervised learning of compressed video representations": spec(
        "Compressed Video Representation Learning (CVRL-C)", "Pretext / Predictive",
        "I-frames, motion vectors, and residuals provide complementary self-supervision directly in the compressed-video domain.",
        "Kinetics-400", "Kinetics-400; UCF101; HMDB51", "ICLR 2021", "ICLR",
        url="https://openreview.net/forum?id=jMPcEkJpdD",
    ),
    "Spatiotemporal contrastive video representation learning": spec(
        "CVRL", "Contrastive",
        "Two temporally separated clips receive temporally consistent spatial augmentation and are contrasted as views of one video.",
        "Kinetics-400", "Kinetics-400; UCF101; HMDB51; AVA", "CVPR 2021", "CVPR",
        url="https://openaccess.thecvf.com/content/CVPR2021/html/Qian_Spatio-Temporal_Contrastive_Video_Representation_Learning_CVPR_2021_paper.html", doi="10.1109/CVPR46437.2021.00689", arxiv="2008.03800",
    ),
    "Modist: Motion distillation for self-supervised video representation learning": spec(
        "MoDist", "Distillation / Teacher-Student",
        "An optical-flow teacher distills motion-sensitive targets into an RGB video encoder without flow at inference.",
        "Kinetics-400", "UCF101; HMDB51", "arXiv / Preprint", "arXiv / Preprint",
        status="preprint", url="https://arxiv.org/abs/2106.09703", arxiv="2106.09703", new_title="MoDist: Motion Distillation for Self-Supervised Video Representation Learning",
    ),
    "Broaden your views for self-supervised video learning": spec(
        "BraVe", "Distillation / Teacher-Student",
        "A short-view encoder predicts a momentum target from a much broader temporal view without negative samples.",
        "Kinetics-400", "Kinetics-400; UCF101; HMDB51", "ICCV 2021", "ICCV",
        url="https://openaccess.thecvf.com/content/ICCV2021/html/Recasens_Broaden_Your_Views_for_Self-Supervised_Video_Learning_ICCV_2021_paper.html", doi="10.1109/ICCV48922.2021.00129", arxiv="2103.16559",
    ),
    "Vi2CLR: Video and image for visual contrastive learning of representation": spec(
        "Vi2CLR", "Contrastive",
        "Image and video batches share a contrastive encoder, transferring spatial appearance supervision into spatiotemporal learning.",
        "ImageNet-1K; Kinetics-400", "Kinetics-400; UCF101; HMDB51", "ICCV 2021", "ICCV",
        url="https://openaccess.thecvf.com/content/ICCV2021/html/Diba_Vi2CLR_Video_and_Image_for_Visual_Contrastive_Learning_of_Representation_ICCV_2021_paper.html",
    ),
    "Contrast and order representations for video self-supervised learning": spec(
        "Contrast and Order Representation (CORP)", "Other / Hybrid",
        "Instance contrast is combined with clip-order modeling so the embedding retains appearance and temporal sequence information.",
        "UCF101; Kinetics-400", "UCF101; HMDB51", "ICCV 2021", "ICCV",
        url="https://openaccess.thecvf.com/content/ICCV2021/html/Hu_Contrast_and_Order_Representations_for_Video_Self-Supervised_Learning_ICCV_2021_paper.html", doi="10.1109/ICCV48922.2021.00784",
    ),
    "Motion-augmented self-training for video recognition at smaller scale": spec(
        "MotionFit", "Distillation / Teacher-Student",
        "A small labeled optical-flow teacher pseudo-labels a large unlabeled collection, then an RGB student learns with a multi-clip loss.",
        "Kinetics-400; UCF101; HMDB51", "UCF101; HMDB51", "ICCV 2021", "ICCV",
        url="https://openaccess.thecvf.com/content/ICCV2021/html/Gavrilyuk_Motion-Augmented_Self-Training_for_Video_Recognition_at_Smaller_Scale_ICCV_2021_paper.html", arxiv="2105.01646",
        notes="Kinetics-400 supplies unlabeled self-training video; the small target datasets train the motion teacher and evaluate transfer.",
    ),
    "Video contrastive learning with global context": spec(
        "VCLR", "Contrastive",
        "Segment-level positives capture global video context and temporal-order regularization preserves long-range sequence structure.",
        "Kinetics-400", "Kinetics-400; UCF101; HMDB51; ActivityNet; THUMOS14", "ICCV Workshops 2021", "ICCV Workshops",
        url="https://openaccess.thecvf.com/content/ICCV2021W/CVEU/html/Kuang_Video_Contrastive_Learning_With_Global_Context_ICCVW_2021_paper.html", arxiv="2108.02722",
    ),
    "Motion-focused contrastive learning of video representations": spec(
        "Motion-Focused Contrastive Learning (MCL)", "Contrastive",
        "Optical flow guides tubelet sampling and aligns convolutional gradient maps with spatial and temporal motion patterns.",
        "ImageNet-1K; Kinetics-400; UCF101", "Kinetics-400; UCF101; HMDB51", "ICCV 2021", "ICCV",
        url="https://openaccess.thecvf.com/content/ICCV2021/html/Li_Motion-Focused_Contrastive_Learning_of_Video_Representations_ICCV_2021_paper.html", doi="10.1109/ICCV48922.2021.00211", arxiv="2201.04029",
    ),
    "Back to the Future: Cycle Encoding Prediction for Self-supervised Video Representation Learning": spec(
        "Cycle Encoding Prediction (CEP)", "Pretext / Predictive",
        "Forward and backward temporal cycle encoders are trained so elapsed-time transitions remain predictable and reversible.",
        "UCF101", "UCF101; HMDB51", "BMVC 2021", "BMVC",
        url="https://www.bmva-archive.org.uk/bmvc/2021/assets/papers/0399.pdf", arxiv="2010.07217",
    ),
    "Composable augmentation encoding for video representation learning": spec(
        "Composable Augmentation Encoding (CATE)", "Contrastive",
        "Relative spatial and temporal augmentation parameters are encoded explicitly in the contrastive projection head.",
        "Kinetics-400", "Kinetics-400; UCF101; HMDB51; Something-Something V2; Diving48", "ICCV 2021", "ICCV",
        url="https://openaccess.thecvf.com/content/ICCV2021/html/Sun_Composable_Augmentation_Encoding_for_Video_Representation_Learning_ICCV_2021_paper.html", doi="10.1109/ICCV48922.2021.00871", arxiv="2104.00616",
    ),
    "Learning temporal dynamics from cycles in narrated video": spec(
        "Multimodal Temporal Cycle Consistency (MMCC)", "Multimodal / Audio-Visual",
        "Vision and language dynamics predict forward and backward in time and are constrained to form invertible temporal cycles.",
        "HowTo100M", "CrossTask; COIN; EPIC-KITCHENS-100", "ICCV 2021", "ICCV",
        url="https://openaccess.thecvf.com/content/ICCV2021/html/Epstein_Learning_Temporal_Dynamics_From_Cycles_in_Narrated_Video_ICCV_2021_paper.html", arxiv="2101.02337",
    ),
    "Crossclr: Cross-modal contrastive learning for multi-modal video representations": spec(
        "CrossCLR", "Multimodal / Audio-Visual",
        "Cross-modal contrastive learning removes highly related false negatives using intra-modal similarity and aligns local and global embeddings.",
        "YouCook2; LSMDC", "YouCook2; LSMDC; MSR-VTT", "ICCV 2021", "ICCV",
        url="https://openaccess.thecvf.com/content/ICCV2021/html/Zolfaghari_CrossCLR_Cross-Modal_Contrastive_Learning_for_Multi-Modal_Video_Representations_ICCV_2021_paper.html", arxiv="2109.14910", new_title="CrossCLR: Cross-Modal Contrastive Learning for Multi-Modal Video Representations",
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
    elif data["year"] != 2021:
        paper["audit_notes"] = "The initial 2021 record was reconciled to the final journal volume year."
    paper["audited_at"] = VERIFIED_AS_OF
    paper["discovery_source"] = "exact_title_scholarly_search_then_primary_source"


def main():
    papers = json.loads(PAPERS_PATH.read_text())
    initial = [p for p in papers if p.get("year") == 2021]
    initial_titles = {p["title"] for p in initial}
    if initial_titles != set(SPECS):
        raise SystemExit(f"2021 mapping mismatch: missing={sorted(initial_titles-set(SPECS))}, extra={sorted(set(SPECS)-initial_titles)}")
    for paper in initial:
        apply_spec(paper, SPECS[paper["title"]])

    completed = {}
    years = (2026, 2025, 2024, 2023, 2022, 2021)
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
        "last_checkpoint_at": VERIFIED_AS_OF, "completed_years": list(years), "next_year": 2020,
        "verified_paper_count": verified, "remaining_paper_count": len(papers) - verified,
        "resume_instruction": "Start with 2020. Verify exact-title publication history, fill method and split pretraining/evaluation datasets, rebuild the site, validate the catalog, and save the 2020 checkpoint.",
    })
    progress["year_status"] = {str(year): status_block(year, completed[year]) for year in years}
    progress_path.write_text(json.dumps(progress, indent=2, ensure_ascii=False) + "\n")
    print("Finalized original 2021 cohort and reconciled completed years: " + ", ".join(f"{year}={len(completed[year])}" for year in years))


if __name__ == "__main__":
    main()
