'''
Utilities for other modules
'''

import pandas as pd
import numpy as np
from statsmodels.stats.weightstats import DescrStatsW
from scipy import spatial

def cap_grades(data, cap):
    '''
    Cap grades to a selected value
    :param data:
    :param cap:
    :return:
    '''
    capped_data = np.array(data.copy())
    capped_data[capped_data > cap] = cap
    return capped_data;

def check_data(data):
    '''
    Check to see if the data is a ``pandas.DataFrame`` object or a csv. If object is a csv, csv is read to
    a ``pandas.DataFrame`` object.
    :param data: pandas.Dataframe or *.csv
    :return: pandas.DataFrame
    '''

    try:
        if isinstance(data, pd.DataFrame):
            df = data
        else:
            df = pd.read_csv(data)
        return df;
    except:
        raise "Data object is not a pandas.DataFrame"

def weighted_cdf(weights):
    '''
    Calculated cdf values for weighted data.
    :param weights:
    :return:
    '''

    assert np.sum(weights) != 0., "The sum of the weights must not equal zero"

    weights = np.array(weights)
    sumweights = np.sum(weights)
    offset = (weights[0] / sumweights) / 2.
    return np.cumsum(weights) / sumweights - offset;

def weighted_standard_deviation(data, weights):
    '''
    Calculate weighted standard deviation
    :param data:
    :param weights:
    :return:
    '''
    return weighted_variance(data, weights)**0.5;

def weighted_variance(data, weights):
    '''
    Calculate weighted variance.
    :param data:
    :param weights:
    :return:
    '''

    assert np.sum(weights) != 0., "The sum of the weights must not equal zero"

    weighted_stats = DescrStatsW(data, weights=weights, ddof=-1)
    return weighted_stats.var;

def weighted_stats(z, weights, gradef=None, dom=None):

    stats = pd.DataFrame(index=[0])

    if gradef is not None:
        stats['Variable'] = gradef
    if dom is not None:
        stats["Domain"] = dom
    stats['Count'] = len(z)
    stats['Sum of Weights'] = np.sum(weights)
    stats['Minimum'] = np.min(z)
    stats['Maximum'] = np.max(z)
    if np.sum(weights) > 0:
        stats['Average'] = np.average(z, weights=weights)
        stats['Stdev'] = weighted_standard_deviation(z, weights=weights)
        stats['Variance'] = stats['Stdev'] ** 2
        stats['CV'] = stats['Stdev'] / stats['Average']
    else:
        stats['Average'] = -99.
        stats['Stdev'] = -99.
        stats['Variance'] = -99.
        stats['CV'] = -99.

    return stats;

def nearest_neighbour_idx(xyz1, xyz2):
    dists = 0
    for i in range(3):
        dists += (xyz1[i]-xyz2[:, i])**2
    sort_idx = np.argsort(dists)
    return dists**0.5, np.arange(len(xyz2))[sort_idx];

def nearest_neighbour_idx2(xyz1, xyz2):

    dists = spatial.distance.cdist(xyz2, np.reshape(xyz1, (1, 3))).flatten()
    sort_idx = np.argsort(dists)

    return dists, np.arange(len(xyz2))[sort_idx];

def get_dist_nearest_dholes(holeid, holeids, dists, idx, nearest_neighbours):
    '''
    Given the distances and ranked indices to nearest samples calculates using nearest_neighbour_idx2,
    calculate the distance for nearest samples from k nearest drillholes
    :param holeid: str
        holeid to for sample of question
    :param holeids: [str]
        list of holeids for each sample
    :param dists: [float]
        distances from samples of question
    :param idx: [int]
        ranked indices for distance to sample of question
    :return: float
        average distance to nearest samples from k nearest ddh
    '''

    chk = 0
    cnt = 0
    avg_dist = 0
    # add the hole of question and add the it to a list of holes we have already looked at
    different_holeids = [holeid]

    while chk < nearest_neighbours:
        if holeids[idx[cnt]] not in different_holeids:
            different_holeids.append(holeids[idx[cnt]])
            avg_dist += dists[idx[cnt]]
            chk += 1
        cnt += 1

    return avg_dist / float(nearest_neighbours);






