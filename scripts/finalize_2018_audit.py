#!/usr/bin/env python3
"""Finalize the 2018 paper cohort."""

from pathlib import Path
import sys

from audit_year_common import finalize_year, spec


ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
YEAR = 2018


def paper(method, family, description, pretraining, evaluation, venue, venue_normalized,
          *, status="peer_reviewed", url="", doi="", arxiv="", notes="", new_title=""):
    return spec(
        method, family, description, pretraining, evaluation, venue, venue_normalized,
        year=YEAR, status=status, url=url, doi=doi, arxiv=arxiv, notes=notes, new_title=new_title,
    )


SPECS = {
    "Geometry guided convolutional neural networks for self-supervised video representation learning": paper(
        "Geometry-Guided CNN", "Pretext / Predictive",
        "A progressive geometry curriculum first predicts optical flow from synthetic image pairs and then predicts stereo disparity from real 3D movies while distillation preserves the learned motion representation.",
        "FlyingChairs; Web 3D Movies", "UCF101; HMDB51", "CVPR 2018", "CVPR",
        url="https://openaccess.thecvf.com/content_cvpr_2018/html/Gan_Geometry_Guided_Convolutional_CVPR_2018_paper.html", doi="10.1109/CVPR.2018.00586",
        new_title="Geometry Guided Convolutional Neural Networks for Self-Supervised Video Representation Learning",
        notes="Web 3D Movies denotes the authors' private collection of approximately 80 stereoscopic films and 40,000 frame pairs.",
    ),
    "Self-supervised spatiotemporal feature learning via video rotation prediction": paper(
        "3DRotNet / Video Rotation Prediction", "Pretext / Predictive",
        "A 3D ConvNet predicts one of four in-plane rotations applied consistently to every frame of a clip, encouraging joint spatial and temporal understanding.",
        "Kinetics-400", "UCF101; HMDB51", "arXiv / Preprint", "arXiv / Preprint",
        status="preprint", url="https://arxiv.org/abs/1811.11387", arxiv="1811.11387",
        new_title="Self-Supervised Spatiotemporal Feature Learning via Video Rotation Prediction",
    ),
    "Cooperative learning of audio and video models from self-supervised synchronization": paper(
        "Audio-Visual Temporal Synchronization (AVTS)", "Multimodal / Audio-Visual",
        "Two-stream audio and video encoders learn temporal synchronization with a contrastive objective and a curriculum that progresses from easy to hard negative pairs.",
        "Kinetics-400; AudioSet; SoundNet Dataset", "Kinetics-400; AudioSet; UCF101; HMDB51; ESC-50; DCASE2014", "NeurIPS 2018", "NeurIPS",
        url="https://proceedings.neurips.cc/paper/2018/hash/c4616f5a24a66668f11ca4fa80525dc4-Abstract.html", arxiv="1807.00230",
        new_title="Cooperative Learning of Audio and Video Models from Self-Supervised Synchronization",
        notes="The paper trains separate AVTS models on Kinetics-400, AudioSet, and the SoundNet collection; downstream experiments cover both visual and audio recognition.",
    ),
    "Audio-visual scene analysis with self-supervised multisensory features": paper(
        "Multisensory Temporal Alignment", "Multimodal / Audio-Visual",
        "A fused 3D visual and raw-waveform audio network predicts whether sound and video are temporally aligned, producing features used for localization, action recognition, and source separation.",
        "AudioSet-750K; VoxCeleb; VoxCeleb2", "UCF101; Kinetics-Sounds; VoxCeleb; GRID", "ECCV 2018", "ECCV",
        url="https://openaccess.thecvf.com/content_ECCV_2018/html/Andrew_Owens_Audio-Visual_Scene_Analysis_ECCV_2018_paper.html", doi="10.1007/978-3-030-01231-1_39", arxiv="1804.03641",
        new_title="Audio-Visual Scene Analysis with Self-Supervised Multisensory Features",
        notes="The core multisensory representation is learned from about 750,000 AudioSet videos. VoxCeleb and VoxCeleb2 are used for task-specific source-separation training and GRID for transfer evaluation.",
    ),
    "Compressed video action recognition": paper(
        "Compressed Video Action Recognition (CoViAR)", "Other / Hybrid",
        "Separate CNN streams process I-frames, motion vectors, and residuals directly from compressed video, and recurrent aggregation combines their predictions over time.",
        "ImageNet-1K", "UCF101; HMDB51; Charades", "CVPR 2018", "CVPR",
        url="https://openaccess.thecvf.com/content_cvpr_2018/html/Wu_Compressed_Video_Action_CVPR_2018_paper.html", arxiv="1712.00636",
        new_title="Compressed Video Action Recognition",
        notes="This is a supervised action-recognition paper rather than a self-supervised pretraining method. Its component CNNs use supervised ImageNet-1K initialization.",
    ),
    "Improving spatiotemporal self-supervision by deep reinforcement learning": paper(
        "Reinforcement-Learned Spatiotemporal Permutations", "Pretext / Predictive",
        "A REINFORCE policy adaptively samples useful spatial and temporal ordering permutations while a shared network learns to solve both tasks.",
        "ImageNet-1K; UCF101", "UCF101; HMDB51; ImageNet-1K; PASCAL VOC 2007; PASCAL VOC 2012", "ECCV 2018", "ECCV",
        url="https://openaccess.thecvf.com/content_ECCV_2018/html/Uta_Buchler_Improving_Spatiotemporal_Self-Supervision_ECCV_2018_paper.html", doi="10.1007/978-3-030-01267-0_47", arxiv="1807.11293",
        new_title="Improving Spatiotemporal Self-Supervision by Deep Reinforcement Learning",
        notes="ImageNet-1K supplies images for the spatial ordering task, while UCF101 supplies video frames for the temporal ordering task.",
    ),
    "Learning and using the arrow of time": paper(
        "Temporal Class Activation Map Network (T-CAM) / Arrow of Time", "Pretext / Predictive",
        "A long-range forward-versus-reversed video classifier learns temporal features, with class activation maps and preprocessing used to localize evidence and suppress codec, camera, and editing shortcuts.",
        "UCF101; Flickr-AoT; Kinetics-AoT", "UCF101; HMDB51; Flickr-AoT; Kinetics-AoT; TA180; ReverseFilm", "CVPR 2018", "CVPR",
        url="https://openaccess.thecvf.com/content_cvpr_2018/html/Wei_Learning_and_Using_CVPR_2018_paper.html", doi="10.1109/CVPR.2018.00840",
        new_title="Learning and Using the Arrow of Time",
        notes="Flickr-AoT and Kinetics-AoT are constructed for arrow-of-time training and testing; TA180 and ReverseFilm are targeted temporal-asymmetry evaluation sets.",
    ),
}


if __name__ == "__main__":
    finalize_year(
        ROOT, YEAR, SPECS,
        (2026, 2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018),
        2017,
    )
