#!/usr/bin/env python3
"""Finalize the 2017 paper cohort."""

from pathlib import Path
import sys

from audit_year_common import finalize_year, spec


ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
YEAR = 2017


def paper(method, family, description, pretraining, evaluation, venue, venue_normalized,
          *, status="peer_reviewed", url="", doi="", arxiv="", notes="", new_title=""):
    return spec(
        method, family, description, pretraining, evaluation, venue, venue_normalized,
        year=YEAR, status=status, url=url, doi=doi, arxiv=arxiv, notes=notes, new_title=new_title,
    )


SPECS = {
    "Unsupervised representation learning by sorting sequences": paper(
        "Order Prediction Network (OPN)", "Pretext / Predictive",
        "A Siamese CNN extracts features from every pair in a shuffled frame tuple and predicts its chronological permutation, using motion-aware sampling, spatial jittering, and channel splitting to suppress shortcuts.",
        "UCF101; HMDB51", "UCF101; HMDB51; PASCAL VOC 2007", "ICCV 2017", "ICCV",
        url="https://openaccess.thecvf.com/content_ICCV_2017/papers/Lee_Unsupervised_Representation_Learning_ICCV_2017_paper.pdf", doi="10.1109/ICCV.2017.79", arxiv="1708.01246",
        new_title="Unsupervised Representation Learning by Sorting Sequences",
        notes="The main model is self-supervised on UCF101 and transferred to UCF101, HMDB51, and PASCAL VOC 2007. The paper also reports dataset-specific unsupervised pretraining on HMDB51.",
    ),
    "Self-supervised video representation learning with odd-one-out networks": paper(
        "Odd-One-Out Network (O3N)", "Pretext / Predictive",
        "A multi-branch CNN receives several temporally ordered subsequences and one frame-shuffled subsequence from the same video, then learns to identify the odd input through shared encoders and feature fusion.",
        "UCF101; HMDB51", "UCF101; HMDB51", "CVPR 2017", "CVPR",
        url="https://openaccess.thecvf.com/content_cvpr_2017/html/Fernando_Self-Supervised_Video_Representation_CVPR_2017_paper.html", doi="10.1109/CVPR.2017.607", arxiv="1611.06646",
        new_title="Self-Supervised Video Representation Learning With Odd-One-Out Networks",
        notes="Self-supervised feature learning and downstream action classification are reported on UCF101 and HMDB51 without external pretrained weights or optical-flow inputs.",
    ),
}


if __name__ == "__main__":
    finalize_year(
        ROOT, YEAR, SPECS,
        (2026, 2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017),
        2016,
    )
