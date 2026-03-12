import requests
import time
import random
import pandas as pd
from .agent_paper_search import AgentCompare, AgentScan, AgentSelect
from .find_new_paper import find_missing_papers, save_csv


def load_zotero_titles(csv_path):
    try:
        df = pd.read_csv(csv_path)
        titles = set(df["Title"].dropna().str.lower())
        return titles
    except Exception as e:
        print("Zotero CSV 读取失败:", e)
        return set()

def scan_paper(text, topic='dynamics learning', require='', flag_show_resp=False, api_key=None):
    """粗筛论文，返回索引列表"""
    agn = AgentScan(api_key=api_key)
    return agn.identify(paper=text, topic=topic, require=require, flag_show_resp=flag_show_resp)

def idetify_paper(text, topic='dynamics learning', require='', flag_show_resp=False, api_key=None):
    agn = AgentCompare(api_key=api_key)
    return agn.identify(paper=text, topic=topic, require=require, flag_show_resp=flag_show_resp)

def select_paper(text, topic='dynamics learning', require='', flag_show_resp=False, api_key=None):
    """选择最相关的论文"""
    agn = AgentSelect(api_key=api_key)
    return agn.identify(paper=text, topic=topic, require=require, flag_show_resp=flag_show_resp)

def resolve_to_paper_id(paper_id):
    """
    将 DOI / arXiv / CorpusId / paperId 统一解析成 paperId
    """
    url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}"
    params = {"fields": "paperId"}

    r = requests.get(url, params=params)
    if r.status_code != 200:
        print(f"⚠️ 无法解析论文ID {paper_id}, 状态码: {r.status_code}")
        return None

    data = r.json()
    return data.get("paperId")

def fetch_paper_network(paper_id, scan_func, filter_func, api_key=None, flag_precise_screen=True, min_year=None, flag_filter_zotero=False, zotero_csv="我的文库.csv"):

    zotero_titles = set()
    if flag_filter_zotero:
        zotero_titles = load_zotero_titles(zotero_csv)
        print(f"已加载 Zotero 文献: {len(zotero_titles)} 篇")

    base_url = "https://api.semanticscholar.org/graph/v1"
    headers = {"x-api-key": api_key} if api_key else {}

    fields = "title,abstract,citationCount,year,paperId"
    results = []
    connection_types = ["references", "citations"]

    time.sleep(5)
    for conn in connection_types:
        endpoint = f"{base_url}/paper/{paper_id}/{conn}"
        params = {"fields": fields, "limit": 100}

        try:
            print(f"--- 正在请求 {conn} (Paper: {paper_id}) ---")
            response = requests.get(endpoint, params=params, headers=headers)

            if response.status_code == 429:
                print("⚠️ 触发频率限制，跳过当前节点。")
                break
            if response.status_code != 200:
                continue

            time_start = time.time()
            data = response.json().get("data", [])

            papers = []
            all_info = []

            # ===== 收集标题 & 年份筛选 =====
            for item in data:
                paper_info = item.get('citedPaper') or item.get('citingPaper')
                if not paper_info:
                    continue

                year = paper_info.get("year")
                if min_year and (not year or year < min_year):
                    continue  # 跳过年份小于 min_year 的论文

                title = paper_info.get("title", "").lower()

                # ===== Zotero 去重 =====
                if flag_filter_zotero and title in zotero_titles:
                    print(f"  [已存在于提供的文库] {title}")
                    continue

                abstract = paper_info.get("abstract")
                if not abstract:
                    continue

                papers.append(paper_info)
                all_info.append(abstract)

            if not papers:
                continue

            # ===== 分块标题粗筛 =====
            idx_list = []
            chunk_size = 10
            total_chunks = (len(all_info) + chunk_size - 1) // chunk_size  # 计算总块数

            for chunk_num, start in enumerate(range(0, len(all_info), chunk_size), 1):
                chunk_titles = all_info[start:start + chunk_size]

                title_text = ""
                for i, t in enumerate(chunk_titles):
                    title_text += f"{i + 1}. {t}\n"

                chunk_idx = scan_func(title_text)
                chunk_idx = [i - 1 for i in chunk_idx]  # 转换为 0-based index

                # 转换为全局 index
                idx_list.extend([start + i for i in chunk_idx])

                print(f"粗筛进度: 已处理 {chunk_num}/{total_chunks}，当前通过粗筛论文序号: {idx_list}")

            print("\n最终通过粗筛的论文序号:", idx_list)

            # ===== 摘要精筛 =====
            for idx in idx_list:
                if idx >= len(papers):
                    continue

                paper_info = papers[idx]
                abstract = paper_info.get("abstract")

                if flag_precise_screen:
                    if abstract and filter_func(abstract):
                        print(f"[精筛：匹配成功 ✅] {paper_info.get('title')}")
                        results.append(paper_info)
                    else:
                        print(f"[精筛：匹配失败 ❌] {paper_info.get('title')}")
                else:
                    results.append(paper_info)

            if not api_key:
                t_wait = time.time() - time_start
                t_limit = 60 / (1000 / 100)
                if t_wait < t_limit:
                    time.sleep(t_limit)

        except Exception as e:
            print(f"发生异常: {e}")

    return results

