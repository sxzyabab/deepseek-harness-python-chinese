"""发给 LLM 提供方的静态公开应用身份。

对齐上游 `llm/src/attribution.ts`。公开面仅中文名；无英文别名。
产品／版本／url 字面量保持上游。
"""

__all__=('版本','应用身份','用户代理','归属头')#仅中文公开名

版本='0.1.0-rc.5'#来自本包清单，绝不手抄漂移

应用身份={#Harness 默认身份
    'product':'deepseek-harness',#产品记号
    'version':版本,#来自本包清单
    'url':'https://github.com/deepseek-ai/deepseek-harness',#仓库主页
}#身份结束

def 用户代理(身份=None):#渲染 User-Agent 头值
    """标准 User-Agent 值：product/version (+url)。"""
    if 身份 is None:#省略则默认
        身份=应用身份#默认 Harness 身份
    return 身份['product']+'/'+身份['version']+' (+'+身份['url']+')'#product/version (+url)

def 归属头(身份=None):#构造归属头
    """构造适配器在每条提供方请求上必须发送的归属头。"""
    if 身份 is None:#省略不能压制归属
        身份=应用身份#默认 Harness 身份
    return {'user-agent':用户代理(身份)}#目前只发 user-agent
