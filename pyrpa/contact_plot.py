import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors
import matplotlib.pyplot as plt
import warnings
from matplotlib.backends.backend_pdf import PdfPages

warnings.simplefilter("ignore")


def knn(head, tail):
    nn = NearestNeighbors(n_neighbors=1).fit(tail)
    return nn.kneighbors(head);

class contact_plot(object):

    def __init__(self, sample, gradefield=None):

        self.data = sample.data
        self.gradef = gradefield
        self.rockf = sample.domainf
        self.xyzf = sample.xyzfields
        self.pairs = None

    def _process_pairs(self, x, y, isprimary=True):

        distances, indices = knn(x[self.xyzf], y[self.xyzf])
        if isprimary:
            distances *= -1
        df = x[[self.rockf, self.gradef]]
        df['Contact'] = str(self.rock1) + "-" + str(self.rock2)
        df['Distance'] = distances
        try:
            self.pairs = self.pairs.append(df).reset_index(drop=True)
        except:
            raise 'This is an internal proces'

    def fit(self, rock1, rock2):

        self.rock1 = rock1
        self.rock2 = rock2

        head = self.data[self.data[self.rockf]==rock1]
        tail = self.data[self.data[self.rockf]==rock2]
        self.pairs = pd.DataFrame()
        # head
        self._process_pairs(head, tail)
        # tail
        self._process_pairs(tail, head, isprimary=False)


    def plot(self, lagdist=5, numlags=10, figsize=(15,10)):

        self.lags = (np.arange(numlags*2) - numlags) * lagdist
        self.avg_grade = np.empty(numlags*2)
        self.num_pairs = np.empty(numlags*2)
        self.avg_dist = np.empty(numlags*2)

        for i, lag in enumerate(self.lags):
            idx = (self.pairs['Distance'] >= lag) & (self.pairs['Distance'] < lag + lagdist)
            if len(self.pairs[idx]) > 0:
                self.avg_grade[i] = np.average(self.pairs[self.gradef][idx])
            else:
                self.avg_grade[i] = 0.
            if np.sum(idx) > 0:
                self.num_pairs[i] = float(len(self.pairs[idx]))
            else:
                self.num_pairs[i] = 0
            self.avg_dist[i] = np.average(self.pairs['Distance'][idx])

        x = [0.00, 0.00]
        y = [0.00, np.max(self.avg_grade)]

        # standardise number of pairs
        self.num_pairs /= np.max(self.num_pairs)
        self.num_pairs *= np.max(self.avg_grade)
        plt.figure(figsize=figsize)
        plt.plot(x, y, '--k')
        plt.plot(self.avg_dist[self.avg_dist<0.], self.avg_grade[self.avg_dist<0.], 'o-r')
        plt.plot(self.avg_dist[self.avg_dist>=0.], self.avg_grade[self.avg_dist>=0.], 'o-k')
        plt.bar(self.lags + lagdist/2.0, self.num_pairs, width=lagdist, color='black', alpha=0.2)

        plt.xlabel('Distance to Contact (m)')
        plt.ylabel(self.gradef)
        plt.title(self.rockf + ": contact " + self.pairs['Contact'].iloc[0])
        plt.legend(("Contact", self.rock1, self.rock2, "Relative Number of Pairs"))

        return plt;















