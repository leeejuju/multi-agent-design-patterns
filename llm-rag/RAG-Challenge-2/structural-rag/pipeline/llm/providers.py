from dataclasses import dataclass


@dataclass(frozen=True)
class LLMProvider:
    name: str
    base_url: str | None
    api_key_env: str
    default_model: str
    recommended_models: tuple[str, ...]


PROVIDERS: dict[str, LLMProvider] = {
    "openai": LLMProvider(
        name="openai",
        base_url=None,
        api_key_env="OPENAI_API_KEY",
        default_model="gpt-5.4",
        recommended_models=("gpt-5.4", "gpt-5.4-pro", "gpt-5.4-mini", "gpt-5.4-nano"),
    ),
    "dashscope": LLMProvider(
        name="dashscope",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key_env="DASHSCOPE_API_KEY",
        default_model="qwen3.6-plus",
        recommended_models=(
            "qwen3.6-plus",
            "qwen3-max",
            "qwen2.5-72b-instruct",
            "qwen2.5-32b-instruct",
            "qwen2.5-14b-instruct",
            "qwen2.5-7b-instruct",
            "qwen2-72b-instruct",
            "qwen2-7b-instruct",
            "qwen-plus",
            "qwen-turbo",
        ),
    ),
    "gemini": LLMProvider(
        name="gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        api_key_env="GEMINI_API_KEY",
        default_model="gemini-3-pro-preview",
        recommended_models=("gemini-3-pro-preview", "gemini-3-flash-preview", "gemini-2.5-pro"),
    ),
    "deepseek": LLMProvider(
        name="deepseek",
        base_url="https://api.deepseek.com",
        api_key_env="DEEPSEEK_API_KEY",
        default_model="deepseek-chat",
        recommended_models=("deepseek-chat", "deepseek-reasoner"),
    ),
    "siliconflow": LLMProvider(
        name="siliconflow",
        base_url="https://api.siliconflow.cn/v1",
        api_key_env="SILICONFLOW_API_KEY",
        default_model="deepseek-ai/DeepSeek-V3.2",
        recommended_models=(
            "deepseek-ai/DeepSeek-V3.2",
            "deepseek-ai/DeepSeek-R1",
            "Qwen/Qwen3-235B-A22B-Instruct-2507",
            "Qwen/Qwen3-235B-A22B-Thinking-2507",
        ),
    ),
    "zhipu": LLMProvider(
        name="zhipu",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key_env="ZHIPU_API_KEY",
        default_model="glm-5.1",
        recommended_models=("glm-5.1", "glm-5", "glm-4.7", "glm-4.7-flashx"),
    ),
}
