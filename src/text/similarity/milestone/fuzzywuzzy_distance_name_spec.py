#!/usr/bin/env python3
import csv

import pandas as pd
from fuzzywuzzy import process


# 计算每对文本之间的相似度
def calculate_wl_name_similarity(row_name, wl_csv):
    return process.extractBests(row_name['MATERIEL_NAME'], wl_csv['MATERIEL_NAME'], limit=1000, score_cutoff=60)
    # return process.extractBests(row_name['MATERIEL_NAME'],
    #                             wl_csv.loc[row_name.name:(wl_csv.shape[0] - 1), 'MATERIEL_NAME'],
    #                             limit=1000, score_cutoff=60)


# 计算每对文本之间的相似度
def calculate_spec_similarity(row_name, spec_csv):
    return process.extractBests(str(row_name['SPEC_MODEL_NUMBER']),
                                str(spec_csv['SPEC_MODEL_NUMBER']), limit=100, score_cutoff=95)


def group_by(csv_group, column, column_similarity):
    # [('三防篷布', 100, 0), ('三防篷布', 100, 1), ('篷布', 90, 4)]
    moved_row = []
    moved_sim = []
    csv_new = pd.DataFrame(columns=csv_group.columns)
    for _, row in csv_group.iterrows():
        temp_size = 0
        csv_temp = pd.DataFrame(columns=csv_group.columns)
        simi = row[column_similarity]  # 'wl_name_similarity'
        # 如果当前行，不在已动标记里就添加进新的
        if len(simi) > 0 and simi[0][2] not in moved_row:
            moved_row.append(simi[0][2])
            conceited = False
            for sim in simi:
                if sim[2] not in moved_sim:
                    curr_name = row[column]  # 'MATERIEL_NAME'
                    sim_useful = csv_group.loc[sim[2]][column_similarity]  # 'wl_name_similarity'
                    sim_name = [tup[0] for tup in sim_useful if isinstance(tup[0], str)]  # 这里需不需要根据分数阀值来过滤
                    # 相互在对方里
                    si = -1
                    try:
                        si = sim_name.index(curr_name)
                    except ValueError:
                        pass
                    if si > -1 and sim_useful[si][1] >= 0:  # 分值
                        moved_sim.append(sim[2])
                        csv_temp = pd.concat([csv_temp, csv_group.loc[sim[2]].to_frame().T], ignore_index=True)
                        conceited = True
                        temp_size += 1
            if conceited and temp_size > 1:
                if 'spec_similarity' not in csv_new.columns:
                    csv_temp['spec_similarity'] = csv_temp.apply(
                        lambda spe_row: calculate_spec_similarity(spe_row, csv_temp), axis=1)
                    csv_temp = group_by(csv_temp, 'SPEC_MODEL_NUMBER', 'spec_similarity')
                if csv_temp.shape[0] > 0:
                    # csv_temp.sort_values(by=['MATERIEL_NAME', 'SPEC_MODEL_NUMBER'], ascending=[True, True], inplace=True)
                    csv_new = pd.concat([csv_new, csv_temp], ignore_index=True)
                    if column == 'MATERIEL_NAME':
                        empty_row = pd.DataFrame(index=range(csv_new.index[-1] + 1, csv_new.index[-1] + 2))
                        csv_new = pd.concat([csv_new, empty_row], ignore_index=True)

    csv_new = csv_new.drop(column_similarity, axis=1)
    return csv_new


# 读取CSV文件
wl = pd.read_csv('500.csv', low_memory=False)

wl['MATERIEL_NAME'] = wl['MATERIEL_NAME'].astype(str)
wl['SPEC_MODEL_NUMBER'] = wl['SPEC_MODEL_NUMBER'].astype(str)

wl.sort_values(by=['MATERIEL_NAME', 'SPEC_MODEL_NUMBER'], ascending=[True, True], inplace=True)

# 给DataFrame添加一个新列来存储相似度得分
wl['wl_name_similarity'] = wl.apply(lambda name_row: calculate_wl_name_similarity(name_row, wl), axis=1)

wl_new = group_by(wl, 'MATERIEL_NAME', 'wl_name_similarity')

# 输出排序后的CSV文件
wl_new.to_csv('res.csv', index=False, quoting=csv.QUOTE_ALL, encoding='utf-8-sig')
