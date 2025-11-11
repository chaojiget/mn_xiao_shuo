"""使用 Claude Agent SDK 进行自动生成"""

import asyncio
import json
from pathlib import Path


async def generate_with_agent(title: str, novel_type: str, user_prompt: str = None):
    """
    使用 Claude Agent SDK 生成小说设定

    这个版本使用 Agent 的工具能力,可以:
    - 调用自定义 tools
    - 使用 MCP servers
    - 更智能的推理和规划

    通过环境变量配置使用 DeepSeek 模型:
    - ANTHROPIC_API_BASE=http://localhost:4000 (LiteLLM Proxy)
    - 或直接使用 LITELLM_MODEL=deepseek
    """
    try:
        import os
        from config.settings import settings

        # 配置使用 LiteLLM Proxy + DeepSeek（统一通过 settings 覆盖，保留合理兜底）
        if not os.getenv("ANTHROPIC_BASE_URL"):
            if settings.anthropic_base_url:
                os.environ["ANTHROPIC_BASE_URL"] = settings.anthropic_base_url
            else:
                os.environ["ANTHROPIC_BASE_URL"] = "http://localhost:4000"
        if not os.getenv("ANTHROPIC_AUTH_TOKEN"):
            token = settings.anthropic_auth_token or settings.litellm_master_key or os.getenv("LITELLM_MASTER_KEY", "sk-litellm-default")
            os.environ["ANTHROPIC_AUTH_TOKEN"] = token
        if not os.getenv("ANTHROPIC_MODEL"):
            model = settings.anthropic_model
            if not model:
                # 从默认模型构造 openrouter 前缀形式
                default_model = settings.default_model
                model = f"openrouter/{default_model}"
            os.environ["ANTHROPIC_MODEL"] = model

        # 动态导入 Claude Agent SDK
        from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, TextBlock, query

        # 构建提示词
        type_guide = {
            "scifi": {
                "name": "科幻",
                "elements": "星际旅行、高科技、外星文明、人工智能、太空探索",
                "protagonist_roles": "飞行员、科学家、军官、赏金猎人、殖民者",
                "world_aspects": "时间设定、科技水平、星际格局、主要势力、核心冲突",
            },
            "xianxia": {
                "name": "玄幻/仙侠",
                "elements": "修炼体系、门派势力、灵兽法宝、秘境宝藏、天道轮回",
                "protagonist_roles": "修仙者、散修、宗门弟子、魔道修士、炼器师",
                "world_aspects": "修炼等级、门派势力、地理格局、修炼资源、天道规则",
            },
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

注意：只返回 JSON，不要任何解释性文字。
"""

        # 配置 Agent 选项
        options = ClaudeAgentOptions(
            system_prompt="你是一位专业的小说设定生成助手，擅长创作丰富、有深度的世界观和角色设定。",
            max_turns=1,  # 单次生成
            # 可以添加自定义工具
            # allowed_tools=["Read", "Write"],  # 如果需要读写文件
        )

        # 使用 Agent 生成
        full_response = ""
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        full_response += block.text

        # 提取 JSON
        content = full_response.strip()

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
            return {
                "success": True,
                "setting": {
                    "title": title,
                    "novel_type": novel_type,
                    "world_setting": data["world_setting"],
                    "protagonist": {
                        "name": data["protagonist"]["name"],
                        "role": data["protagonist"]["role"],
                        "personality": data["protagonist"]["personality"],
                        "background": data["protagonist"]["background"],
                        "abilities": data["protagonist"].get("abilities", []),
                    },
                    "npcs": [
                        {
                            "id": npc["id"],
                            "name": npc["name"],
                            "role": npc["role"],
                            "personality": npc["personality"],
                            "background": npc["background"],
                        }
                        for npc in data["npcs"]
                    ],
                },
            }
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"无法解析生成的 JSON: {str(e)}",
                "raw_response": content,
            }

    except ImportError:
        # 如果没有安装 Claude Agent SDK,降级到普通 LLM
        return {
            "success": False,
            "error": "Claude Agent SDK 未安装,请运行: pip install claude-agent-sdk",
            "fallback": "使用 LiteLLM 降级模式",
        }

    except Exception as e:
        return {"success": False, "error": f"生成失败: {str(e)}"}


# 示例：创建自定义工具用于小说生成
def create_novel_generation_tools():
    """
    创建用于小说生成的自定义 Agent 工具

    这些工具可以帮助 Agent:
    - 查询世界观数据库
    - 生成角色名称
    - 检查设定一致性
    """
    from claude_agent_sdk import create_sdk_mcp_server, tool

    @tool("generate_character_name", "生成符合类型的角色名称", {"novel_type": str, "role": str})
    async def generate_character_name(args):
        """根据小说类型和角色定位生成名称"""
        novel_type = args.get("novel_type", "scifi")
        role = args.get("role", "protagonist")

        # 简单的名称生成逻辑（实际可以调用更复杂的 LLM）
        scifi_names = {
            "protagonist": ["艾伦·克拉克", "莎拉·陈", "马克斯·雷诺"],
            "scientist": ["维克多·李", "艾米莉亚·沃森", "林晨"],
            "military": ["詹姆斯·哈里斯", "卡拉·桑切斯", "赵军"],
        }

        xianxia_names = {
            "protagonist": ["林风", "叶尘", "萧炎"],
            "master": ["玄机真人", "太虚老祖", "云中子"],
            "companion": ["苏灵儿", "青衣", "剑心"],
        }

        names = scifi_names if novel_type == "scifi" else xianxia_names
        import random

        name = random.choice(names.get(role, ["未命名"]))

        return {"content": [{"type": "text", "text": f"生成的角色名称: {name}"}]}

    @tool(
        "check_consistency", "检查设定一致性", {"world_setting": str, "character_description": str}
    )
    async def check_consistency(args):
        """检查角色设定是否与世界观一致"""
        # 简单的一致性检查（实际可以用 LLM 分析）
        world = args.get("world_setting", "").lower()
        character = args.get("character_description", "").lower()

        # 检查科技/修炼元素是否匹配
        scifi_keywords = ["科技", "星际", "太空", "AI", "飞船"]
        xianxia_keywords = ["修炼", "灵气", "法宝", "仙", "道"]

        is_consistent = True
        issues = []

        if any(k in world for k in scifi_keywords) and any(
            k in character for k in xianxia_keywords
        ):
            is_consistent = False
            issues.append("科幻世界观与修仙角色设定冲突")

        if any(k in world for k in xianxia_keywords) and any(
            k in character for k in scifi_keywords
        ):
            is_consistent = False
            issues.append("修仙世界观与科技角色设定冲突")

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {"is_consistent": is_consistent, "issues": issues}, ensure_ascii=False
                    ),
                }
            ]
        }

    # 创建 MCP Server
    server = create_sdk_mcp_server(
        name="novel-tools", version="1.0.0", tools=[generate_character_name, check_consistency]
    )

    return server


# 使用自定义工具的高级版本
async def generate_with_custom_tools(title: str, novel_type: str, user_prompt: str = None):
    """
    使用自定义工具增强的 Agent 生成
    """
    try:
        from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, TextBlock, query

        # 创建自定义工具
        novel_tools = create_novel_generation_tools()

        # 配置 Agent
        options = ClaudeAgentOptions(
            system_prompt="你是专业的小说设定生成助手，可以使用工具生成角色名称和检查一致性。",
            max_turns=5,  # 允许多轮交互使用工具
            mcp_servers={"novel_tools": novel_tools},
            allowed_tools=[
                "mcp__novel_tools__generate_character_name",
                "mcp__novel_tools__check_consistency",
            ],
        )

        prompt = f"""为小说《{title}》（类型：{novel_type}）生成完整设定。

步骤：
1. 使用 generate_character_name 工具生成主角和 NPC 的名称
2. 创建世界观设定
3. 使用 check_consistency 工具检查一致性
4. 返回完整的 JSON 格式设定

{user_prompt or ""}
"""

        full_response = ""
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        full_response += block.text

        # 解析并返回结果
        # ... (与前面相同的解析逻辑)

        return {"success": True, "message": "使用自定义工具生成成功", "response": full_response}

    except Exception as e:
        return {"success": False, "error": str(e)}
