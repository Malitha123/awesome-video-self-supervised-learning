#!/usr/bin/env python3
"""Finalize the 2019 paper cohort."""

from pathlib import Path
import sys

from audit_year_common import finalize_year, spec


ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
YEAR = 2019


def paper(method, family, description, pretraining, evaluation, venue, venue_normalized,
          *, status="peer_reviewed", url="", doi="", arxiv="", notes="", new_title=""):
    return spec(
        method, family, description, pretraining, evaluation, venue, venue_normalized,
        year=YEAR, status=status, url=url, doi=doi, arxiv=arxiv, notes=notes, new_title=new_title,
    )


SPECS = {
    "Self-supervised spatio-temporal representation learning for videos by predicting motion and appearance statistics": paper(
        "Motion and Appearance Statistics (MAS)", "Pretext / Predictive",
        "A C3D encoder regresses local and global motion-boundary locations, directions, and spatiotemporal color statistics.",
        "UCF101; Kinetics-400", "UCF101; HMDB51; ASLAN; YUPENN", "CVPR 2019", "CVPR",
        url="https://openaccess.thecvf.com/content_CVPR_2019/html/Wang_Self-Supervised_Spatio-Temporal_Representation_Learning_for_Videos_by_Predicting_Motion_and_CVPR_2019_paper.html", doi="10.1109/CVPR.2019.00413", arxiv="1904.03597",
        notes="UCF101 is the default self-supervised pretraining set; the paper also reports a Kinetics-400 pretraining variant.",
    ),
    "Video representation learning by dense predictive coding": paper(
        "Dense Predictive Coding (DPC)", "Pretext / Predictive",
        "A recurrent context model predicts dense latent feature maps for future spatiotemporal blocks using contrastive predictive coding.",
        "Kinetics-400", "UCF101; HMDB51", "ICCV Workshops 2019", "ICCV Workshops",
        url="https://openaccess.thecvf.com/content_ICCVW_2019/html/HVU/Han_Video_Representation_Learning_by_Dense_Predictive_Coding_ICCVW_2019_paper.html", arxiv="1909.04656",
    ),
    "Self-supervised spatiotemporal learning via video clip order prediction": paper(
        "Video Clip Order Prediction (VCOP)", "Pretext / Predictive",
        "A siamese 3D ConvNet encodes clips and predicts the permutation of their pairwise-concatenated features.",
        "UCF101", "UCF101; HMDB51", "CVPR 2019", "CVPR",
        url="https://openaccess.thecvf.com/content_CVPR_2019/html/Xu_Self-Supervised_Spatiotemporal_Learning_via_Video_Clip_Order_Prediction_CVPR_2019_paper.html",
    ),
    "Video jigsaw: Unsupervised learning of spatiotemporal context for video action recognition": paper(
        "Video Jigsaw", "Pretext / Predictive",
        "Spatial patches sampled across several frames are permuted, and a shared CNN predicts the spatiotemporal jigsaw arrangement.",
        "Kinetics-400; UCF101", "UCF101; HMDB51", "WACV 2019", "WACV",
        url="https://doi.org/10.1109/WACV.2019.00025", doi="10.1109/WACV.2019.00025", arxiv="1808.07507", new_title="Video Jigsaw: Unsupervised Learning of Spatiotemporal Context for Video Action Recognition",
        notes="The main transferable model is pretrained on Kinetics-400; UCF101 is also used in pretraining ablations.",
    ),
    "Self-supervised video representation learning with space-time cubic puzzles": paper(
        "Space-Time Cubic Puzzles", "Pretext / Predictive",
        "A four-tower 3D ResNet rearranges permuted spatial or temporal video cubes while jittering and channel replication block trivial cues.",
        "Kinetics-400", "UCF101; HMDB51", "AAAI 2019", "AAAI",
        url="https://ojs.aaai.org/index.php/AAAI/article/view/4873", doi="10.1609/aaai.v33i01.33018545", arxiv="1811.09795",
    ),
    "Learning video representations using contrastive bidirectional transformer": paper(
        "Contrastive Bidirectional Transformer (CBT)", "Multimodal / Video-Language",
        "A bidirectional Transformer replaces masked-token softmax with noise-contrastive estimation and optionally aligns video with ASR text.",
        "Kinetics-600; HowTo100M", "UCF101; HMDB51; ActivityNet; Breakfast; 50Salads; YouCook2; COIN", "arXiv / Preprint", "arXiv / Preprint",
        status="preprint", url="https://arxiv.org/abs/1906.05743", arxiv="1906.05743", new_title="Learning Video Representations Using Contrastive Bidirectional Transformer",
        notes="Kinetics-600 supports short-term visual pretraining; HowTo100M and its ASR support long-term and cross-modal pretraining. The temporal branch also uses a supervised Kinetics S3D feature extractor and a frozen text BERT checkpoint.",
    ),
    "Dynamonet: Dynamic action and motion network": paper(
        "DynamoNet", "Other / Hybrid",
        "Dynamic motion filters predict short-term future frames while a shared 3D CNN jointly learns action classification.",
        "Kinetics-400; UCF101; HMDB51", "Kinetics-400; UCF101; HMDB51", "ICCV 2019", "ICCV",
        url="https://openaccess.thecvf.com/content_ICCV_2019/html/Diba_DynamoNet_Dynamic_Action_and_Motion_Network_ICCV_2019_paper.html", arxiv="1904.11407", new_title="DynamoNet: Dynamic Action and Motion Network",
        notes="The future-prediction branch is self-supervised, but the joint action-classification branch uses labels; training and evaluation are reported dataset-wise.",
    ),
    "Temporal cycle-consistency learning": paper(
        "Temporal Cycle-Consistency Learning (TCC)", "Contrastive",
        "Soft nearest-neighbor cycle-back classification or regression aligns frames across different videos of the same process.",
        "Pouring; Penn Action; ImageNet-1K", "Pouring; Penn Action", "CVPR 2019", "CVPR",
        url="https://openaccess.thecvf.com/content_CVPR_2019/html/Dwibedi_Temporal_Cycle-Consistency_Learning_CVPR_2019_paper.html", arxiv="1904.07846", new_title="Temporal Cycle-Consistency Learning",
        notes="The paper reports both training from scratch and self-supervised fine-tuning from an ImageNet-1K supervised ResNet-50 initialization.",
    ),
    "Videobert: A joint model for video and language representation learning": paper(
        "VideoBERT", "Multimodal / Video-Language",
        "BERT jointly models masked sequences of vector-quantized visual tokens and ASR word tokens with a visual-language alignment objective.",
        "YouTube Cooking-312K; Kinetics-400; BooksCorpus; English Wikipedia", "YouCook2", "ICCV 2019", "ICCV",
        url="https://openaccess.thecvf.com/content_ICCV_2019/html/Sun_VideoBERT_A_Joint_Model_for_Video_and_Language_Representation_Learning_ICCV_2019_paper.html", arxiv="1904.01766", new_title="VideoBERT: A Joint Model for Video and Language Representation Learning",
        notes="The 312K-video cooking corpus is a private YouTube collection. Kinetics-400 initializes S3D; BooksCorpus and English Wikipedia initialize the released BERT-Large text checkpoint.",
    ),
}


if __name__ == "__main__":
    finalize_year(
        ROOT, YEAR, SPECS,
        (2026, 2025, 2024, 2023, 2022, 2021, 2020, 2019),
        2018,
    )
