import pandas as pd
import numpy as np


def get_split_string(string, lookup):

    return string.split(lookup, 1)


class read_bef(object):

    def __init__(self, filename=None):

        self.filename = filename

        file = open(filename, 'r')

        file_list = []

        for line in file:

            file_list.append(line.strip())

        file_list = np.array(file_list)

        start = np.char.startswith(file_list,prefix='BEGIN$DEF ')
        end = np.char.startswith(file_list,prefix='END$DEF ')

        start_idx = []
        end_idx = []

        for i in range(len(start)):

            if start[i] == True:
                start_idx.append(i)
            if end[i] == True:
                end_idx.append(i)

        loop_range = np.array(end_idx) - np.array(start_idx)

        frames = []
        for i in range(len(start_idx)):

            dftemp = pd.DataFrame(index=[0])

            for j in range(loop_range[i]):

                if j == 0:
                    split_string = get_split_string(file_list[start_idx[i] + j], 'BEGIN$DEF ')
                    dftemp['Par_ID'] = split_string[1]
                else:
                    split_string = get_split_string(file_list[start_idx[i] + j], '=')
                    dftemp[split_string[0]] = split_string[1]

            frames.append(dftemp)

        self.df = pd.concat(frames) if frames else pd.DataFrame()

    def list_parameter_IDs(self):

        return self.df['Par_ID']

    def filter_df_parameter(self, contains_parameter=None):

        filtered_df = self.df.dropna(subset=[contains_parameter])

        return filtered_df.dropna(axis=1);

    def filter_df_Par_ID(self, parameter_ids=None):

        filtered_df = self.df.copy()

        filtered_df['ISIN'] = filtered_df['Par_ID'].isin(parameter_ids)

        filtered_df = filtered_df[filtered_df['ISIN'] == True]

        filtered_df = filtered_df.drop(columns=['ISIN'])

        return filtered_df.dropna(axis=1);









