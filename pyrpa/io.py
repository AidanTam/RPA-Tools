'''
Input output module
-------------------
Read and write proprietary file formats to and from pandas dataframes
Currently supports extended precision datamine files only with character limit of 8 characters for fieldnames

Functions included
-------------------

io.read_datamine()
io.pd_to_datamine()

Example usage:
--------------

df = io.read_datamine('some_dm_file.dm)
io.df_to_datamine(df)

'''

import pandas as pd
import struct
import numpy as np


def read_datamine(dmfile):

    '''
    Convert a datamine file to a pandas DataFrame

    :param dmfile: .dm file
         Extended precision Datamine file with max 8 character field names
    :return: pd.DataFrame
        Pandas DataFrame, implicit fields are stored in the dataframe
    '''

    assert dmfile[-3:] == ".dm", "Extension must be '*.dm'"

    dmfile_obj = open(dmfile, "rb")
    numfields, numpages, lastrecord = _get_dm_file_desc(open_file=dmfile_obj)
    fld_arr = _get_dm_field_desc(open_file=dmfile_obj, numfields=numfields)
    temp_column_names, datatypes = _get_data_types(fld_arr=fld_arr, numfields=numfields)

    maxlength = len(temp_column_names)

    # accumulate the page data in memory

    offset = 4096
    page = 1
    buffers = []

    while True:
        dmfile_obj.seek(offset)
        if page == numpages - 1:
            buf_length = int(maxlength * lastrecord * 8)
        else:
            buf_length = int(508 / maxlength) * maxlength * 8
        buf = dmfile_obj.read(buf_length)
        if not buf:
            break
        buffers.append(buf)
        offset += 4096
        page += 1

    dmfile_obj.close()

    # interpret the accumulated binary data as a structured array

    dd = np.frombuffer(b"".join(buffers), dtype=datatypes)
    df = pd.DataFrame(dd.tolist(), columns=temp_column_names)

    # concatenate alphanumeric fields

    fld_arr_expl = fld_arr[fld_arr[:, 2] != "0"]
    for fn, ft, wn in zip(fld_arr_expl[:, 0], fld_arr_expl[:, 1], fld_arr_expl[:, 3]):
        if ft == 'A':
            if wn == '1':
                df[fn] = df[fn + wn].str.decode('ascii').str.rstrip()
            else:
                df[fn] += df[fn + wn].str.decode('ascii').str.rstrip()

            df = df.drop(columns=[fn + wn])

    # add the implicit fields to the dataframe

    fld_arr_impl = fld_arr[fld_arr[:, 2] == "0"]
    if len(fld_arr_impl) > 0:
        for fn, dv in zip(fld_arr_impl[:, 0], fld_arr_impl[:, 4]):
            df[fn] = float(dv)

    # reorder the columns

    output_columns = []
    for fn, wn in zip(fld_arr[:, 0], fld_arr[:, 3]):
        if wn == '1':
            output_columns.append(fn)
    df = df[output_columns]

    return df;

