"""自动生成 API - 根据标题生成小说设定"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.llm import LiteLLMClient

router = APIRouter()

# 全局 LLM 客户端
llm_client = None


class GenerateSettingRequest(BaseModel):
    """生成设定请求"""
    title: str
    novel_type: str = "scifi"  # scifi | xianxia
    user_prompt: Optional[str] = None  # 用户额外说明


class NPCInfo(BaseModel):
    """NPC 信息"""
    id: str
    name: str
    role: str
    personality: str
    background: str


class ProtagonistInfo(BaseModel):
    """主角信息"""
    name: str
    role: str
    personality: str
    background: str
    abilities: List[str]


class GeneratedSetting(BaseModel):
    """生成的设定"""
    title: str
    novel_type: str
    world_setting: str
    protagonist: ProtagonistInfo
    npcs: List[NPCInfo]


def build_generation_prompt(title: str, novel_type: str, user_prompt: Optional[str] = None) -> str:
    """构建生成提示词"""

    type_guide = {
        "scifi": {
            "name": "科幻",
            "elements": "星际旅行、高科技、外星文明、人工智能、太空探索",
            "protagonist_roles": "飞行员、科学家、军官、赏金猎人、殖民者",
            "world_aspects": "时间设定、科技水平、星际格局、主要势力、核心冲突"
        },
        "xianxia": {
            "name": "玄幻/仙侠",
            "elements": "修炼体系、门派势力、灵兽法宝、秘境宝藏、天道轮回",
            "protagonist_roles": "修仙者、散修、宗门弟子、魔道修士、炼器师",
            "world_aspects": "修炼等级、门派势力、地理格局、修炼资源、天道规则"
        }
    }

    guide = type_guide.get(novel_type, type_guide["scifi"])

    prompt = f"""你是一位专业的{guide['name']}小说设定生成助手。请根据标题《{title}》生成完整的小说世界设定。

要求：
1. 世界观要丰富、有深度、有吸引力
2. 主角设定要有特点、有成长空间
3. 至少生成 3 个重要 NPC（导师、伙伴、对手等角色类型）
4. 每个 NPC 要有独特的性格和背景
5. 确保所有设定相互关联、逻辑自洽

{guide['name']}类型要点：
- 核心元素：{guide['elements']}
- 主角可选角色：{guide['protagonist_roles']}
- 世界观包含：{guide['world_aspects']}
"""

    if user_prompt:
        prompt += f"\n\n用户补充说明：{user_prompt}"

    prompt += """

请严格按照以下 JSON 格式返回（不要包含任何其他文本）：

```json
{
  "world_setting": "详细的世界观设定（300-500字），包括时代背景、社会结构、核心矛盾等",
  "protagonist": {
    "name": "主角姓名",
    "role": "主角身份/职业",
    "personality": "主角性格特点（50字左右）",
    "background": "主角背景故事（100-200字）",
    "abilities": ["能力1", "能力2", "能力3"]
  },
  "npcs": [
    {
      "id": "npc_001",
      "name": "NPC 姓名",
      "role": "角色定位（导师/伙伴/对手/神秘人物等）",
      "personality": "性格特点（30-50字）",
      "background": "背景故事（80-150字）"
    },
    {
      "id": "npc_002",
      "name": "NPC 姓名",
      "role": "角色定位",
      "personality": "性格特点",
      "background": "背景故事"
    },
    {
      "id": "npc_003",
      "name": "NPC 姓名",
      "role": "角色定位",
      "personality": "性格特点",
      "background": "背景故事"
    }
  ]
}
```

