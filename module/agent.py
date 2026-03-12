from openai import OpenAI
from .utils import clean_think

class Agent():
    def __init__(self, name='Agent', system="你是一个 AI 助手", temperature=0.7, max_token=1000, his_recorder=None, type_model='kimi', model_name='kimi-k2-0905-preview', api_key=None):
        self.name = name
        self.model = model_name
        self.type_model = type_model
        self.conversation = [{"role": "system", "content": system}]
        self.temperature = temperature
        self.max_token = max_token
        self.dialog_history = []  # 存 dict，而不是 string
        self.his_recorder = his_recorder
        if api_key is None:
            raise ValueError("请传入 API Key")
        else:
            self.api_key = api_key
        self._init_client()

    def _init_client(self):
        """初始化 OpenAI 客户端（不可序列化）"""

        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://open.bigmodel.cn/api/paas/v4",
        )

    def ask(self, user_input, round_id=None, his_recorder=None, flag_clean=True, flag_show_resp=True):
        his_recorder = his_recorder if his_recorder is not None else self.his_recorder
        self.conversation.append({"role": "user", "content": user_input})
        self.dialog_history.append({"round": round_id, "speaker": "用户", "content": user_input})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.conversation,
            temperature=self.temperature,
            max_tokens=self.max_token,
            stream=True
        )

        if flag_show_resp: print('## ' + self.name + '：')
        ai_response = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                text = chunk.choices[0].delta.content
                if flag_show_resp: print(text, end='')
                ai_response += text

        print()
        self.conversation.append({"role": "assistant", "content": ai_response})
        self.dialog_history.append({"round": round_id, "speaker": self.name, "content": ai_response})
        if his_recorder is not None:
            his_recorder.update(round=round_id, speaker=self.name, content=ai_response)

        if flag_clean:
            ai_response = clean_think(ai_response)
        return ai_response

    def get_history(self):
        """格式化输出历史记录"""
        history = ""
        for h in self.dialog_history:
            prefix = f"[第{h['round']}轮] {h['speaker']}："
            history += prefix + h['content'] + "\n"
        return history

    # -----------------------------
    # pickle 支持
    # -----------------------------
    def __getstate__(self):
        """返回可序列化状态，不包含 client"""
        state = self.__dict__.copy()
        if "client" in state:
            del state["client"]
        return state

    def __setstate__(self, state):
        """恢复状态，同时重新初始化 client"""
        self.__dict__.update(state)
        self._init_client()

