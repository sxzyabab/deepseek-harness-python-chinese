"""`@earendil-works/pi-ai` 桩，含其 `/providers/all` 与 `/api/*.lazy` 子路径。

对齐上游 `webworker-runtime/src/node/external_packages/pi-ai.ts`。
文件名下划线：Python 无法 import 连字符模块名。
"""
from ..未实现失败 import 未实现失败#未实现桩

__all__=[#Node面
    'createProvider','createModels','getSupportedThinkingLevels','isContextOverflow',
    'builtinProviders','getBuiltinProviders','getBuiltinModels',
    'anthropicMessagesApi','openAICompletionsApi','openAIResponsesApi',
    '__esModule','default',
]#公开结束

模块='@earendil-works/pi-ai'#模块名
createProvider=未实现失败(模块,'createProvider')#createProvider桩
createModels=未实现失败(模块,'createModels')#createModels桩
getSupportedThinkingLevels=未实现失败(模块,'getSupportedThinkingLevels')#思考级别桩
isContextOverflow=未实现失败(模块,'isContextOverflow')#溢出谓词桩

内置提供方标识们=(#内置提供方id，按目录顺序
    'amazon-bedrock','ant-ling','anthropic','azure-openai-responses','baseten','cerebras',#批次1
    'cloudflare-ai-gateway','cloudflare-workers-ai','deepseek','fireworks','github-copilot',#批次2
    'google','google-vertex','groq','huggingface','kimi-coding','minimax','minimax-cn',#批次3
    'mistral','moonshotai','moonshotai-cn','nvidia','openai','openai-codex','opencode',#批次4
    'opencode-go','openrouter','qwen-token-plan','qwen-token-plan-cn',#批次5
    'qwen-token-plan-individual','together',#批次6
    'vercel-ai-gateway','xai','xiaomi','xiaomi-token-plan-ams','xiaomi-token-plan-cn',#批次7
    'xiaomi-token-plan-sgp','zai','zai-coding-cn',#批次8
)#内置提供方标识们结束

def builtinProviders():#目录提供方列表
    """已安装目录提供方，在 `llm-pi-ai` 激活时读取。"""
    return [{'id':标识,'name':标识,'auth':{'apiKey':{'type':'api-key'}},'models':[]} for 标识 in 内置提供方标识们]#映射条目

def getBuiltinProviders():#提供方id列表
    """已安装目录的提供方路由 id。"""
    return list(内置提供方标识们)#拷贝数组

def getBuiltinModels():#模型列表
    """某个已安装目录提供方的模型。"""
    return []#恒空

anthropicMessagesApi=未实现失败(模块,'anthropicMessagesApi')#Anthropic绑定桩
openAICompletionsApi=未实现失败(模块,'openAICompletionsApi')#completions绑定桩
openAIResponsesApi=未实现失败(模块,'openAIResponsesApi')#responses绑定桩
__esModule=True#CJS互操作

default={#默认导出
    'createProvider':createProvider,'createModels':createModels,#工厂
    'getSupportedThinkingLevels':getSupportedThinkingLevels,'isContextOverflow':isContextOverflow,#谓词
    'builtinProviders':builtinProviders,'getBuiltinModels':getBuiltinModels,#目录
    'getBuiltinProviders':getBuiltinProviders,'anthropicMessagesApi':anthropicMessagesApi,#模型与API
    'openAICompletionsApi':openAICompletionsApi,'openAIResponsesApi':openAIResponsesApi,#responses
}#默认导出结束
