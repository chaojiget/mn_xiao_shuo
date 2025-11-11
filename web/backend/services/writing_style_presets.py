"""
文风预设配置
提供常用的网络小说文风模板
"""

from models.world_models import WritingStyle


class WritingStylePresets:
    """文风预设工具类"""

    @staticmethod
    def get_preset(name: str) -> WritingStyle:
        """
        获取预设配置

        Args:
            name: 预设名称

        Returns:
            WritingStyle: 文风配置对象
        """
        presets = {
            # 网络小说风格
            "web_novel_cool": WritingStylePresets.web_novel_cool(),
            "web_novel_warm": WritingStylePresets.web_novel_warm(),
            "web_novel_dark": WritingStylePresets.web_novel_dark(),
            # 传统文风
            "classical_elegant": WritingStylePresets.classical_elegant(),
            "archaic_vernacular": WritingStylePresets.archaic_vernacular(),
            "modern_literary": WritingStylePresets.modern_literary(),
            # 特殊风格
            "poetic_beauty": WritingStylePresets.poetic_beauty(),
            "cinematic_thriller": WritingStylePresets.cinematic_thriller(),
            "vernacular_humorous": WritingStylePresets.vernacular_humorous(),
        }

        return presets.get(name, WritingStylePresets.modern_literary())

    # ========== 网络小说风格 ==========

    @staticmethod
    def web_novel_cool() -> WritingStyle:
        """
        网文爽文风格
        适用于：玄幻、仙侠、系统流
        特点：爽点密集、装逼打脸、金手指
        """
        return WritingStyle(
            style_type="modern",
            vocabulary_level="moderate",
            use_metaphor=True,
            use_personification=False,
            use_parallelism=True,  # "不是...不是...而是..."
            use_allusion=False,
            classical_syntax=False,
            four_character_phrases=True,  # "天赋异禀"、"横扫千军"
            poetic_language=False,
            narrative_pov="third_limited",
            description_style="balanced",
            cultural_flavor="仙侠爽文",
        )

    @staticmethod
    def web_novel_warm() -> WritingStyle:
        """
        网文温情风格
        适用于：都市、日常、恋爱
        特点：温馨日常、情感细腻、对话丰富
        """
        return WritingStyle(
            style_type="vernacular",
            vocabulary_level="simple",
            use_metaphor=True,
            use_personification=True,
            use_parallelism=False,
            use_allusion=False,
            classical_syntax=False,
            four_character_phrases=False,
            poetic_language=False,
            narrative_pov="first",  # 第一人称更亲切
            description_style="balanced",
            cultural_flavor="都市温情",
        )

    @staticmethod
    def web_novel_dark() -> WritingStyle:
        """
        网文黑暗风格
        适用于：末世、黑暗流、无限流
        特点：阴暗压抑、写实残酷、镜头感强
        """
        return WritingStyle(
            style_type="cinematic",
            vocabulary_level="advanced",
            use_metaphor=True,
            use_personification=True,
            use_parallelism=False,
            use_allusion=False,
            classical_syntax=False,
            four_character_phrases=False,
            poetic_language=False,
            narrative_pov="third_limited",
            description_style="lush",  # 丰富描写营造氛围
            cultural_flavor="黑暗末世",
        )

    # ========== 传统文风 ==========

    @staticmethod
    def classical_elegant() -> WritingStyle:
        """
        古典雅致风格
        适用于：历史、武侠、传统仙侠
        特点：文言白话混合、典雅庄重、古韵悠长
        """
        return WritingStyle(
            style_type="archaic",
            vocabulary_level="archaic",
            use_metaphor=True,
            use_personification=True,
            use_parallelism=True,
            use_allusion=True,  # 使用典故
            classical_syntax=True,  # 古典句式
            four_character_phrases=True,
            poetic_language=True,
            narrative_pov="third_omniscient",
            description_style="ornate",  # 华丽
            cultural_flavor="传统武侠",
        )

    @staticmethod
    def archaic_vernacular() -> WritingStyle:
        """
        古风白话风格
        适用于：穿越、宫斗、古代背景
        特点：古风韵味但易读、四字词语多
        """
        return WritingStyle(
            style_type="archaic",
            vocabulary_level="moderate",
            use_metaphor=True,
            use_personification=True,
            use_parallelism=False,
            use_allusion=False,
            classical_syntax=False,
            four_character_phrases=True,
            poetic_language=False,
            narrative_pov="third_limited",
            description_style="balanced",
            cultural_flavor="古代宫廷",
        )

    @staticmethod
    def modern_literary() -> WritingStyle:
        """
        现代文学风格（默认）
        适用于：现代背景、纯文学
        特点：现代白话、文学性强、适合大众
        """
        return WritingStyle(
            style_type="literary",
            vocabulary_level="moderate",
            use_metaphor=True,
            use_personification=True,
            use_parallelism=False,
            use_allusion=False,
            classical_syntax=False,
            four_character_phrases=False,
            poetic_language=False,
            narrative_pov="third_limited",
            description_style="balanced",
            cultural_flavor=None,
        )

    # ========== 特殊风格 ==========

    @staticmethod
    def poetic_beauty() -> WritingStyle:
        """
        诗意优美风格
        适用于：散文、唯美向、情感细腻
        特点：诗化语言、意境悠远、美感十足
        """
        return WritingStyle(
            style_type="poetic",
            vocabulary_level="advanced",
            use_metaphor=True,
            use_personification=True,
            use_parallelism=True,
            use_allusion=True,
            classical_syntax=False,
            four_character_phrases=False,
            poetic_language=True,
            narrative_pov="first",
            description_style="lush",
            cultural_flavor="诗意唯美",
        )

    @staticmethod
    def cinematic_thriller() -> WritingStyle:
        """
        镜头感惊悚风格
        适用于：悬疑、惊悚、侦探
        特点：画面感强、节奏紧凑、镜头语言
        """
        return WritingStyle(
            style_type="cinematic",
            vocabulary_level="moderate",
            use_metaphor=True,
            use_personification=False,
            use_parallelism=False,
            use_allusion=False,
            classical_syntax=False,
            four_character_phrases=False,
            poetic_language=False,
            narrative_pov="third_limited",
            description_style="minimalist",  # 极简，聚焦关键
            cultural_flavor="悬疑惊悚",
        )

    @staticmethod
    def vernacular_humorous() -> WritingStyle:
        """
        口语化幽默风格
        适用于：轻松搞笑、日常向
        特点：口语化、幽默诙谐、接地气
        """
        return WritingStyle(
            style_type="vernacular",
            vocabulary_level="simple",
            use_metaphor=True,
            use_personification=True,
            use_parallelism=False,
            use_allusion=False,
            classical_syntax=False,
            four_character_phrases=False,
            poetic_language=False,
            narrative_pov="first",
            description_style="minimalist",
            cultural_flavor="轻松搞笑",
        )

    @staticmethod
    def list_presets() -> dict:
        """
        列出所有可用的预设配置

        Returns:
            dict: 预设名称和描述的字典
        """
        return {
            # 网络小说风格
            "web_novel_cool": {
                "name": "网文爽文",
                "description": "装逼打脸、爽点密集、四字成语多",
                "tags": ["网文", "爽文", "仙侠"],
                "suitable_for": ["玄幻", "仙侠", "系统流"],
            },
            "web_novel_warm": {
                "name": "网文温情",
                "description": "温馨日常、对话丰富、第一人称",
                "tags": ["网文", "温情", "都市"],
                "suitable_for": ["都市", "日常", "恋爱"],
            },
            "web_novel_dark": {
                "name": "网文黑暗",
                "description": "阴暗压抑、写实残酷、镜头感强",
                "tags": ["网文", "黑暗", "末世"],
                "suitable_for": ["末世", "黑暗流", "无限流"],
            },
            # 传统文风
            "classical_elegant": {
                "name": "古典雅致",
                "description": "文言白话、典雅庄重、使用典故",
                "tags": ["古典", "雅致", "武侠"],
                "suitable_for": ["历史", "武侠", "传统仙侠"],
            },
            "archaic_vernacular": {
                "name": "古风白话",
                "description": "古风韵味、易读易懂、四字词多",
                "tags": ["古风", "白话", "宫斗"],
                "suitable_for": ["穿越", "宫斗", "古代背景"],
            },
            "modern_literary": {
                "name": "现代文学（默认）",
                "description": "现代白话、文学性强、适合大众",
                "tags": ["现代", "文学", "通用"],
                "suitable_for": ["现代背景", "纯文学"],
            },
            # 特殊风格
            "poetic_beauty": {
                "name": "诗意优美",
                "description": "诗化语言、意境悠远、美感十足",
                "tags": ["诗意", "唯美", "文艺"],
                "suitable_for": ["散文", "唯美向", "情感细腻"],
            },
            "cinematic_thriller": {
                "name": "镜头感惊悚",
                "description": "画面感强、极简风格、镜头语言",
                "tags": ["镜头", "惊悚", "悬疑"],
                "suitable_for": ["悬疑", "惊悚", "侦探"],
            },
            "vernacular_humorous": {
                "name": "口语化幽默",
                "description": "口语表达、幽默诙谐、接地气",
                "tags": ["口语", "幽默", "轻松"],
                "suitable_for": ["轻松搞笑", "日常向"],
            },
        }
