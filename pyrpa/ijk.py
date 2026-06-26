'''
module for assigning ijk values
Uses datamine convention for IJK
'''

import numpy as np

def get_idx_from_IJK(ijk, numblocks):
    ijk = np.array(ijk)
    i = np.floor(ijk / (numblocks[1] * numblocks[2]))
    n = ijk - i * numblocks[1] * numblocks[2]
    j = np.floor(n / numblocks[2])
    k = np.floor(n - j * numblocks[2])
    idx = np.array([i, j, k])
    x, y = np.shape(idx)
    if y > x:
        idx = idx.transpose()
    return idx;

def get_XYZ_from_idx(idx, blocksize, origin):
    x = idx[:, 0] * blocksize[0] + origin[0] + 0.5*blocksize[0]
    y = idx[:, 1] * blocksize[1] + origin[1] + 0.5*blocksize[1]
    z = idx[:, 2] * blocksize[2] + origin[2] + 0.5*blocksize[2]
    return np.array([x, y, z]);

def get_idx_from_XYZ(xyz, blocksize, origin):
    xyz = np.array(xyz)
    i  = np.floor((xyz[:, 0] - float(origin[0])) / float(blocksize[0]))
    j  = np.floor((xyz[:, 1] - float(origin[1])) / float(blocksize[1]))
    k  = np.floor((xyz[:, 2] - float(origin[2])) / float(blocksize[2]))
    idx = np.array([i,j,k])
    x, y = np.shape(idx)
    if y > x:
        idx = idx.transpose()
    return idx;

def get_IJK_from_idx(idx, numblocks):
    ijk = idx[:, 0] * numblocks[1] * numblocks[2] + idx[:, 1] * numblocks[2] + idx[:, 2]
    return ijk;

def get_IJK_from_XYZ(xyz, blocksize, origin, numblocks):
    xyz = np.array(xyz)
    idx = get_idx_from_XYZ(xyz, blocksize, origin)
    return get_IJK_from_idx(idx, numblocks);

def get_XYZ_from_ijk(ijk, blocksize, origin, numblocks):
    idx = get_idx_from_IJK(ijk=ijk, numblocks=numblocks)
    return get_XYZ_from_idx(idx=idx, blocksize=blocksize, origin=origin);