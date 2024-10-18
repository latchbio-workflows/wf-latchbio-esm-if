# ESM Inverse Folding (ESM-IF1) predicts protein sequences from backbone structures.

<p align="center">
    <img src="https://pbs.twimg.com/tweet_video_thumb/FQFk7PsXsAMcV5N.jpg:large" alt="ESM Inverse figure" width="800px"/>
</p>

<html>
<p align="center">
<img src="https://user-images.githubusercontent.com/31255434/182289305-4cc620e3-86ae-480f-9b61-6ca83283caa5.jpg" alt="Latch Verified" width="100">
</p>

<p align="center">
<strong>
Latch Verified
</strong>
</p>

# ESM Inverse Folding

This functionality is built on top of the ESM (Evolutionary Scale Modeling) framework, leveraging its powerful language modeling capabilities for protein sequence prediction.

## Functionality

- Designs new sequences for given protein structures
- Scores how well sequences match structures
- Works with partial structures
- Handles protein complexes and multi-state proteins

## Key features

- Trained on 12M AlphaFold2-predicted structures
- 51% accuracy in recovering native sequences (72% for buried residues)
- ~10% improvement over previous methods
- Uses invariant geometric input processing layers followed by a sequence-to-sequence transformer
- Trained with span masking to tolerate missing backbone coordinates

## Citation

Learning inverse folding from millions of predicted structures
Chloe Hsu, Robert Verkuil, Jason Liu, Zeming Lin, Brian Hie, Tom Sercu, Adam Lerer, Alexander Rives
bioRxiv 2022.04.10.487779; doi: https://doi.org/10.1101/2022.04.10.487779
