'''
Block Model Object
'''

import pandas as pd
import pyrpa.utils as ut
import pyrpa.plotting as plotting
import pyrpa.ijk as ijk
import numpy as np
from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt

rotconventions = ['sxyz', 'sxyx', 'sxzy',
                'sxzx', 'syzx', 'syzy',
                'syxz', 'syxy', 'szxy',
                'szxz', 'szyx', 'szyz',
                'rzyx', 'rxyx', 'ryzx',
                'rxzx', 'rxzy', 'ryzy',
                'rzxy', 'ryxy', 'ryxz',
                'rzxz', 'rxyz', 'rzyz']

def block_model_setup_datamine():
    raise NotImplementedError("block_model_setup_datamine is not yet implemented")

def block_model_setup(origin=[0,0,0], blocksize=[10,10,10], numblocks=[100,100,100],
                      rotangles=[0.,0.,0.], rotation_origin=[0.,0.,0.], rotconvention='rzxz'):

    '''
    Block Model Setup
    ------------------
    Uses bottom left corner
    :param origin: list
        block model origin, bottom left corner of block model
    :param blocksize: list
        parent block size in each direction
    :param numblocks: list
        number of blocks in each direction
    :return: dict
        python dictionary with block model setup
    :usage:
        >>> import pyrpa
        >>> pyrpa.blk.block_model_setup(origin=[0,0,0], blocksize=[10,10,10], numblocks=[100,100,100])
        {'Block Size X': 10,
         'Block Size Y': 10,
         'Block Size Z': 10,
         'Number of Blocks X': 100,
         'Number of Blocks Y': 100,
         'Number of Blocks Z': 100,
         'Origin X': 0,
         'Origin Y': 0,
         'Origin Z': 0}

    '''

    assert len(origin)==3, "origin must have shape (3)"
    assert len(blocksize) == 3, "blocksize must have shape (3)"
    assert len(numblocks) == 3, "numblocks must have shape (3)"
    assert len(rotangles) == 3, "rotangles must have shape (3)"
    assert len(rotation_origin) == 3, "rotation_origin must have shape (3)"
    # check to see that the rotation convention
    assert rotconvention in rotconventions, "rotconvention must be one of the following:" + rotconventions

    setup = {'Origin X': origin[0],
             'Origin Y': origin[1],
             'Origin Z': origin[2],
             'Block Size X': blocksize[0],
             'Block Size Y': blocksize[1],
             'Block Size Z': blocksize[2],
             'Number of Blocks X': numblocks[0],
             'Number of Blocks Y': numblocks[1],
             'Number of Blocks Z': numblocks[2],
             'Rotation Angle 1': rotangles[0],
             'Rotation Angle 2': rotangles[1],
             'Rotation Angle 3': rotangles[2],
             'Rotation Origin X': rotation_origin[0],
             'Rotation Origin Y': rotation_origin[1],
             'Rotation Origin Z': rotation_origin[2],
             'Rotation Convention': rotconvention}

    return setup;

