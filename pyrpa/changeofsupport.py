'''
Class for performing support correction
gammabar not working yet
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


def gammabar(block_size,
             discretisation=[4, 4, 4],
             rotation=[20, 10, 30],
             nugget=0.1,
             structure_types=[1, 1],
             variances=[0.5, 0.3],
             vranges=[[100, 50, 10], [120, 60, 15]]):

    os.chdir(path)

    gammabar_par = open("gammabar.par", "w")
    gammabar_par.write("Parameters for Gammabar " + "\n")
    gammabar_par.write("************************ " + "\n")
    gammabar_par.write("  " + "\n")
    gammabar_par.write("START OF PARAMETERS: " + "\n")
    gammabar_par.write(str(block_size[0]) + " " + str(block_size[1]) + " " + str(block_size[2]) + " " + "\n")
    gammabar_par.write(
        str(discretisation[0]) + " " + str(discretisation[1]) + " " + str(discretisation[2]) + " " + "\n")
    gammabar_par.write("0             - calculate measure of dissemination? 0-no, 1-yes \n")
    gammabar_par.write(str(len(variances)) + " " + str(nugget) + " " + "\n")

    for structure_type, var, vrange in zip(structure_types, variances, vranges):
        gammabar_par.write(
            str(structure_type) + " " + str(var) + " " + str(rotation[0]) + " " + str(rotation[1]) + " " + str(
                rotation[2]) + " " + "\n")
        gammabar_par.write(str(vrange[0]) + " " + str(vrange[1]) + " " + str(vrange[2]) + " " + "\n")

    gammabar_par.close()

    subprocess.call("echo gammabar.par | powershell.exe ./gammabar.exe > gammabar.out", shell=True)

    with open("gammabar.out") as f:
        content = f.readlines()

    avg_var = content[-4].replace('/n', ' ').split("=")[-1]
    # avg_var = float(content[-4].strip("/n").split("=")[-1])

    os.chdir(cwd)

    return avg_var;









