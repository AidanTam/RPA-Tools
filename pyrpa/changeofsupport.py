'''
Class for performing support correction
gammabar: pure-Python GSLIB gammabar (no external .exe; runs on any platform)
DGM still to come
'''

import numpy as np
import subprocess
import pandas as pd
import os
import pyrpa.utils as ut
from scipy.optimize import brentq
import scipy.stats as st
from math import exp

path = os.path.dirname(os.path.abspath(__file__)) + os.sep
cwd = os.getcwd()

def stnormpdf(x):
    denom = (2*3.1415926)**.5
    num = exp(-x**2/2)
    return num/denom;

class supportcorrection(object):

    def __init__(self, samples, gradefield=None, mean=None, variance_reduction=1., number_polynomials=100):

        self.samples = samples
        self.gradefield = gradefield

        if mean is not None:
            self.mean = mean
        else:
            self.mean = np.average(self.samples.data[self.gradefield], weights=self.samples.weights)

        self.variance_reduction = variance_reduction
        self.number_polynomials = number_polynomials


    def affine_correction(self, outfield='ILC'):

        self.samples.data[outfield] = np.sqrt(self.variance_reduction)*(self.samples.data[self.gradefield]-self.mean)+self.mean;


    def indirect_lognormal_correction(self, outfield='ILC'):

        if np.sum(self.samples.data[self.gradefield]) > 0.:
            cv = self.mean / ut.weighted_standard_deviation(self.samples.data[self.gradefield],
                                                            weights=self.samples.weights)
            b = (np.log((self.variance_reduction * cv ** 2 + 1)) / np.log(cv ** 2 + 1)) ** 0.5
            a = (self.mean / (self.variance_reduction * cv ** 2 + 1) ** 0.5) * (((cv ** 2 + 1) ** 0.5) / self.mean) ** b
            q = a * self.samples.data[self.gradefield] ** b
            mq = np.average(q)
            q_prime = q * (self.mean / mq)
        else:
            q_prime = np.zeros(len(self.samples.data[self.gradefield]))
            
        self.samples.data[outfield] = q_prime

    def direct_lognormal_correction(self, outfield='DLC'):

        cv = self.mean / ut.weighted_standard_deviation(self.samples.data[self.gradefield],
                                                        weights=self.samples.weights)
        b = (np.log((self.variance_reduction * cv ** 2 + 1)) / np.log(cv ** 2 + 1)) ** 0.5
        a = (self.mean / (self.variance_reduction * cv ** 2 + 1) ** 0.5) * (((cv ** 2 + 1) ** 0.5) / self.mean) ** b
        q = a * self.samples.data[self.gradefield] ** b

        self.samples.data[outfield] = q


    def discrete_gaussian_model(self, outfield='DGM'):
        '''


                                  Parameters for HISTSCALE
                          ************************

        START OF PARAMETERS:
        data.out                      -input file with data
        4         0                   -   columns for variable and weight
        -1.0      1.0e21              -   trimming limits
        1                             -option for computation of variance adjustment factor f
        0.80                          -   1-value of variance adjustment factor f
        16.0      3.2                 -   2-dispersion variances at point and block supports
        10.0   10.0   10.0            -   3-dispersion variances from gammabar: size of block in X, Y, Z directions
        5      5      5               -     discretization of grid in X, Y, Z directions
        2  0.1                        -     standardized variogram model: number of structures, nugget effect
        1  0.7    0.0    0.0    0.0   -     type of structure #1, variance contribution, anisotropy angle 1, angle 2, angle 3
                100.0  300.0   10.0   -     semivariogram ranges a_hmax, a_hmin, a_vert
        1  0.2    0.0    0.0    0.0   -     type of structure #2, variance contribution, anisotropy angle 1, angle 2, angle 3
                500.0 1500.0   20.0   -     semivariogram ranges a_hmax, a_hmin, a_vert
        1.0e-6    1.0                 -DGM: acceptable error for dispersion variance at block support, upper_r_limit (set >1 for downscaling)
        100                           -     number of Hermite polynomials to use
        histscale.out                 -output file for adjusted data
        summary.out                   -output file for summary statistics

        :param outfield:
        :return:
        '''


        grades = np.array(self.samples.data[self.gradefield]).flatten()
        weights = np.array(self.samples.weights).flatten()

        os.chdir(path)

        if os.path.isfile("histscale.par"):
            os.remove("histscale.par")

        if os.path.isfile("histscale.out"):
            os.remove("histscale.out")

        if os.path.isfile("histscale.dat"):
            os.remove("histscale.dat")

        histcale_dat = open(path + "histscale.dat", "w")
        histcale_dat.write("BLA" + "\n")
        histcale_dat.write("2" + "\n")
        histcale_dat.write("GRADE" + "\n")
        histcale_dat.write("WEIGHT" + "\n")

        print('Converting to GSLIB format...')
        for i in range(len(self.samples.data)):
            histcale_dat.write(str(grades[i]) + " " + str(weights[i])  + "\n")
        histcale_dat.close()

        histcale_par = open(path + "histscale.par", "w")
        histcale_par.write("Parameters for HISTSCALE " + "\n")
        histcale_par.write("************************ " + "\n")
        histcale_par.write("  " + "\n")
        histcale_par.write("START OF PARAMETERS: " + "\n")
        histcale_par.write("./histscale.dat " + "\n")
        histcale_par.write("1 2 0 " + "\n")
        histcale_par.write("-1.0       1.0e21 " + "\n")
        histcale_par.write("1" + "\n")
        histcale_par.write(str(self.variance_reduction) + "\n")
        histcale_par.write("16.0      3.2" + "\n")
        histcale_par.write("10.0   10.0   10.0" + "\n")
        histcale_par.write("5      5      5" + "\n")
        histcale_par.write("2  0.1" + "\n")
        histcale_par.write("1  0.7    0.0    0.0    0.0 " + "\n")
        histcale_par.write("        100.0  300.0   10.0 " + "\n")
        histcale_par.write("1  0.2    0.0    0.0    0.0 " + "\n")
        histcale_par.write("        500.0 1500.0   20.0  " + "\n")
        histcale_par.write("1.0e-6    1.0  " + "\n")
        histcale_par.write("100 " + "\n")
        histcale_par.write("histscale.out " + "\n")
        histcale_par.write("summary.out " + "\n")
        histcale_par.close()
        print('Running Histcale...')
        subprocess.check_call(["histscale.exe", "histscale.par"], shell=True)
        print('Reading Results...')
        df = pd.read_csv(path + "histscale.out", delimiter=r"\s+", header=None, skiprows=9)

        self.samples.data[outfield] = np.array(df)[:, 5].flatten()

        os.chdir(cwd)

        return;

    def discrete_gaussian_model2(self, outfield='DGM'):

        z = np.array(self.samples.data[self.gradefield])
        cdf = ut.weighted_cdf(self.samples.weights)
        y = st.norm.ppf(cdf)

        H = np.ones((self.number_polynomials + 1, len(y)))
        H[1, :] = -y  # second monomial

        # recurrent formula
        for k in range(1, self.number_polynomials):
            H[k + 1, :] = -1 / np.sqrt(k + 1) * y * H[k, :] - np.sqrt(k / float(k + 1)) * H[k - 1, :]

        PCI = np.zeros([H.shape[0]])
        g = np.zeros([H.shape[1]])
        PCI[0] = np.average(self.samples.data[self.gradefield], weights=self.samples.weights)

        n, m = H.shape[0], H.shape[1]

        # standard normal pdf at each gaussian-transformed value (independent of p)
        for i in range(1, m):
            g[i] = stnormpdf(y[i])

        for p in range(1, n):
            PCI[p] = np.sum((z[:m - 1] - z[1:m]) * H[p - 1, 1:m] * g[1:m]) / np.sqrt(p)

        def f_var_Zv(r, PCI, Var_Zv):

            a = 0.
            for i in range(1, len(PCI)):
                a += PCI[i] ** 2. * r ** (2. * i)

            return a-Var_Zv;

        r = brentq(f=f_var_Zv, a=0, b=1, args=(PCI, 1.0-self.variance_reduction))
        Z = np.zeros(H.shape[1])
        Z[:] = PCI[0]

        for p in range(1, len(PCI)):
            Z += PCI[p] * H[p, :] * r ** p

        self.samples.data[outfield] = Z


    def compare_gtcurve(self, blockmodel, 
                        model_gradefield,
                        gcos_field='DGM',
                        precision=2):

        cutoffs = np.unique(np.round(self.samples.data[gcos_field], precision))
        cutoffs = np.sort(cutoffs)

        model_proportion = []
        gcos_proportion = []
        model_grade = []
        gcos_grade = []

        for cutoff in cutoffs:

            model_IDX = blockmodel.data[model_gradefield] >= cutoff
            gcos_IDX = self.samples.data[gcos_field] >= cutoff
            gcos_grades = np.array(self.samples.data[gcos_field][gcos_IDX]).flatten()
            gcos_weights = np.array(self.samples.weights[gcos_IDX]).flatten()

            if blockmodel.tonnes[model_IDX].sum() != 0.:
                model_proportion.append(blockmodel.tonnes[model_IDX].sum() / blockmodel.tonnes.sum())
                model_grade.append(np.average(blockmodel.data[model_gradefield][model_IDX], weights=blockmodel.tonnes[model_IDX]))
            else:
                model_grade.append(np.nan)
                model_proportion.append(np.nan)

            if np.sum(np.array(self.samples.weights[gcos_IDX])) != 0.:
                gcos_grade.append(np.average(gcos_grades, weights=gcos_weights))
                gcos_proportion.append(np.sum(gcos_weights) / np.sum(np.array(self.samples.weights)))
            else:
                gcos_proportion.append(np.nan)
                gcos_grade.append(np.nan)


        return pd.DataFrame({"Cut Off": cutoffs,
                             "Model Proportion": model_proportion,
                             "Model Grade": model_grade,
                             "GCOS Proportion": gcos_proportion,
                             "GCOS Grade": gcos_grade});


