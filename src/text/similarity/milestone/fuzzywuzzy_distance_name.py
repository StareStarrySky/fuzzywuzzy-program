#!/usr/bin/env python3
import csv

import pandas as pd
from fuzzywuzzy import process


# 计算每对文本之间的相似度
def calculate_similarity(row_name):
    return process.extractBests(row_name['MATERIEL_NAME'], wl['MATERIEL_NAME'], limit=1000, score_cutoff=60)
    # return process.extractBests(row_name['MATERIEL_NAME'], wl.loc[row_name.name:(wl.shape[0] - 1), 'MATERIEL_NAME'], limit=1000, score_cutoff=60)


# 读取CSV文件
wl = pd.read_csv('86115-3.csv', low_memory=False)

wl.sort_values(by=['MATERIEL_NAME', 'SPEC_MODEL_NUMBER'], ascending=[True, True], inplace=True)

# 给DataFrame添加一个新列来存储相似度得分
wl['similarity'] = wl.apply(calculate_similarity, axis=1)

# [('三防篷布', 100, 0), ('三防篷布', 100, 1), ('篷布', 90, 4)]

moved_row = []
moved_sim = []
wl_new = pd.DataFrame(columns=wl.columns)
for _, row in wl.iterrows():
    temp_size = 0
    wl_temp = pd.DataFrame(columns=wl.columns)
    simi = row['similarity']
    # 如果当前行，不在已动标记里就添加进新的
    if len(simi) > 0 and simi[0][2] not in moved_row:
        moved_row.append(simi[0][2])
        conceited = False
        for sim in simi:
            if sim[2] not in moved_sim:
                curr_name = row['MATERIEL_NAME']
                sim_useful = wl.loc[sim[2]]['similarity']
                sim_name = [tup[0] for tup in sim_useful if isinstance(tup[0], str)]  # 这里需不需要根据分数阀值来过滤
                # 相互在对方里
                si = -1
                try:
                    si = sim_name.index(curr_name)
                except ValueError:
                    pass
                if sim_useful[si][2] >= 60:   # 分值
                    moved_sim.append(sim[2])
                    wl_temp = pd.concat([wl_temp, wl.loc[sim[2]].to_frame().T], ignore_index=True)
                    conceited = True
                    temp_size += 1
        if conceited and temp_size > 1:
            wl_new = pd.concat([wl_new, wl_temp], ignore_index=True)
            empty_row = pd.DataFrame(index=range(wl_new.index[-1] + 1, wl_new.index[-1] + 2))
            wl_new = pd.concat([wl_new, empty_row], ignore_index=True)

wl_new = wl_new.drop('similarity', axis=1)

# 输出排序后的CSV文件
wl_new.to_csv('res-3.csv', index=False, quoting=csv.QUOTE_ALL, encoding='utf-8-sig')