def df_to_datamine(df, outname):

    '''
    Convert pandas DataFrame to an extended precision datamine file.

    :param df: pd.DataFrame
        Pandas DataFrame in regular flat file format
    :param outname: str
        Name of output file name, must end in ".dm"
    :return: .dm file
        Extended precision datamine file with maximum 8 character field names

    :notes:
        Reserved field names such as XMORIG, NZ and RADIUS will be saved as implicit fields
        while fields names such as SVOL and VAR_F will be saved as alphanumeric fields with a
        length of 8 characters.

    '''

    assert outname[-3:] == ".dm", "Extension must be '*.dm'"

    bin_out = open(outname, 'wb')
    fld_arr = _gen_dm_field_desc(df)

    # write the filename
    bin_out.seek(0, 0)
    bin_out.write(outname[:4].encode('ascii'))
    bin_out.seek(8, 0)
    bin_out.write(outname[4:].encode('ascii'))

    # some file description
    filedescription = "Double Precision datamine file generated in Python."
    fdesc_len = len(filedescription)
    bin_out.seek(32, 0)
    i = 0
    while fdesc_len + 4 > i * 4:
        bin_out.seek(8, 1)
        bin_out.write(filedescription[i * 4: i * 4 + 4].encode('ascii'))
        i += 1

    # write date (not sure how dates are serialized in datamine so just add a fake date)
    bin_out.seek(192, 0)
    bin_out.write(struct.pack('d', 456789))

    maxlength = len(fld_arr[fld_arr[:, 2] != '0'])
    # number of logical records per page
    nlrp = int(508 / maxlength)
    numpages = int(np.round(float(len(df)) / float(nlrp), 0) + 1)
    # number of last record on last page
    lastrecord = nlrp - ((numpages - 1) * nlrp - len(df))

    # now for the useful data
    bin_out.seek(200, 0)
    # number of fields, pages and last record
    bin_out.write(struct.pack('d', len(fld_arr)))
    bin_out.seek(208, 0)
    bin_out.write(struct.pack('d', float(numpages)))
    bin_out.seek(216, 0)
    bin_out.write(struct.pack('d', float(lastrecord)))

    # write the field data to the file

    for i in range(len(fld_arr)):
        # write the field name
        bin_out.seek(224 + 56 * i, 0)
        bin_out.write(fld_arr[i, 0][:4].encode('ascii'))
        bin_out.seek(224 + 56 * i + 8, 0)
        bin_out.write(fld_arr[i, 0][4:].encode('ascii'))
        # Field type
        bin_out.seek(224 + 56 * i + 16, 0)
        bin_out.write(fld_arr[i, 1].encode('ascii'))
        # Stored Word Number
        bin_out.seek(224 + 56 * i + 24, 0)
        bin_out.write(struct.pack('d', float(fld_arr[i, 2])))
        # Word Number
        bin_out.seek(224 + 56 * i + 32, 0)
        bin_out.write(struct.pack('d', float(fld_arr[i, 3])))
        # Default value
        bin_out.seek(224 + 56 * i + 48, 0)
        if fld_arr[i, 1] == 'A':
            bin_out.write(fld_arr[i, 4].encode('ascii'))
        else:
            bin_out.write(struct.pack('d', float(fld_arr[i, 4])))

    # slice the alphanumeric fields into length/4 columns and create a temporary column name list for output
    temp_col_names = []
    for i in range(len(fld_arr)):
        if fld_arr[i, 1] == 'A':
            concat_name = fld_arr[i, 0] + fld_arr[i, 3]
            temp_col_names.append(concat_name)
            df[concat_name] = df[fld_arr[i, 0]].str.slice((int(fld_arr[i, 3]) - 1) * 4,
                                                                        (int(fld_arr[i, 3]) - 1) * 4 + 4)
        else:
            temp_col_names.append(fld_arr[i, 0])

    df = df[temp_col_names]

    # convert to numpy array for efficiency

    np_dat = np.array(df)

    # write the data to the file
    bin_out.seek(4096)
    cnt = 0
    page = 1
    for i in range(len(np_dat)):
        for j in range(len(fld_arr)):
            if fld_arr[j, 2] != '0':
                if fld_arr[j, 1] == 'A':
                    bytes_out = np_dat[i, j].encode('ascii')
                    bin_out.write(bytes_out)
                    bin_out.seek(8 - len(bytes_out), 1)
                else:
                    bin_out.write(struct.pack('d', float(np_dat[i, j])))
        if cnt == nlrp - 1:
            page += 1
            cnt = 0
            bin_out.seek(page * 4096)
        else:
            cnt += 1
    bin_out.close()

