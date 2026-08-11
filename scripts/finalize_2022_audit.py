#!/usr/bin/env python3
"""Finalize the original 2022 cohort and reconcile its later versions."""

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


def s(value):
    return [item.strip() for item in value.split(";") if item.strip()]


def norm_title(value):
    return " ".join("".join(ch.lower() if ch.isalnum() else " " for ch in value).split())


def meta(method, family, description, pretraining, evaluation, notes=""):
    return {
        "method": method,
        "method_family": family,
        "method_description": description,
        "pretraining_datasets": s(pretraining),
        "evaluation_datasets": s(evaluation),
        "dataset_notes": notes,
    }


META = {
    "BEVT: BERT Pretraining of Video Transformers": meta(
        "BEVT", "Generative / Masked",
        "A bidirectional image tokenizer and image and video teachers supervise masked visual-token prediction in a shared video transformer.",
        "ImageNet-1K; Kinetics-400; Something-Something V2; HowTo100M",
        "Kinetics-400; Something-Something V2; Diving48",
    ),
    "Masked Autoencoders As Spatiotemporal Learners": meta(
        "MAE-ST", "Generative / Masked",
        "A spatiotemporal masked autoencoder reconstructs randomly masked RGB tubelets using a high mask ratio and a lightweight decoder.",
        "ImageNet-1K; Kinetics-400; Kinetics-600; Kinetics-700; Instagram videos",
        "Kinetics-400; AVA v2.2; Something-Something V2",
    ),
    "SPAct: Self-supervised Privacy Preservation for Action Recognition": meta(
        "SPAct", "Other / Hybrid",
        "Adversarial self-supervision suppresses privacy attributes while preserving features that remain useful for action recognition.",
        "UCF101; HMDB51; PA-HMDB; VISPR; P-HVU",
        "UCF101; HMDB51; PA-HMDB; VISPR; P-HVU",
    ),
    "Suppressing Static Visual Cues via Normalizing Flows for Self-Supervised Video Representation Learning": meta(
        "Static-cue suppression with normalizing flows", "Contrastive",
        "A normalizing-flow branch models and removes static visual shortcuts so contrastive learning emphasizes temporal evidence.",
        "Kinetics-400; UCF101; HMDB51", "Kinetics-400; UCF101; HMDB51",
    ),
    "Self-supervised Video Representation Learning with Motion-Aware Masked Autoencoders": meta(
        "MotionMAE", "Generative / Masked",
        "Motion-aware masking selects dynamic regions for reconstruction and jointly models appearance and motion with spatial and temporal heads.",
        "Kinetics-400; Something-Something V2",
        "Kinetics-400; Something-Something V2; UCF101; HMDB51; DAVIS 2017",
    ),
    "Self-supervised Video Transformer": meta(
        "SVT", "Distillation / Teacher-Student",
        "A Siamese video transformer learns from local and global views with temporal consistency and teacher-student feature alignment.",
        "Kinetics-400", "Kinetics-400; UCF101; HMDB51; Something-Something V2",
    ),
    "Exploring Relations in Untrimmed Videos for Self-Supervised Learning": meta(
        "ERUV", "Pretext / Predictive",
        "Shot-level, video-level, and dataset-level co-occurrence relations plus rotation prediction provide supervision from untrimmed video.",
        "THUMOS14; UCF101", "UCF101; HMDB51",
    ),
    "MaMiCo: Macro-to-Micro Semantic Correspondence for Self-supervised Video Representation Learning": meta(
        "MaMiCo", "Contrastive",
        "Nested video, clip, and frame pyramids impose macro-to-micro spatial and temporal semantic correspondence.",
        "AVA; AVA-Kinetics; JHMDB-21; UCF101-24", "AVA; AVA-Kinetics; JHMDB-21; UCF101-24",
        "The paper reports action-detection protocols; the listed corpora are used across representation learning and downstream evaluation.",
    ),
    "TCGL: Temporal Contrastive Graph for Self-Supervised Video Representation Learning": meta(
        "TCGL", "Contrastive",
        "A temporal contrastive graph connects intra-snippet and inter-snippet relations to learn short- and long-range dynamics.",
        "UCF101; Kinetics-400", "UCF101; HMDB51; Something-Something V2",
    ),
    "Cross-Architecture Self-supervised Video Representation Learning": meta(
        "CACL", "Contrastive",
        "CNN and transformer encoders contrast cross-architecture representations while predicting temporal shuffle degree.",
        "UCF101; Kinetics-400", "UCF101; HMDB51",
    ),
    "Contrastive spatio-temporal pretext learning for self-supervised video representation": meta(
        "CSTP", "Other / Hybrid",
        "Spatial and temporal transformation prediction is combined with instance contrastive learning.",
        "UCF101; Kinetics-400", "UCF101; HMDB51",
    ),
    "Transrank: Self-supervised video representation learning via ranking-based transformation recognition": meta(
        "TransRank", "Pretext / Predictive",
        "The encoder ranks relative strengths of temporal and spatial transformations instead of assigning isolated transformation classes.",
        "Mini-Kinetics-200; Something-Something V1", "Mini-Kinetics-200; Something-Something V1; UCF101; HMDB51",
    ),
    "Learning from untrimmed videos: Self-supervised video representation learning with hierarchical consistency": meta(
        "HiCo", "Contrastive",
        "Clip-level and video-level objectives enforce hierarchical consistency across untrimmed videos.",
        "Kinetics-400", "Kinetics-400; UCF101; HMDB51; ActivityNet",
    ),
    "Motion-aware contrastive video representation learning via foreground-background merging": meta(
        "FAME", "Contrastive",
        "Foregrounds are merged with unrelated backgrounds to break scene shortcuts while preserving action motion for contrastive learning.",
        "Kinetics-400", "Kinetics-400; UCF101; HMDB51; Diving48",
    ),
    "Self-Supervised Video Representation Learning with Motion-Contrastive Perception": meta(
        "MCP", "Contrastive",
        "Long-range residual motion clips are contrasted with ordinary RGB clips to emphasize motion-sensitive features.",
        "Kinetics-100; Kinetics-400", "Kinetics-100; Kinetics-400; UCF101; HMDB51",
    ),
    "Self-supervised video representation learning using improved instance-wise contrastive learning and deep clustering": meta(
        "Improved instance contrast plus deep clustering", "Contrastive",
        "Temporal semantic positives and cluster pseudo-labels extend instance-wise contrastive learning beyond individual clips.",
        "UCF101; Kinetics-400", "UCF101; HMDB51",
    ),
    "TCLR: Temporal contrastive learning for video representation": meta(
        "TCLR", "Contrastive",
        "Instance-level and group-level temporal contrastive losses distinguish clips while preserving temporal structure within each video.",
        "UCF101; Kinetics-400", "UCF101; HMDB51; Diving48; Kinetics-400",
    ),
    "Self-supervised motion perception for spatiotemporal representation learning": meta(
        "Self-Supervised Motion Perception (SMP)", "Pretext / Predictive",
        "Discriminative and generative playback-rate tasks, motion attention, and multi-granularity prediction teach motion-sensitive representations.",
        "UCF101; Kinetics-400", "UCF101; HMDB51",
    ),
    "Self-supervised spatiotemporal representation learning by exploiting video continuity": meta(
        "CPNet", "Pretext / Predictive",
        "Continuity justification, discontinuity localization, and missing-section approximation model temporal continuity at multiple levels.",
        "Kinetics-400", "UCF101; HMDB51; Diving48; ActivityNet",
    ),
    "Similarity Contrastive Estimation for Image and Video Soft Contrastive Self-Supervised Learning": meta(
        "Similarity Contrastive Estimation (SCE)", "Contrastive",
        "A soft target distribution blends instance identity with target-branch similarities to retain meaningful relations among negatives.",
        "ImageNet-1K; ImageNet-100; Kinetics-200; Kinetics-400",
        "CIFAR-10; CIFAR-100; STL-10; Tiny ImageNet; PASCAL VOC 2007; COCO; UCF101; HMDB51; Kinetics-400; AVA; Something-Something V2",
    ),
    "Probabilistic representations for video contrastive learning": meta(
        "Probabilistic Video Contrastive Learning", "Contrastive",
        "Video embeddings are learned as distributions with uncertainty rather than as deterministic points in contrastive space.",
        "Kinetics-400", "UCF101; HMDB51; ActivityNet",
    ),
    "Contextualized spatio-temporal contrastive learning with self-supervision": meta(
        "ConST-CL", "Contrastive",
        "Contextualized spatial and temporal contrastive objectives align local tokens and global video representations.",
        "Kinetics-400", "Kinetics-400; UCF101; HMDB51; AVA",
    ),
    "Videomae: Masked autoencoders are data-efficient learners for self-supervised video pre-training": meta(
        "VideoMAE", "Generative / Masked",
        "A tube-masked autoencoder reconstructs pixels from very sparse visible video tokens.",
        "Kinetics-400; Something-Something V2; UCF101; HMDB51", "Kinetics-400; Something-Something V2; UCF101; HMDB51",
    ),
    "Efficient Video Representation Learning via Masked Video Modeling with Motion-centric Token Selection": meta(
        "EVEREST", "Generative / Masked",
        "Motion-rich frames and tokens are retained while redundant spatiotemporal tokens are removed during masked pretraining and fine-tuning.",
        "Kinetics-400; Something-Something V2; Ego4D", "Kinetics-400; Something-Something V2; UCF101; HMDB51; Ego4D",
    ),
    "Self-supervised video representation learning with cross-stream prototypical contrasting": meta(
        "ViCC", "Contrastive",
        "RGB and optical-flow streams exchange cluster prototypes to learn appearance and motion correspondences.",
        "UCF101", "UCF101; HMDB51",
    ),
    "SLIC: Self-supervised learning with iterative clustering for human action videos": meta(
        "SLIC", "Contrastive",
        "Iterative clustering mines semantically related positives and hard negatives for action-video contrastive learning.",
        "UCF101; Kinetics-400", "UCF101; HMDB51",
    ),
    "GOCA: guided online cluster assignment for self-supervised video representation Learning": meta(
        "GOCA", "Contrastive",
        "Motion-guided views and online cluster assignment produce group-aware targets without offline clustering.",
        "UCF101; Kinetics-400", "UCF101; HMDB51; Diving48",
    ),
    "TCVM: Temporal Contrasting Video Montage Framework for Self-supervised Video Representation Learning": meta(
        "TCVM", "Contrastive",
        "Video montages create temporal context changes that are contrasted to learn transformation-sensitive dynamics.",
        "Kinetics-400", "Something-Something V2; UCF101; HMDB51",
    ),
    "Static and Dynamic Concepts for Self-supervised Video Representation Learning": meta(
        "Static-Dynamic Concept Learning", "Contrastive",
        "Frame, frame-difference, and video views separate static appearance concepts from dynamic motion concepts.",
        "Kinetics-400", "UCF101; HMDB51; Diving48; Kinetics-400",
    ),
    "Audio-Visual Contrastive Learning for Self-Supervised Action Recognition": meta(
        "Audio-Visual Contrastive Learning (AVCL)", "Multimodal / Audio-Visual",
        "Audio-modulated feature mapping, cross-modal relation attention, and within-modal contrast jointly learn action representations.",
        "Kinetics-Sounds32; Kinetics-Sounds100", "Kinetics-Sounds32; Kinetics-Sounds100",
    ),
    "SOS! Self-supervised Learning over Sets of Handled Objects in Egocentric Action Recognition": meta(
        "SOS", "Other / Hybrid",
        "Handled-object sets provide object-centric predictive and contrastive supervision for egocentric actions.",
        "EPIC-KITCHENS-100", "EPIC-KITCHENS-100",
    ),
    "Self-Supervised Video Representation Learning with Cascade Positive Retrieval": meta(
        "Cascade Positive Retrieval (CPR)", "Contrastive",
        "Positive clips are progressively retrieved across augmented views to enlarge the semantic positive set.",
        "UCF101", "UCF101; HMDB51",
    ),
    "Self-Supervised Learning of Audio Representations From Audio-Visual Data Using Spatial Alignment": meta(
        "Audio-Visual Spatial Alignment (AVSA)", "Multimodal / Audio-Visual",
        "A spatial alignment pretext predicts the correspondence between 360-degree visual direction and ambisonic audio channels.",
        "YouTube-360", "UCF101; HMDB51; EigenScape; TAU Audio-Visual Urban Scenes 2021",
    ),
    "Hierarchically decoupled spatial-temporal contrast for self-supervised video representation learning": meta(
        "HDC", "Contrastive",
        "Spatial and temporal factors are decoupled and contrasted at multiple hierarchy levels.",
        "Kinetics-400", "UCF101; HMDB51",
    ),
    "Spatio-temporal self-supervision enhanced transformer networks for action recognition": meta(
        "STTNet", "Pretext / Predictive",
        "A transformer is enhanced with spatiotemporal self-supervision that detects temporal ordering and clip transformations.",
        "Kinetics-400", "Kinetics-400; Something-Something V2; UCF101; HMDB51",
    ),
    "Inter-Intra Cross-Modality Self-Supervised Video Representation Learning by Contrastive Clustering": meta(
        "IICMVC", "Contrastive",
        "Inter-modal and intra-modal cluster contrast aligns RGB and motion representations while maintaining complementary structure.",
        "UCF101; Kinetics-400", "UCF101; HMDB51",
    ),
    "Self-Supervised Scene-Debiasing for Video Representation Learning via Background Patching": meta(
        "Background Patching", "Contrastive",
        "Video backgrounds are patched with unrelated scenes and contrasted to reduce scene bias while retaining action evidence.",
        "Kinetics-400", "Kinetics-400; UCF101; HMDB51",
    ),
    "SCVRL: Shuffled Contrastive Video Representation Learning": meta(
        "SCVRL", "Contrastive",
        "Temporally shuffled clips form structured hard negatives that make contrastive models attend to temporal order.",
        "Kinetics-400", "Kinetics-400; Something-Something V2; Diving48; UCF101",
    ),
    "XKD: Cross-modal Knowledge Distillation with Domain Alignment for Video Representation Learning": meta(
        "XKD", "Multimodal / Audio-Visual",
        "Bidirectional audio-video knowledge distillation combines cross-modal relevance weighting with feature-domain alignment.",
        "Kinetics-Sounds; Kinetics-400; AudioSet", "Kinetics-400; UCF101; HMDB51; Kinetics-Sounds; ESC-50; FSD50K",
    ),
    "InternVideo: General Video Foundation Models via Generative and Discriminative Learning": meta(
        "InternVideo", "Other / Hybrid",
        "Masked video modeling and video-text contrastive encoders are pretrained separately and fused into a general video foundation model.",
        "Kinetics-400; Something-Something V2; WebVid-2M; WebVid-10M; HowTo100M; LAION-400M",
        "Kinetics-400; Kinetics-600; Something-Something V2; ActivityNet; AVA; THUMOS14; UCF101; HMDB51; MSR-VTT; MSVD; DiDeMo; LSMDC; ActivityNet Captions",
        "The paper evaluates 39 datasets; the catalog lists the principal action, detection, and video-language benchmarks.",
    ),
    "Video Motion Perception for Self-supervised Representation Learning": meta(
        "Video Motion Perception (VMP)", "Pretext / Predictive",
        "Motion direction and magnitude prediction provide explicit motion supervision for a spatiotemporal encoder.",
        "UCF101; Kinetics-400", "UCF101; HMDB51",
    ),
    "An improved inter-intra contrastive learning framework on self-supervised video representation": meta(
        "Improved Inter-Intra Contrastive Learning", "Contrastive",
        "An enhanced inter-video and intra-video contrastive framework models instance discrimination and temporal coherence together.",
        "UCF101; Kinetics-400", "UCF101; HMDB51",
    ),
    "Auxiliary Learning for Self-Supervised Video Representation via Similarity-based Knowledge Distillation": meta(
        "AuxSKD", "Distillation / Teacher-Student",
        "Similarity-based knowledge distillation transfers relational structure while an auxiliary variable-speed segment task improves motion features.",
        "Kinetics-100; Kinetics-400", "UCF101; HMDB51",
    ),
    "LgNet: A local-global network for action recognition and beyond": meta(
        "LgNet", "Other / Hybrid",
        "Local action units are integrated through a global temporal relation module, with self-supervised and supervised objectives sharing the representation.",
        "Kinetics-400", "Kinetics-400; UCF101; HMDB51; Something-Something V2",
    ),
    "Motion Sensitive Contrastive Learning for Self-supervised Video Representation": meta(
        "MoSI", "Contrastive",
        "Motion-sensitive positives and negatives discourage appearance shortcuts and emphasize changes across time.",
        "Kinetics-400", "Kinetics-400; UCF101; HMDB51; Something-Something V2",
    ),
    "Unsupervised Video-based Action Recognition With Imagining Motion And Perceiving Appearance": meta(
        "IMPA", "Other / Hybrid",
        "Separate branches imagine motion and perceive appearance before their complementary representations are fused for action recognition.",
        "UCF101; Kinetics-400", "UCF101; HMDB51",
    ),
    "Unsupervised Learning of Spatio-Temporal Representation with Multi-Task Learning for Video Retrieval": meta(
        "Spatiotemporal Multi-Task Learning", "Pretext / Predictive",
        "Multiple spatial and temporal pretext tasks are jointly optimized for transferable video retrieval features.",
        "UCF101; HMDB51", "UCF101; HMDB51",
    ),
    "Federated Self-supervised Learning for Video Understanding": meta(
        "FedVSSL", "Contrastive",
        "Client-local self-supervised video learning and global federated aggregation train a shared model without centralizing videos.",
        "Kinetics-400; UCF101; HMDB51", "Kinetics-400; UCF101; HMDB51",
    ),
    "Contrastive predictive coding with transformer for video representation learning": meta(
        "CPCTR", "Pretext / Predictive",
        "A transformer predicts future latent video features under a contrastive predictive coding objective.",
        "UCF101", "UCF101; HMDB51",
    ),
    "Video representation learning by identifying spatio-temporal transformation": meta(
        "Spatiotemporal Transformation Identification", "Pretext / Predictive",
        "The encoder identifies applied spatial and temporal transformations to learn transferable action features.",
        "UCF101", "UCF101; HMDB51",
    ),
    "On temporal granularity in self-supervised video representation learning": meta(
        "Temporal Granularity Study", "Other / Hybrid",
        "A controlled contrastive study varies clip duration, sampling rate, and temporal span to quantify the role of temporal granularity.",
        "Kinetics-400", "Kinetics-400; UCF101; HMDB51",
    ),
    "LAVA: Language Audio Vision Alignment for Data-Efficient Video Pre-Training": meta(
        "LAVA", "Multimodal / Audio-Visual",
        "Language, audio, and visual embeddings are aligned with multimodal contrastive objectives for data-efficient video pretraining.",
        "Kinetics-700", "UCF101; HMDB51; ESC-50",
        "The study uses about 300,000 Kinetics-700 clips with usable audio from an initial 480,000-video collection.",
    ),
    "It Takes Two: Masked Appearance-Motion Modeling for Self-supervised Video Transformer Pre-training": meta(
        "MAM2", "Generative / Masked",
        "A shared encoder and regressor feed separate appearance and RGB-difference motion decoders for masked appearance-motion modeling.",
        "Kinetics-400; Something-Something V2; UCF101; HMDB51", "Kinetics-400; Something-Something V2; UCF101; HMDB51",
    ),
    "MAC: Mask-Augmentation for Motion-Aware Video Representation Learning": meta(
        "MAC", "Contrastive",
        "Mask augmentation creates motion-aware paired views and adds a motion-sensitive contrastive objective.",
        "Kinetics-400; UCF101", "UCF101; HMDB51",
    ),
    "Temporal-Invariant Video Representation Learning with Dynamic Temporal Resolutions.": meta(
        "Temporal-Invariant Dynamic-Resolution Learning", "Contrastive",
        "Clips sampled at different temporal resolutions are aligned to learn representations invariant to action speed.",
        "Kinetics-400", "Kinetics-400; UCF101; HMDB51",
    ),
    "Frequency Selective Augmentation for Video Representation Learning": meta(
        "Frequency Selective Augmentation (FreqAug)", "Contrastive",
        "Selective spatiotemporal frequency perturbations produce contrastive views that preserve action semantics while suppressing shortcuts.",
        "Mini-Kinetics; Kinetics-400", "Mini-Kinetics; Kinetics-400; Something-Something V2; UCF101; HMDB51; Diving48; Breakfast",
    ),
    "Dual Contrastive Learning for Spatio-temporal Representation": meta(
        "Dual Contrastive Learning (DCL)", "Contrastive",
        "Global video-level and local spatiotemporal contrastive objectives jointly capture action semantics and fine motion.",
        "Kinetics-400", "Kinetics-400; UCF101; HMDB51",
    ),
    "Consistent Intra-video Contrastive Learning with Asynchronous Long-term Memory Bank": meta(
        "Consistent Intra-Video Contrastive Learning", "Contrastive",
        "An asynchronous long-term memory bank and consistency refinement enlarge intra-video positives without stale-target instability.",
        "Kinetics-400; UCF101", "UCF101; HMDB51",
    ),
    "Controllable Augmentations for Video Representation Learning": meta(
        "Controllable Augmentations", "Contrastive",
        "Local and global views use soft region contrast, mutual-information minimization, and temporal-order dependency to align appearance and motion patterns.",
        "Kinetics-400; UCF101", "Kinetics-400; UCF101; HMDB51; ActivityNet",
    ),
    "MoQuad: Motion-focused Quadruple Construction for Video Contrastive Learning": meta(
        "MoQuad", "Contrastive",
        "Four clips with controlled appearance and motion changes form motion-focused positive and negative pairs for video contrastive learning.",
        "Kinetics-400", "UCF101; HMDB51; Diving48",
    ),
    "On Negative Sampling for Audio-Visual Contrastive Learning from Movies": meta(
        "Within-Movie Audio-Visual Negative Sampling", "Multimodal / Audio-Visual",
        "Within-movie negative sampling is adapted to recurring semantics and movie-specific nonsemantic cues in uncurated long-form content.",
        "Long-form movies", "UCF101; HMDB51; ESC-50",
        "The pretraining collection is described as uncurated long-form movies rather than released as a named benchmark.",
    ),
    "Frame-wise Action Representations for Long Videos via Sequence Contrastive Learning": meta(
        "CARL", "Contrastive",
        "Sequence contrastive learning aligns frame-wise embeddings across temporally transformed views while preserving action progression.",
        "Penn Action; FineGym; Pouring", "Penn Action; FineGym; Pouring",
    ),
    "Masked feature prediction for self-supervised visual pre-training": meta(
        "MaskFeat", "Generative / Masked",
        "Masked video tokens predict hand-crafted HOG features instead of raw pixels.",
        "Kinetics-400", "Kinetics-400; Kinetics-600; Kinetics-700; Something-Something V2; AVA",
    ),
    "Pixel-level Correspondence for Self-Supervised Learning from Video": meta(
        "PiCo", "Contrastive",
        "Optical-flow tracks define dense pixel-level positive correspondences for learning localized visual features from video.",
        "YouTube-8M Segments; Kinetics-400", "COCO; PASCAL VOC 2012; Cityscapes; DAVIS 2017; JHMDB",
    ),
    "Temporal alignment networks for long-term video": meta(
        "Temporal Alignment Networks (TAN)", "Contrastive",
        "A temporal alignment objective learns frame representations from narrated instructional video and transfers to long-term alignment tasks.",
        "HowTo100M (HTM-370K)", "HTM-Align; Breakfast; YouCook2",
    ),
    "Simvtp: Simple video text pre-training with masked autoencoders": meta(
        "SimVTP", "Multimodal / Audio-Visual",
        "A simple video-text masked autoencoder jointly reconstructs masked visual tokens and aligns video with text.",
        "WebVid-2M", "MSR-VTT; MSVD; DiDeMo; LSMDC; ActivityNet Captions; MSRVTT-QA",
    ),
    "Learning audio-visual speech representation by masked multimodal cluster prediction": meta(
        "AV-HuBERT", "Multimodal / Audio-Visual",
        "Masked multimodal cluster prediction iteratively derives and predicts shared audio-visual speech units.",
        "LRS3; VoxCeleb2", "LRS3",
    ),
}


