import pickle
import os
import datetime
import re

def save_pickle(data, file_name, flag_show=True):
    # 将data保存成pkl文件
    f = open(file_name, 'wb')
    pickle.dump(data, f)
    f.close()
    if flag_show:
        print(file_name + ' save successfully')

def load_pickle(file_name, flag_show=True):
    if os.path.exists(file_name):
        # pkl文件读取
        f = open(file_name, 'rb+')
        data = pickle.load(f)
        f.close()
        if flag_show:
            print(file_name + ' load successfully')
    else:
        data = None

    return data

def load_str_pkl(file_name, flag_show=True):
    text = load_pickle(file_name, flag_show)
    text = '' if text is None else text
    return text

def save_txt(history_dict, filename=None, filepath='./'):
    if filename is None:
        filename = filepath + f"dialog_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    with open(filename, "w", encoding="utf-8") as f:
        for h in history_dict:
            f.write(f"[第{h['round']}轮] {h['speaker']}：{h['content']}\n")

    print(f"对话已保存为 {filename}")

class history_recorder():
    def __init__(self):
        self.history = []

    def update(self, round, speaker, content):
        self.history.append({'round': round, 'speaker': speaker, 'content': content})

    def str_history(self):
        """格式化输出历史记录"""
        history = ""
        for h in self.history:
            prefix = f"[第{h['round']}轮] {h['speaker']}："
            history += prefix + h['content'] + "\n"
        return history

def sys_prompt(context):
    return '【系统：' + context + '】'

def clean_think(s):
    cleaned = re.sub(r"<think>.*?</think>", "", s, flags=re.DOTALL)
    return cleaned