import numpy as np
import pyrpa.utils as ut
import pyrpa.ijk as ijk
import scipy.spatial
import pandas as pd


def nnblk_declustering(samples, blocks):

    '''
    Nearest Neighbour block declustering

    Blocks containing samples sum the tonnes of nearest neighbours. The weight is then determined by
    dividing this sum of the tonnes by the number of samples in each block. The weights are then normalised
    such that the sum of the weights is equal to the number of samples.

    :param samples: pyrpa.smp.Sample object
        sample object created using pyrpa.smp.Sample class
    :param blocks: pyrpa.blk.BlockModel
        block model object created using pyrpa.blk.BlockModel class
    :return: str
        writes column '_dcweight' to sample.data DataFrame

    Usage:
    ------

    >>> nnblk_declustering(samples=samp_data, blocks=block_data)
    >>> samp_data['_dcweight']
    1.2
    0.8
    ...
    0.3
    0.5

    '''

    # assert isinstance(blocks, pyrpa.blockmodel.BlockModel), "Block model not a pyrpa.blockmodel.BlockModel object"

    # assign an ijk to the samples/composites based on their position and the blockmodel setup

    samp_ijk = ijk.get_IJK_from_XYZ(samples.data[samples.xyzfields],
                                    blocksize=[blocks.setup['Block Size X'],
                                               blocks.setup['Block Size Y'],
                                               blocks.setup['Block Size Z']],
                                    origin=[blocks.setup['Origin X'],
                                            blocks.setup['Origin Y'],
                                            blocks.setup['Origin Z']],
                                    numblocks=[blocks.setup['Number of Blocks X'],
                                               blocks.setup['Number of Blocks Y'],
                                               blocks.setup['Number of Blocks Z']])

    # find all the blocks that have samples in them

    unique_smp_ijks, samp_counts = np.unique(samp_ijk, return_counts=True)

    xyz_smp_ijk = ijk.get_XYZ_from_ijk(ijk=unique_smp_ijks,
                                       blocksize=[blocks.setup['Block Size X'],
                                                  blocks.setup['Block Size Y'],
                                                  blocks.setup['Block Size Z']],
                                       origin=[blocks.setup['Origin X'],
                                               blocks.setup['Origin Y'],
                                               blocks.setup['Origin Z']],
                                       numblocks=[blocks.setup['Number of Blocks X'],
                                                  blocks.setup['Number of Blocks Y'],
                                                  blocks.setup['Number of Blocks Z']])

    # quick reblocking routine in case this is a sub-blocked model
    blocks.data['_ijk'] = blocks.ijk
    blocks.data['_tonnes'] = blocks.tonnes
    # unique_blk_ijks = np.unique(blocks.ijk)
    unique_blk_ijks = blocks.data.groupby(['_ijk'], as_index=False, sort=True)['_tonnes'].sum()
    xyz_blk_ijk = ijk.get_XYZ_from_ijk(ijk=unique_blk_ijks['_ijk'],
                                       blocksize=[blocks.setup['Block Size X'],
                                                  blocks.setup['Block Size Y'],
                                                  blocks.setup['Block Size Z']],
                                       origin=[blocks.setup['Origin X'],
                                               blocks.setup['Origin Y'],
                                               blocks.setup['Origin Z']],
                                       numblocks=[blocks.setup['Number of Blocks X'],
                                                  blocks.setup['Number of Blocks Y'],
                                                  blocks.setup['Number of Blocks Z']])


    # find the nearest neighbours
    mytree = scipy.spatial.cKDTree(xyz_smp_ijk.transpose())
    distances, indices = mytree.query(xyz_blk_ijk.transpose())
    unique_blk_ijks['_idx']=indices
    block_counts = unique_blk_ijks.groupby(['_idx'], as_index=False)['_tonnes'].sum()['_tonnes']
    # idx, block_counts = np.unique(indices, return_counts=True)

    # not needed for python 3
    samp_counts = samp_counts.astype(float)
    block_counts = block_counts.astype(float)

    # calculating weights
    weights = block_counts / samp_counts

    # assign the weights to the samples based on the ijk values
    samples.data['_dcweight'] = 0.
    for w, ijkn in zip(weights, unique_smp_ijks):
        samples.data.loc[samp_ijk==ijkn, '_dcweight'] = w

    samples.data._dcweight /= np.sum(samples.data._dcweight)
    samples.data._dcweight *= float(len(samples.data))
    blocks.data.drop(columns=['_ijk', '_tonnes'], inplace=True)


