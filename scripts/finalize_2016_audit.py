#!/usr/bin/env python3
"""Finalize the 2016 paper cohort and complete the year-by-year audit."""

from pathlib import Path
import sys

from audit_year_common import finalize_year, spec


ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
YEAR = 2016


def paper(method, family, description, pretraining, evaluation, venue, venue_normalized,
          *, status="peer_reviewed", url="", doi="", arxiv="", notes="", new_title=""):
    return spec(
        method, family, description, pretraining, evaluation, venue, venue_normalized,
        year=YEAR, status=status, url=url, doi=doi, arxiv=arxiv, notes=notes, new_title=new_title,
    )


SPECS = {
    "Shuffle and learn: unsupervised learning using temporal order verification": paper(
        "Shuffle and Learn / Temporal Order Verification", "Pretext / Predictive",
        "A triplet Siamese CNN learns from high-motion frame tuples by classifying whether the middle frame makes the sequence temporally valid, treating both forward and reverse chronology as valid.",
        "UCF101", "UCF101; HMDB51; FLIC; MPII", "ECCV 2016", "ECCV",
        url="https://link.springer.com/chapter/10.1007/978-3-319-46448-0_32", doi="10.1007/978-3-319-46448-0_32", arxiv="1603.08561",
        new_title="Shuffle and Learn: Unsupervised Learning Using Temporal Order Verification",
        notes="The self-supervised model is pretrained on unlabeled UCF101 training videos, then evaluated on action recognition and human pose estimation. A separate experiment combines it with supervised ImageNet-1K initialization.",
    ),
}


if __name__ == "__main__":
    finalize_year(
        ROOT, YEAR, SPECS,
        (2026, 2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016),
        None,
    )
