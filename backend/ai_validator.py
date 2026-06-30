"""AI大模型校验模块 - 通过LLM验证建筑结构规范"""
import json
import os
import requests
from typing import Optional, Dict, List

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'data', 'ai_config.json')

# AI配置
_ai_config = {
    "base_url": "",
    "token": "",
    "model": "gpt-3.5-turbo",
}

def _load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                _ai_config.update(saved)
        except Exception:
            pass

def _save_config():
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(_ai_config, f, ensure_ascii=False, indent=2)

def update_config(base_url: str, token: str, model: str):
    _ai_config["base_url"] = base_url.rstrip("/")
    if token:
        _ai_config["token"] = token
    _ai_config["model"] = model
    _save_config()

def get_config() -> Dict:
    return {
        "base_url": _ai_config["base_url"],
        "has_token": bool(_ai_config["token"]),
        "model": _ai_config["model"],
    }

# 启动时加载配置
_load_config()

def validate_standards_with_ai(standards: List[Dict]) -> List[Dict]:
    """
    使用AI大模型批量校验规范
    standards: [{"number": "GB 50010-2010", "name": "混凝土结构设计规范"}, ...]
    返回: [{"number": "...", "name": "...", "status": "正确/名称错误/标准号错误/已废止", "correct_name": "...", "correct_number": "...", "message": "..."}, ...]
    """
    if not _ai_config["base_url"] or not _ai_config["token"]:
        return []

    standards_text = "\n".join(
        f"{i+1}. 标准号：{s['number']}，名称：{s['name']}"
        for i, s in enumerate(standards)
    )

    prompt = f"""你是一名建筑结构规范专家。请校验以下建筑结构规范的标准号和名称是否正确匹配。

待校验规范：
{standards_text}

请对每条规范返回JSON数组，每条包含以下字段：
- number: 输入的标准号
- name: 输入的名称
- status: "正确" / "名称错误" / "标准号错误" / "已废止" / "未找到"
- correct_name: 正确的规范名称（如果名称错误或标准号错误，填写正确的名称）
- correct_number: 正确的标准号（如果标准号错误，填写正确的标准号）
- replaced_by: 被替代的标准号（如果已废止，填写替代标准号）
- message: 说明信息

只返回JSON数组，不要其他内容。"""

    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {_ai_config['token']}",
        }

        payload = {
            "model": _ai_config["model"],
            "messages": [
                {"role": "system", "content": "你是建筑结构规范专家。只返回JSON数组，不要其他文字。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 4000,
        }

        # 自动处理base_url：如果已包含/v1则不再重复添加
        base = _ai_config['base_url'].rstrip('/')
        if base.endswith('/v1'):
            api_url = f"{base}/chat/completions"
        else:
            api_url = f"{base}/v1/chat/completions"

        resp = requests.post(api_url, headers=headers, json=payload, timeout=60)

        if resp.status_code != 200:
            return []

        data = resp.json()
        content = data["choices"][0]["message"]["content"] or ""
        # 推理模型（如mimo）可能将内容放在reasoning_content中
        if not content.strip():
            content = data["choices"][0]["message"].get("reasoning_content") or ""
        # 如果仍然为空，尝试从整个response提取
        if not content.strip():
            content = json.dumps(data, ensure_ascii=False)

        # 提取JSON
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

        results = json.loads(content)
        return results

    except Exception as e:
        return []
