import pandas as pd
import pickle

def normalize_title(t):
    """
    标题标准化：小写 + 去首尾空格
    """
    if not isinstance(t, str):
        return ""
    return t.strip().lower()


def load_final_list(pkl_path):
    """
    读取你的 paper.pkl
    """
    with open(pkl_path, "rb") as f:
        papers = pickle.load(f)
    return papers


def load_zotero_titles(csv_path):
    """
    读取 Zotero CSV 并提取标题
    """
    df = pd.read_csv(csv_path)

    if "Title" not in df.columns:
        raise ValueError("CSV 中没有 Title 列，请确认 Zotero 导出的格式")

    titles = set()

    for t in df["Title"].dropna():
        titles.add(normalize_title(t))

    return titles


def find_missing_papers(final_list, zotero_titles):
    """
    找出 Zotero 没有的论文，返回格式与 final_list 一致
    """
    missing = []

    for p in final_list:
        title = normalize_title(p.get("title", ""))

        if title not in zotero_titles:
            # 直接加入整个 paper dict
            missing.append(p)

    return missing


def save_csv(papers, path):
    """
    保存 CSV，保持 papers 原始字段
    """
    if not papers:
        print("⚠️ 没有论文可保存，跳过写入。")
        return

    # 自动获取所有字段
    all_keys = set()
    for p in papers:
        all_keys.update(p.keys())
    all_keys = list(all_keys)

    df = pd.DataFrame(papers, columns=all_keys)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"✅ 已保存 {len(papers)} 篇论文到 {path}")


if __name__ == "__main__":

    # 你的文件路径
    paper_pkl = "./log/paper.pkl"
    zotero_csv = "./我的文库.csv"

    final_list = load_final_list(paper_pkl)

    zotero_titles = load_zotero_titles(zotero_csv)
    missing_papers = find_missing_papers(final_list, zotero_titles)
    print("Zotero 中没有的论文数量:", len(missing_papers))

    for p in missing_papers:
        print(p["title"], "|", p["year"])

    save_csv(missing_papers, "../missing_papers.csv")

    print("\n已生成文件: missing_papers.csv")