def pub(year, venue, normalized, status="peer_reviewed", **kwargs):
    return {"year": year, "venue": venue, "venue_normalized": normalized, "publication_status": status, **kwargs}


P = {
    "BEVT: BERT Pretraining of Video Transformers": pub(2022, "CVPR 2022", "CVPR", url="https://openaccess.thecvf.com/content/CVPR2022/html/Wang_BEVT_BERT_Pretraining_of_Video_Transformers_CVPR_2022_paper.html", arxiv="2112.01529"),
    "Masked Autoencoders As Spatiotemporal Learners": pub(2022, "NeurIPS 2022", "NeurIPS", url="https://proceedings.neurips.cc/paper_files/paper/2022/hash/e97d1081481a4017df96b51be31001d3-Abstract-Conference.html", arxiv="2205.09113"),
    "SPAct: Self-supervised Privacy Preservation for Action Recognition": pub(2022, "CVPR 2022", "CVPR", url="https://openaccess.thecvf.com/content/CVPR2022/html/Dave_SPAct_Self-Supervised_Privacy_Preservation_for_Action_Recognition_CVPR_2022_paper.html", arxiv="2203.15205"),
    "Suppressing Static Visual Cues via Normalizing Flows for Self-Supervised Video Representation Learning": pub(2022, "AAAI 2022", "AAAI", url="https://ojs.aaai.org/index.php/AAAI/article/view/20254", arxiv="2112.03803"),
    "Self-supervised Video Representation Learning with Motion-Aware Masked Autoencoders": pub(2024, "BMVC 2024", "BMVC", url="https://bmvc2024.org/proceedings/499/", arxiv="2210.04154", new_title="MotionMAE: Self-supervised Video Representation Learning with Motion-Aware Masked Autoencoders"),
    "Self-supervised Video Transformer": pub(2022, "CVPR 2022", "CVPR", url="https://openaccess.thecvf.com/content/CVPR2022/html/Ranasinghe_Self-Supervised_Video_Transformer_CVPR_2022_paper.html"),
    "Exploring Relations in Untrimmed Videos for Self-Supervised Learning": pub(2022, "ACM Transactions on Multimedia Computing, Communications, and Applications 2022", "ACM TOMM", arxiv="2008.02711"),
    "MaMiCo: Macro-to-Micro Semantic Correspondence for Self-supervised Video Representation Learning": pub(2022, "ACM Multimedia 2022", "ACM Multimedia", url="https://dl.acm.org/doi/10.1145/3503161.3547888", doi="10.1145/3503161.3547888"),
    "TCGL: Temporal Contrastive Graph for Self-Supervised Video Representation Learning": pub(2022, "IEEE Transactions on Image Processing 2022", "IEEE TIP", url="https://ieeexplore.ieee.org/document/9713748", doi="10.1109/TIP.2022.3152521"),
    "Cross-Architecture Self-supervised Video Representation Learning": pub(2022, "CVPR 2022", "CVPR", url="https://openaccess.thecvf.com/content/CVPR2022/html/Guo_Cross-Architecture_Self-Supervised_Video_Representation_Learning_CVPR_2022_paper.html"),
    "Contrastive spatio-temporal pretext learning for self-supervised video representation": pub(2022, "AAAI 2022", "AAAI", arxiv="2112.08913"),
    "Transrank: Self-supervised video representation learning via ranking-based transformation recognition": pub(2022, "CVPR 2022", "CVPR", url="https://openaccess.thecvf.com/content/CVPR2022/html/Duan_TransRank_Self-Supervised_Video_Representation_Learning_via_Ranking-Based_Transformation_Recognition_CVPR_2022_paper.html"),
    "Learning from untrimmed videos: Self-supervised video representation learning with hierarchical consistency": pub(2022, "CVPR 2022", "CVPR", url="https://openaccess.thecvf.com/content/CVPR2022/html/Qing_Learning_From_Untrimmed_Videos_Self-Supervised_Video_Representation_Learning_With_Hierarchical_CVPR_2022_paper.html"),
    "Motion-aware contrastive video representation learning via foreground-background merging": pub(2022, "CVPR 2022", "CVPR", url="https://openaccess.thecvf.com/content/CVPR2022/html/Ding_Motion-Aware_Contrastive_Video_Representation_Learning_via_Foreground-Background_Merging_CVPR_2022_paper.html"),
    "Self-Supervised Video Representation Learning with Motion-Contrastive Perception": pub(2022, "ICME 2022", "ICME", arxiv="2204.04607"),
    "Self-supervised video representation learning using improved instance-wise contrastive learning and deep clustering": pub(2022, "IEEE Transactions on Circuits and Systems for Video Technology 2022", "IEEE TCSVT", url="https://ieeexplore.ieee.org/document/9761901"),
    "TCLR: Temporal contrastive learning for video representation": pub(2022, "Computer Vision and Image Understanding 2022", "Computer Vision and Image Understanding", url="https://doi.org/10.1016/j.cviu.2022.103406", doi="10.1016/j.cviu.2022.103406", arxiv="2101.07974"),
    "Self-supervised motion perception for spatiotemporal representation learning": pub(2023, "IEEE Transactions on Neural Networks and Learning Systems 2023", "IEEE TNNLS", url="https://ieeexplore.ieee.org/document/9745754", doi="10.1109/TNNLS.2022.3160860"),
    "Self-supervised spatiotemporal representation learning by exploiting video continuity": pub(2022, "AAAI 2022", "AAAI", arxiv="2112.05883"),
    "Similarity Contrastive Estimation for Image and Video Soft Contrastive Self-Supervised Learning": pub(2023, "Machine Vision and Applications 2023", "Machine Vision and Applications", url="https://link.springer.com/article/10.1007/s00138-023-01444-9", doi="10.1007/s00138-023-01444-9", arxiv="2212.11187"),
    "Probabilistic representations for video contrastive learning": pub(2022, "CVPR 2022", "CVPR", url="https://openaccess.thecvf.com/content/CVPR2022/html/Park_Probabilistic_Representations_for_Video_Contrastive_Learning_CVPR_2022_paper.html", arxiv="2204.03946"),
    "Contextualized spatio-temporal contrastive learning with self-supervision": pub(2022, "CVPR 2022", "CVPR", url="https://openaccess.thecvf.com/content/CVPR2022/html/Yuan_Contextualized_Spatio-Temporal_Contrastive_Learning_With_Self-Supervision_CVPR_2022_paper.html"),
    "Videomae: Masked autoencoders are data-efficient learners for self-supervised video pre-training": pub(2022, "NeurIPS 2022", "NeurIPS", url="https://proceedings.neurips.cc/paper_files/paper/2022/hash/416f9cb3276121c42eebb86352a4354a-Abstract-Conference.html", arxiv="2203.12602", new_title="VideoMAE: Masked Autoencoders Are Data-Efficient Learners for Self-Supervised Video Pre-Training"),
    "Efficient Video Representation Learning via Masked Video Modeling with Motion-centric Token Selection": pub(2024, "ICML 2024", "ICML", url="https://proceedings.mlr.press/v235/hwang24d.html", arxiv="2211.10636", new_title="EVEREST: Efficient Masked Video Autoencoder by Removing Redundant Spatiotemporal Tokens"),
    "Self-supervised video representation learning with cross-stream prototypical contrasting": pub(2022, "WACV 2022", "WACV", url="https://openaccess.thecvf.com/content/WACV2022/html/Toering_Self-Supervised_Video_Representation_Learning_With_Cross-Stream_Prototypical_Contrasting_WACV_2022_paper.html", arxiv="2106.10137"),
    "SLIC: Self-supervised learning with iterative clustering for human action videos": pub(2022, "CVPR 2022", "CVPR", url="https://openaccess.thecvf.com/content/CVPR2022/html/Khorasgani_SLIC_Self-Supervised_Learning_With_Iterative_Clustering_for_Human_Action_Videos_CVPR_2022_paper.html", arxiv="2206.12534"),
    "GOCA: guided online cluster assignment for self-supervised video representation Learning": pub(2022, "ECCV 2022", "ECCV", url="https://link.springer.com/chapter/10.1007/978-3-031-20050-2_15", arxiv="2207.10158"),
    "TCVM: Temporal Contrasting Video Montage Framework for Self-supervised Video Representation Learning": pub(2022, "ACCV 2022", "ACCV", url="https://openaccess.thecvf.com/content/ACCV2022/html/Tian_TCVM_Temporal_Contrasting_Video_Montage_Framework_for_Self-supervised_Video_Representation_ACCV_2022_paper.html"),
    "Static and Dynamic Concepts for Self-supervised Video Representation Learning": pub(2022, "ECCV 2022", "ECCV", arxiv="2207.12795"),
    "Audio-Visual Contrastive Learning for Self-Supervised Action Recognition": pub(2023, "ICIP 2023", "ICIP", url="https://ieeexplore.ieee.org/document/10222383", arxiv="2204.13386", new_title="Self-Supervised Contrastive Learning for Audio-Visual Action Recognition"),
    "SOS! Self-supervised Learning over Sets of Handled Objects in Egocentric Action Recognition": pub(2022, "ECCV 2022", "ECCV", arxiv="2204.04796"),
    "Self-Supervised Video Representation Learning with Cascade Positive Retrieval": pub(2022, "CVPR Workshops 2022", "CVPR Workshops", url="https://openaccess.thecvf.com/content/CVPR2022W/L3D-IVU/html/Wu_Self-Supervised_Video_Representation_Learning_With_Cascade_Positive_Retrieval_CVPRW_2022_paper.html"),
    "Self-Supervised Learning of Audio Representations From Audio-Visual Data Using Spatial Alignment": pub(2022, "IEEE Journal of Selected Topics in Signal Processing 2022", "IEEE JSTSP", url="https://ieeexplore.ieee.org/document/9790080", arxiv="2206.00970"),
    "Hierarchically decoupled spatial-temporal contrast for self-supervised video representation learning": pub(2022, "WACV 2022", "WACV", url="https://openaccess.thecvf.com/content/WACV2022/html/Zhang_Hierarchically_Decoupled_Spatial-Temporal_Contrast_for_Self-Supervised_Video_Representation_Learning_WACV_2022_paper.html"),
    "Spatio-temporal self-supervision enhanced transformer networks for action recognition": pub(2022, "ICME 2022", "ICME", url="https://ieeexplore.ieee.org/document/9859741"),
    "Inter-Intra Cross-Modality Self-Supervised Video Representation Learning by Contrastive Clustering": pub(2022, "ICPR 2022", "ICPR", url="https://ieeexplore.ieee.org/document/9956697"),
    "Self-Supervised Scene-Debiasing for Video Representation Learning via Background Patching": pub(2023, "IEEE Transactions on Multimedia 2023", "IEEE TMM", url="https://ieeexplore.ieee.org/document/9839482", doi="10.1109/TMM.2022.3193559"),
    "SCVRL: Shuffled Contrastive Video Representation Learning": pub(2022, "CVPR Workshops 2022", "CVPR Workshops", url="https://openaccess.thecvf.com/content/CVPR2022W/L3D-IVU/html/Dorkenwald_SCVRL_Shuffled_Contrastive_Video_Representation_Learning_CVPRW_2022_paper.html"),
    "XKD: Cross-modal Knowledge Distillation with Domain Alignment for Video Representation Learning": pub(2024, "AAAI 2024", "AAAI", url="https://ojs.aaai.org/index.php/AAAI/article/view/29407", doi="10.1609/aaai.v38i13.29407", arxiv="2211.13929"),
    "InternVideo: General Video Foundation Models via Generative and Discriminative Learning": pub(2022, "arXiv / Preprint", "arXiv / Preprint", "preprint", url="https://arxiv.org/abs/2212.03191", arxiv="2212.03191"),
    "Video Motion Perception for Self-supervised Representation Learning": pub(2022, "ICANN 2022", "ICANN", url="https://link.springer.com/chapter/10.1007/978-3-031-15937-4_43", doi="10.1007/978-3-031-15937-4_43"),
    "An improved inter-intra contrastive learning framework on self-supervised video representation": pub(2022, "IEEE Transactions on Circuits and Systems for Video Technology 2022", "IEEE TCSVT", url="https://ieeexplore.ieee.org/document/9674754"),
    "Auxiliary Learning for Self-Supervised Video Representation via Similarity-based Knowledge Distillation": pub(2022, "CVPR Workshops 2022", "CVPR Workshops", url="https://openaccess.thecvf.com/content/CVPR2022W/L3D-IVU/html/Dadashzadeh_Auxiliary_Learning_for_Self-Supervised_Video_Representation_via_Similarity-Based_Knowledge_Distillation_CVPRW_2022_paper.html"),
    "LgNet: A local-global network for action recognition and beyond": pub(2023, "IEEE Transactions on Multimedia 2023", "IEEE TMM", url="https://ieeexplore.ieee.org/document/9817623", doi="10.1109/TMM.2022.3189253"),
    "Motion Sensitive Contrastive Learning for Self-supervised Video Representation": pub(2022, "ECCV 2022", "ECCV", url="https://link.springer.com/chapter/10.1007/978-3-031-19833-5_27", doi="10.1007/978-3-031-19833-5_27"),
    "Unsupervised Video-based Action Recognition With Imagining Motion And Perceiving Appearance": pub(2023, "IEEE Transactions on Circuits and Systems for Video Technology 2023", "IEEE TCSVT", url="https://ieeexplore.ieee.org/document/9944692", doi="10.1109/TCSVT.2022.3221280", new_title="Unsupervised Video-Based Action Recognition With Imagining Motion and Perceiving Appearance"),
    "Unsupervised Learning of Spatio-Temporal Representation with Multi-Task Learning for Video Retrieval": pub(2022, "National Conference on Communications 2022", "NCC", url="https://ieeexplore.ieee.org/document/9806811"),
    "Federated Self-supervised Learning for Video Understanding": pub(2022, "ECCV 2022", "ECCV", url="https://link.springer.com/chapter/10.1007/978-3-031-19821-2_29", doi="10.1007/978-3-031-19821-2_29"),
    "Contrastive predictive coding with transformer for video representation learning": pub(2022, "Neurocomputing 2022", "Neurocomputing", url="https://www.sciencedirect.com/science/article/pii/S0925231221017082", doi="10.1016/j.neucom.2021.11.031"),
    "Video representation learning by identifying spatio-temporal transformation": pub(2022, "Applied Intelligence 2022", "Applied Intelligence", url="https://link.springer.com/article/10.1007/s10489-021-02790-9", doi="10.1007/s10489-021-02790-9"),
    "On temporal granularity in self-supervised video representation learning": pub(2022, "BMVC 2022", "BMVC", url="https://bmvc2022.mpi-inf.mpg.de/541/"),
    "LAVA: Language Audio Vision Alignment for Data-Efficient Video Pre-Training": pub(2022, "ICML Pre-training Workshop 2022", "ICML Workshops", arxiv="2207.08024"),
    "It Takes Two: Masked Appearance-Motion Modeling for Self-supervised Video Transformer Pre-training": pub(2022, "arXiv / Preprint", "arXiv / Preprint", "preprint", url="https://arxiv.org/abs/2210.05234", arxiv="2210.05234"),
    "MAC: Mask-Augmentation for Motion-Aware Video Representation Learning": pub(2022, "BMVC 2022", "BMVC", url="https://bmvc2022.mpi-inf.mpg.de/5/"),
    "Temporal-Invariant Video Representation Learning with Dynamic Temporal Resolutions.": pub(2022, "AVSS 2022", "AVSS", url="https://ieeexplore.ieee.org/document/9959310"),
    "Frequency Selective Augmentation for Video Representation Learning": pub(2023, "AAAI 2023", "AAAI", url="https://ojs.aaai.org/index.php/AAAI/article/view/25194", doi="10.1609/aaai.v37i1.25194", arxiv="2204.03865", new_title="Spatiotemporal Augmentation on Selective Frequencies for Video Representation Learning"),
    "Dual Contrastive Learning for Spatio-temporal Representation": pub(2022, "ACM Multimedia 2022", "ACM Multimedia", url="https://dl.acm.org/doi/10.1145/3503161.3547783", doi="10.1145/3503161.3547783"),
    "Consistent Intra-video Contrastive Learning with Asynchronous Long-term Memory Bank": pub(2023, "IEEE Transactions on Circuits and Systems for Video Technology 2023", "IEEE TCSVT", url="https://ieeexplore.ieee.org/document/9893855", doi="10.1109/TCSVT.2022.3207174"),
    "Controllable Augmentations for Video Representation Learning": pub(2024, "Visual Intelligence 2024", "Visual Intelligence", url="https://link.springer.com/article/10.1007/s44267-023-00034-7", doi="10.1007/s44267-023-00034-7", arxiv="2203.16632", authors="Rui Qian; Weiyao Lin; John See; Dian Li"),
    "MoQuad: Motion-focused Quadruple Construction for Video Contrastive Learning": pub(2022, "ECCV Workshops 2022", "ECCV Workshops", url="https://link.springer.com/chapter/10.1007/978-3-031-25069-9_2", doi="10.1007/978-3-031-25069-9_2", arxiv="2212.10870", authors="Yuan Liu; Jiacheng Chen; Hao Wu"),
    "On Negative Sampling for Audio-Visual Contrastive Learning from Movies": pub(2022, "arXiv / Preprint", "arXiv / Preprint", "preprint", url="https://arxiv.org/abs/2205.00073", arxiv="2205.00073", authors="Mahdi M. Kalayeh; Shervin Ardeshir; Lingyi Liu; Nagendra Kamath; Ashok Chandrashekar"),
    "Frame-wise Action Representations for Long Videos via Sequence Contrastive Learning": pub(2022, "CVPR 2022", "CVPR", url="https://openaccess.thecvf.com/content/CVPR2022/html/Chen_Frame-Wise_Action_Representations_for_Long_Videos_via_Sequence_Contrastive_Learning_CVPR_2022_paper.html"),
    "Masked feature prediction for self-supervised visual pre-training": pub(2022, "CVPR 2022", "CVPR", url="https://openaccess.thecvf.com/content/CVPR2022/html/Wei_Masked_Feature_Prediction_for_Self-Supervised_Visual_Pre-Training_CVPR_2022_paper.html", arxiv="2112.09133", new_title="Masked Feature Prediction for Self-Supervised Visual Pre-Training"),
    "Pixel-level Correspondence for Self-Supervised Learning from Video": pub(2022, "arXiv / Preprint", "arXiv / Preprint", "preprint", url="https://arxiv.org/abs/2207.03866", arxiv="2207.03866", authors="Yash Sharma; Yanchao Zhu; Chris Russell; Thomas Brox"),
    "Temporal alignment networks for long-term video": pub(2022, "CVPR 2022", "CVPR", url="https://openaccess.thecvf.com/content/CVPR2022/html/Han_Temporal_Alignment_Networks_for_Long-Term_Video_CVPR_2022_paper.html", arxiv="2204.02968", new_title="Temporal Alignment Networks for Long-Term Video"),
    "Simvtp: Simple video text pre-training with masked autoencoders": pub(2022, "arXiv / Preprint", "arXiv / Preprint", "preprint", url="https://arxiv.org/abs/2212.03490", arxiv="2212.03490", new_title="SimVTP: Simple Video Text Pre-Training with Masked Autoencoders"),
    "Learning audio-visual speech representation by masked multimodal cluster prediction": pub(2022, "ICLR 2022", "ICLR", url="https://openreview.net/forum?id=Z1Qlm11uOM", arxiv="2201.02184", new_title="Learning Audio-Visual Speech Representation by Masked Multimodal Cluster Prediction"),
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


def apply_publication(paper, publication):
    old_title = paper["title"]
    new_title = publication.get("new_title", old_title)
    if new_title != old_title:
        paper["previous_titles"] = unique(paper.get("previous_titles", []) + [old_title])
        paper["title"] = new_title
        paper["normalized_title"] = norm_title(new_title)

    paper.update({
        "year": publication["year"],
        "date_label": str(publication["year"]),
        "venue": publication["venue"],
        "venue_normalized": publication["venue_normalized"],
        "publication_status": publication["publication_status"],
        "published_date": str(publication["year"]),
    })
    if publication.get("url"):
        paper["paper_url"] = publication["url"]
    if publication.get("doi"):
        paper["doi"] = publication["doi"]
    else:
        paper["doi"] = ""
    if publication.get("arxiv"):
        paper["arxiv_id"] = publication["arxiv"]
    elif not paper.get("arxiv_id"):
        match = re.search(r"(?:abs/|pdf/|arXiv:)(\d{4}\.\d{4,5})", paper.get("paper_url", "") + " " + paper.get("venue", ""), re.I)
        paper["arxiv_id"] = match.group(1) if match else ""
    if publication.get("authors"):
        paper["authors"] = s(publication["authors"])
        paper["authors_display"] = ", ".join(paper["authors"])

    verification = [paper.get("paper_url", "")]
    if paper.get("doi"):
        verification.append("https://doi.org/" + paper["doi"])
    if paper.get("arxiv_id"):
        verification.append("https://arxiv.org/abs/" + paper["arxiv_id"])
    paper["verification_urls"] = unique(verification)
    paper["venue_evidence"] = (
        "arxiv_record_and_exact_title_publication_search"
        if publication["publication_status"] == "preprint"
        else "official_proceedings_or_publisher_record"
    )
    if publication["publication_status"] == "preprint":
        paper["audit_notes"] = "Exact-title and author-record searches found no peer-reviewed version through the verification date."
    elif publication["year"] != 2022:
        paper["audit_notes"] = "The initial 2022 record was reconciled to the final proceedings or journal volume year."


def main():
    papers = json.loads(PAPERS_PATH.read_text())
    initial = [p for p in papers if p.get("year") == 2022]
    initial_titles = {p["title"] for p in initial}
    expected = set(META)
    if initial_titles != expected or set(P) != expected:
        raise SystemExit(
            "2022 mapping mismatch: "
            f"missing_meta={sorted(initial_titles-expected)}, extra_meta={sorted(expected-initial_titles)}, "
            f"missing_publication={sorted(initial_titles-set(P))}, extra_publication={sorted(set(P)-initial_titles)}"
        )

    for paper in initial:
        old_title = paper["title"]
        paper.update(META[old_title])
        paper["datasets"] = unique(paper["pretraining_datasets"] + paper["evaluation_datasets"])
        paper["benchmarks"] = paper["evaluation_datasets"]
        paper["benchmark_text"] = ", ".join(paper["evaluation_datasets"])
        apply_publication(paper, P[old_title])
        paper["audited_at"] = VERIFIED_AS_OF
        paper["discovery_source"] = "exact_title_scholarly_search_then_primary_source"

    completed = {}
    for year in (2026, 2025, 2024, 2023, 2022):
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
        "completed_years": [2026, 2025, 2024, 2023, 2022],
        "next_year": 2021,
        "verified_paper_count": verified,
        "remaining_paper_count": len(papers) - verified,
        "resume_instruction": "Start with 2021. Verify exact-title publication history, fill method and split pretraining/evaluation datasets, rebuild the site, validate the catalog, and save the 2021 checkpoint.",
    })
    progress["year_status"] = {str(year): status_block(year, completed[year]) for year in (2026, 2025, 2024, 2023, 2022)}
    progress_path.write_text(json.dumps(progress, indent=2, ensure_ascii=False) + "\n")
    print("Finalized original 2022 cohort and reconciled completed years: " + ", ".join(f"{year}={len(completed[year])}" for year in (2026, 2025, 2024, 2023, 2022)))


if __name__ == "__main__":
    main()
