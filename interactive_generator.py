#!/usr/bin/env python3
"""
交互式小说生成器
快速原型 - 验证整体流程
"""

import asyncio
import json
import sys
import uuid
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.llm import LiteLLMClient
from src.utils.database import Database
from src.models import WorldState, Character

load_dotenv()


class InteractiveNovelGenerator:
    """交互式小说生成器"""

    def __init__(self, setting_file: str):
        """初始化"""
        # 加载设定
        with open(setting_file, "r", encoding="utf-8") as f:
            self.setting = json.load(f)

        # LLM 客户端
        self.llm_client = LiteLLMClient()

        # 数据库
        self.db = Database()
        self.db.connect()

        # 小说ID
        self.novel_id = f"novel_{uuid.uuid4().hex[:8]}"

        # 状态
        self.current_chapter = 0
        self.world_state = None

        # 历史上下文
        self.chapter_summaries = []

    def initialize(self):
        """初始化小说"""
        print("\n" + "=" * 60)
        print(f"开始创建小说: {self.setting['title']}")
        print("=" * 60)

        # 创建数据库记录
        self.db.create_novel(
            novel_id=self.novel_id,
            title=self.setting["title"],
            novel_type=self.setting["novel_type"],
            setting_json=self.setting,
            preference=self.setting.get("preference", "hybrid")
        )

        # 初始化世界状态
        self.world_state = WorldState(timestamp=0, turn=0)

        # 添加主角
        protagonist_setting = self.setting.get("主角设定", {})
        protagonist = Character(
            id="PROTAGONIST",
            name=protagonist_setting.get("姓名", "主角"),
            role="protagonist",
            description=protagonist_setting.get("职业", "主角"),
            attributes=protagonist_setting.get("能力", {}),
            resources=protagonist_setting.get("初始资源", {})
        )
        self.world_state.characters["PROTAGONIST"] = protagonist

        # 保存初始状态
        self.db.save_world_state(self.novel_id, self.world_state)

        print(f"✅ 小说ID: {self.novel_id}")
        print(f"   类型: {self.setting['novel_type']}")
        print(f"   主角: {protagonist.name}")

    async def generate_chapter(self, chapter_num: int, user_choice: str = None):
        """生成一章"""
        print(f"\n{'=' * 60}")
        print(f"正在生成第 {chapter_num} 章...")
        print("=" * 60)

        # 构建提示词
        prompt = self._build_chapter_prompt(chapter_num, user_choice)

        # 选择模型 (全部使用 DeepSeek V3 - 性价比高且中文友好)
        model = "deepseek"

        # 生成
        try:
            content = await self.llm_client.generate(
                prompt=prompt,
                model=model,
                max_tokens=2000,
                temperature=0.8
            )

            # 保存章节
            self.db.save_chapter(
                novel_id=self.novel_id,
                chapter_num=chapter_num,
                content=content
            )

            # 更新进度
            self.current_chapter = chapter_num
            self.world_state.turn += 1
            self.db.save_world_state(self.novel_id, self.world_state)
            self.db.update_novel_progress(self.novel_id, self.world_state.turn, chapter_num)

            # 添加摘要到历史
            summary = content[:200] + "..."
            self.chapter_summaries.append(f"第{chapter_num}章: {summary}")

            return content

        except Exception as e:
            print(f"❌ 生成失败: {e}")
            return None

    def _build_chapter_prompt(self, chapter_num: int, user_choice: str = None):
        """构建章节生成提示词"""
        novel_type = self.setting["novel_type"]
        protagonist = self.world_state.get_protagonist()

        # 基础提示
        prompt = f"""你是一个{self._get_type_name(novel_type)}作家。

【小说设定】
{self.setting.get('setting_text', '')}

【主角】
姓名: {protagonist.name if protagonist else '主角'}
"""

        # 添加能力/属性
        if protagonist and protagonist.attributes:
            prompt += f"能力: {json.dumps(protagonist.attributes, ensure_ascii=False)}\n"

        if protagonist and protagonist.resources:
            prompt += f"资源: {json.dumps(protagonist.resources, ensure_ascii=False)}\n"

        # 前情提要
        if self.chapter_summaries:
            prompt += f"\n【前情提要】\n"
            prompt += "\n".join(self.chapter_summaries[-3:])  # 最近3章

        # 用户选择
        if user_choice:
            prompt += f"\n\n【玩家选择】\n{user_choice}\n"

        # 当前章节目标
        if chapter_num == 1:
            prompt += f"\n\n【本章目标】\n开篇,引入主角和核心冲突\n"
            start_event = self.setting.get("起始事件", {})
            if start_event:
                prompt += f"起始事件: {start_event.get('trigger', '')}\n"
        else:
            prompt += f"\n\n【本章目标】\n推进剧情,深化冲突\n"

        # 约束
        constraints = self.setting.get("constraints", {})
        if constraints.get("hard_rules"):
            prompt += f"\n【硬规则】\n"
            for rule in constraints["hard_rules"]:
                prompt += f"- {rule}\n"

        # 输出要求
        prompt += f"""
【输出要求】
1. 字数: 800-1200字
2. 包含具体场景描写
3. 有人物对话
4. 推进剧情
5. 结尾留下悬念或选择点

请开始创作第 {chapter_num} 章:
"""

        return prompt

    def _get_type_name(self, novel_type: str) -> str:
        """获取类型名称"""
        type_names = {
            "scifi": "科幻",
            "xianxia": "玄幻修仙"
        }
        return type_names.get(novel_type, novel_type)

    def display_chapter(self, chapter_num: int, content: str):
        """显示章节"""
        print(f"\n{'=' * 60}")
        print(f"第 {chapter_num} 章")
        print("=" * 60)
        print(content)
        print("\n" + "=" * 60)

    async def run(self):
        """运行交互式生成"""
        self.initialize()

        print("\n📖 开始生成小说...")
        print("\n提示:")
        print("  - 每章生成后,你可以输入选择影响后续剧情")
        print("  - 输入 'quit' 退出")
        print("  - 输入 'save' 保存并查看统计")
        print("  - 直接回车继续自动生成")

        while True:
            # 生成章节
            chapter_num = self.current_chapter + 1
            content = await self.generate_chapter(chapter_num)

            if content is None:
                print("生成失败,退出")
                break

            # 显示章节
            self.display_chapter(chapter_num, content)

            # 用户交互
            print("\n你的选择:")
            user_input = input("> ").strip()

            if user_input.lower() == 'quit':
                print("\n退出生成")
                break
            elif user_input.lower() == 'save':
                self.show_stats()
                choice = input("继续? (y/n): ")
                if choice.lower() != 'y':
                    break
                user_input = None
            elif user_input == '':
                user_input = None

            # 下一章会使用用户选择
            if user_input:
                print(f"✅ 已记录你的选择: {user_input}")

            # 继续下一章 (将用户选择传入)
            # 下次循环会使用这个选择

    def show_stats(self):
        """显示统计信息"""
        stats = self.db.get_stats(self.novel_id)

        print("\n" + "=" * 60)
        print("📊 小说统计")
        print("=" * 60)
        print(f"小说ID: {self.novel_id}")
        print(f"标题: {self.setting['title']}")
        print(f"已生成章节: {stats['chapters']}")
        print(f"总回合数: {self.world_state.turn}")
        print("=" * 60)

    def export(self, output_file: str):
        """导出小说"""
        chapters = self.db.get_all_chapters(self.novel_id)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# {self.setting['title']}\n\n")
            f.write(f"作者: AI (使用长篇小说生成系统)\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d')}\n\n")
            f.write("---\n\n")

            for chapter in chapters:
                f.write(f"## 第 {chapter['chapter_num']} 章\n\n")
                f.write(chapter["content"])
                f.write("\n\n---\n\n")

        print(f"✅ 小说已导出到: {output_file}")

    def __del__(self):
        """析构"""
        if hasattr(self, 'db') and self.db:
            self.db.close()


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print(" 交互式小说生成器")
    print("=" * 60)

    # 选择设定
    print("\n选择小说类型:")
    print("1. 科幻小说 (能源纪元)")
    print("2. 玄幻小说 (逆天改命录)")

    choice = input("\n请选择 (1/2): ").strip()

    if choice == "1":
        setting_file = "examples/scifi_setting.json"
    elif choice == "2":
        setting_file = "examples/xianxia_setting.json"
    else:
        print("无效选择,使用默认设定 (科幻)")
        setting_file = "examples/scifi_setting.json"

    # 创建生成器
    generator = InteractiveNovelGenerator(setting_file)

    try:
        # 运行
        await generator.run()

        # 导出
        print("\n")
        export = input("是否导出小说? (y/n): ")
        if export.lower() == 'y':
            output_file = f"output_{generator.novel_id}.md"
            generator.export(output_file)

        print("\n🎉 生成完成!")

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        generator.show_stats()


if __name__ == "__main__":
    asyncio.run(main())
