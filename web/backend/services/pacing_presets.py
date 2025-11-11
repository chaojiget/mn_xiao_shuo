"""
节奏预设配置
提供常用的节奏模板
"""

from models.world_models import PacingControl


class PacingPresets:
    """节奏预设工具类"""

    @staticmethod
    def get_preset(name: str) -> PacingControl:
        """
        获取预设配置

        Args:
            name: 预设名称（action/literary/epic/horror/detective/slice_of_life）

        Returns:
            PacingControl: 节奏配置对象
        """
        presets = {
            "action": PacingPresets.action(),
            "literary": PacingPresets.literary(),
            "epic": PacingPresets.epic(),
            "horror": PacingPresets.horror(),
            "detective": PacingPresets.detective(),
            "slice_of_life": PacingPresets.slice_of_life(),
            "balanced": PacingPresets.balanced(),
        }

        return presets.get(name, PacingPresets.balanced())

    @staticmethod
    def action() -> PacingControl:
        """
        动作快节奏配置
        适用于：动作冒险、战斗、追逐场景
        """
        return PacingControl(
            global_pace="fast",
            avg_sentence_len=12,
            sentence_len_variance=0.5,
            prefer_active_voice=True,
            paragraph_rhythm="staccato",
            description_ratio=0.2,
            action_density=0.9,
            dialogue_frequency=0.2,
            scene_transition_speed="abrupt",
            event_frequency=0.9,
            conflict_intensity_curve="escalating",
            exposition_pace="minimal",
            time_compression=0.3,
            skip_mundane=True,
        )

    @staticmethod
    def literary() -> PacingControl:
        """
        文学慢节奏配置
        适用于：文艺小说、心理描写、氛围营造
        """
        return PacingControl(
            global_pace="slow",
            avg_sentence_len=28,
            sentence_len_variance=0.6,
            prefer_active_voice=False,
            paragraph_rhythm="flowing",
            description_ratio=0.7,
            action_density=0.2,
            dialogue_frequency=0.4,
            scene_transition_speed="gradual",
            event_frequency=0.3,
            conflict_intensity_curve="wave",
            exposition_pace="gradual",
            time_compression=3.0,
            skip_mundane=False,
        )

    @staticmethod
    def epic() -> PacingControl:
        """
        史诗节奏配置
        适用于：仙侠、奇幻史诗、大场景
        """
        return PacingControl(
            global_pace="varied",
            avg_sentence_len=22,
            sentence_len_variance=0.7,
            prefer_active_voice=True,
            paragraph_rhythm="mixed",
            description_ratio=0.5,
            action_density=0.6,
            dialogue_frequency=0.3,
            scene_transition_speed="moderate",
            event_frequency=0.6,
            conflict_intensity_curve="escalating",
            exposition_pace="upfront",
            time_compression=1.5,
            skip_mundane=True,
        )

    @staticmethod
    def horror() -> PacingControl:
        """
        恐怖悬疑节奏配置
        适用于：恐怖、悬疑、惊悚
        """
        return PacingControl(
            global_pace="slow",
            avg_sentence_len=16,
            sentence_len_variance=0.8,
            prefer_active_voice=True,
            paragraph_rhythm="staccato",
            description_ratio=0.6,
            action_density=0.4,
            dialogue_frequency=0.2,
            scene_transition_speed="gradual",
            event_frequency=0.4,
            conflict_intensity_curve="wave",
            exposition_pace="gradual",
            time_compression=2.0,
            skip_mundane=False,
        )

    @staticmethod
    def detective() -> PacingControl:
        """
        推理节奏配置
        适用于：侦探、推理、解谜
        """
        return PacingControl(
            global_pace="moderate",
            avg_sentence_len=20,
            sentence_len_variance=0.4,
            prefer_active_voice=True,
            paragraph_rhythm="varied",
            description_ratio=0.5,
            action_density=0.5,
            dialogue_frequency=0.5,
            scene_transition_speed="moderate",
            event_frequency=0.5,
            conflict_intensity_curve="steady",
            exposition_pace="gradual",
            time_compression=1.0,
            skip_mundane=False,
        )

    @staticmethod
    def slice_of_life() -> PacingControl:
        """
        日常节奏配置
        适用于：日常、校园、温馨
        """
        return PacingControl(
            global_pace="slow",
            avg_sentence_len=18,
            sentence_len_variance=0.3,
            prefer_active_voice=True,
            paragraph_rhythm="flowing",
            description_ratio=0.5,
            action_density=0.3,
            dialogue_frequency=0.6,
            scene_transition_speed="gradual",
            event_frequency=0.3,
            conflict_intensity_curve="steady",
            exposition_pace="upfront",
            time_compression=1.5,
            skip_mundane=False,
        )

    @staticmethod
    def balanced() -> PacingControl:
        """
        平衡节奏配置（默认）
        适用于：通用场景、混合类型
        """
        return PacingControl(
            global_pace="moderate",
            avg_sentence_len=18,
            sentence_len_variance=0.3,
            prefer_active_voice=True,
            paragraph_rhythm="varied",
            description_ratio=0.4,
            action_density=0.5,
            dialogue_frequency=0.3,
            scene_transition_speed="moderate",
            event_frequency=0.5,
            conflict_intensity_curve="escalating",
            exposition_pace="gradual",
            time_compression=1.0,
            skip_mundane=True,
        )

    @staticmethod
    def list_presets() -> dict:
        """
        列出所有可用的预设配置

        Returns:
            dict: 预设名称和描述的字典
        """
        return {
            "action": {
                "name": "动作快节奏",
                "description": "短句密集、动作紧凑，适合战斗和追逐场景",
                "tags": ["快节奏", "动作", "紧张"],
            },
            "literary": {
                "name": "文学慢节奏",
                "description": "长句流畅、描写细腻，适合心理和氛围营造",
                "tags": ["慢节奏", "文艺", "细腻"],
            },
            "epic": {
                "name": "史诗节奏",
                "description": "变化丰富、场景宏大，适合仙侠和奇幻史诗",
                "tags": ["变化", "史诗", "宏大"],
            },
            "horror": {
                "name": "恐怖悬疑",
                "description": "节奏舒缓、气氛压抑，适合恐怖和惊悚",
                "tags": ["悬疑", "压抑", "恐怖"],
            },
            "detective": {
                "name": "推理节奏",
                "description": "节奏平稳、逻辑清晰，适合侦探和推理",
                "tags": ["推理", "逻辑", "平稳"],
            },
            "slice_of_life": {
                "name": "日常节奏",
                "description": "舒缓温馨、对话丰富，适合日常和校园",
                "tags": ["日常", "温馨", "舒缓"],
            },
            "balanced": {
                "name": "平衡节奏",
                "description": "各项均衡、通用性强，适合大多数场景",
                "tags": ["平衡", "通用", "默认"],
            },
        }
