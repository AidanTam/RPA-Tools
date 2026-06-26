'''
Sample Object
e.g. Assays or composites
'''

import pandas as pd
import pyrpa.utils as ut
import pyrpa.ijk as ijk
import numpy as np
import pyrpa.plotting as pl
import matplotlib.pyplot as plt
import scipy.spatial as spatial
from multiprocessing.pool import ThreadPool as Pool
from sklearn.neighbors import NearestNeighbors
import scipy.stats as st
from IPython.display import display, HTML


class Sample(object):

    def __init__(self, data, gradefields=None, holeid=None, xyzfields=['X', 'Y', 'Z'],
                 domainf=None, weightf=None):
        '''
        Geological sample object. Normally a desurveyed drill hole object with xyz coordinates and some
        attributes. A gradefield is required
        :param data: pd.DataFrame or .csv file
            input data. can be dataframe or csv object
        :param gradefields: [str]
            list of grade fields
        :param holeid: str
            field name for holeid
        :param xyzfields: [list]
            list of field names e.g. ['x', 'y', 'z']
        :param domainf: str
            field name for domain field, e.g. 'ZONE'
        :param weightf: str
            field name for weight field e.g. 'length'. If not supplied a weight of 1.0 will be applied to all samples
        '''

        assert gradefields is not None, "A list of grade fields is required, e.g. ['Au','Aucap']"

        self.data = ut.check_data(data)

        if isinstance(gradefields, str):
            gradefields = [gradefields]

        self.gradefields = gradefields
        self.xyzfields = xyzfields
        self.domainf = domainf
        self.holeid = holeid
        self.weightf = weightf

        if weightf is not None:
            self.weights = self.data[weightf]
        else:
            self.weights = np.ones(len(self.data), dtype=float)

        # if a domain fields is specified we can report a stats for each grade field and each domain
        # if not report the stats on the entire block model
        self.stats = pd.DataFrame()
        for gradef in self.gradefields:
            if self.domainf is not None:
                for dom in self.data[domainf].unique():
                    filt = (self.data[domainf]==dom)
                    self.stats = self.stats.append(ut.weighted_stats(self.data.loc[filt, gradef],
                                                                     weights=self.weights[filt],
                                                                     gradef=gradef, dom=dom))
                sortfields = ["Domain", "Variable"]
            else:
                self.stats = self.stats.append(ut.weighted_stats(self.data[gradef],
                                                                 weights=self.weights,
                                                                 gradef=gradef))
                sortfields = ["Variable"]
        self.stats = self.stats.sort_values(by=sortfields).reset_index(drop=True)

        # to use for comparing data sets

        self.flagfield = None
        self.flag = None
        self.gradefield_paired = None

    def spacing(self, nearest_neighbours=3, by_domain=False):
        '''
        Calculate drill hole spacing using a nearest neighbour approach.
        :param nearest_neighbours: int
            number of nearest drill holes for spacing calculation
        :param by_domain: boolean
            if true calculate ddh spacing will be calculated by domain
        :return: pd.DataFrame
            adds field '_spacing' to the ``self.data`` DataFrame

        usage:
            >> import pyrpa
            >> sample = smp.Sample(data=df, holeid="BHID", xyzfields=['X', 'Y', 'Z'], gradefields=['AU'])
            >> sample.spacing(nearest_neighbours=3, by_domain=True)

        '''

        assert self.holeid is not None, "No holeid specified"
        df_out= None
        if by_domain:
            df_out = pd.DataFrame()
            assert self.domainf is not None, "Domain field is not specified"
            self.data['sort_order'] = np.arange(len(self.data))
            for dom in self.data[self.domainf].unique():
                print (dom)
                df = self.data[self.data[self.domainf]==dom].copy()
                spacing = np.zeros(len(df)) + 999.
                if len(df) > 1:
                    for i in range(len(df)):
                        dists, idx = ut.nearest_neighbour_idx2(np.array([df[self.xyzfields].iloc[i]]),
                                                               np.array(df[self.xyzfields]))
                        spacing[i]=ut.get_dist_nearest_dholes(df[self.holeid].iloc[i],
                                                                         np.array(df[self.holeid]), dists, idx,
                                                                         nearest_neighbours)
                df['_spacing'] = spacing
                df_out = df_out.append(df).reset_index(drop=True)
            df_out = df_out.sort_values(by=['sort_order']).reset_index(drop=True)
        else:
            df = self.data.copy()
            spacing = np.zeros(len(df)) + 999.
            for i in range(len(df)):
                dists, idx = ut.nearest_neighbour_idx2(np.array([df[self.xyzfields].iloc[i]]),
                                                       np.array(df[self.xyzfields]))
                spacing[i] = ut.get_dist_nearest_dholes(df[self.holeid].iloc[i],
                                                                   np.array(df[self.holeid]), dists, idx,
                                                                   nearest_neighbours)
            df['_spacing'] = spacing
            df_out = df
        if df_out is not None:
            self.data = df_out

        df_out=None
        df=None

    def thin_ddh_spacing(self, target_spacing=50., nearest_neighbours=3):
        '''
        Thin out the drill hole spacing to a minimum spacing. A field will be added to the
        sample object dataframe which flags holes to be removed to achieve desired drill spacing.
        The routine works as follows:

            - The drill hole spacing is calculated.
            - If the minimum spacing is less than target spacing,
              the drill hole with the minumum drill hole spacing is removed.
            - The process is repeated until the minimum drill hole spacing is
              greater or equal to the target spacing

        :param target_spacing: float
            desired minimum drill hole spacing.
        :param nearest_neighbours: int
            number of nearest drill holes to consider when calculating drill hole spacing
        :return: series(int)
            field [_spacing_lt_ + target spacing] added to ``smp.data`` DataFrame
             e.g. "_spacing_lt_50". If value=1, record to be removed to achieve desired spacing

        usage:
            >> import pyrpa
            >> sample = smp.Sample(data=df, holeid="BHID", xyzfields=['X', 'Y', 'Z'], gradefields=['AU'])
            >> sample.thin_ddh_spacing(target_spacing=50, nearest_neighbours=3)

        '''

        # first calculate the drillhole spacing in a temp df

        df = pd.DataFrame(self.data.copy())
        spacing = np.zeros(len(df)) + 999.
        for i in range(len(df)):
            dists, idx = ut.nearest_neighbour_idx2(np.array([df[self.xyzfields].iloc[i]]),
                                                   np.array(df[self.xyzfields]))
            spacing[i] = ut.get_dist_nearest_dholes(df[self.holeid].iloc[i],
                                                    np.array(df[self.holeid]), dists, idx,
                                                    nearest_neighbours)

        dhlist = []
        spacing[np.isnan(spacing)]=0.
        while np.min(spacing) < target_spacing:
            print ("Current min spacing =" + str(np.min(spacing)))
            min_idx = np.argmin(spacing)
            if spacing[min_idx] < target_spacing:
                dhlist.append(df[self.holeid].iloc[min_idx])
                df = df[df[self.holeid] != dhlist[-1]].copy()
                spacing = np.zeros(len(df)) + 999.
                for i in range(len(df)):
                    dists, idx = ut.nearest_neighbour_idx2(np.array([df[self.xyzfields].iloc[i]]),
                                                           np.array(df[self.xyzfields]))
                    spacing[i] = ut.get_dist_nearest_dholes(df[self.holeid].iloc[i],
                                                            np.array(df[self.holeid]), dists, idx,
                                                            nearest_neighbours)

        outfield = '_spacing_lt_' + str(target_spacing)
        self.data[outfield] = 0
        self.data.loc[self.data[self.holeid].isin(dhlist), outfield] = 1
        # for dh in dhlist:
        #     self.data[outfield][self.data[self.holeid] == dh] = 1

    def thin_ddh_spacing_v2(self, target_spacings=[25., 50., 75]):
        '''

        :param target_spacings:
        :param spacing_multiplier:
        :return:
        '''


        for tg, target_spacing in enumerate(target_spacings):
            print("Working on spacing =", target_spacing)
            outfield = '_spacing_lt_' + str(target_spacing)
            if target_spacing != target_spacings[0]:
                self.data[outfield] = self.data['_spacing_lt_' + str(target_spacings[tg-1])]
                outfield = '_spacing_lt_' + str(target_spacing)
            else:
                self.data[outfield] = 0

            print("Final thinning (Longest part).....")

            dftemp = self.data[self.data[outfield]==0].copy().reset_index(drop=True)

            if len(dftemp)>1:

                dhlist = []
                closest = 0.
                while closest < target_spacing:
                    print(closest)
                    holeids = np.array(dftemp[self.holeid])
                    hx, hy = np.meshgrid(holeids, holeids)
                    dists = spatial.distance_matrix(dftemp[self.xyzfields], dftemp[self.xyzfields])
                    dists[hx == hy] = 9999999.
                    dists[np.isnan(dists)] = 100000.
                    dists = dists + np.random.rand() / 10000.
                    closest = dists.min()
                    mindix = np.unravel_index(dists.argmin(), dists.shape)
                    dhlist.append(hx[mindix])
                    dftemp = dftemp[dftemp[self.holeid] != dhlist[-1]].copy()

                self.data.loc[self.data[self.holeid].isin(dhlist), outfield] = 1



    def capped_vs_uncapped_plot(self, cappedfield, uncappedfield,
                                label=None, unit=None, figsize=(15,10), log=False, sortby='uncapped'):

        '''
        Simple plot with domain name on x axis and Grade on y axis showing capped versus uncapped values. Used for
        visual comparison of capping grades over mutiple domains.

        :param cappedfield: str
            dataframe field with capped values
        :param uncappedfield: str
            dataframe field with uncapped values
        :param label: str
            label for y axis. If not provided the uncapped fieldname will be used
        :param unit: str
            unit for values
        :param figsize: tuple
        :return:
        '''

        if label is None:
            label = uncappedfield
        if unit is not None:
            label += (" (" + unit + ")")

        assert cappedfield is not None, 'Capped field must be supplied'
        assert uncappedfield is not None, 'Uncapped field must be supplied'

        if sortby == 'capped':
            sf = cappedfield
        else:
            sf = uncappedfield

        means = self.data.groupby([self.domainf], as_index=False, sort=True)[cappedfield, uncappedfield].mean()
        means = means.sort_values(by=[sf], ascending=False)
        means['_x'] = np.arange(len(means)) + 1

        self.data = pd.merge(self.data, means[[self.domainf, '_x']], on=self.domainf)
        x = self.data['_x'].copy()
        self.data = self.data.drop('_x', 1)

        plt.figure(figsize=figsize)
        plt.plot(x, self.data[uncappedfield], 'or')
        plt.plot(x, self.data[cappedfield], 'ok')
        plt.xlabel(self.domainf)
        plt.ylabel(label)

        if log:
            plt.yscale('log')

        plt.xticks(np.arange(len(means)) + 1, labels=means[self.domainf], rotation=90)
        plt.legend(['Uncapped ' + label, 'Capped ' + label])

        return plt;

    def create_spatial_pairs(self, flagfield=None, flag=None, gradefield=None):
        '''

        :param flagfield:
        :param flag:
        :return:
        '''

        assert flagfield is not None, 'flagfield not defined'
        assert flag is not None, 'flag1'

        self.flagfield = flagfield
        self.flag = flag
        self.gradefield_paired = gradefield

        Y = np.array(self.data.loc[self.data[flagfield]==flag, self.xyzfields])
        X = np.array(self.data[self.xyzfields])

        nbrs = NearestNeighbors(n_neighbors=1).fit(Y)
        distances, indices = nbrs.kneighbors(X)
        indices = indices.flatten()
        distances = distances.flatten()

        self.data['_dist_to_' + str(flag)] = distances
        self.data['_paired_' + gradefield] = np.array(self.data[gradefield])[indices]

    def paired_plots(self, flag2=None, distance=10., binwidth=1.0, histymax=None):

        assert self.flagfield is not None, 'need to run "create_spatial_pairs" function'

        filt = (self.data[self.flagfield] == flag2) & (self.data['_dist_to_' + str(self.flag)] < distance)

        x1 = self.data.loc[filt, self.gradefield_paired]
        x2 = self.data.loc[filt, '_paired_' + self.gradefield_paired]
        w = np.ones(len(x1))
        cdf = ut.weighted_cdf(w)
        y = st.norm.ppf(cdf)

        stats1 = ut.weighted_stats(z=x1, weights=w, gradef=self.gradefield_paired)
        stats2 = ut.weighted_stats(z=x2, weights=w, gradef='_paired_' + self.gradefield_paired)
        stats1 = stats1.append(stats2)

        pl.cdf_plot_compare(x1=np.sort(x1), x2=np.sort(x2),
                                        frequencies1=y,
                                        frequencies2=y,
                                        xlabel=self.gradefield_paired,
                                        figsize=(10, 10),
                                        legend=[self.gradefield_paired, '_paired_' + self.gradefield_paired])

        plt.show()
        gmax = np.max([np.max(x1), np.max(x2)])
        bins = np.arange(0., gmax, binwidth)
        plt.figure(figsize=(10,10))
        plt.hist(x1, bins=bins, color='black')
        plt.hist(x2, bins=bins, facecolor="None", edgecolor='red')
        if histymax is not None:
            plt.ylim(0., histymax)
        plt.xlabel(self.gradefield_paired)
        plt.ylabel('Count')
        pl.set_plot_font()
        plt.legend([self.gradefield_paired, self.gradefield_paired + '_paired_'], loc=1)
        plt.show()

        fig, ax = plt.subplots(figsize=(10,10))
        plt.plot(np.sort(x1), np.sort(x2), 'o-r', markersize=3)
        plt.plot(np.sort(x1),np.sort(x1), '-k')
        plt.xlabel(self.gradefield_paired)
        plt.ylabel('_paired_' + self.gradefield_paired)
        plt.title('QQ plot')
        # plt.xlim((0,gmax))
        # plt.ylim((0, gmax))
        plt.xscale('log')
        plt.yscale('log')
        pl.set_plot_font()
        pl.scientific_to_normal_ticks(ax)
        plt.show()

        display(HTML(stats1.to_html()))





























