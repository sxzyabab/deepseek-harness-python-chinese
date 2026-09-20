"""向 web 注册 DeepSeek 搜索提供方；复用 DEEPSEEK_API_KEY 但不复用 DEEPSEEK_BASE_URL。"""
from ...依赖.schemastery import 字符串字段,整数字段
from ...凭据.凭据 import 凭证引用
from ...配置.配置 import 安装设置段,设置命名空间
from ...工具.启动环境 import 取启动环境
from .提供方 import (
    DeepSeek搜索提供方,
    默认接口版本,
    默认基址,
    默认最大令牌,
    默认最大使用次数,
    默认模型,
)

__all__=['包名','名称','依赖','应用','默认','配置模式']

默认密钥环境='DEEPSEEK_API_KEY'
搜索基址环境='DEEPSEEK_SEARCH_BASE_URL'#有意区别于 chat-completions 的 DEEPSEEK_BASE_URL
网页搜索深度求索设置命名空间=设置命名空间('web-search-deepseek')

包名='@deepseek-ai/dsh-web-search-deepseek'
名称='web-search-deepseek'
依赖=['web']

配置模式={
    'apiKey':字符串字段(),#字面量密钥；优先用 apiKeyEnv，以免密钥进入配置文件
    'apiKeyEnv':字符串字段(默认值=默认密钥环境),#每次搜索解析的凭证引用
    #写在模式里而不只在使用点：配置面渲染已解析段，模式未携带的默认值在那里会读成完全没有值。
    'baseURL':字符串字段(),#Anthropic 兼容端点基址；会接上 /messages；无模式默认
    'model':字符串字段(默认值=默认模型),#Anthropic 格式模型名
    'apiVersion':字符串字段(默认值=默认接口版本),#anthropic-version 头
    'maxTokens':整数字段(默认值=默认最大令牌),#Messages 请求生成 token 上限
    'maxUses':整数字段(默认值=默认最大使用次数),#每次请求最多使用 web_search 的次数
}#插件配置（全部可选——应用 填环境变量与常量默认值）

def 解析选项(上下文,配置):#把已解析段投影成提供方下次搜索所用的选项
    """环境回退留在这里而不是提供方里：它读到的每个值都已经完全套上默认。"""
    密钥环境名=配置['apiKeyEnv'] if 'apiKeyEnv' in 配置 else None#配置里的引用
    if 密钥环境名 is None:#缺省
        密钥环境名=默认密钥环境#默认 DEEPSEEK_API_KEY
    密钥引用=凭证引用(密钥环境名)#规范化密钥引用
    字面量=配置['apiKey'] if 'apiKey' in 配置 else None#字面量密钥
    字面量密钥=字面量 if (字面量 is not None and len(字面量)>0) else None#非空才采用
    def 解析密钥():#每次搜索解析密钥
        """有凭证服务则走凭证解析；否则环境就是整个凭证平面。"""
        凭证=上下文.获取服务('credentials')
        if 凭证 is not None:
            命中=凭证.解析(密钥引用)
            if 命中 is not None:
                return 命中['value']
            return None
        环境项=取启动环境(上下文).取(密钥引用)
        if 环境项 is not None:
            环境值=环境项['value']
            if 环境值 is not None and len(环境值)>0:
                return 环境值
        return None
    def 记请求(请求):
        """派发前立刻记录不含密钥的精确请求。"""
        代理=上下文.获取服务('agents')
        if 代理 is None:
            return
        发起方=代理.当前发起方()
        if 发起方 is None:
            return
        发起方.session.追加('web/deepseek-search-llm-request',请求)
    基址=配置['baseURL'] if 'baseURL' in 配置 else None
    if 基址 is None:
        环境项=取启动环境(上下文).取(搜索基址环境)
        基址=环境项['value'] if 环境项 is not None else None
    if 基址 is None:
        基址=默认基址
    模型=配置['model'] if 'model' in 配置 else None
    if 模型 is None:
        模型=默认模型
    接口版本=配置['apiVersion'] if 'apiVersion' in 配置 else None
    if 接口版本 is None:
        接口版本=默认接口版本
    最大令牌=配置['maxTokens'] if 'maxTokens' in 配置 else None
    if 最大令牌 is None:
        最大令牌=默认最大令牌
    最大使用=配置['maxUses'] if 'maxUses' in 配置 else None
    if 最大使用 is None:
        最大使用=默认最大使用次数
    选项={
        'resolveApiKey':解析密钥,
        'apiKeyEnv':密钥引用,
        'baseURL':基址,
        'model':模型,
        'apiVersion':接口版本,
        'maxTokens':最大令牌,
        'maxUses':最大使用,
        'recordRequest':记请求,
    }
    if 字面量密钥 is not None:
        选项['apiKey']=字面量密钥
    return 选项

def 应用(上下文,配置):
    """安装 DeepSeek 搜索提供方。注册不携带已解析值：提供方按次搜索投影该段，已提交的改动无需重新注册。"""
    def 读入口():
        """组合入口配置源。"""
        return 配置
    当前=读入口
    def 设源(源):
        """之后按源读取。"""
        nonlocal 当前
        当前=源
    def 变更时():
        """文档变化时没有从源派生、需要重建的东西。"""
        return
    安装设置段(上下文,网页搜索深度求索设置命名空间,配置模式,配置,{
        'setSource':设源,
        'onChange':变更时,
    })
    def 选项thunk():
        """按当前权威段投影提供方选项。"""
        return 解析选项(上下文,当前())
    上下文.web.注册搜索提供方(DeepSeek搜索提供方(选项thunk))

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
Config=配置模式#框架槽
default=默认#框架槽
