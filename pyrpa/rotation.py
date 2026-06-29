'''
Rotate points in 3D
'''

import numpy as np

def _rot_matrix(a1, a2, a3, rottype='ZXZ'):

    a1 = np.radians(a1)
    a2 = np.radians(a2)
    a3 = np.radians(a3)

    c1 = np.cos(a1)
    c2 = np.cos(a2)
    c3 = np.cos(a3)

    s1 = np.sin(a1)
    s2 = np.sin(a2)
    s3 = np.sin(a3)

    if rottype == 'ZXZ':

        rotmat = np.array([[c1 * c3, -c1 * s3 - c2 * c3 * s1, s1 * s2],
                           [c3 * s1 + c1 * c2 * s3, c1 * c2 * c3 - s1 * s3, -c1 * s2],
                           [s2 * s3, c3 * s2, c2]])

    return rotmat;


def rotate_xyz(xyz, a1=0., a2=0., a3=0., origin=None):

    '''

    :param xyz:
    :param a1:
    :param a2:
    :param a3:
    :return:
    '''
    if origin is None:
        origin = [np.average(xyz[0, :]), np.average(xyz[1, :]), np.average(xyz[2, :])]

    xyz_trans = xyz

    for i in range(3):
        xyz_trans[i, :] = xyz[i, :] - float(origin[i])

    rotmat = _rot_matrix(a1, a2, a3)

    xyz_rot = np.zeros((len(xyz_trans), 3))

    for i in range(len(xyz_trans[0,:])):
        xyz_rot[i] = np.matmul(xyz_trans[i, :], rotmat)

    # xyz_rot = xyz_trans*rotmat[:, :, np.newaxis]

    for i in range(3):
        xyz_rot[i, :] += origin[i]

    return xyz_rot;

