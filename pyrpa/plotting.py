'''
RPA plotting routines and standards
'''
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.ticker import ScalarFormatter
import numpy as np
import scipy.stats as st

RPA_COLOR_CYCLE = ["#3C6136", "#2B4670", "#5B4B6C", "#A04344", "#7A7CA0"]

def gt_curve(df, cogf='Cutoff', tonnesf="Tonnes", gradefields=None, domain_value=None, domain_field=None):

    markersize=10
    linewidth=3

    assert gradefields is not None, "Grade fields required"
    fig, ax1 = plt.subplots(figsize=(10,10))
    fig.patch.set_facecolor(color="white")
    ax1.plot(df[cogf], df[tonnesf], 'o-',
             color=RPA_COLOR_CYCLE[0], markersize=markersize, linewidth=linewidth)
    ax1.set_xlabel(cogf)
    ax1.set_ylabel(tonnesf)
    scientific_to_normal_ticks(ax1)
    comma_sep(ax1)
    ax1.legend(tonnesf, loc=1)

    ax2 = ax1.twinx()

    for i, gf in enumerate(gradefields):
        ax2.plot(df[cogf], df[gf], 'o-',
                 color=RPA_COLOR_CYCLE[i+1], markersize=markersize, linewidth=linewidth)
    ax2.set_ylabel('Average Grade')
    comma_sep(ax2)
    ax2.legend(gradefields)
    set_plot_font()

    if domain_value is not None:
        plt.title("Grade Tonnage Curve for " + domain_field + "=" + str(domain_value))
    else:
        plt.title("Global Grade Tonnage Curve")




def cdf_plot(grades, frequencies, xlabel, figsize=(10,10), caps=None, position='left'):
    '''
    :param grades:
    :param frequencies:
    :param xlabel:
    :param figsize:
    :param show_caps:
    :return:
    '''

    # main plotting block
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(color="white")
    plt.plot(grades, frequencies, '-ok', markersize=3, linestyle = 'None', color='#004587')
    plt.xscale('log')
    scientific_to_normal_ticks(ax)
    comma_sep(ax)
    ticks, labels = gaussian_frequencies()
    plt.yticks(ticks, labels)
    plt.xlabel(xlabel)
    plt.ylim((-5, 5))
    plt.ylabel('Percentile (%)')
    ax.yaxis.grid(True, which='major', linestyle='--', color='lightgray')
    ax.xaxis.grid(True, which='major', linestyle='--', color='lightgray')
    ax.xaxis.grid(True, which='minor', linestyle='--', color='lightgray')


    if caps is not None:

        y = circle_points(x=caps, xp=grades, fp=frequencies, return_y=True)
        radial_annotation(x=caps, y=y, position=position)
        

    # final text formatting
    set_plot_font()

    return fig;

def cdf_plot_compare(x1, x2, frequencies1, frequencies2, xlabel, figsize=(10, 10), legend=['Original Grade', 'Comparison']):
        '''
        :param grades:
        :param frequencies:
        :param xlabel:
        :param figsize:
        :param show_caps:
        :return:
        '''

        # main plotting block

        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor(color="white")
        plt.plot(x1, frequencies1, '-ok', markersize=3)
        plt.plot(x2, frequencies2, '-or', markersize=3)
        plt.xscale('log')
        ticks, labels = gaussian_frequencies()
        plt.yticks(ticks, labels)
        plt.xlabel(xlabel)
        plt.ylim((-5, 5))
        plt.ylabel('Percentile (%)')
        scientific_to_normal_ticks(ax)
        comma_sep(ax)
        ax.yaxis.grid(True, which='major', linestyle='-', color='k')
        ax.xaxis.grid(True, which='major', linestyle='-', color='k')
        ax.xaxis.grid(True, which='minor', linestyle='-', color='k')
        plt.legend(legend, loc=2)

        # final text formatting
        set_plot_font()




        return fig;


def radial_annotation(x, y, position='left'):
    '''
    annotate points using radial positioning either left or right of monotonic x, y chart
    :param x:
    :param y:
    :param position:
    :return:
    '''

    ang_inc = 90. / float(int(len(x)))

    for i, (xx, yy) in enumerate(zip(x, y)):
        ang = np.radians((180. + ang_inc) - float(i) * ang_inc)
        if position != 'left':
            ang += (3.14/2.)
        xp = 70. * np.cos(ang)
        yp = 70. * np.sin(ang)

        plt.annotate(x[i],
                     xy=(xx, yy), xytext=(xp, yp),
                     textcoords='offset points', ha='right', va='bottom',
                     bbox=dict(boxstyle='square,pad=0.3', fc='white'),
                     arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'), fontsize=12)

def circle_points(x, xp, fp, return_y=False):
    '''
    Draw circles around points x given monotonic data xp and fp
    :param x:
    :param xp:
    :param fp:
    :return:
    '''
    y = np.interp(x=x, xp=xp, fp=fp)
    plt.plot(x, y,
             'o',
             markeredgecolor='red',
             markeredgewidth=1.5,
             markerfacecolor='none',
             markersize=15)

    if return_y:
        return y;

def comma_sep(ax):
    xticks = []
    for tick in ax.get_xticks():
        if float(tick) < 10:
            xticks.append(round(tick, 3))
        else:
            xticks.append(format(tick, ',.0f'))
    ax.set_xticklabels(xticks)

def gaussian_frequencies():
    labels = ([0.01,0.05,0.1,0.2,0.5,1,2,5,10,20,30,40,50,60,70,80,90,95,98,99.5,99.8,99.95,99.99])
    cdf = np.array(labels) / 100
    ticks = st.norm.ppf(cdf)
    return ticks,labels;

def log_scale_bins(minx, maxx, num_bins):
    bins = 10 ** np.linspace(np.log10(minx), np.log10(maxx), num_bins)
    return bins;

def scientific_to_normal_ticks(ax):
    for axis in [ax.xaxis]:
        formatter = ScalarFormatter()
        formatter.set_scientific(False)
        axis.set_major_formatter(formatter)
    for axis in [ax.yaxis]:
        formatter = ScalarFormatter()
        formatter.set_scientific(False)
        axis.set_major_formatter(formatter)

def set_plot_font():
    SMALL_SIZE = 8
    MEDIUM_SIZE = 10
    BIGGER_SIZE = 15

    plt.rc('font', size=BIGGER_SIZE)  # controls default text sizes
    plt.rc('axes', titlesize=BIGGER_SIZE)  # fontsize of the axes title
    plt.rc('axes', labelsize=BIGGER_SIZE)  # fontsize of the x and y labels
    plt.rc('xtick', labelsize=BIGGER_SIZE)  # fontsize of the tick labels
    plt.rc('ytick', labelsize=BIGGER_SIZE)  # fontsize of the tick labels
    plt.rc('legend', fontsize=BIGGER_SIZE)  # legend fontsize
    plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title


