"""
1- return dictionary which has all of index and string, length of lines, the indexes of starting with 'minor'
2- concatenate each line between the range number
"""

# file_cacti = 'cacti.txt'
# keyword = 'minor'


def _set_line_number(multiple_line, keyword):
    number_line_dict = {}
    m = []
    # with open(file_cacti, 'r', encoding='utf-8') as f:
    multiple_lines = multiple_line.split('\n')
    for i, d in enumerate(multiple_lines):
        number_line_dict.setdefault(i, d.strip())
        if d.lower().startswith(keyword):
            m.append(i)
    return number_line_dict, len(number_line_dict), m


def _get_new_list(multiple_line, keyword):
    origin_dict, len_origin, minor_index_list = _set_line_number(multiple_line, keyword)

    new_list = []
    for index, minor_index in enumerate(minor_index_list):

        minor_next = index != len(minor_index_list) - 1 and minor_index_list[index + 1] or len_origin

        new_each_list = []
        # for i in range(minor_index, minor_next):
        for i, d in enumerate(range(minor_index, minor_next)):
            row = origin_dict.get(d, '')
            if i == 0:
                new_each_list.append(row)
            else:
                if row.lower().startswith(keyword):
                    new_each_list.append(row)
        new_list.append(' '.join(new_each_list))

    return new_list


def merge_lines(multiple_line, keyword):
    return _get_new_list(multiple_line, keyword)