class BlockModel(object):

    '''
    Block Model Class
    -----------------

    For creating a block model class for use in other processes
    '''

    def __init__(self, data, setup=None, gradefields=None, xyzfields=['XC', 'YC', 'ZC'],
                 block_sizes=None,
                 domainf=None, densityf=None, partial_percentf=None):

        self.data = ut.check_data(data)
        if setup is not None:
            assert isinstance(setup, dict), "A dictionary is required for the block model setup," \
                                            "use the block_model_setup function to define the dictionary."
            self.setup = setup
        else:
            self.setup = block_model_setup()

        self.gradefields = gradefields
        self.xyzfields = xyzfields
        self.domainf = domainf
        self.block_sizes = block_sizes
        self.densityf = densityf

        if densityf is not None:
            self.density = np.array(self.data[densityf])
        else:
            self.density = np.ones(len(self.data), dtype=float)

        if partial_percentf is not None:
            self.partial_percent = np.array(data[partial_percentf])
            if self.partial_percent.max() > 2.:
                self.partial_percent /= 100.
        else:
            self.partial_percent = np.ones(len(self.data), dtype=float)

        if block_sizes is not None:
            self.tonnes = self.data[block_sizes].product(axis=1) * self.density * self.partial_percent
        else:
            self.tonnes = self.setup['Block Size X'] * self.setup['Block Size Y'] * self.setup['Block Size Z'] \
                          * self.density * self.partial_percent

        self.ijk = ijk.get_IJK_from_XYZ(self.data[self.xyzfields],
                                        blocksize=[self.setup['Block Size X'],
                                                   self.setup['Block Size Y'],
                                                   self.setup['Block Size Z']],
                                        origin=[self.setup['Origin X'],
                                                self.setup['Origin Y'],
                                                self.setup['Origin Z']],
                                        numblocks=[self.setup['Number of Blocks X'],
                                                   self.setup['Number of Blocks Y'],
                                                   self.setup['Number of Blocks Z']])

        # if a domain fields is specified we can report a stats for each grade field and each domain
        # if not report the stats on the entire block model

        stats_rows = []
        for gradef in self.gradefields:
            if self.domainf is not None:
                for dom in self.data[domainf].unique():
                    filter = (self.data[domainf] == dom)
                    stats_rows.append(ut.weighted_stats(self.data[gradef][filter],
                                                        weights=self.tonnes[filter],
                                                        gradef=gradef, dom=dom))
                sortfields = ["Domain", "Variable"]
            else:
                stats_rows.append(ut.weighted_stats(self.data[gradef], weights=self.tonnes, gradef=gradef))
                sortfields = ["Variable"]
        self.stats = pd.concat(stats_rows, ignore_index=True).sort_values(by=sortfields).reset_index(drop=True)


    def gt_curve(self, cutoffs, gradefield,
                 reporting_grades=None, domain_value=None,
                 plot=True):

        '''
        Grade Tonnage Curve:
        --------------------
        Uses the setup from the block model object
        :param cutoffs: list
            list of cutoff grades
        :param gradefield: float
            grade field for which the cutoff grade is applied
        :param reporting_grades: list
            list of grades to be reported based on the gradefield applied to the cutoffs. If None, the
            gradefield will beb reported
        :param domain_value: int, float, str
            optional domain value corresponding to the block model domainfield
        :param plot: boolean
            If True, will output a grade tonnage plot
        :return: df and/or plot
            returns dataframe and/or grade tonnage plot
        '''


        grades = []
        tonnes = []

        for cutoff in cutoffs:
            if domain_value is not None:
                filt = (self.data[gradefield]>=cutoff) & (self.data[self.domainf]==domain_value)
            else:
                filt = (self.data[gradefield]>=cutoff)

            tonnes.append(np.sum(self.tonnes[filt]))

            if reporting_grades is not None:
                temp=[]
                for rep_grade in reporting_grades:
                    temp.append(np.average(self.data[rep_grade][filt], weights=self.tonnes[filt]))
                grades.append(temp)
            else:
                grades.append(np.average(self.data[gradefield][filt], weights=self.tonnes[filt]))

        df = pd.DataFrame({"Cutoff": cutoffs, "Tonnes": tonnes})

        if reporting_grades is not None:
            for i, rep_grade in enumerate(reporting_grades):
                df[rep_grade] = np.array(grades)[:,i]
        else:
            df[gradefield] = grades

        if plot:
            if reporting_grades is not None:
                plotting.gt_curve(df, gradefields=reporting_grades, domain_value=domain_value,
                            domain_field=self.domainf)
            else:
                plotting.gt_curve(df, gradefields=[gradefield], domain_value=domain_value,
                            domain_field=self.domainf)

        return df;

    def swath_analysis(self, blockgrade_fields=None,
                       samples=None, samplegrade_fields=None,
                       direction='X', spacing=50.,
                       domain_value=None,
                       plot=False, figsize=(15,10)):

        '''

        :param blockgrade_fields: list str
            list of block grade fields e.g. ['Au', 'AuNN']
        :param samples: pyrpa.Sample object
            sample object
        :param samplegrade_fields:
            list of sample grade fields e.g. ['Au', 'AuCap']
        :param direction: str
            swath plot direction along the orthogonal direction options are 'X', 'Y' or 'Z'
        :param spacing: float
            swath spacing
        :param domain_value:  str
            optional domain value, only used if a domain field is defined for the block model object
        :param plot: boolean
            if true returns a plot
        :param figsize:
            optional resizing of the the figure, default is (15, 10)
        :return:
            a dataframe with the calculate swaths and if plot == True, will return a plot
        '''

        bm=None
        smp=None
        bmswath=[]
        swath=None
        smpswath=None

        spacing = float(spacing)

        assert blockgrade_fields is not None, 'A block model grade field must be supplied in a list'

        if direction == 'X':
            bmaxf = self.xyzfields[0]
            if samples is not None:
                smpaxf = samples.xyzfields[0]
        elif direction == 'Y':
            bmaxf = self.xyzfields[1]
            if samples is not None:
                smpaxf = samples.xyzfields[1]
        elif direction == 'Z':
            bmaxf = self.xyzfields[2]
            if samples is not None:
                smpaxf = samples.xyzfields[2]
        else:
            raise ValueError("Swath direction must be defined and must be 'X', 'Y' or 'Z'")

        bm = self.data.copy()
        if domain_value is not None:
            assert self.domainf is not None, "Block Model domain field must be defined"
            bm = bm[bm[self.domainf] == domain_value].copy()
            assert len(bm) > 0, "No block values in domain."
            bm['_tonnes'] = self.tonnes[self.data[self.domainf] == domain_value]
        else:
            bm['_tonnes'] = self.tonnes

        bm['_swath'] = np.floor(bm[bmaxf] / spacing) * spacing
        print(blockgrade_fields)
        for bmgf in blockgrade_fields:
            if bmgf != '_tonnes':
                bm[bmgf] *= bm['_tonnes']

        if '_tonnes' not in blockgrade_fields:
            blockgrade_fields.append('_tonnes')
        bmswath = bm.groupby(['_swath'], as_index=False, sort=True)[blockgrade_fields].sum()
        blockgrade_fields = blockgrade_fields[:-1]

        for bmgf in blockgrade_fields:
            bmswath[bmgf] /= bmswath._tonnes

        if samples is not None:
            if '_weights' not in samplegrade_fields:
                samplegrade_fields.append('_weights')
            smp = samples.data.copy()
            if domain_value is not None:
                assert samples.domainf is not None, "Sample domain field must be defined"
                smp = smp[smp[samples.domainf] == domain_value].copy()
                assert len(smp) > 0, "No sample domain values"
                smp['_weights'] = samples.weights[samples.data[samples.domainf] == domain_value]
            else:
                smp['_weights'] = samples.weights

            smp['_swath'] = np.floor(smp[smpaxf] / spacing) * spacing

            for smpgf in samplegrade_fields:
                if smpgf != '_weights':
                    smp[smpgf] *= smp['_weights']

            smpswath = smp.groupby(['_swath'], as_index=False, sort=True)[samplegrade_fields].sum()
            samplegrade_fields = samplegrade_fields[:-1]

            for smpgf in samplegrade_fields:
                smpswath[smpgf] /= smpswath._weights

            swath = pd.merge(bmswath, smpswath, on='_swath', how='left')
        else:
            swath = bmswath

        if plot:
            fig, ax = plt.subplots(figsize=figsize)
            fig.patch.set_facecolor(color="white")
            maxv = 0
            for bmfg in blockgrade_fields:
                plt.plot(swath._swath, swath[bmfg], 'o-')
                if maxv < np.max(swath[bmfg]):
                    maxv = np.max(swath[bmfg])
            if samples is not None:
                for smpfg in samplegrade_fields:
                    plt.plot(smpswath._swath, smpswath[smpfg], 'o-')
                    if maxv < np.max(swath[smpfg]):
                        maxv = np.max(swath[smpfg])

            plt.bar(swath._swath, swath._tonnes/swath._tonnes.max()*maxv, width=spacing, alpha=0.5)
            if samples is not None:
                plt.bar(swath._swath, swath._weights/swath._weights.max()*maxv, width=spacing, alpha=0.5)

            legend = blockgrade_fields
            if samples is not None:
                for smpfg in samplegrade_fields:
                    legend.append(smpfg)
            legend.append('Proportion of total blocks')
            legend.append('Proportion of total samples')

            plt.legend(legend)
            if domain_value is not None:
                plt.xlabel(str(domain_value) + " " + direction + ' Swath')
            else:
                plt.xlabel(direction + ' Swath')
            plt.ylabel('Grade')
            plotting.set_plot_font()


        return swath;

    def mean_comparison(self, samples=None, blk_benchmarkf=None, smp_benchmarkf=None, tolerance=0.1):
        '''

        :param blockmodel: object
            pypra.blk.BlockModel object
        :param samples: object
            pyrpa.smp.Sample object
        :param blk_benchmarkf: str
            Field in block model to use as benchmark for chart. Data will be sorted according to the mean value of this
            field.
        :param smp_benchmarkf: str
            Field in sample file to use as benchmark for chart. Data will be sorted according to the mean value of this
            field. If both blk_benchmarkf and smp_benchmarkf are defined, smp_benchmarkf will take preference. If none
            of the two are defined the first sample field will be used as the benchmark
        :param tolerance:
            Tolerance field for plotting acceptable limits window. 0.1 is the deafult which = 10%.
        :return:
        '''

        assert samples is not None, "Need to provide a pyrpa.smp.Sample object"

        blk_avgs = self.stats.pivot(index="Domain", columns="Variable", values="Average")

        for col in blk_avgs.columns:
            blk_avgs['blk - ' + col] = blk_avgs[col]
            blk_avgs = blk_avgs.drop(columns=[col])
        smp_avgs = samples.stats.pivot(index="Domain", columns="Variable", values="Average")
        for col in smp_avgs.columns:
            smp_avgs['smp - ' + col] = smp_avgs[col]
            smp_avgs = smp_avgs.drop(columns=[col])

        avgs = smp_avgs
        avgs[blk_avgs.columns] = blk_avgs
        avgs.reset_index(inplace=True)

        if smp_benchmarkf is not None:
            sortcol = 'smp - ' + smp_benchmarkf
        elif blk_benchmarkf is not None:
            sortcol = 'blk - ' + blk_benchmarkf
        else:
            sortcol = avgs.columns[1]

        avgs = avgs.sort_values(by=sortcol).reset_index(drop=True)
        avgs = avgs.dropna()

        plt.figure(figsize=(15, 10))

        for col in avgs.columns:
            if col != "Domain":
                plt.plot(avgs[col], 'o-')

        plt.plot(avgs[sortcol] * (1. + tolerance), '--r')
        plt.plot(avgs[sortcol] * (1. - tolerance), '--r')

        legend = [x for x in avgs.columns[1:]]
        legend.append(sortcol + ' +' + str(int(tolerance * 100.)) + '%')
        legend.append(sortcol + ' -' + str(int(tolerance * 100.)) + '%')
        plt.legend(legend, loc=0)
        plt.xticks(np.arange(len(avgs)), avgs['Domain'], rotation=90)
        plt.xlabel('Domain')
        plt.ylabel('Average')

        return avgs;

    def reblock(self, blocksizes=[10, 10, 10],
                dominant_fields=None, numeric_fields=None,
                dilute=False, dilution_density=None):
        '''
        Reblock the model to given block size. The routine preserves the origin of the block model so make sure
        the original and reblocking setups are compatible (the routine does not check this and total tonnages
        will be exact). Hint, check the percent field for strange values.

        :param blocksizes: list
        :param dominant_fields: list
        :param numeric_fields: list
        :param dilute: boolean
        :param dilution_density:
        :return:
        '''

        print ("Setting number of blocks for the reblocked model.....")

        # ratio between block sizes
        xf = float(blocksizes[0]) / float(self.setup['Block Size X'])
        yf = float(blocksizes[1]) / float(self.setup['Block Size Y'])
        zf = float(blocksizes[2]) / float(self.setup['Block Size Z'])

        # adjust IJK and assign to model

        numblocks = [np.round(self.setup['Number of Blocks X'] / xf, 0),
                     np.round(self.setup['Number of Blocks Y'] / yf, 0),
                     np.round(self.setup['Number of Blocks Z'] / zf, 0)]

        dftmp = self.data.copy()

        print ("Setting reblocked IJK....")

        origin = np.array([self.setup['Origin X'], self.setup['Origin Y'], self.setup['Origin Z']])

        dftmp['_rIJK'] = ijk.get_IJK_from_XYZ(xyz=dftmp[self.xyzfields].values,
                                              blocksize=blocksizes,
                                              numblocks=numblocks,
                                              origin=origin)

        print ("Setting temporary variables....")

        dftmp['_volume'] = self.tonnes / self.density
        dftmp['_tonnes'] = self.tonnes
        dftmp['_density'] = self.tonnes
        dftmp = dftmp.sort_values(['_rIJK']).reset_index(drop=True)

        print ("Reblocking....")

        rb_md = dftmp.groupby(['_rIJK'], as_index=False, sort=True)[['_tonnes', '_volume']].sum()
        dens_tmp = dftmp.groupby(['_rIJK'], as_index=False, sort=True)['_density'].sum()
        rb_md['_density'] = dens_tmp['_density'] / rb_md['_volume']
        dens_tmp = None

        if numeric_fields is not None:
            print ("Reblocking numeric fields....")
            for numf in numeric_fields:
                print("Pre-processing " + numf + "...")
                try:
                    dftmp[numf] = dftmp[numf].apply(lambda x: float(x))
                except:
                    print("Data contains non-numeric values, set these to zero")
                dftmp[numf] *= dftmp['_tonnes']
            num_tmp = dftmp.groupby(['_rIJK'], as_index=False, sort=True)[numeric_fields].sum()
            for numf in numeric_fields:
                rb_md[numf] = num_tmp[numf] / rb_md['_tonnes']
            num_tmp = None

        if dominant_fields is not None:
            print ("Reblocking dominant fields....")
            for domf in dominant_fields:
                print ("Reblocking " + str(domf) + "....")
                tmp_dom = dftmp.groupby(['_rIJK', domf], as_index=False, sort=True)['_tonnes'].sum()
                tmp_dom = tmp_dom.sort_values(by=['_rIJK', '_tonnes'], ascending=True).reset_index(drop=True)
                tmp_dom = tmp_dom.drop_duplicates(subset=['_rIJK'], keep='last').reset_index(drop=True)
                rb_md[domf] = tmp_dom[domf]
            tmp_dom = None

        print ("Calculating percent field...")

        rb_md['Percent'] = (rb_md['_volume'] / np.product(blocksizes))*100.

        print ("Adding coordinates to reblocked centroids...")

        xyz = ijk.get_XYZ_from_ijk(ijk=rb_md._rIJK.values, blocksize=blocksizes, origin=origin, numblocks=numblocks)
        rb_md[self.xyzfields] = pd.DataFrame(data=xyz.transpose(), columns=self.xyzfields)

        # all numeric fields will be diluted by a zero grade and will consider
        if dilute:
            print("Diluting numeric values")
            dens = rb_md._density*rb_md.Percent/100. + dilution_density*(1. - rb_md.Percent/100.)
            vol = blocksizes[0]*blocksizes[1]*blocksizes[2]*np.ones(len(dens))
            tonnes = vol*dens
            for numf in numeric_fields:
                print('Diluting ' + numf)
                met = rb_md.loc[:, '_tonnes'] * rb_md.loc[:, numf]
                rb_md.loc[:, numf] = met/tonnes
            rb_md.loc[:, '_tonnes'] = tonnes
            rb_md.loc[:, '_density'] = dens
            rb_md.loc[:, '_volume'] = vol
            rb_md.loc[:, 'Percent'] = 100.

        return rb_md;

    def downscale(self, block_sizes=[1, 1, 1]):

        raise NotImplementedError("downscale is not yet implemented")

    def label_connected_blocks(self, block_flag_f=None, full_face=False, min_touching_blocks=1, maxgap=0):
        '''

        Method to provide a unique label for "clumps" of connected blocks. Useful for the purposes of cleaning
        up block models for resource reporting and classification.

        :param block_flag_f: int
            Field with 1's anf 0's. The method looks for connectivity between the 1's
        :param full_face: boolean
            If full face = true, corner blocks will not be considered if maxgap=0
        :param min_touching_blocks: int
            Number of touching blocks to consider for labelling.
        :param maxgap: int
            Maximum space between blocks to consider a "clump" of blocks
        :return: int, float
            Returns 'con_label' (connectivity label 0-n) and 'con_index' (a measure of how connected blocks are) fields.
            df.con_label = -1 for blocks with no connectivity according to parameters.
            The 'con_index' is a connectivity index between 0 and 1, 0 is no connectivity while 1 is high connectivity.
        '''


        assert block_flag_f is not None, "Block flag to test for connnected objects required, " \
                                         "must be ones and zeros"
        assert self.data[block_flag_f].min() == 0 and self.data[block_flag_f].max() == 1, "Must be 1's and 0's"

        xyz = np.array(self.data[self.xyzfields][self.data[block_flag_f]==1])

        # reblock the xyz

        dbijks = ijk.get_IJK_from_XYZ(xyz=xyz,
                                      blocksize=[self.setup['Block Size X'],
                                                 self.setup['Block Size Y'],
                                                 self.setup['Block Size Z']],
                                      origin=[self.setup['Origin X'],
                                              self.setup['Origin Y'],
                                              self.setup['Origin Z']],
                                      numblocks=[self.setup['Number of Blocks X'],
                                                 self.setup['Number of Blocks Y'],
                                                 self.setup['Number of Blocks Z']])

        udbijks = np.unique(dbijks)


        idx = ijk.get_idx_from_IJK(udbijks, numblocks=[self.setup['Number of Blocks X'],
                                                       self.setup['Number of Blocks Y'],
                                                       self.setup['Number of Blocks Z']])

        X = np.column_stack((idx[:, 0], idx[:, 1], idx[:, 2]))

        if not full_face:
            eps = (maxgap + 1.)
        else:
            eps = (maxgap + 1.)*1.8

        labels = DBSCAN(eps=eps, min_samples=min_touching_blocks, metric='euclidean', n_jobs=-1).fit(X).labels_

        # make a connectivity index

        # corners
        eps = 1
        clabel = DBSCAN(eps=eps, min_samples=min_touching_blocks, metric='euclidean', n_jobs=-1).fit(X).labels_

        # rows:
        X = np.column_stack((idx[:, 0], idx[:, 1] * 1000, idx[:, 2] * 1000))
        xlabel = DBSCAN(eps=eps, min_samples=min_touching_blocks, metric='euclidean', n_jobs=-1).fit(X).labels_

        # columns:
        X = np.column_stack((idx[:, 0] * 1000, idx[:, 1], idx[:, 2] * 1000))
        ylabel = DBSCAN(eps=eps, min_samples=min_touching_blocks, metric='euclidean', n_jobs=-1).fit(X).labels_

        # elevation:
        X = np.column_stack((idx[:, 0] * 1000, idx[:, 1] * 1000, idx[:, 2]))
        zlabel = DBSCAN(eps=eps, min_samples=min_touching_blocks, metric='euclidean', n_jobs=-1).fit(X).labels_

        conn_matrix = np.array([clabel, xlabel, ylabel, zlabel])
        conn_matrix[conn_matrix >= 0] = 1.
        conn_matrix[conn_matrix < 0] = 0.
        # reduce the weight of the corners
        conn_matrix[0, :][conn_matrix[0, :] >= 0] = 0.5
        connectivity = np.average(conn_matrix, axis=0)

        dftemp = pd.DataFrame({'_ijk_': udbijks, 'con_label': labels, 'con_index': connectivity})
        self.data['_ijk_'] = self.ijk
        self.data = pd.merge(self.data, dftemp, on='_ijk_')



