注意：
1. 只返回 JSON，不要任何解释性文字
2. 确保 JSON 格式正确，可以被解析
3. 所有中文内容要生动、具体、有画面感
"""

    return prompt


async def generate_novel_setting(
    title: str,
    novel_type: str,
    user_prompt: Optional[str] = None
) -> GeneratedSetting:
    """生成小说设定"""
    global llm_client

    # 初始化 LLM 客户端
    if llm_client is None:
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / "config" / "litellm_config.yaml"
        llm_client = LiteLLMClient(config_path=str(config_path))

    # 构建提示词
    prompt = build_generation_prompt(title, novel_type, user_prompt)

    # 调用 LLM 生成
    try:
        response = await llm_client.generate(
            prompt=prompt,
            model="deepseek",
            temperature=0.9,  # 更高的创造性
            max_tokens=3000,
            system="你是一位专业的小说设定生成助手，擅长创作丰富、有深度的世界观和角色设定。"
        )

        # 提取 JSON
        content = response.strip()

        # 尝试提取 JSON 代码块
        if "```json" in content:
            json_start = content.find("```json") + 7
            json_end = content.find("```", json_start)
            content = content[json_start:json_end].strip()
        elif "```" in content:
            json_start = content.find("```") + 3
            json_end = content.find("```", json_start)
            content = content[json_start:json_end].strip()

        # 解析 JSON
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"无法解析生成的 JSON: {content}\n错误: {e}")

        # 构建返回对象
        protagonist = ProtagonistInfo(
            name=data["protagonist"]["name"],
            role=data["protagonist"]["role"],
            personality=data["protagonist"]["personality"],
            background=data["protagonist"]["background"],
            abilities=data["protagonist"].get("abilities", [])
        )

        npcs = [
            NPCInfo(
                id=npc["id"],
                name=npc["name"],
                role=npc["role"],
                personality=npc["personality"],
                background=npc["background"]
            )
            for npc in data["npcs"]
        ]

        return GeneratedSetting(
            title=title,
            novel_type=novel_type,
            world_setting=data["world_setting"],
            protagonist=protagonist,
            npcs=npcs
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成设定失败: {str(e)}")


@router.post("/api/generate-setting")
async def generate_setting_endpoint(request: GenerateSettingRequest):
    """
    生成小说设定 API 端点

    输入: 标题、类型、可选的用户说明
    输出: 完整的世界观、主角、NPC 设定

    优先使用 Claude Agent SDK (如果可用),否则降级到 LiteLLM
    """
    try:
        # 尝试使用 Agent SDK
        try:
            from agent_generation import generate_with_agent

            result = await generate_with_agent(
                title=request.title,
                novel_type=request.novel_type,
                user_prompt=request.user_prompt
            )

            if result.get("success"):
                return result
            elif "未安装" in result.get("error", ""):
                # Agent SDK 未安装,使用降级模式
                pass
            else:
                # Agent 生成失败,也尝试降级
                print(f"Agent 生成失败,降级到 LiteLLM: {result.get('error')}")

        except ImportError:
            print("Agent SDK 未安装,使用 LiteLLM")

        # 降级到 LiteLLM
        setting = await generate_novel_setting(
            title=request.title,
            novel_type=request.novel_type,
            user_prompt=request.user_prompt
        )

        return {
            "success": True,
            "setting": setting.dict(),
            "method": "litellm"  # 标注使用的方法
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/api/optimize-setting")
async def optimize_setting_endpoint(request: Dict[str, Any]):
    """
    优化已有设定

    根据用户反馈和上下文，优化角色设定、剧情大纲等
    """
    global llm_client

    if llm_client is None:
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / "config" / "litellm_config.yaml"
        llm_client = LiteLLMClient(config_path=str(config_path))

    try:
        current_setting = request.get("current_setting")
        optimization_request = request.get("optimization_request")

        prompt = f"""当前小说设定：
{json.dumps(current_setting, ensure_ascii=False, indent=2)}

用户优化需求：{optimization_request}

请根据用户需求优化设定，保持 JSON 格式返回优化后的完整设定。
"""

        response = await llm_client.generate(
            prompt=prompt,
            model="deepseek",
            temperature=0.8,
            max_tokens=3000
        )

        # 提取并解析 JSON
        content = response.strip()
        if "```json" in content:
            json_start = content.find("```json") + 7
            json_end = content.find("```", json_start)
            content = content[json_start:json_end].strip()

        optimized_setting = json.loads(content)

        return {
            "success": True,
            "optimized_setting": optimized_setting
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
