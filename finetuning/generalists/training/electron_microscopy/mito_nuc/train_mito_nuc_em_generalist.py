import os
import argparse

import torch

import micro_sam.training as sam_training
from micro_sam.util import export_custom_sam_model

from obtain_mito_nuc_em_datasets import get_generalist_mito_nuc_loaders


def finetune_mito_nuc_em_generalist(args):
    """Code for finetuning SAM on mitochondria and nuclei electron microscopy datasets"""
    # override this (below) if you have some more complex set-up and need to specify the exact gpu
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # training settings:
    model_type = args.model_type
    checkpoint_path = None  # override this to start training from a custom checkpoint
    patch_shape = (1, 512, 512)  # the patch shape for training
    n_objects_per_batch = args.n_objects  # this is the number of objects per batch that will be sampled (default: 25)
    checkpoint_name = f"{args.model_type}/mito_nuc_em_generalist_sam"

    # all the stuff we need for training
    train_loader, val_loader = get_generalist_mito_nuc_loaders(input_path=args.input_path, patch_shape=patch_shape)
    scheduler_kwargs = {"mode": "min", "factor": 0.9, "patience": 15}

    # Run training.
    sam_training.train_sam(
        name=checkpoint_name,
        model_type=model_type,
        train_loader=train_loader,
        val_loader=val_loader,
        early_stopping=None,  # Avoid early stopping for training the generalist model.
        n_objects_per_batch=n_objects_per_batch,
        checkpoint_path=checkpoint_path,
        with_segmentation_decoder=True,
        device=device,
        lr=1e-5,
        n_iterations=args.iterations,
        save_root=args.save_root,
        scheduler_kwargs=scheduler_kwargs,
        verify_n_labels_in_loader=None,  # Verifies all labels in the loader(s).
        box_distortion_factor=0.05,
    )

    if args.export_path is not None:
        checkpoint_path = os.path.join(
            "" if args.save_root is None else args.save_root, "checkpoints", checkpoint_name, "best.pt"
        )
        export_custom_sam_model(
            checkpoint_path=checkpoint_path,
            model_type=model_type,
            save_path=args.export_path,
        )


def main():
    parser = argparse.ArgumentParser(description="Finetune Segment Anything for the Mito. & Nuclei EM datasets.")
    parser.add_argument(
        "--input_path", "-i", default="/mnt/vast-nhr/projects/cidas/cca/experiments/micro_sam/data",
        help="The filepath to all the respective EM datasets. If the data does not exist yet it will be downloaded"
    )
    parser.add_argument(
        "--model_type", "-m", default="vit_b",
        help="The model type to use for fine-tuning. Either vit_t, vit_b, vit_l or vit_h."
    )
    parser.add_argument(
        "--save_root", "-s", default="/mnt/vast-nhr/projects/cidas/cca/experiments/micro_sam/v4",
        help="Where to save the checkpoint and logs. By default they will be saved where this script is run from."
    )
    parser.add_argument(
        "--iterations", type=int, default=int(25e4),
        help="For how many iterations should the model be trained? By default 250k."
    )
    parser.add_argument(
        "--export_path", "-e",
        help="Where to export the finetuned model to. The exported model can be used in the annotation tools."
    )
    parser.add_argument(
        "--n_objects", type=int, default=25, help="The number of instances (objects) per batch used for finetuning."
    )
    args = parser.parse_args()
    finetune_mito_nuc_em_generalist(args)


if __name__ == "__main__":
    main()
