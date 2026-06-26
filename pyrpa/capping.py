'''
Capping class
Various capping analyses
'''

import pandas as pd
import numpy as np
import scipy.stats as st
from scipy.spatial import distance_matrix
from statsmodels.stats.weightstats import DescrStatsW
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
from matplotlib import rcParams
from matplotlib import rc
from pyrpa import metal_at_risk
import sklearn.neighbors as nn
import warnings
from pyrpa import plotting
import pyrpa.utils as ut
import pyrpa.changeofsupport as cs


warnings.simplefilter("ignore")

def cap_grades(data, capping_level):
    capped_data = np.array(data.copy())
    capped_data[capped_data > capping_level] = capping_level
    return capped_data

def _prop_metal(x, weights, thresholds):

    prop_metal = np.zeros(len(thresholds), dtype=float)

    for i in range(len(thresholds)):
        # capped = cap_grades(x, thresholds)
        capped = x.copy()
        capped[capped > thresholds[i]] = thresholds[i]
        prop_metal[i] = np.sum(capped * weights) / np.sum(x * weights)

    return prop_metal

class capping(object):

    def __init__(self, samples, gradefield, capping_levels=None, label=None, unit=None, decimal_places=2):
        '''

        :param samples:
        :param gradefield:
        :param weights:
        :param capping_levels:
        :param label:
        :param unit:
        '''

        assert len(samples.data) > 0, "Input data required"
        assert gradefield, "Grade field required"

        self.samples = samples
        self.gradefield = gradefield
        self.samples.data = self.samples.data.sort_values(by=self.gradefield).reset_index(drop=True)
        if self.samples.weightf is None:
            self.samples.weights = np.ones(len(samples.data))
        else:
            self.samples.weights = self.samples.data[self.samples.weightf]
        self.decimal_places = decimal_places

        if label is None:
            self.label = self.gradefield
        else:
            self.label = label

        if unit is not None:
            self.label += " (" + str(unit) + ")"

        self.weights = samples.weights

        self.cdf = ut.weighted_cdf(self.weights)
        self.zscore = st.norm.ppf(self.cdf)

        if capping_levels is None:
            self.capping_levels = np.interp(x=[0.9, 0.95, 0.96, 0.97, 0.98, 0.99, 0.995],
                                            xp=self.cdf,
                                            fp=self.samples.data[self.gradefield])
            self.capping_levels = np.round(self.capping_levels, self.decimal_places)
        else:
            self.capping_levels = capping_levels


    def cutting_curve(self, target_average=None, figsize=(15, 10)):

        x = np.array(self.samples.data[self.gradefield])
        avg_grade = [np.average(cap_grades(x, val), weights=self.weights) for val in x]

        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor(color="white")
        plt.plot(x, avg_grade, 'o-r')

        if target_average is not None:
            target_grade = np.interp(target_average, avg_grade, x)
            print ("Target Cap =", np.round(target_grade, self.decimal_places))
            plt.plot([target_grade, target_grade], [0, np.max(avg_grade)], '--g')
            plt.plot([np.min(x), np.max(x)],
                     [target_average, target_average], '--g')

        plt.xlabel("Capping Grade: " + self.label)
        plt.ylabel(" Average Grade: " + self.label)
        plt.legend(["Average Grade", "Target Capping Grade"], loc=4)

        plotting.set_plot_font()

        return plt;

    def decile_analysis(self, plot=False, figsize=(15, 10)):

        # add an the max grade, i.e. uncapped
        if isinstance(self.capping_levels, (list,)):
            caps = self.capping_levels
        else:
            caps = self.capping_levels.tolist()

        caps.append(np.round(np.max(self.samples.data[self.gradefield]), 2))
        columns = ['Percent Metal Loss','Min', 'Max', 'Average Grade', 'CV', 'Capping Percentile', 'Number of Caps']
        df = pd.DataFrame()
        grades = np.array(self.samples.data[self.gradefield].copy())
        totmetal = np.sum(grades * self.weights)

        for cap in caps:
            capped_grades = cap_grades(self.samples.data[self.gradefield], cap)
            metal = np.sum(capped_grades * self.weights)
            perc_mloss = abs(np.round((metal / totmetal - 1.) * 100., self.decimal_places))
            ming = np.round(np.min(capped_grades), self.decimal_places)
            maxg = np.round(np.max(capped_grades), self.decimal_places)
            avg_grade = np.round(np.average(capped_grades, weights=self.weights), self.decimal_places)
            cv = np.round(ut.weighted_standard_deviation(capped_grades, weights=self.weights) / avg_grade, self.decimal_places)
            cap_perc = np.round(np.interp(x=cap, xp=self.samples.data[self.gradefield], fp=self.cdf), 3)
            filt = self.samples.data[self.gradefield] > cap
            numcaps = int(len(self.samples.data[filt]))
            dftemp = pd.DataFrame(data=np.reshape([perc_mloss, ming, maxg, avg_grade, cv, cap_perc, numcaps], (1, 7)),
                                  columns=columns, index=[str(cap) + " Cap"])
            decmet = 0.
            for i in range(90, 100):
                filt = (self.cdf >= float(i) / 100.) & (self.cdf < float(i + 1) / 100.)
                tmetal = np.sum(capped_grades[filt] * self.weights[filt])
                dftemp[str(i) + "%"] = np.round(tmetal / metal * 100., self.decimal_places)
                decmet += dftemp.loc[str(cap) + " Cap", str(i) + "%"]
            dftemp["90%-100%"] = decmet
            df = df.append(dftemp)
        df = df.transpose()
        df = df.rename(columns={str(np.max(self.samples.data[self.gradefield])) + " Cap": "Uncapped"})

        if plot:
            x = np.arange(len(df.loc['90%-100%'][:-1]))
            fig, ax = plt.subplots(figsize=figsize)
            fig.patch.set_facecolor(color="white")
            plt.bar(x + 0.5, df.loc['90%-100%'][:-1], color="red")
            plt.bar(x + 0.5, df.loc['99%'][:-1], color="black")
            plt.plot([-0.5, len(x) + 0.5], [10, 10], '--g', linewidth=5)
            plt.plot([-0.5, len(x) + 0.5], [40, 40], '--b', linewidth=5)
            plt.xticks(x + 0.5, self.capping_levels)
            plt.xlabel("Capping Level: " + self.label)
            plt.ylabel("Proportion of Total Metal")
            plt.xlim((-0.5, len(x)))
            plt.legend(["Parish P99 Limit", "Parish P90 Limit", 'P90 - P100', 'P99'], loc=0)

        return df;

    def disintegration_analysis(self, plot=True, logx=True, xmin=0., xmax=None, figsize=(15, 10)):

        disint = abs((self.samples.data[self.gradefield].shift(1) / self.samples.data[self.gradefield]) - 1.) * 100.

        if plot:
            fig, ax = plt.subplots(figsize=figsize)
            fig.patch.set_facecolor(color="white")

            if xmax is not None:
                xlim = (self.samples.data[self.gradefield] >= xmin) & (self.samples.data[self.gradefield] < xmax)
            else:
                xlim = (self.samples.data[self.gradefield] >= xmin)

            plt.plot(self.samples.data[self.gradefield][xlim], disint[xlim], 'or-')
            plt.xlabel(self.label)
            plt.ylabel("Metal Disintegration (1.0 - g(x)/g(x-1)*100)")

            for axis in [ax.xaxis, ax.yaxis]:
                axis.set_major_formatter(ScalarFormatter())
            ax.yaxis.grid(True, which='major', linestyle='-', color='k')
            ax.xaxis.grid(True, which='major', linestyle='-', color='k')
            ax.xaxis.grid(True, which='minor', linestyle='-', color='k')

            if logx:
                plt.xscale("log")
                for axis in [ax.xaxis, ax.yaxis]:
                    axis.set_major_formatter(ScalarFormatter())
            plotting.set_plot_font()

        return disint;

    def hg_spacing(self, figsize=(15, 10)):

        assert self.capping_levels is not None, "capping levels not defined"

        avg_dists = []
        for cap in self.capping_levels:
            xyz = np.array(self.samples.data[self.samples.xyzfields][self.samples.data[self.gradefield] >= cap])
            dmat = distance_matrix(xyz, xyz)
            try:
                avg_dists.append(np.average(dmat[dmat!=0]))
            except:
                avg_dists.append(0)

        plt.figure(figsize=figsize)
        plt.plot(self.capping_levels, avg_dists, '-or')
        plt.xlabel('Cut-off ' + self.label)
        plt.ylabel('Average Distance (m)')

    def log_probability_plot(self, show_caps=False, figsize=(10, 10)):

        xlabel = self.label

        if show_caps:

            fig = plotting.cdf_plot(grades=self.samples.data[self.gradefield],
                                     frequencies=self.zscore,
                                     xlabel=xlabel,
                                     figsize=figsize,
                                     caps=self.capping_levels)
            
        else:

            fig = plotting.cdf_plot(grades=self.samples.data[self.gradefield],
                     frequencies=self.zscore,
                     xlabel=xlabel,
                     figsize=figsize)


        return fig;

    def histogram(self, num_bins=None, bin_width=None, xmax=None, ymax=None, log=False, figsize=(15, 10)):

        bins = None

        if xmax is not None:
            x = self.samples.data[self.gradefield][self.samples.data[self.gradefield] <= xmax].copy()
        else:
            x = self.samples.data[self.gradefield].copy()

        if num_bins is None and bin_width is None:
            num_bins = 20

        if bin_width is not None:
            bins = np.arange(np.min(x), np.max(x) + bin_width, bin_width)
            num_bins = int((np.max(x) - np.min(x)) / float(bin_width))

        if log:
            x[x <= 0] = 0.0001
            bins = plotting.log_scale_bins(minx=np.min(x), maxx=np.max(x), num_bins=num_bins)

        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor(color="white")

        if bins is None:
            plt.hist(x, bins=num_bins, color='red')
        else:
            plt.hist(x, bins=bins, color='red')

        if ymax is not None:
            plt.ylim((0, ymax))

        if log:
            plt.xscale("log")
            for axis in [ax.xaxis, ax.yaxis]:
                axis.set_major_formatter(ScalarFormatter())

        # add comma separator for 1000s
        xticks = []
        for tick in ax.get_xticks():
            if float(tick) < 10:
                xticks.append(round(tick, 3))
            else:
                xticks.append(format(tick, ',.0f'))
        ax.set_xticklabels(xticks)

        plt.xlabel(self.label)
        plt.ylabel("Count")
        plotting.set_plot_font()

        return plt;

    def location_map(self, xyzfields=None, plane='XY', unit='m', p1=0.95, p2=0.99):

        p95 = np.interp(x=p1, xp=self.cdf, fp=self.samples.data[self.gradefield])
        p99 = np.interp(x=p2, xp=self.cdf, fp=self.samples.data[self.gradefield])

        if xyzfields is not None:
            self.samples.xyzfields = xyzfields

        assert self.samples.xyzfields is not None, "xyzfields required."

        xyz_dat = np.array(self.samples.data[self.samples.xyzfields])

        if plane == 'XY':

            x = xyz_dat[:, 0]
            y = xyz_dat[:, 1]
            xlabel = "Easting"
            ylabel = "Northing"

        elif plane == 'XZ':

            x = xyz_dat[:, 0]
            y = xyz_dat[:, 2]
            xlabel = "Easting"
            ylabel = "Elevation"

        else:

            x = xyz_dat[:, 1]
            y = xyz_dat[:, 2]

            xlabel = "Northing"
            ylabel = "Elevation"

        xlabel += " (" + unit + ")"
        ylabel += " (" + unit + ")"

        p95x = x[self.samples.data[self.gradefield] > p95].copy()
        p95y = y[self.samples.data[self.gradefield] > p95].copy()
        p99x = x[self.samples.data[self.gradefield] > p99].copy()
        p99y = y[self.samples.data[self.gradefield] > p99].copy()

        xrange = np.max(x) - np.min(x)
        yrange = np.max(y) - np.min(y)
        aniso = yrange / xrange
        if xrange > yrange:
            fig = plt.figure(figsize=(20, 20 * aniso))
        else:
            fig = plt.figure(figsize=(20 / aniso, 20))
        ax = plt.subplot(111)
        fig.patch.set_facecolor(color="white")
        ax.plot(x, y, 'ok', markersize=3, label='Data')
        ax.plot(p95x, p95y, 'og', markersize=10, label='P' + str(np.round(p1 * 100, 1)) + '=' + str(np.round(p95, self.decimal_places)))
        ax.plot(p99x, p99y, 'or', markersize=15, label='P' + str(np.round(p2 * 100, 1)) + '=' + str(np.round(p99, self.decimal_places)))
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        # ax.legend(['Data', 'P95 = ' + str(np.round(p95, 1)), 'P99 = ' + str(np.round(p99, 1))])
        plotting.set_plot_font()
        # Shrink current axis's height by 10% on the bottom
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.1,
                         box.width, box.height * 0.9])

        if xrange > yrange:
            # ax.legend(loc='upper center',
            #           bbox_to_anchor=(0.5, -0.25),
            #           fancybox=True, shadow=True, ncol=5)
            ax.legend(loc='best')
        else:
            # ax.legend(loc='upper center',
            #           bbox_to_anchor=(0.5, -0.05),
            #           fancybox=True, shadow=True, ncol=5)
            ax.legend(loc='best')

        return plt;

    def metal_map(self, xyzfields=None, plane='XY', unit='m', scale=10000.):

        pass

    def simulation(self, resource_tonnes=10000., production_rate=1000., number_of_samples=100000, plot=True, figsize=(15, 10)):

        mar = metal_at_risk.MetalAtRisk(x=self.samples.data[self.gradefield],
                                        weights=self.samples.weights,
                                        discretization=number_of_samples)
        results = []
        for thresh in self.capping_levels:
            mar.calculate(hg_threshold=thresh,
                          resource_tonnes=resource_tonnes,
                          production_rate=production_rate,
                          realizations=1000)

            p1 = mar.simulation['Adjusted-Unadjusted Ratio'].iloc[200]
            results.append([thresh, p1])

        df = pd.DataFrame(data=results,
                          columns=["HG Threshold", "Target Metal"])

        df["Actual Metal"] = _prop_metal(x=self.samples.data[self.gradefield],
                                        weights=self.samples.weights,
                                        thresholds=self.capping_levels)
        df["Target/Actual"] = df["Actual Metal"] / df["Target Metal"]

        if plot:
            fig, ax = plt.subplots(figsize=figsize)
            fig.patch.set_facecolor(color="white")
            labels = ["Target/Actual", "Target Metal", "Actual Metal", 'Implied Cap']
            plt.plot(df['HG Threshold'], df["Target/Actual"], '-ro')
            plt.plot(df['HG Threshold'], df["Target Metal"], '-ko')
            plt.plot(df['HG Threshold'], df["Actual Metal"], '-bo')
            cap = np.interp(x=1., xp=df["Target/Actual"], fp=df['HG Threshold'])
            plt.plot([cap, cap], [0, 1.1], '--g')
            plt.plot([df['HG Threshold'].min(), df['HG Threshold'].max()], [1., 1.], '--r')
            plt.xlabel(self.label)
            plt.ylabel('Metal/Ratio')
            plotting.set_plot_font()
            plt.legend(labels, loc='best', fancybox=True)

        return df;

    def stats(self, cap=None):

        index = ["Variable", "Count", "Min", "Max", "Average", "CV", "Number Capped", "Metal Loss",
                 "Cap Percentile"]
        columns = ["Uncapped", "Capped"]

        df = pd.DataFrame(columns=columns, index=index)

        x = self.samples.data[self.gradefield]
        capped = x.copy()

        if cap is not None:
            capped[capped >= cap] = cap

        for column in columns:
            df[column].loc["Variable"] = self.label
            df[column].loc["Count"] = len(x)
            df[column].loc["Min"] = np.min(x)

        df['Uncapped'].loc["Max"] = np.round(np.max(x), self.decimal_places)
        df['Capped'].loc["Max"] = np.round(np.max(capped), self.decimal_places)
        df['Uncapped'].loc["Average"] = np.round(np.average(x, weights=self.weights), self.decimal_places)
        df['Capped'].loc["Average"] = np.round(np.average(capped, weights=self.weights), self.decimal_places)
        df['Uncapped'].loc["CV"] = np.round(np.sqrt(ut.weighted_variance(x, weights=self.weights)) / df['Uncapped'].loc[
            "Average"], self.decimal_places)
        df['Capped'].loc["CV"] = np.round(np.sqrt(ut.weighted_variance(capped, weights=self.weights)) / df['Capped'].loc[
            "Average"], self.decimal_places)
        df['Uncapped'].loc["Number Capped"] = 0
        df['Capped'].loc["Number Capped"] = len(x[x != capped])
        df['Uncapped'].loc["Metal Loss"] = "0%"
        df['Capped'].loc["Metal Loss"] = str(
            np.round(abs(df['Capped'].loc["Average"] / df['Uncapped'].loc["Average"] - 1.) * 100., self.decimal_places)) + "%"
        df['Uncapped'].loc["Cap Percentile"] = 100.
        if cap is None:
            df['Capped'].loc["Cap Percentile"] = 100.
        else:
            df['Capped'].loc["Cap Percentile"] =np.round(np.interp(x=cap, xp=x, fp=self.cdf) * 100.,3)

        return df

    def capping_vs_resource_grade(self, mincut=None, maxcut=None, step=None, cap_granularity=1.0,
                                  cap_grade_factor=10., log=True):

        ''''''

        cutoffs = np.arange(mincut, maxcut + step, step)
        vareds = [0.001, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.999]

        grades = np.array(self.samples.data[self.gradefield])
        weights = self.weights

        idx = np.argsort(grades)
        grades = grades[idx]
        weights = weights[idx]

        plt.figure(figsize=(15,10))
        for vr in vareds:
            caps = []
            grades_cor = np.sqrt(vr)*(grades-np.average(grades, weights=weights))+ np.average(grades, weights=weights)
            for cog in cutoffs:
                filt = grades >= cog
                cap = grades[-1]
                gf_capped = grades_cor.copy()
                while cap / np.average(gf_capped[filt], weights=weights[filt]) > cap_grade_factor:
                    gf_capped = cap_grades(gf_capped, cap)
                    cap -= cap_granularity
                caps.append(cap)
            plt.plot(cutoffs, caps, 'o-')
        plt.xlabel("Cut-off Grade " + self.label)
        plt.ylabel("Capping Grade " + self.label)
        plt.legend(vareds, title="Smoothing Ratios", loc='best')
        if log:
            plt.yscale('log')









