import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pyrpa.utils import weighted_cdf

def discretize_cdf(x, cdf, discretization):
    '''

    :param x:
    :param cdf:
    :param discretization:
    :return:
    '''
    offset = (1. / discretization) / 2.
    disc_cdf = np.cumsum(np.zeros(discretization) + 1. / discretization) + offset
    return disc_cdf, np.interp(x=disc_cdf, xp=cdf, fp=x);

def prop_metal(x):

    # For each value v = x[j], compute sum(min(x, v)) / sum(x).
    # Vectorised via a single sort: for sorted values, the capped sum at
    # threshold v is sum(x <= v) + v * count(x > v). O(n log n) instead of O(n^2).
    x = np.asarray(x, dtype=float)
    n = len(x)
    total = np.sum(x)
    order = np.argsort(x, kind='stable')
    xs = x[order]
    csum = np.cumsum(xs)
    right = np.searchsorted(xs, xs, side='right')
    capped_sums = csum[right - 1] + xs * (n - right)

    prop_metal = np.empty(n, dtype=float)
    prop_metal[order] = capped_sums / total

    return prop_metal;



class MetalAtRisk(object):

    def __init__(self, x, weights, discretization=10000):

        self.x = np.array(x)
        self.weights = np.array(weights)
        self.discretization = discretization

        sort_idx = np.argsort(self.x)

        self.x = self.x[sort_idx]
        self.weights = self.weights[sort_idx]
        self.cdf = weighted_cdf(self.weights)
        self.disc_cdf, self.disc_x = discretize_cdf(self.x, self.cdf, discretization=self.discretization)

        self.simulation = None

    def calculate(self, hg_threshold=None,
                  resource_tonnes=None,
                  production_rate=None,
                  realizations=1000):

        assert hg_threshold < np.max(self.x), "Maximum high grade threshold must be lower or equal to maximum of data."

        if hg_threshold is None:
            hg_threshold = np.interp(x=0.95, xp=self.disc_cdf, fp=self.disc_x)
            print ("No high grade threshold given, 95th percentile used (thresh =", hg_threshold,").")

        assert resource_tonnes is not None, "Resource tonnes is required."

        if production_rate is None:
            production_rate = resource_tonnes / 10.
            print ("No production rate given, a 10 year mine life assumed.")

        self.num_samps = int(self.discretization * (production_rate / resource_tonnes))
        self.tonnes_per_sample = resource_tonnes / self.discretization
        low_grades = self.disc_x[self.disc_x < hg_threshold]
        high_grades = self.disc_x[self.disc_x >= hg_threshold]
        sim_samps = np.zeros(realizations, dtype=int)
        hg_sim_num = np.zeros(realizations, dtype=int)
        hg_avg_grade = np.zeros(realizations)

        # print ("Number of samples per annum", self.num_samps)

        for i in range(realizations):

            # simulate number of HG samples
            samples = np.random.choice(a=self.disc_x, size=self.num_samps)
            hg_sim_num[i] = int(len(samples[samples >= hg_threshold]))
            sim_samps[i] = len(samples)
            # simulate HG samples
            hg_avg_grade[i] = np.average(np.random.choice(a=high_grades, size=hg_sim_num[i]))

        hg_tonnes = self.tonnes_per_sample * (float(len(high_grades)) / float(len(self.disc_x))) * self.num_samps
        adj_hg_tonnes = self.tonnes_per_sample * hg_sim_num
        lg_tonnes = self.tonnes_per_sample * (float(len(low_grades)) / float(len(self.disc_x))) * self.num_samps

        self.simulation = pd.DataFrame({"Number of Samples": sim_samps,
                           "Number of High Grades": hg_sim_num,
                           "HG Tonnes": hg_tonnes,
                           "LG Tonnes": lg_tonnes,
                           "Adjusted HG grade": hg_avg_grade,
                           "Adjusted HG tonnes": adj_hg_tonnes})

        self.simulation['LG Grade'] = np.average(self.disc_x[self.disc_x < hg_threshold])
        self.simulation['Unadjusted HG grade'] = np.average(self.disc_x[self.disc_x >= hg_threshold])
        self.simulation['Adjusted-Unadjusted Ratio'] = (self.simulation['LG Grade']*lg_tonnes + \
                                          self.simulation["Adjusted HG grade"]*self.simulation["Adjusted HG tonnes"]) / \
                                          (self.simulation['LG Grade']*lg_tonnes + \
                                          self.simulation["Unadjusted HG grade"]*self.simulation["HG Tonnes"])

        self.simulation = self.simulation.sort_values(by=(['Adjusted-Unadjusted Ratio'])).reset_index(drop=True)


    def implied_capping_grade(self, p_interval=0.2, return_ratio=False):

        self.capped_prop_metal = prop_metal(self.disc_x)
        unad_ad_ratio = self.simulation['Adjusted-Unadjusted Ratio'].iloc[int(p_interval*len(self.simulation))]
        implied_cap = np.interp(x=unad_ad_ratio, xp=self.capped_prop_metal, fp=self.disc_x)
        if return_ratio:
            return implied_cap, unad_ad_ratio;
        else:
            return implied_cap;