def _gen_dm_field_desc(df):

    CHAR8_FIELDS = ['VALUE_IN', 'VALUE_OU', 'NUMSAM_F', 'SVOL_F', 'VAR_F', 'MINDIS_F']
    IMPLICIT_FIELDS = ['XMORIG', 'YMORIG', 'ZMORIG',
                       'NX', 'NY', 'NZ', 'RADIUS',
                       'X0', 'Y0', 'Z0',
                       'ANGLE1', 'ANGLE2', 'ANGLE3',
                       'ROTAXIS1', 'ROTAXIS2', 'ROTAXIS3']

    INT_FIELDS = ['NX', 'NY', 'NZ', 'RADIUS', 'ROTAXIS1', 'ROTAXIS2', 'ROTAXIS3']

    field_lengths = [4, 8, 24, 48, 64, 128, 256]
    fld_arr = []
    sw_c = 0
    for col in df.columns:
        if df[col].dtype == 'float' or df[col].dtype == 'int':
            if col in IMPLICIT_FIELDS:
                sw = '0'
                if col in INT_FIELDS:
                    dfv = int(df[col].iloc[0])
                else:
                    dfv = float(df[col].iloc[0])
            else:
                sw_c += 1
                sw = str(sw_c)
                dfv = "-1.0e30"
            fld_arr.append([col, 'N', sw, '1', dfv])
        else:
            if col in CHAR8_FIELDS:
                fl = 8
            else:
                pd_fl = df[col].str.len().max()
                # np.searchsorted finds location in array
                fl = field_lengths[np.searchsorted(field_lengths, pd_fl, 'right')]
            for i in range(int(fl / 4)):
                sw_c += 1
                fld_arr.append([col, 'A', str(sw_c), str(i + 1), ""])

    return np.array(fld_arr);

def _get_dm_file_desc(open_file):

    # the file description is the first 224 bytes of the file
    fdesc = open_file.read(224)

    # # the following 3 variables are not really used for anything
    # filename = fdesc[0:4] + fdesc[8:12]
    # filedescription = ""
    # for i in range(2, 19):
    #     filedescription += fdesc[i * 8:i * 8 + 4]
    # filedescription = np.char.strip(filedescription)
    # date = int(struct.unpack('d', fdesc[192:200])[0])

    # now for the useful data
    numfields = int(struct.unpack('d', fdesc[200:208])[0])
    numpages = int(struct.unpack('d', fdesc[208:216])[0])
    lastrecord = int(struct.unpack('d', fdesc[216:224])[0])

    return numfields, numpages, lastrecord;

def _get_default(dat, i):

    if dat[i * 56 + 16:i * 56 + 20].decode('ascii') != 'A   ':
        default = struct.unpack('d', dat[i * 56 + 48:i * 56 + 56])[0]
    else:
        default = dat[i * 56 + 48:i * 56 + 56].decode('ascii')
    return default;

def _get_dm_field_desc(open_file, numfields):

    fld_arr = []

    # field descriptions start at byte 224 and end at 224 + 3839
    open_file.seek(224)
    flddesc = open_file.read(3839)

    # loop through the fields

    for i in range(numfields):
        fld_arr.append([flddesc[i * 56:i * 56 + 4].decode('ascii') + flddesc[i * 56 + 8:i * 56 + 8 + 4].decode('ascii'),
                        flddesc[i * 56 + 16:i * 56 + 20],
                        int(struct.unpack('d', flddesc[i * 56 + 24:i * 56 + 32])[0]),
                        int(struct.unpack('d', flddesc[i * 56 + 32:i * 56 + 40])[0]),
                        _get_default(flddesc, i)])

    # strip the whitespace

    fld_arr = np.array(fld_arr)

    for i in range(numfields):
        for j in range(5):
            fld_arr[i, j] = fld_arr[i, j].rstrip()

    return fld_arr;

def _get_data_types(fld_arr, numfields):

    temp_column_names = []
    datatypes = []

    for i in range(numfields):
        # skip implicit fields
        if fld_arr[i, 2] != '0':
            # relabel alphanumeric fields
            if fld_arr[i, 1] == 'A':
                temp_column_names.append(fld_arr[i, 0] + fld_arr[i, 3])
                datatypes.append((temp_column_names[-1] + fld_arr[i, 3], 'S8'))
            else:
                temp_column_names.append(fld_arr[i, 0])
                datatypes.append((temp_column_names[-1], 'f8'))

    datatypes = np.dtype(datatypes)

    return temp_column_names, datatypes;

def get_dm_field_desc(dmfile):

    open_file = open(dmfile, "rb")
    numfields, numpages, lastrecord = _get_dm_file_desc(open_file=open_file)
    fld_arr = _get_dm_field_desc(open_file=open_file, numfields=numfields)
    open_file.close()

    return fld_arr;

