#!/usr/bin/env python3
"""Finalize the 2023 cohort and reconcile later versions of its papers."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
PAPERS_PATH = ROOT / "data" / "papers.json"
AUDITS_DIR = ROOT / "data" / "audits"
VERIFIED_AS_OF = "2026-08-11"


def unique(items):
    return list(dict.fromkeys(items))


def u(
    *, year, venue, venue_normalized, status, method, family, description,
    pretraining, evaluation, paper_url, verification, evidence, doi="",
    arxiv_id="", notes="", audit_notes="", published_date=None,
    title=None, benchmark_suites=None,
):
    out = {
        "year": year,
        "date_label": str(year),
        "venue": venue,
        "venue_normalized": venue_normalized,
        "publication_status": status,
        "method": method,
        "method_family": family,
        "method_description": description,
        "pretraining_datasets": pretraining,
        "evaluation_datasets": evaluation,
        "datasets": unique(pretraining + evaluation),
        "benchmarks": evaluation,
        "benchmark_text": ", ".join(evaluation),
        "dataset_notes": notes,
        "paper_url": paper_url,
        "doi": doi,
        "arxiv_id": arxiv_id,
        "published_date": published_date or str(year),
        "verification_urls": unique(verification),
        "venue_evidence": evidence,
        "audit_notes": audit_notes,
    }
    if title:
        out["title"] = title
        out["normalized_title"] = " ".join(
            "".join(ch.lower() if ch.isalnum() else " " for ch in title).split()
        )
    if benchmark_suites:
        out["benchmark_suites"] = benchmark_suites
    return out


ARXIV = "arxiv_record_and_exact_title_publication_search"
UPDATES = {
    "AdaMAE: Adaptive Masking for Efficient Spatiotemporal Learning with Masked Autoencoders": u(
        year=2023, venue="CVPR 2023", venue_normalized="CVPR", status="peer_reviewed",
        method="AdaMAE", family="Generative / Masked",
        description="An adaptive token sampler learns where to mask so that a masked autoencoder spends reconstruction capacity on informative spatiotemporal regions.",
        pretraining=["Something-Something V2", "Kinetics-400"], evaluation=["Something-Something V2", "Kinetics-400"],
        paper_url="https://openaccess.thecvf.com/content/CVPR2023/html/Bandara_AdaMAE_Adaptive_Masking_for_Efficient_Spatiotemporal_Learning_With_Masked_Autoencoders_CVPR_2023_paper.html",
        verification=["https://openaccess.thecvf.com/content/CVPR2023/html/Bandara_AdaMAE_Adaptive_Masking_for_Efficient_Spatiotemporal_Learning_With_Masked_Autoencoders_CVPR_2023_paper.html", "https://arxiv.org/abs/2211.09120"],
        evidence="official_cvf_proceedings", arxiv_id="2211.09120",
    ),
    "Spatio-Temporal Crop Aggregation for Video Representation Learning": u(
        year=2023, venue="ICCV 2023", venue_normalized="ICCV", status="peer_reviewed",
        method="SCALE", family="Other / Hybrid",
        description="SCALE aggregates a set of frozen-backbone clip features with masked clip modeling and set-level contrastive learning to represent short and long videos.",
        pretraining=["Kinetics-400", "UCF101", "HMDB51", "Something-Something V2"],
        evaluation=["Kinetics-400", "UCF101", "HMDB51", "Something-Something V2", "Long-form Video Understanding (LVU)"],
        paper_url="https://openaccess.thecvf.com/content/ICCV2023/html/Sameni_Spatio-Temporal_Crop_Aggregation_for_Video_Representation_Learning_ICCV_2023_paper.html",
        verification=["https://openaccess.thecvf.com/content/ICCV2023/html/Sameni_Spatio-Temporal_Crop_Aggregation_for_Video_Representation_Learning_ICCV_2023_paper.html", "https://arxiv.org/abs/2211.17042", "https://ieeexplore.ieee.org/document/10377464"],
        evidence="official_cvf_proceedings_and_ieee_record", arxiv_id="2211.17042",
        audit_notes="The arXiv-only venue was promoted to the final ICCV 2023 proceedings record.",
    ),
    "Motion-Guided Masking for Spatiotemporal Representation Learning": u(
        year=2023, venue="ICCV 2023", venue_normalized="ICCV", status="peer_reviewed",
        method="Motion-Guided Masking (MGM)", family="Generative / Masked",
        description="Motion vectors guide the mask distribution toward dynamic regions while retaining a small amount of context for masked video reconstruction.",
        pretraining=["Kinetics-400", "Something-Something V2"],
        evaluation=["Kinetics-400", "Something-Something V2", "UCF101", "HMDB51", "Diving48"],
        paper_url="https://openaccess.thecvf.com/content/ICCV2023/html/Fan_Motion-Guided_Masking_for_Spatiotemporal_Representation_Learning_ICCV_2023_paper.html",
        verification=["https://openaccess.thecvf.com/content/ICCV2023/html/Fan_Motion-Guided_Masking_for_Spatiotemporal_Representation_Learning_ICCV_2023_paper.html", "https://arxiv.org/abs/2308.12962", "https://davidfan.io/publications/"],
        evidence="official_cvf_proceedings", arxiv_id="2308.12962",
    ),
    "Fine-Grained Spatiotemporal Motion Alignment for Contrastive Video Representation Learning": u(
        year=2023, venue="ACM Multimedia 2023", venue_normalized="ACM Multimedia", status="peer_reviewed",
        method="FIMA", family="Contrastive",
        description="Fine-grained motion alignment combines local pixel-level motion reconstruction with global and local contrastive objectives.",
        pretraining=["UCF101", "Kinetics-400"], evaluation=["UCF101", "HMDB51", "Diving48", "Kinetics-400"],
        paper_url="https://dl.acm.org/doi/10.1145/3581783.3611932",
        verification=["https://dl.acm.org/doi/10.1145/3581783.3611932", "https://arxiv.org/abs/2309.00297"],
        evidence="official_acm_version_of_record", doi="10.1145/3581783.3611932", arxiv_id="2309.00297",
    ),
    "Unmasked Teacher: Towards Training-Efficient Video Foundation Models": u(
        year=2023, venue="ICCV 2023", venue_normalized="ICCV", status="peer_reviewed",
        method="Unmasked Teacher (UMT)", family="Distillation / Teacher-Student",
        description="A masked video student aligns its visible tokens to an unmasked CLIP teacher and can be extended with multimodal co-training.",
        pretraining=["Kinetics-710", "Something-Something V2", "Kinetics-400", "WebVid-2M", "WebVid-10M", "Conceptual Captions 3M", "Conceptual Captions 12M", "COCO", "Visual Genome", "SBU Captions"],
        evaluation=["Kinetics-400", "Kinetics-600", "Kinetics-700", "Something-Something V2", "Moments in Time V1", "AVA v2.2", "MSR-VTT", "DiDeMo", "ActivityNet Captions", "LSMDC", "MSVD", "ActivityNet-QA", "MSRVTT-QA", "MSRVTT-MC", "MSVD-QA"],
        paper_url="https://openaccess.thecvf.com/content/ICCV2023/html/Li_Unmasked_Teacher_Towards_Training-Efficient_Video_Foundation_Models_ICCV_2023_paper.html",
        verification=["https://openaccess.thecvf.com/content/ICCV2023/html/Li_Unmasked_Teacher_Towards_Training-Efficient_Video_Foundation_Models_ICCV_2023_paper.html", "https://arxiv.org/abs/2303.16058"],
        evidence="official_cvf_proceedings", arxiv_id="2303.16058",
        notes="The multimodal variants use 5M, 17M, and 25M mixtures assembled from the listed image-text and video-text corpora.",
    ),
    "Concatenated Masked Autoencoders as Spatial-Temporal Learner": u(
        year=2023, venue="arXiv / Preprint", venue_normalized="arXiv / Preprint", status="preprint",
        method="CatMAE", family="Generative / Masked",
        description="The first frame is visible while later frames are 95 percent masked; concatenated visible context reconstructs motion correspondences, aided by Video-Reverse augmentation.",
        pretraining=["Kinetics-400"], evaluation=["DAVIS 2017", "Kinetics-400"],
        paper_url="https://arxiv.org/abs/2311.00961", verification=["https://arxiv.org/abs/2311.00961"],
        evidence=ARXIV, arxiv_id="2311.00961",
        audit_notes="Exact-title and author-record searches found no peer-reviewed version through the verification date.",
    ),
    "AV-MaskEnhancer: Enhancing Video Representations through Audio-Visual Masked Autoencoder": u(
        year=2023, venue="ICTAI 2023", venue_normalized="ICTAI", status="peer_reviewed",
        method="AV-MaskEnhancer", family="Multimodal / Audio-Visual",
        description="An audio-visual masked autoencoder reconstructs masked video content while cross-attention injects synchronized acoustic context.",
        pretraining=["Kinetics-400"], evaluation=["UCF101"],
        paper_url="https://ieeexplore.ieee.org/document/10356561", verification=["https://ieeexplore.ieee.org/document/10356561", "https://arxiv.org/abs/2309.08738"],
        evidence="official_ieee_conference_record", arxiv_id="2309.08738",
    ),
    "OmniMAE: Single Model Masked Pretraining on Images and Videos": u(
        year=2023, venue="CVPR 2023", venue_normalized="CVPR", status="peer_reviewed",
        method="OmniMAE", family="Generative / Masked",
        description="One masked autoencoder is jointly pretrained on images and videos with a shared transformer and modality-specific masking ratios.",
        pretraining=["ImageNet-1K", "Something-Something V2"],
        evaluation=["ImageNet-1K", "iNaturalist 2018", "Places365", "Kinetics-400", "Something-Something V2", "EPIC-KITCHENS-100"],
        paper_url="https://openaccess.thecvf.com/content/CVPR2023/html/Girdhar_OmniMAE_Single_Model_Masked_Pretraining_on_Images_and_Videos_CVPR_2023_paper.html",
        verification=["https://openaccess.thecvf.com/content/CVPR2023/html/Girdhar_OmniMAE_Single_Model_Masked_Pretraining_on_Images_and_Videos_CVPR_2023_paper.html", "https://arxiv.org/abs/2206.08356"],
        evidence="official_cvf_proceedings", arxiv_id="2206.08356",
    ),
    "TimeBalance: Temporally-Invariant and Temporally-Distinctive Video Representations for Semi-Supervised Action Recognition": u(
        year=2023, venue="CVPR 2023", venue_normalized="CVPR", status="peer_reviewed",
        method="TimeBalance", family="Distillation / Teacher-Student",
        description="Temporally invariant and temporally distinctive teacher branches reweight pseudo-label supervision according to temporal similarity.",
        pretraining=["Kinetics-400", "UCF101", "HMDB51"], evaluation=["Kinetics-400", "UCF101", "HMDB51"],
        paper_url="https://openaccess.thecvf.com/content/CVPR2023/html/Dave_TimeBalance_Temporally-Invariant_and_Temporally-Distinctive_Video_Representations_for_Semi-Supervised_Action_Recognition_CVPR_2023_paper.html",
        verification=["https://openaccess.thecvf.com/content/CVPR2023/html/Dave_TimeBalance_Temporally-Invariant_and_Temporally-Distinctive_Video_Representations_for_Semi-Supervised_Action_Recognition_CVPR_2023_paper.html", "https://arxiv.org/abs/2303.16268"],
        evidence="official_cvf_proceedings", arxiv_id="2303.16268",
    ),
    "Self-supervised Video Representation Learning via Capturing Semantic Changes Indicated by Saccades": u(
        year=2024, venue="IEEE Transactions on Circuits and Systems for Video Technology 2024", venue_normalized="IEEE TCSVT", status="peer_reviewed",
        method="Saccade-inspired semantic-change learning", family="Contrastive",
        description="Bio-inspired saccades locate semantic changes for contrastive learning, with fixation consistency and prototypical reorganization objectives.",
        pretraining=["UCF101", "HMDB51"], evaluation=["UCF101", "HMDB51"],
        paper_url="https://ieeexplore.ieee.org/document/10168973", verification=["https://ieeexplore.ieee.org/document/10168973", "https://doi.org/10.1109/TCSVT.2023.3290938"],
        evidence="official_ieee_version_of_record", doi="10.1109/TCSVT.2023.3290938", published_date="2024-08",
        audit_notes="The 2023 early-access record belongs to volume 34, issue 8, published in 2024; the final issue year is used.",
    ),
    "Attentive spatial-temporal contrastive learning for self-supervised video representation": u(
        year=2023, venue="Image and Vision Computing 2023", venue_normalized="Image and Vision Computing", status="peer_reviewed",
        method="ASTCNet", family="Contrastive",
        description="Attentive spatial-temporal contrastive learning combines saliency-aware spatial features with temporal relation modeling.",
        pretraining=["UCF101", "HMDB51"], evaluation=["UCF101", "HMDB51"],
        paper_url="https://www.sciencedirect.com/science/article/pii/S0262885623001397", verification=["https://www.sciencedirect.com/science/article/pii/S0262885623001397", "https://doi.org/10.1016/j.imavis.2023.104765"],
        evidence="official_publisher_version_of_record", doi="10.1016/j.imavis.2023.104765",
    ),
    "MGMAE: Motion Guided Masking for Video Masked Autoencoding": u(
        year=2023, venue="ICCV 2023", venue_normalized="ICCV", status="peer_reviewed",
        method="MGMAE", family="Generative / Masked",
        description="Optical-flow saliency is warped through time to form coherent motion-guided masking volumes for video masked autoencoding.",
        pretraining=["Kinetics-400", "Something-Something V2"], evaluation=["Kinetics-400", "Something-Something V2"],
        paper_url="https://openaccess.thecvf.com/content/ICCV2023/html/Huang_MGMAE_Motion_Guided_Masking_for_Video_Masked_Autoencoding_ICCV_2023_paper.html",
        verification=["https://openaccess.thecvf.com/content/ICCV2023/html/Huang_MGMAE_Motion_Guided_Masking_for_Video_Masked_Autoencoding_ICCV_2023_paper.html", "https://arxiv.org/abs/2308.10794"],
        evidence="official_cvf_proceedings", arxiv_id="2308.10794",
    ),
    "Cross-modal Manifold Cutmix for Self-supervised Video Representation Learning": u(
        year=2023, venue="MVA 2023", venue_normalized="MVA", status="peer_reviewed",
        method="Cross-modal Manifold CutMix (CMMC / STC-mix)", family="Multimodal / Audio-Visual",
        description="Feature-space CutMix exchanges spatiotemporal regions across RGB, optical-flow, and skeleton views to learn cross-modal invariance.",
        pretraining=["UCF101", "HMDB51", "NTU RGB+D 60"], evaluation=["UCF101", "HMDB51", "NTU RGB+D 60"],
        paper_url="https://ieeexplore.ieee.org/document/10216260", verification=["https://ieeexplore.ieee.org/document/10216260"], evidence="official_ieee_conference_record",
    ),
    "CHAIN: Exploring Global-Local Spatio-Temporal Information for Improved Self-Supervised Video Hashing": u(
        year=2023, venue="ACM Multimedia 2023", venue_normalized="ACM Multimedia", status="peer_reviewed",
        method="CHAIN", family="Other / Hybrid",
        description="Global contrastive hashing is combined with frame-order verification and scene-change regularization to retain local temporal information.",
        pretraining=["FCVID", "UCF101", "ActivityNet", "HMDB51"], evaluation=["FCVID", "UCF101", "ActivityNet", "HMDB51"],
        paper_url="https://dl.acm.org/doi/10.1145/3581783.3613440", verification=["https://dl.acm.org/doi/10.1145/3581783.3613440"],
        evidence="official_acm_version_of_record", doi="10.1145/3581783.3613440",
    ),
    "Data-Efficient Masked Video Modeling for Self-supervised Action Recognition": u(
        year=2023, venue="ACM Multimedia 2023", venue_normalized="ACM Multimedia", status="peer_reviewed",
        method="Data-Efficient Masked Video Modeling (DEMVM)", family="Generative / Masked",
        description="Flow-Guided Dense Masking applies denser masks to dynamic regions and sparser masks to background so useful motion is learned from small video datasets.",
        pretraining=["UCF101", "HMDB51"], evaluation=["UCF101", "HMDB51", "Diving48"],
        paper_url="https://dl.acm.org/doi/10.1145/3581783.3612496", verification=["https://dl.acm.org/doi/10.1145/3581783.3612496", "https://www.sigmm.org/opentoc/MM2023-TOC"],
        evidence="official_acm_version_of_record", doi="10.1145/3581783.3612496",
    ),
    "MAR: Masked Autoencoders for Efficient Action Recognition": u(
        year=2024, venue="IEEE Transactions on Multimedia 2024", venue_normalized="IEEE TMM", status="peer_reviewed",
        method="Masked Action Recognition (MAR)", family="Generative / Masked",
        description="Cell-running masks preserve alternating spatiotemporal evidence and a bridging classifier adapts reconstruction features for efficient action recognition.",
        pretraining=["Kinetics-400", "Something-Something V2"], evaluation=["Kinetics-400", "Something-Something V2", "UCF101", "HMDB51"],
        paper_url="https://ieeexplore.ieee.org/document/10089159", verification=["https://ieeexplore.ieee.org/document/10089159", "https://doi.org/10.1109/TMM.2023.3263288", "https://arxiv.org/abs/2207.11660"],
        evidence="official_ieee_version_of_record", doi="10.1109/TMM.2023.3263288", arxiv_id="2207.11660",
        audit_notes="The 2023 early-access article is assigned to IEEE TMM volume 26, pages 218-233, in 2024.",
    ),
    "Temporal Transformer Networks with Self-Supervision for Action Recognition": u(
        year=2023, venue="IEEE Internet of Things Journal 2023", venue_normalized="IEEE Internet of Things Journal", status="peer_reviewed",
        method="Temporal Transformer Self-Supervision Network (TTSN)", family="Pretext / Predictive",
        description="An efficient temporal transformer is trained with random-batch random-channel reversal to recognize and exploit temporal sequence consistency.",
        pretraining=["ImageNet-1K", "Kinetics-400"], evaluation=["HMDB51", "UCF101", "Something-Something V1"],
        paper_url="https://ieeexplore.ieee.org/document/10064011", verification=["https://ieeexplore.ieee.org/document/10064011", "https://doi.org/10.1109/JIOT.2023.3257992", "https://arxiv.org/abs/2112.07338"],
        evidence="official_ieee_version_of_record", doi="10.1109/JIOT.2023.3257992", arxiv_id="2112.07338",
    ),
    "CMAE-V: Contrastive Masked Autoencoders for Video Action Recognition": u(
        year=2023, venue="arXiv / Preprint", venue_normalized="arXiv / Preprint", status="preprint",
        method="CMAE-V", family="Other / Hybrid",
        description="CMAE is extended to video by replacing pixel shift with temporal shift while retaining contrastive and masked reconstruction objectives.",
        pretraining=["Kinetics-400", "Something-Something V2"], evaluation=["Kinetics-400", "Something-Something V2"],
        paper_url="https://arxiv.org/abs/2301.06018", verification=["https://arxiv.org/abs/2301.06018"], evidence=ARXIV, arxiv_id="2301.06018",
        audit_notes="Exact-title and author-record searches found only the arXiv report through the verification date.",
    ),
    "Learning Representational Invariances for Data-Efficient Action Recognition": u(
        year=2023, venue="Computer Vision and Image Understanding 2023", venue_normalized="Computer Vision and Image Understanding", status="peer_reviewed",
        method="Representational-invariance augmentation study", family="Contrastive",
        description="A controlled study learns invariance to temporally coherent photometric, geometric, and temporal transformations, including ActorCutMix.",
        pretraining=["UCF101", "HMDB51", "Kinetics-100", "Kinetics-400", "Mini Something-Something V2"],
        evaluation=["UCF101", "HMDB51", "Kinetics-100", "Mini Something-Something V2"],
        paper_url="https://www.sciencedirect.com/science/article/pii/S1077314222001748", verification=["https://www.sciencedirect.com/science/article/pii/S1077314222001748", "https://doi.org/10.1016/j.cviu.2022.103597", "https://arxiv.org/abs/2103.16565"],
        evidence="official_publisher_version_of_record", doi="10.1016/j.cviu.2022.103597", arxiv_id="2103.16565",
    ),
    "SOR-TC: Self-attentive octave ResNet with temporal consistency for compressed video action recognition": u(
        year=2023, venue="Neurocomputing 2023", venue_normalized="Neurocomputing", status="peer_reviewed",
        method="SOR-TC", family="Pretext / Predictive",
        description="A self-attentive Octave ResNet fuses I-frame, residual, and motion-vector streams while temporal-consistency regularization links multiple clips.",
        pretraining=["UCF101", "HMDB51"], evaluation=["UCF101", "HMDB51"],
        paper_url="https://www.sciencedirect.com/science/article/pii/S0925231223001959", verification=["https://www.sciencedirect.com/science/article/pii/S0925231223001959", "https://doi.org/10.1016/j.neucom.2023.02.045"],
        evidence="official_publisher_version_of_record", doi="10.1016/j.neucom.2023.02.045",
    ),
    "VicTR: Video-conditioned Text Representations for Activity Recognition": u(
        year=2024, venue="CVPR 2024", venue_normalized="CVPR", status="peer_reviewed",
        method="VicTR", family="Multimodal / Audio-Visual",
        description="Video-conditioned text embeddings and visually grounded auxiliary semantics create a flexible contrastive space for activity recognition.",
        pretraining=["Kinetics-400"], evaluation=["HMDB51", "UCF101", "Kinetics-400", "Charades"],
        paper_url="https://openaccess.thecvf.com/content/CVPR2024/html/Kahatapitiya_VicTR_Video-conditioned_Text_Representations_for_Activity_Recognition_CVPR_2024_paper.html",
        verification=["https://openaccess.thecvf.com/content/CVPR2024/html/Kahatapitiya_VicTR_Video-conditioned_Text_Representations_for_Activity_Recognition_CVPR_2024_paper.html", "https://arxiv.org/abs/2304.02560", "https://www3.cs.stonybrook.edu/~kkahatapitiy/"],
        evidence="official_cvf_proceedings", arxiv_id="2304.02560",
        audit_notes="The 2023 arXiv paper was promoted to the CVPR 2024 proceedings.",
    ),
    "Masked Motion Encoding for Self-Supervised Video Representation Learning": u(
        year=2023, venue="CVPR 2023", venue_normalized="CVPR", status="peer_reviewed",
        method="Masked Motion Encoding (MME)", family="Generative / Masked",
        description="Masked motion trajectories derived from dense optical flow are predicted to make the encoder model fine-grained movement rather than appearance alone.",
        pretraining=["Kinetics-400", "Something-Something V2"], evaluation=["Kinetics-400", "Something-Something V2", "UCF101", "HMDB51"],
        paper_url="https://openaccess.thecvf.com/content/CVPR2023/html/Sun_Masked_Motion_Encoding_for_Self-Supervised_Video_Representation_Learning_CVPR_2023_paper.html",
        verification=["https://openaccess.thecvf.com/content/CVPR2023/html/Sun_Masked_Motion_Encoding_for_Self-Supervised_Video_Representation_Learning_CVPR_2023_paper.html", "https://arxiv.org/abs/2210.06096"],
        evidence="official_cvf_proceedings", arxiv_id="2210.06096",
    ),
    "Spatiotemporal consistency enhancement self-supervised representation learning for action recognition": u(
        year=2023, venue="Signal, Image and Video Processing 2023", venue_normalized="Signal, Image and Video Processing", status="peer_reviewed",
        method="Spatiotemporal Consistency Enhancement (STCE)", family="Contrastive",
        description="Motion-preserving augmentation and inserted static frames create spatiotemporal consistency constraints for contrastive action representation learning.",
        pretraining=["UCF101", "HMDB51"], evaluation=["UCF101", "HMDB51"],
        paper_url="https://link.springer.com/article/10.1007/s11760-022-02357-2", verification=["https://link.springer.com/article/10.1007/s11760-022-02357-2", "https://doi.org/10.1007/s11760-022-02357-2"],
        evidence="official_publisher_version_of_record", doi="10.1007/s11760-022-02357-2",
    ),
    "Self-Supervised Video-Based Action Recognition With Disturbances": u(
        year=2023, venue="IEEE Transactions on Image Processing 2023", venue_normalized="IEEE TIP", status="peer_reviewed",
        method="VARD", family="Contrastive",
        description="Visual clip disturbances and semantic embedding disturbances train the model to preserve action-principal information while ignoring actor and scene variations.",
        pretraining=["UCF101", "HMDB51"], evaluation=["UCF101", "HMDB51"],
        paper_url="https://ieeexplore.ieee.org/document/10109672", verification=["https://ieeexplore.ieee.org/document/10109672", "https://doi.org/10.1109/TIP.2023.3269228", "https://pubmed.ncbi.nlm.nih.gov/37099471/"],
        evidence="official_ieee_version_of_record", doi="10.1109/TIP.2023.3269228",
    ),
    "Masked Video Distillation: Rethinking Masked Feature Modeling for Self-supervised Video Representation Learning": u(
        year=2023, venue="CVPR 2023", venue_normalized="CVPR", status="peer_reviewed",
        method="Masked Video Distillation (MVD)", family="Distillation / Teacher-Student",
        description="A masked video student distills complementary targets from frozen image and video teachers instead of reconstructing raw pixels.",
        pretraining=["ImageNet-1K", "Kinetics-400"], evaluation=["Kinetics-400", "Something-Something V2", "UCF101", "HMDB51", "AVA v2.2"],
        paper_url="https://openaccess.thecvf.com/content/CVPR2023/html/Wang_Masked_Video_Distillation_Rethinking_Masked_Feature_Modeling_for_Self-Supervised_Video_Representation_CVPR_2023_paper.html",
        verification=["https://openaccess.thecvf.com/content/CVPR2023/html/Wang_Masked_Video_Distillation_Rethinking_Masked_Feature_Modeling_for_Self-Supervised_Video_Representation_CVPR_2023_paper.html", "https://arxiv.org/abs/2212.04500"],
        evidence="official_cvf_proceedings", arxiv_id="2212.04500",
    ),
    "Enhancing motion visual cues for self-supervised video representation learning": u(
        year=2023, venue="Engineering Applications of Artificial Intelligence 2023", venue_normalized="Engineering Applications of Artificial Intelligence", status="peer_reviewed",
        method="Enhancing Motion Visual Cues (EMVC)", family="Contrastive",
        description="Motion-focused visual cues are enhanced and aligned with appearance representations to reduce static-scene bias in video contrastive learning.",
        pretraining=["UCF101", "HMDB51"], evaluation=["UCF101", "HMDB51"],
        paper_url="https://www.sciencedirect.com/science/article/pii/S0952197623003871", verification=["https://www.sciencedirect.com/science/article/pii/S0952197623003871", "https://doi.org/10.1016/j.engappai.2023.106203"],
        evidence="official_publisher_version_of_record", doi="10.1016/j.engappai.2023.106203",
    ),
    "Continuous frame motion sensitive self-supervised collaborative network for video representation learning": u(
        year=2023, venue="Advanced Engineering Informatics 2023", venue_normalized="Advanced Engineering Informatics", status="peer_reviewed",
        method="Continuous-frame motion-sensitive collaborative network", family="Other / Hybrid",
        description="Collaborative appearance and continuous-frame motion branches learn complementary static and dynamic video representations.",
        pretraining=["UCF101", "HMDB51"], evaluation=["UCF101", "HMDB51"],
        paper_url="https://www.sciencedirect.com/science/article/pii/S1474034623000691", verification=["https://www.sciencedirect.com/science/article/pii/S1474034623000691", "https://doi.org/10.1016/j.aei.2023.101941"],
        evidence="official_publisher_version_of_record", doi="10.1016/j.aei.2023.101941",
    ),
    "Self-supervised pretext task collaborative multi-view contrastive learning for video action recognition": u(
        year=2023, venue="Signal, Image and Video Processing 2023", venue_normalized="Signal, Image and Video Processing", status="peer_reviewed",
        method="Pretext-task collaborative multi-view contrastive learning", family="Other / Hybrid",
        description="A video-cloze pretext task supplies pseudo-categories while consecutive multi-view contrast learns motion characteristics and global semantics.",
        pretraining=["UCF101", "HMDB51"], evaluation=["UCF101", "HMDB51"],
        paper_url="https://link.springer.com/article/10.1007/s11760-023-02605-z", verification=["https://link.springer.com/article/10.1007/s11760-023-02605-z", "https://doi.org/10.1007/s11760-023-02605-z"],
        evidence="official_publisher_version_of_record", doi="10.1007/s11760-023-02605-z",
    ),
    "Self-Supervised Learning from Untrimmed Videos via Hierarchical Consistency": u(
        year=2023, venue="IEEE Transactions on Pattern Analysis and Machine Intelligence 2023", venue_normalized="IEEE TPAMI", status="peer_reviewed",
        method="Hierarchical Consistency Learning (HiCo)", family="Contrastive",
        description="Visual consistency among nearby clips and topical consistency across longer ranges are learned with gradual temporal sampling from untrimmed video.",
        pretraining=["Kinetics-400", "Untrimmed Kinetics-400"], evaluation=["UCF101", "HMDB51", "ActivityNet"],
        paper_url="https://ieeexplore.ieee.org/document/10119224", verification=["https://ieeexplore.ieee.org/document/10119224", "https://doi.org/10.1109/TPAMI.2023.3273415", "https://openaccess.thecvf.com/content/CVPR2022/html/Qing_Learning_From_Untrimmed_Videos_Self-Supervised_Video_Representation_Learning_With_Hierarchical_CVPR_2022_paper.html"],
        evidence="official_ieee_version_of_record", doi="10.1109/TPAMI.2023.3273415",
        notes="The journal study compares standard Kinetics-400 with a 157K-video Untrimmed Kinetics-400 corpus and evaluates action localization on ActivityNet.",
    ),
    "Self-Supervised Video Representation Learning by Video Incoherence Detection": u(
        year=2024, venue="IEEE Transactions on Cybernetics 2024", venue_normalized="IEEE Transactions on Cybernetics", status="peer_reviewed",
        method="Video Incoherence Detection (VID)", family="Pretext / Predictive",
        description="Hierarchically sampled subclips create incoherence whose location and duration are predicted, with intra-video contrastive regularization.",
        pretraining=["UCF101", "HMDB51", "Kinetics-400"], evaluation=["UCF101", "HMDB51", "Kinetics-400"],
        paper_url="https://ieeexplore.ieee.org/document/10106103", verification=["https://ieeexplore.ieee.org/document/10106103", "https://doi.org/10.1109/TCYB.2023.3265393", "https://arxiv.org/abs/2109.12493"],
        evidence="official_ieee_version_of_record", doi="10.1109/TCYB.2023.3265393", arxiv_id="2109.12493", published_date="2024-06",
        audit_notes="The 2023 early-access article is assigned to volume 54, issue 6, pages 3810-3822, in 2024.",
    ),
    "Audio-Visual Contrastive Learning with Temporal Self-Supervision": u(
        year=2023, venue="AAAI 2023", venue_normalized="AAAI", status="peer_reviewed",
        method="Audio-visual contrastive learning with temporal self-supervision", family="Multimodal / Audio-Visual",
        description="Nearest-neighbor contrastive pairs are combined with playback speed, direction, and intra- and cross-modal temporal ordering tasks.",
        pretraining=["Kinetics-600", "Kinetics-400"], evaluation=["UCF101", "HMDB51", "ESC-50", "VGGSound", "Kinetics-600"],
        paper_url="https://ojs.aaai.org/index.php/AAAI/article/view/25967", verification=["https://ojs.aaai.org/index.php/AAAI/article/view/25967", "https://doi.org/10.1609/aaai.v37i7.25967", "https://arxiv.org/abs/2302.07702"],
        evidence="official_aaai_proceedings", doi="10.1609/aaai.v37i7.25967", arxiv_id="2302.07702",
        audit_notes="The catalog's preprint label was replaced with the AAAI 2023 version of record.",
    ),
    "Video Test-Time Adaptation for Action Recognition": u(
        year=2023, venue="CVPR 2023", venue_normalized="CVPR", status="peer_reviewed",
        method="ViTTA", family="Other / Hybrid",
        description="Online test-time adaptation aligns test feature statistics with stored source statistics and enforces prediction consistency across temporal views.",
        pretraining=["Kinetics-400", "ImageNet-1K"], evaluation=["UCF101", "Something-Something V2", "Kinetics-400", "UCF101-C", "Something-Something V2-C", "Kinetics-400-C"],
        paper_url="https://openaccess.thecvf.com/content/CVPR2023/html/Lin_Video_Test-Time_Adaptation_for_Action_Recognition_CVPR_2023_paper.html",
        verification=["https://openaccess.thecvf.com/content/CVPR2023/html/Lin_Video_Test-Time_Adaptation_for_Action_Recognition_CVPR_2023_paper.html", "https://doi.org/10.1109/CVPR52729.2023.02198", "https://arxiv.org/abs/2211.15393"],
        evidence="official_cvf_proceedings", doi="10.1109/CVPR52729.2023.02198", arxiv_id="2211.15393",
        notes="The corrupted benchmark variants cover 12 common video corruptions.",
        audit_notes="The previous arXiv ID pointed to an unrelated record and was corrected to 2211.15393.",
    ),
    "Self-Supervised Video Representation Learning via Latent Time Navigation": u(
        year=2023, venue="AAAI 2023", venue_normalized="AAAI", status="peer_reviewed",
        method="Latent Time Navigation (LTN)", family="Contrastive",
        description="A time-parameterized contrastive objective preserves temporal displacement along an orthogonal latent subspace instead of enforcing full temporal invariance.",
        pretraining=["Kinetics-400"], evaluation=["Toyota Smarthome", "Kinetics-400", "UCF101", "HMDB51"],
        paper_url="https://ojs.aaai.org/index.php/AAAI/article/view/25416", verification=["https://ojs.aaai.org/index.php/AAAI/article/view/25416", "https://doi.org/10.1609/aaai.v37i3.25416", "https://arxiv.org/abs/2305.06437"],
        evidence="official_aaai_proceedings", doi="10.1609/aaai.v37i3.25416", arxiv_id="2305.06437",
        audit_notes="The catalog's preprint label was replaced with the AAAI 2023 version of record.",
    ),
    "Temporal Contrastive Learning with Curriculum": u(
        year=2023, venue="ICASSP 2023", venue_normalized="ICASSP", status="peer_reviewed",
        method="Contrastive Curriculum Learning (ConCur)", family="Contrastive",
        description="A curriculum progressively enlarges the temporal gap between positives and pairs contrastive learning with temporal-distance prediction.",
        pretraining=["Kinetics-400", "Kinetics-200"], evaluation=["UCF101", "HMDB51"],
        paper_url="https://ieeexplore.ieee.org/document/10095948", verification=["https://ieeexplore.ieee.org/document/10095948", "https://arxiv.org/abs/2209.00760"],
        evidence="official_ieee_conference_record", arxiv_id="2209.00760",
    ),
    "Nearest-Neighbor Inter-Intra Contrastive Learning from Unlabeled Videos": u(
        year=2023, venue="ICLR Workshops 2023", venue_normalized="ICLR Workshops", status="peer_reviewed",
        method="Inter-Intra Video Contrastive Learning (IIVCL)", family="Contrastive",
        description="Global nearest-neighbor videos supply additional positive keys alongside standard intra-video clips, increasing semantic positive diversity.",
        pretraining=["Kinetics-400"], evaluation=["UCF101", "HMDB51", "Kinetics-400", "Something-Something V2", "AVA"],
        paper_url="https://openreview.net/forum?id=-5_B8g3CcSr", verification=["https://openreview.net/forum?id=-5_B8g3CcSr", "https://iclr.cc/media/iclr-2023/Slides/13624.pdf", "https://arxiv.org/abs/2303.07317", "https://davidfan.io/publications/"],
        evidence="official_iclr_workshop_openreview_and_program", arxiv_id="2303.07317",
        audit_notes="The arXiv comments and official workshop materials confirm acceptance at the ICLR 2023 ME-FoMo workshop.",
    ),
    "Tubelet-Contrastive Self-Supervision for Video-Efficient Generalization": u(
        year=2023, venue="ICCV 2023", venue_normalized="ICCV", status="peer_reviewed",
        method="Tubelet-Contrastive", family="Contrastive",
        description="Synthetic tubelets with shared local motion but changed appearance create motion-focused contrastive pairs that remain effective with less pretraining data.",
        pretraining=["Kinetics-400", "Mini-Kinetics"],
        evaluation=["UCF101", "HMDB51", "Something-Something V2", "FineGym Gym99", "FineGym FX-S1", "FineGym UB-S1", "UCFRep", "Charades", "Diving48"],
        paper_url="https://openaccess.thecvf.com/content/ICCV2023/html/Thoker_Tubelet-Contrastive_Self-Supervision_for_Video-Efficient_Generalization_ICCV_2023_paper.html",
        verification=["https://openaccess.thecvf.com/content/ICCV2023/html/Thoker_Tubelet-Contrastive_Self-Supervision_for_Video-Efficient_Generalization_ICCV_2023_paper.html", "https://arxiv.org/abs/2303.11003"],
        evidence="official_cvf_proceedings", arxiv_id="2303.11003", benchmark_suites=["SEVERE"],
        audit_notes="The catalog's preprint label was replaced with the ICCV 2023 proceedings record.",
    ),
    "Multi-scale Compositional Constraints for Representation Learning on Videos": u(
        year=2023, venue="ICASSP 2023", venue_normalized="ICASSP", status="peer_reviewed",
        method="Multi-scale compositional AVID-CMA", family="Multimodal / Audio-Visual",
        description="Explicit regression or implicit contrastive composition constrains a coarse clip representation to agree with its constituent fine temporal segments.",
        pretraining=["AudioSet"], evaluation=["UCF101", "SumMe"],
        paper_url="https://www.amazon.science/publications/multi-scale-compositional-constraints-for-representation-learning-on-videos",
        verification=["https://www.amazon.science/publications/multi-scale-compositional-constraints-for-representation-learning-on-videos", "https://ieeexplore.ieee.org/document/10096573"],
        evidence="official_amazon_publication_page_and_ieee_record",
        notes="Experiments initialize from an AVID-CMA checkpoint pretrained on the balanced 18K subset of AudioSet.",
    ),
    "Flavr: Flow-agnostic Video Representations for Fast Frame Interpolation": u(
        year=2023, venue="WACV 2023", venue_normalized="WACV", status="peer_reviewed",
        method="FLAVR", family="Pretext / Predictive",
        description="A flow-free 3D U-Net learns multi-frame interpolation as a self-supervised pretext whose features transfer to recognition, flow, and segmentation.",
        pretraining=["Vimeo-90K", "GoPro"],
        evaluation=["Vimeo-90K", "UCF101", "DAVIS", "Adobe-240FPS", "GoPro", "SNU-FILM", "Middlebury", "HMDB51", "MPI Sintel", "KITTI", "DAVIS 2017"],
        paper_url="https://openaccess.thecvf.com/content/WACV2023/html/Kalluri_FLAVR_Flow-Agnostic_Video_Representations_for_Fast_Frame_Interpolation_WACV_2023_paper.html",
        verification=["https://openaccess.thecvf.com/content/WACV2023/html/Kalluri_FLAVR_Flow-Agnostic_Video_Representations_for_Fast_Frame_Interpolation_WACV_2023_paper.html"], evidence="official_cvf_proceedings",
    ),
    "HomE: Homography-Equivariant Video Representation Learning": u(
        year=2023, venue="arXiv / Preprint", venue_normalized="arXiv / Preprint", status="preprint",
        method="HomE", family="Pretext / Predictive",
        description="Vector-neuron features are trained to transform equivariantly with known homographies between views rather than collapsing the views to one invariant embedding.",
        pretraining=["Synthetic CIFAR-10", "UCF101", "Stanford-TRI Intent Prediction"], evaluation=["Synthetic CIFAR-10", "UCF101", "Stanford-TRI Intent Prediction"],
        paper_url="https://arxiv.org/abs/2306.01623", verification=["https://arxiv.org/abs/2306.01623"], evidence=ARXIV, arxiv_id="2306.01623",
        audit_notes="Exact-title and author-record searches found no peer-reviewed version through the verification date.",
    ),
    "ViewCLR: Learning Self-supervised Video Representation for Unseen Viewpoints": u(
        year=2023, venue="WACV 2023", venue_normalized="WACV", status="peer_reviewed",
        method="ViewCLR", family="Contrastive",
        description="A learnable viewpoint generator and contrastive objective synthesize view variations so action representations generalize to unseen cameras.",
        pretraining=["NTU RGB+D 60", "NTU RGB+D 120", "Northwestern-UCLA"], evaluation=["NTU RGB+D 60", "NTU RGB+D 120", "Northwestern-UCLA"],
        paper_url="https://openaccess.thecvf.com/content/WACV2023/html/Das_ViewCLR_Learning_Self-Supervised_Video_Representation_for_Unseen_Viewpoints_WACV_2023_paper.html",
        verification=["https://openaccess.thecvf.com/content/WACV2023/html/Das_ViewCLR_Learning_Self-Supervised_Video_Representation_for_Unseen_Viewpoints_WACV_2023_paper.html"], evidence="official_cvf_proceedings",
    ),
    "Videomae v2: Scaling Video Masked Autoencoders with Dual Masking": u(
        year=2023, venue="CVPR 2023", venue_normalized="CVPR", status="peer_reviewed",
        method="VideoMAE V2", family="Generative / Masked",
        description="Dual encoder-decoder masking enables billion-parameter masked video pretraining, followed by progressive labeled post-pretraining.",
        pretraining=["UnlabeledHybrid", "LabeledHybrid", "Kinetics-400", "Kinetics-600", "Kinetics-700", "Something-Something V2", "AVA", "WebVid-2M", "Instagram videos"],
        evaluation=["Kinetics-400", "Kinetics-600", "Something-Something V1", "Something-Something V2", "UCF101", "HMDB51", "AVA", "AVA-Kinetics", "THUMOS14", "FineAction"],
        paper_url="https://openaccess.thecvf.com/content/CVPR2023/html/Wang_VideoMAE_V2_Scaling_Video_Masked_Autoencoders_With_Dual_Masking_CVPR_2023_paper.html",
        verification=["https://openaccess.thecvf.com/content/CVPR2023/html/Wang_VideoMAE_V2_Scaling_Video_Masked_Autoencoders_With_Dual_Masking_CVPR_2023_paper.html"], evidence="official_cvf_proceedings",
        notes="UnlabeledHybrid has about 1.35M clips from public datasets and web sources; LabeledHybrid aligns Kinetics-400/600/700 into 710 categories and about 0.66M clips.",
    ),
    "Self-Supervised Audio-Visual Representation Learning with Relaxed Cross-Modal Synchronicity": u(
        year=2023, venue="AAAI 2023", venue_normalized="AAAI", status="peer_reviewed",
        method="CrissCross", family="Multimodal / Audio-Visual",
        description="Intra-modal, synchronous cross-modal, and relaxed asynchronous cross-modal objectives learn audio and video representations jointly.",
        pretraining=["Kinetics-Sounds", "Kinetics-400", "AudioSet"], evaluation=["Kinetics-400", "UCF101", "HMDB51", "ESC-50", "DCASE"],
        paper_url="https://ojs.aaai.org/index.php/AAAI/article/view/25138", verification=["https://ojs.aaai.org/", "https://arxiv.org/abs/2111.05329"], evidence="official_aaai_proceedings_and_arxiv_record", arxiv_id="2111.05329",
    ),
    "Spatiotemporally Discriminative Video-Language Pre-Training with Text Grounding": u(
        year=2024, venue="ICLR 2024", venue_normalized="ICLR", status="peer_reviewed",
        method="S-ViLM", family="Multimodal / Audio-Visual",
        description="Inter-clip spatial grounding aligns learned region groups with nouns, while intra-clip temporal grouping detects cut-and-paste scene changes.",
        pretraining=["Kinetics-400", "VideoCC", "ActivityNet Captions"], evaluation=["MSR-VTT", "MSRVTT-QA", "MSVD-QA", "UCF101", "HMDB51", "ActivityNet"],
        paper_url="https://openreview.net/forum?id=5dlfiJIXoh", verification=["https://openreview.net/forum?id=5dlfiJIXoh", "https://iclr.cc/media/iclr-2024/Slides/19422.pdf", "https://arxiv.org/abs/2303.16341"],
        evidence="official_iclr_openreview_record_and_program", arxiv_id="2303.16341",
        title="Structured Video-Language Modeling with Temporal Grouping and Spatial Grounding",
        audit_notes="The 2023 arXiv title changed before publication; the final ICLR 2024 title and venue are now used, with the former title retained in previous_titles.",
    ),
    "Previts: contrastive pretraining with video tracking supervision": u(
        year=2023, venue="WACV 2023", venue_normalized="WACV", status="peer_reviewed",
        method="PreViTS", family="Contrastive",
        description="Unsupervised tracks choose object-consistent positive crops and a Grad-CAM attention loss focuses MoCo features on the tracked foreground.",
        pretraining=["VGGSound", "Kinetics-400"], evaluation=["UCF101", "ImageNet-1K", "DAVIS", "JHMDB", "Backgrounds Challenge"],
        paper_url="https://openaccess.thecvf.com/content/WACV2023/html/Chen_PreViTS_Contrastive_Pretraining_With_Video_Tracking_Supervision_WACV_2023_paper.html",
        verification=["https://openaccess.thecvf.com/content/WACV2023/html/Chen_PreViTS_Contrastive_Pretraining_With_Video_Tracking_Supervision_WACV_2023_paper.html", "https://arxiv.org/abs/2112.00804"], evidence="official_cvf_proceedings", arxiv_id="2112.00804",
    ),
    "Modeling Video As Stochastic Processes for Fine-Grained Video Representation Learning": u(
        year=2023, venue="CVPR 2023", venue_normalized="CVPR", status="peer_reviewed",
        method="Video Stochastic Processes (VSP)", family="Contrastive",
        description="A Brownian-bridge phase process, supervised contrastive branch, and global cycle consistency model fine-grained action progression.",
        pretraining=["ImageNet-1K", "Penn Action", "Pouring", "IKEA ASM", "FineGym"], evaluation=["Penn Action", "Pouring", "IKEA ASM", "FineGym Gym99", "FineGym Gym288"],
        paper_url="https://openaccess.thecvf.com/content/CVPR2023/html/Zhang_Modeling_Video_As_Stochastic_Processes_for_Fine-Grained_Video_Representation_Learning_CVPR_2023_paper.html",
        verification=["https://openaccess.thecvf.com/content/CVPR2023/html/Zhang_Modeling_Video_As_Stochastic_Processes_for_Fine-Grained_Video_Representation_Learning_CVPR_2023_paper.html"], evidence="official_cvf_proceedings",
    ),
    "Learning Fine-Grained Features for Pixel-wise Video Correspondences": u(
        year=2023, venue="ICCV 2023", venue_normalized="ICCV", status="peer_reviewed",
        method="Adversarial fine-grained correspondence learning", family="Pretext / Predictive",
        description="Synthetic flow supervision, unlabeled real-video reconstruction, adversarial domain alignment, and coarse-to-fine mapping learn efficient pixel correspondences.",
        pretraining=["FlyingThings3D", "YouTube-VOS"], evaluation=["BADJA", "JHMDB", "TAP-Vid-DAVIS", "TAP-Vid-Kinetics", "DAVIS 2017"],
        paper_url="https://openaccess.thecvf.com/content/ICCV2023/html/Li_Learning_Fine-Grained_Features_for_Pixel-Wise_Video_Correspondences_ICCV_2023_paper.html",
        verification=["https://openaccess.thecvf.com/content/ICCV2023/html/Li_Learning_Fine-Grained_Features_for_Pixel-Wise_Video_Correspondences_ICCV_2023_paper.html", "https://doi.org/10.1109/ICCV51070.2023.00883", "https://arxiv.org/abs/2308.03040"],
        evidence="official_cvf_proceedings", doi="10.1109/ICCV51070.2023.00883", arxiv_id="2308.03040",
        audit_notes="The catalog's preprint label was replaced with the ICCV 2023 proceedings record.",
    ),
    "Cali-NCE: Boosting Cross-Modal Video Representation Learning With Calibrated Alignment": u(
        year=2023, venue="CVPR Workshops 2023", venue_normalized="CVPR Workshops", status="peer_reviewed",
        method="Cali-NCE", family="Multimodal / Audio-Visual",
        description="A calibrated cross-modal NCE objective estimates pair-specific alignment confidence and downweights noisy video-text correspondences.",
        pretraining=["WebVid-2M"], evaluation=["MSR-VTT", "MSVD", "UCF101", "HMDB51"],
        paper_url="https://openaccess.thecvf.com/content/CVPR2023W/WFM/html/Zhao_Cali-NCE_Boosting_Cross-Modal_Video_Representation_Learning_With_Calibrated_Alignment_CVPRW_2023_paper.html",
        verification=["https://openaccess.thecvf.com/content/CVPR2023W/WFM/html/Zhao_Cali-NCE_Boosting_Cross-Modal_Video_Representation_Learning_With_Calibrated_Alignment_CVPRW_2023_paper.html"], evidence="official_cvf_workshop_proceedings",
        notes="The controlled robustness experiment trains on a randomly selected one-sixth subset of WebVid-2M.",
    ),
}


ALREADY_COMPLETE = {
    "Self-supervised object-centric learning for videos",
    "Language-based Action Concept Spaces Improve Video Self-Supervised Learning",
    "Uncovering the Hidden Dynamics of Video Self-supervised Learning under Distribution Shifts",
    "Self-supervised video pretraining yields robust and more human-aligned visual representation",
}

AUDIT_UPDATE_FIELDS = [
    "year", "date_label", "venue", "venue_normalized", "publication_status",
    "method", "method_family", "method_description", "pretraining_datasets",
    "evaluation_datasets", "datasets", "benchmarks", "benchmark_suites",
    "benchmark_text", "dataset_notes", "paper_url", "code_url", "project_url",
    "doi", "arxiv_id", "published_date", "verification_urls", "venue_evidence",
    "audit_notes", "previous_titles",
]


def audit_updates(paper):
    return {key: paper[key] for key in AUDIT_UPDATE_FIELDS if key in paper}


def write_audit(year, papers):
    records = [{"normalized_title": p["normalized_title"], "updates": audit_updates(p)} for p in papers]
    payload = {
        "schema_version": 1,
        "year": year,
        "status": "complete",
        "verified_as_of": VERIFIED_AS_OF,
        "paper_count": len(records),
        "source_policy": "Use exact-title scholarly discovery, then verify venue and metadata against an official conference, publisher, DOI, or preprint record. Do not promote a search-result venue without primary-source confirmation.",
        "dataset_policy": "Record separately the datasets used for self-supervised or backbone pretraining and the datasets used for downstream evaluation. Preserve named benchmark suites, document primary-source access limits, and do not silently guess.",
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


def main():
    papers = json.loads(PAPERS_PATH.read_text())
    initial = [p for p in papers if p.get("year") == 2023]
    initial_titles = {p["title"] for p in initial}
    expected = set(UPDATES) | ALREADY_COMPLETE
    if initial_titles != expected:
        raise SystemExit(f"2023 mapping mismatch: missing={sorted(initial_titles-expected)}, extra={sorted(expected-initial_titles)}")

    for paper in initial:
        old_title = paper["title"]
        if old_title in UPDATES:
            update = UPDATES[old_title]
            if update.get("title") and update["title"] != old_title:
                paper["previous_titles"] = unique(paper.get("previous_titles", []) + [old_title])
            paper.update(update)
        paper["audited_at"] = VERIFIED_AS_OF
        paper["discovery_source"] = "exact_title_scholarly_search_then_primary_source"

    completed = {}
    for year in (2026, 2025, 2024, 2023):
        year_papers = [p for p in papers if p.get("year") == year]
        for paper in year_papers:
            paper["audit_status"] = "verified"
            paper["audit_year"] = year
            paper["audited_at"] = VERIFIED_AS_OF
        completed[year] = year_papers

    PAPERS_PATH.write_text(json.dumps(papers, indent=2, ensure_ascii=False) + "\n")
    for year, year_papers in completed.items():
        write_audit(year, year_papers)

    verified = sum(len(items) for items in completed.values())
    progress_path = ROOT / "data" / "audit_progress.json"
    progress = json.loads(progress_path.read_text())
    progress.update({
        "last_checkpoint_at": VERIFIED_AS_OF,
        "completed_years": [2026, 2025, 2024, 2023],
        "next_year": 2022,
        "verified_paper_count": verified,
        "remaining_paper_count": len(papers) - verified,
        "resume_instruction": "Start with 2022. Verify exact-title publication history, fill method and split pretraining/evaluation datasets, rebuild the site, validate the catalog, and save the 2022 checkpoint.",
    })
    progress["year_status"] = {str(year): status_block(year, completed[year]) for year in (2026, 2025, 2024, 2023)}
    progress_path.write_text(json.dumps(progress, indent=2, ensure_ascii=False) + "\n")
    print("Finalized 2023 and reconciled completed years: " + ", ".join(f"{year}={len(completed[year])}" for year in (2026, 2025, 2024, 2023)))


if __name__ == "__main__":
    main()
