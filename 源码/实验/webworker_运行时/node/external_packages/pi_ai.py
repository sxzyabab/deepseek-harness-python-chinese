from ..未实现失败 import 未实现失败

__all__=[
    'createProvider','createModels','getSupportedThinkingLevels','isContextOverflow',
    'builtinProviders','getBuiltinProviders','getBuiltinModels',
    'anthropicMessagesApi','openAICompletionsApi','openAIResponsesApi',
    '__esModule','default',
]

模块='@earendil-works/pi-ai'
createProvider=未实现失败(模块,'createProvider')
createModels=未实现失败(模块,'createModels')
getSupportedThinkingLevels=未实现失败(模块,'getSupportedThinkingLevels')
isContextOverflow=未实现失败(模块,'isContextOverflow')

内置提供方标识列表=(
    'amazon-bedrock','ant-ling','anthropic','azure-openai-responses','baseten','cerebras',
    'cloudflare-ai-gateway','cloudflare-workers-ai','deepseek','fireworks','github-copilot',
    'google','google-vertex','groq','huggingface','kimi-coding','minimax','minimax-cn',
    'mistral','moonshotai','moonshotai-cn','nvidia','openai','openai-codex','opencode',
    'opencode-go','openrouter','qwen-token-plan','qwen-token-plan-cn',
    'qwen-token-plan-individual','together',
    'vercel-ai-gateway','xai','xiaomi','xiaomi-token-plan-ams','xiaomi-token-plan-cn',
    'xiaomi-token-plan-sgp','zai','zai-coding-cn',
)

def builtinProviders():
    """已安装目录提供方，在 `llm-pi-ai` 激活时读取。"""
    return [{'id':标识,'name':标识,'auth':{'apiKey':{'type':'api-key'}},'models':[]} for 标识 in 内置提供方标识列表]

def getBuiltinProviders():
    """已安装目录的提供方路由 id。"""
    return list(内置提供方标识列表)

def getBuiltinModels():
    """某个已安装目录提供方的模型。"""
    return []

anthropicMessagesApi=未实现失败(模块,'anthropicMessagesApi')
openAICompletionsApi=未实现失败(模块,'openAICompletionsApi')
openAIResponsesApi=未实现失败(模块,'openAIResponsesApi')
__esModule=True

default={
    'createProvider':createProvider,'createModels':createModels,
    'getSupportedThinkingLevels':getSupportedThinkingLevels,'isContextOverflow':isContextOverflow,
    'builtinProviders':builtinProviders,'getBuiltinModels':getBuiltinModels,
    'getBuiltinProviders':getBuiltinProviders,'anthropicMessagesApi':anthropicMessagesApi,
    'openAICompletionsApi':openAICompletionsApi,'openAIResponsesApi':openAIResponsesApi,
}