def choose_most_relevant_paper(papers, select_func, chunk_size=5):

    candidates = papers

    round_id = 1

    while len(candidates) > chunk_size:
        print(f"\n--- 相关性重排序轮次 {round_id} ---")
        print("当前候选数:", len(candidates))

        new_candidates = []
        total_chunks = (len(candidates) + chunk_size - 1) // chunk_size

        for chunk_id, start in enumerate(range(0, len(candidates), chunk_size), 1):
            chunk = candidates[start:start+chunk_size]

            text = ""
            for i, p in enumerate(chunk):
                title = p.get("title","")
                abstract = p.get("abstract","")

                text += f"{i+1}. {title}\n{abstract}\n\n"

            idx = select_func(text)
            idx -= 1

            if 0 <= idx < len(chunk):
                new_candidates.append(chunk[idx])

            print(f"进度 {chunk_id}/{total_chunks}")

        candidates = new_candidates
        round_id += 1

    # 最终选择
    text = ""

    for i,p in enumerate(candidates):

        title = p.get("title","")
        abstract = p.get("abstract","")

        text += f"{i+1}. {title}\n{abstract}\n\n"

    idx = select_func(text)
    idx -= 1

    if 0 <= idx < len(candidates):
        return candidates[idx]

    return random.choice(candidates)

def choose_next_paper(
        papers,
        strategy="random",
        select_func=None):

    if not papers:
        return None

    if strategy == "random":
        return random.choice(papers)

    elif strategy == "latest":
        papers = [p for p in papers if p.get("year")]

        if not papers:
            return None

        return max(
            papers,
            key=lambda x: (x.get("year", 0), x.get("citationCount", 0))
        )

    elif strategy == "most_cited":
        papers = [p for p in papers if p.get("citationCount") is not None]

        if not papers:
            return None

        return max(
            papers,
            key=lambda x: x.get("citationCount", 0)
        )

    elif strategy == "most_relevant":
        if select_func is None:
            raise ValueError("select_func is required when strategy is 'most_relevant'")

        return choose_most_relevant_paper(
            papers,
            select_func
        )

    else:
        raise ValueError("Unknown strategy")

