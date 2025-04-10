import unittest

import numpy as np
from skimage.data import binary_blobs
from skimage.measure import label

try:
    from trackastra.model import Trackastra
except ImportError:
    Trackastra = None


class TestMultiDimensionalSegmentation(unittest.TestCase):

    def test_merge_instance_segmentation_3d(self):
        from micro_sam.multi_dimensional_segmentation import merge_instance_segmentation_3d

        n_slices = 5
        data = np.stack(n_slices * binary_blobs(512))
        seg = label(data)

        stacked_seg = []
        offset = 0
        for _ in range(n_slices):
            stack_seg = seg.copy()
            stack_seg[stack_seg != 0] += offset
            offset = stack_seg.max()
            stacked_seg.append(stack_seg)
        stacked_seg = np.stack(stacked_seg)

        merged_seg = merge_instance_segmentation_3d(stacked_seg)

        # Make sure that we don't have any new objects in z + 1.
        # Every object should be merged, since we have full overlap due to stacking.
        ids0 = np.unique(merged_seg[0])
        for z in range(1, n_slices):
            self.assertTrue(np.array_equal(ids0, np.unique(merged_seg[z])))

    def test_merge_instance_segmentation_3d_with_closing(self):
        from micro_sam.multi_dimensional_segmentation import merge_instance_segmentation_3d

        n_slices = 5
        data = np.stack(n_slices * binary_blobs(512))
        seg = label(data)

        stacked_seg = []
        offset = 0
        for z in range(n_slices):
            # Leave the middle slice blank, so that we can check that it
            # gets merged via closing.
            if z == 2:
                stack_seg = np.zeros_like(seg)
            else:
                stack_seg = seg.copy()
                stack_seg[stack_seg != 0] += offset
                offset = stack_seg.max()
            stacked_seg.append(stack_seg)
        stacked_seg = np.stack(stacked_seg)

        merged_seg = merge_instance_segmentation_3d(stacked_seg, gap_closing=1)

        # Make sure that we don't have any new objects in z + 1.
        # Every object should be merged, since we have full overlap due to stacking.
        ids0 = np.unique(merged_seg[0])
        for z in range(1, n_slices):
            self.assertTrue(np.array_equal(ids0, np.unique(merged_seg[z])))

    @unittest.skipIf(Trackastra is None, "Requires trackastra")
    def test_track_across_frames(self):
        from micro_sam.multi_dimensional_segmentation import track_across_frames, get_napari_track_data

        n_slices = 5
        data = binary_blobs(512).astype("uint8")
        seg = label(data)

        stacked_data, stacked_seg = [], []
        offset = 0
        for _ in range(n_slices):
            stack_seg = seg.copy()
            stack_seg[stack_seg != 0] += offset
            offset = stack_seg.max()
            stacked_data.append(data)
            stacked_seg.append(stack_seg)

        stacked_data = np.stack(stacked_data)
        stacked_seg = np.stack(stacked_seg)

        tracks, lineages = track_across_frames(stacked_data, stacked_seg)

        self.assertEqual(tracks.shape, stacked_seg.shape)
        track_ids = set(np.unique(tracks)) - {0}
        lineage_roots = set([next(iter(lin.keys())) for lin in lineages])
        self.assertEqual(track_ids, lineage_roots)

        get_napari_track_data(tracks, lineages)


if __name__ == "__main__":
    unittest.main()