def _gslib_rotmat(ang1, ang2, ang3, anis1, anis2):
    """GSLIB ``setrot``: build the 3x3 matrix that rotates a lag vector and
    scales the minor/vertical axes by 1/anisotropy, so that the squared length
    of the transformed vector is measured in major-axis range units."""
    DEG2RAD = np.pi / 180.0
    EPSLON = 1.0e-20
    if 0.0 <= ang1 < 270.0:
        alpha = (90.0 - ang1) * DEG2RAD
    else:
        alpha = (450.0 - ang1) * DEG2RAD
    beta = -ang2 * DEG2RAD
    theta = ang3 * DEG2RAD
    sina, sinb, sint = np.sin(alpha), np.sin(beta), np.sin(theta)
    cosa, cosb, cost = np.cos(alpha), np.cos(beta), np.cos(theta)
    afac1 = 1.0 / max(anis1, EPSLON)
    afac2 = 1.0 / max(anis2, EPSLON)
    return np.array([
        [cosb * cosa, cosb * sina, -sinb],
        [afac1 * (-cost * sina + sint * sinb * cosa),
         afac1 * (cost * cosa + sint * sinb * sina),
         afac1 * (sint * cosb)],
        [afac2 * (sint * sina + cost * sinb * cosa),
         afac2 * (-sint * cosa + cost * sinb * sina),
         afac2 * (cost * cosb)],
    ])


