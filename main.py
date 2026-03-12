from module.papar_search import paper_deep_search

if __name__ == "__main__":
    # 参数说明：
    # api_key:      智谱 API的密钥，申请网站为：https://bigmodel.cn/usercenter/proj-mgmt/apikeys
    # paper_seed:   种子论文（查询起点），可以是DOI编号、arXiv编号、或其他唯一标识，如 '10.48550/arXiv.2411.14679'、'arXiv:2411.14679' （有时会检索不到，可以换其他标识或其他论文试试）
    # topic:        需要检索的主题，中英文输入均可
    # require:      额外限定条件，对筛选标准的补充
    # round_deep_search:    深度检索的轮数，数值越大，遍历圈数越多
    # type_choose_next_paper: 下一步选择论文的策略（如'latest'为最新优先， 'most_cited'为引用最多优先， 'random'为随机选择, 'most_relevant'为最相关优先）
    # min_year:     检索论文的最早年份（过滤较早文献）
    # flag_precise_screen: 是否开启更严格筛选（True为高标准筛选）
    # flag_filter_zotero:  是否将结果与Zotero文库比对，输出未收录文献
    # zotero_csv:   Zotero导出文库的CSV文件名
    paper_deep_search(
        api_key="",
        paper_seed='10.48550/arXiv.2411.14679',
        topic='Gaussian Process-based online learning of dynamical system',
        require='方法必须具备在线学习能力（如递推形式），而且不要非动态系统学习的方法，也不要没有使用高斯过程的方法',
        round_deep_search=2,
        type_choose_next_paper='most_relevant',
        min_year=2020,
        flag_precise_screen=True,
        flag_filter_zotero=True,
        zotero_csv='我的文库.csv'
    )