def expand_paper_network(
        seed_paper_id,
        scan_func,
        filter_func,
        rounds=3,
        strategy="random",
        api_key=None,
        flag_precise_screen=True,
        min_year=None,
        flag_filter_zotero=False,
        zotero_csv="我的文库.csv",
        select_func=None):

    visited_ids = set()        # 所有出现过的论文
    used_seeds = set()         # 已经作为 seed 使用过的论文
    all_results = []

    current_seed = resolve_to_paper_id(seed_paper_id)
    used_seeds.add(current_seed)

    for r in range(rounds):

        print(f"\n========== 第 {r + 1} 轮深度搜索 ==========")
        print("当前论文 seed:", current_seed)

        papers = fetch_paper_network(
            current_seed,
            scan_func,
            filter_func,
            api_key,
            flag_precise_screen=flag_precise_screen,
            min_year=min_year,
            flag_filter_zotero=flag_filter_zotero,
            zotero_csv=zotero_csv
        )

        if not papers:
            print("⚠️ 没有找到论文")
            break

        # ===== 全局去重 =====
        new_papers = []

        for p in papers:

            pid = p.get("paperId")

            if not pid:
                continue

            if pid not in visited_ids:
                visited_ids.add(pid)
                new_papers.append(p)
                all_results.append(p)

        print("新增论文数:", len(new_papers))

        if not new_papers:
            print("⚠️ 没有新论文，停止扩散")
            break

        # ===== 过滤已经用过的 seed =====
        candidate_papers = [
            p for p in new_papers
            if p.get("paperId") not in used_seeds
        ]

        if not candidate_papers:
            print("⚠️ 没有新的论文可以作为 seed")
            break

        # ===== 选择下一轮 seed =====
        next_paper = choose_next_paper(candidate_papers, strategy, select_func)

        if not next_paper:
            print("⚠️ 无法选择下一篇论文")
            break

        # ===== 再次验证相关性 =====
        abstract = next_paper.get("abstract")

        if not abstract:
            print("⚠️ 选择的下一篇论文没有摘要，停止扩散")
            break

        if not filter_func(abstract):
            print("\n⚠️ 选择的下一篇论文与主题不相关，停止扩散")
            print(
                "论文:",
                next_paper.get("title", ""),
                "| year:", next_paper.get("year"),
                "| cite:", next_paper.get("citationCount")
            )
            break

        # ===== 更新 seed =====
        current_seed = next_paper["paperId"]
        used_seeds.add(current_seed)

        print(
            f"下一轮 seed ({strategy}) ->",
            next_paper.get("title", ""),
            "| year:", next_paper.get("year"),
            "| cite:", next_paper.get("citationCount")
        )

    return all_results

def sort_papers_by_year_and_citations(papers):
    """
    对论文列表进行排序：年份优先，其次引用数
    """
    return sorted(
        papers,
        key=lambda x: (
            x.get("year", 0),           # 年份，缺失默认为0
            x.get("citationCount", 0)   # 引用数，缺失默认为0
        ),
        reverse=True  # 倒序，最新 + 最多引用在前
    )

def paper_deep_search(api_key, paper_seed, topic='', require='', round_deep_search=2, type_choose_next_paper='latest', min_year=2000, flag_precise_screen=True, flag_filter_zotero=False, zotero_csv='我的文库.csv'):
    scan_func = lambda x: scan_paper(x, require='判断标准要非常严格，我希望多筛选掉不太相关的' + require,
                                    topic=topic, api_key=api_key)
    my_custom_filter = lambda x: idetify_paper(x, require='判断标准要非常严格，我希望多筛选掉不太相关的。' + require,
                                    topic=topic, api_key=api_key)
    select_func = lambda x: select_paper(x, topic=topic, require=require, api_key=api_key)

    final_list = expand_paper_network(seed_paper_id=paper_seed, scan_func=scan_func, filter_func=my_custom_filter,
                                    strategy=type_choose_next_paper, rounds=round_deep_search, flag_precise_screen=flag_precise_screen,
                                    min_year=min_year, select_func=select_func)
    final_list = sort_papers_by_year_and_citations(final_list)

    print(f"=========== 最终找到 {len(final_list)} 篇论文 =========== ")
    for p in final_list:
        print(
            f"{p.get('title')} | "
            f"Year: {p.get('year')} | "
            f"Citations: {p.get('citationCount')}"
        )

    if flag_filter_zotero:
        zotero_titles = load_zotero_titles(zotero_csv)
        missing_papers = find_missing_papers(final_list, zotero_titles)
        print("\n=========== Zotero 中没有的论文数量:", len(missing_papers), " ===========")

        for p in missing_papers:
            print(
                f"{p.get('title')} | "
                f"Year: {p.get('year')} | "
                f"Citations: {p.get('citationCount')}"
            )

        save_csv(missing_papers, "./不包含在zotero中的新论文.csv")

    return final_list

