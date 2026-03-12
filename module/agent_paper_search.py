from .agent import Agent
from .utils import history_recorder
import re

class AgentCompare():
    def __init__(self, api_key=None):
        self.recorder = history_recorder()

        system_prompt = (
            "你是一个文献调研专家，需要判断一些文献是否属于用户想要的主题。"
        )

        self.agent = Agent(
            name='文献调研助手',
            system=system_prompt,
            temperature=0,
            max_token=20000,
            his_recorder=self.recorder,
            model_name='glm-4-flash',
            api_key=api_key,
        )

        self.round = 1

    def identify(self, paper='', topic='dynamics learning', require='', flag_show_resp=True):
        prompt = f"需要你调研的主题是：{topic}。请判断以下论文是否属于该主题：\n\n{paper}。你只需要回答”是“或”不是“，你的回答将用于代码判断，所以只能输出以上两个答案。" + require
        resp = self.agent.ask(prompt, round_id=self.round, flag_show_resp=flag_show_resp)
        self.round += 1
        return resp == '是'

class AgentScan():
    def __init__(self, api_key=None):
        self.recorder = history_recorder()

        system_prompt = (
            "你是一个文献调研专家，需要判断一些文献是否属于用户想要的主题。后面会给你几篇文献标题/摘要，分别标号，你需要把符号主题的标题的编号输出。"
            "为了便于后续代码识别，只允许输出数字编号列表，例如：1,3,5。禁止输出任何解释、句子或分析。"
        )

        self.agent = Agent(
            name='文献调研助手',
            system=system_prompt,
            temperature=0,
            max_token=20000,
            his_recorder=self.recorder,
            model_name='glm-4-flash',
            api_key=api_key,
        )

        self.round = 1

    def identify(self, paper='', topic='dynamics learning', require='', flag_show_resp=True):
        prompt = f"需要你调研的主题是：{topic}。请判断以下论文是否属于该主题：\n\n{paper}" + require
        resp = self.agent.ask(prompt, round_id=self.round, flag_show_resp=flag_show_resp)
        self.round += 1

        idx_list = [int(x) for x in re.findall(r'\d+', resp)]
        return idx_list


class AgentSelect():
    def __init__(self, api_key=None):
        self.recorder = history_recorder()

        system_prompt = (
            "你是一个文献调研专家，需要判断一些文献与用户想要的主题的相关度，你需要选出一篇最相关的（最大限度符合用户的主题）。后面会给你几篇文献标题/摘要，分别标号，你需要把符号主题的标题的编号输出。"
            "为了便于后续代码识别，只允许输出数字编号，例如：2。只输出一个编号，禁止输出任何解释、句子或分析。"
        )

        self.agent = Agent(
            name='文献调研助手',
            system=system_prompt,
            temperature=0,
            max_token=20000,
            his_recorder=self.recorder,
            model_name='glm-4-flash',
            api_key=api_key,
        )

        self.round = 1

    def identify(self, paper='', topic='dynamics learning', require='', flag_show_resp=True):
        prompt = f"需要你调研的主题是：{topic}。请输出以下论文中与主题最相关的论文：\n\n{paper}" + require
        resp = self.agent.ask(prompt, round_id=self.round, flag_show_resp=flag_show_resp)
        self.round += 1

        match = re.search(r'\b(\d+)\b', resp)
        if match:
            return int(match.group(1))

        # fallback
        nums = re.findall(r'\d+', resp)
        if nums:
            return int(nums[0])

        return None


if __name__ == '__main__':
    agent = AgentScan()
    agent.identify(paper='1. Exact Inference for Continuous-Time Gaussian Process Dynamics；'
                         '2. Variational multiple shooting for Bayesian ODEs with Gaussian processes；'
                         '3. Neural Extended Kalman Filters for Learning and Predicting Dynamics of Structural Systems；'
                         '4. RBF neural network based adaptive sliding mode control for hypersonic flight vehicles；'
                         '5. 高超声速飞行器的参数辨识δ修正动态面控制；'
                         '6. Neural Internal Model Control: Learning a Robust Control Policy Via Predictive Error Feedback；',
                  topic='dynamics learning', flag_show_resp=True)