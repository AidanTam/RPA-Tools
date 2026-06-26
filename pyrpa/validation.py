'''
Validation module
'''
import pandas as pd
import pyrpa.plotting
import matplotlib.pyplot as plt
import numpy as np

def mean_comparison(blockmodel, samples, blk_benchmarkf=None, smp_benchmarkf=None, tolerance=0.1):
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

    blk_avgs = blockmodel.stats.pivot(index="Domain", columns="Variable", values="Average")
    for col in blk_avgs.columns:
        blk_avgs['blk - ' + col] = blk_avgs[col]
        blk_avgs = blk_avgs.drop([col], 1)
    smp_avgs = samples.stats.pivot(index="Domain", columns="Variable", values="Average")
    for col in smp_avgs.columns:
        smp_avgs['smp - ' + col] = smp_avgs[col]
        smp_avgs = smp_avgs.drop([col], 1)

    avgs = smp_avgs
    avgs[blk_avgs.columns]=blk_avgs
    avgs.reset_index(inplace=True)

    if smp_benchmarkf is not None:
        sortcol = 'smp - ' + smp_benchmarkf
    elif blk_benchmarkf is not None:
        sortcol = 'blk - ' + blk_benchmarkf
    else:
        sortcol = avgs.columns[1]

    avgs = avgs.sort_values(by=sortcol).reset_index(drop=True)
    avgs = avgs.dropna()

    plt.figure(figsize=(15,10))

    for col in avgs.columns:
        if col != "Domain":
            plt.plot(avgs[col], 'o-')

    plt.plot(avgs[sortcol]*(1. + tolerance), '--r')
    plt.plot(avgs[sortcol] * (1. - tolerance), '--r')

    legend = [x for x in avgs.columns[1:]]
    legend.append(sortcol + ' +' + str(int(tolerance * 100.)) + '%')
    legend.append(sortcol + ' -' + str(int(tolerance * 100.)) + '%')
    plt.legend(legend, loc=0)
    plt.xticks(np.arange(len(avgs)) + 1)
    plt.xlabel('Domain')
    plt.ylabel('Average')

    return avgs;

class swathplot(object):

    def __init__(self, blocks, samples):

        self.sample = samples
        self.blocks = blocks

    def fit(self, direction='X', spacing=50., rotation=0.0):

        if direction  == 'X':
            dir = 0
        elif direction == 'Y':
            dir = 1
        else:
            dir = 2

        smp = self.samples.data[self.xyzfields[dir], self.samples.gradefields]
        smp['SWATH'] = np.round(smp[0, :] / spacing, 0) * spacing

        blk = self.blocks.data[self.xyzfields[dir], self.blocks.gradefields, self.blocks.tonnes]
        blk['SWATH'] = np.round(blk[0, :] / spacing, 0) * spacing

        smp = smp.groupby(by='SWATH')[self.samples.gradefields].mean().reset_index()
        smp_count = smp.groupby(by='SWATH')[self.samples.gradefields[0]].count().reset_index()
        smp['SAMPLE COUNT'] = smp_count[self.samples.data.gradefields[0]]

        for gf in self.sample.gradefields:
            smp = smp.rename({gf: gf + "_smp"})

        for gf in self.blocks.gradefields:
            blk[gf] *= self.blocks.tonnes

        blk = blk.groupby(by='SWATH')[self.blocks.gradefields].sum().reset_index()