def _structure_gamma(hr, it):
    """Standardised (sill = 1) variogram value for a lag ratio hr = h / range."""
    if it == 1:      # spherical
        return np.where(hr < 1.0, hr * (1.5 - 0.5 * hr * hr), 1.0)
    elif it == 2:    # exponential
        return 1.0 - np.exp(-3.0 * hr)
    elif it == 3:    # gaussian
        return 1.0 - np.exp(-3.0 * hr * hr)
    raise ValueError("Unsupported structure type %r (expected 1, 2 or 3)" % (it,))


def gammabar(block_size,
             discretisation=[4, 4, 4],
             rotation=[20, 10, 30],
             nugget=0.1,
             structure_types=[1, 1],
             variances=[0.5, 0.3],
             vranges=[[100, 50, 10], [120, 60, 15]]):
    """Average variogram value within a block, gamma-bar(v, v).

    Pure-Python reimplementation of the GSLIB ``gammabar`` program. The previous
    implementation wrote a ``.par`` file and shelled out to a bundled Windows
    ``gammabar.exe`` via ``powershell.exe`` (see git history) -- that cannot run
    on the Linux hosts used by Streamlit Cloud, so the Gammabar tool errored on
    the hosted app. This computes the same quantity directly.

    The block is discretised into nx*ny*nz points and gamma-bar is the mean
    variogram value over every ordered pair of points; the diagonal (lag h = 0)
    contributes 0, matching GSLIB. ``rotation`` is [ang1, ang2, ang3] (GSLIB
    azimuth/dip/plunge in degrees) applied to every structure; each ``vranges``
    entry is [a_major, a_minor, a_vertical]. Structure types are 1=spherical,
    2=exponential, 3=gaussian. With nugget + sum(variances) == 1 (as the caller
    normalises), the result lies in [0, 1].
    """
    bx, by, bz = [float(v) for v in block_size]
    nx, ny, nz = [max(1, int(round(d))) for d in discretisation]

    # Discretisation point offsets inside the block. Only pairwise differences
    # enter gamma-bar, so the block need not be centred on the origin.
    xs = (np.arange(nx) + 0.5) * (bx / nx)
    ys = (np.arange(ny) + 0.5) * (by / ny)
    zs = (np.arange(nz) + 0.5) * (bz / nz)
    gx, gy, gz = np.meshgrid(xs, ys, zs, indexing="ij")
    pts = np.column_stack([gx.ravel(), gy.ravel(), gz.ravel()])   # (N, 3)
    n = pts.shape[0]

    diff = pts[:, None, :] - pts[None, :, :]                      # (N, N, 3) lags

    ang1, ang2, ang3 = rotation[0], rotation[1], rotation[2]
    gamma = np.zeros((n, n))
    for it, cc, vr in zip(structure_types, variances, vranges):
        a_major = float(vr[0])
        anis1 = (float(vr[1]) / a_major) if a_major else 1.0
        anis2 = (float(vr[2]) / a_major) if a_major else 1.0
        rm = _gslib_rotmat(ang1, ang2, ang3, anis1, anis2)
        rot = diff @ rm.T                                        # (N, N, 3)
        h = np.sqrt(np.einsum("ijk,ijk->ij", rot, rot))
        hr = h / a_major if a_major else np.zeros_like(h)
        gamma += float(cc) * _structure_gamma(hr, int(it))

    # Nugget contributes at every non-zero lag; the diagonal stays at 0.
    off = ~np.eye(n, dtype=bool)
    gamma[off] += float(nugget)
    gamma[~off] = 0.0

    return float(gamma.mean())









