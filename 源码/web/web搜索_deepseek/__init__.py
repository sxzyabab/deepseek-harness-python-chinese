"""在 ctx.web 注册 DeepSeek 后端提供方。它调用带原生 web_search_20250305 的 Anthropic 兼容 Messages API。提供方复用 DEEPSEEK_API_KEY 但不复用 DEEPSEEK_BASE_URL，因为搜索与 chat-completions 使用不同基址。"""
from schemastery import 模式#配置校验
from credentials import 凭证引用#凭证引用工厂
from settings import 安装设置段,设置命名空间#设置段安装与命名空间
from launch_environment import 取启动环境#启动环境快照
from cordis.工具 import 是否thenable#可等待判定
from .提供方 import (
    DeepSeek搜索提供方,#DeepSeek 搜索提供方类
    默认接口版本,#默认 anthropic-version
    默认基址,#默认搜索端点基址
    默认最大令牌,#默认生成上限
    默认最大使用次数,#默认 web_search 使用次数
    默认模型,#默认模型名
    提供方标识,#提供方稳定 id
    引用摘要映射,#从 citation 抽摘要
    映射人机响应,#响应映射
)#提供方实现

默认密钥环境='DEEPSEEK_API_KEY'#默认密钥环境变量名
搜索基址环境='DEEPSEEK_SEARCH_BASE_URL'#命名本提供方端点的环境变量；有意区别于 chat-completions 的 DEEPSEEK_BASE_URL
网页搜索深度求索设置命名空间=设置命名空间('web-search-deepseek')#承载本提供方端点、模型与密钥引用的设置命名空间

名称='web-search-deepseek'#loader 诊断所用的 Cordis 插件名
注入=['web']#本提供方注册进去的 web seam
name=名称#Cordis插件名
inject=注入#Cordis依赖声明

配置模式=模式.对象({
    'apiKey':模式.字符串().角色('secret'),#字面量密钥；优先用 apiKeyEnv，以免密钥进入配置文件
    'apiKeyEnv':模式.字符串().角色('credential-ref').默认(默认密钥环境),#每次搜索解析的凭证引用
    #写在模式里而不只在使用点：配置面渲染已解析段，模式未携带的默认值在那里会读成完全没有值。
    'baseURL':模式.字符串(),#Anthropic 兼容端点基址；会接上 /messages；无模式默认
    'model':模式.字符串().默认(默认模型),#Anthropic 格式模型名
    'apiVersion':模式.字符串().默认(默认接口版本),#anthropic-version 头
    'maxTokens':模式.数字().步进(1).最小(1).默认(默认最大令牌),#Messages 请求生成 token 上限
    'maxUses':模式.数字().步进(1).最小(1).默认(默认最大使用次数),#每次请求最多使用 web_search 的次数
})#插件配置（全部可选——应用 填环境变量与常量默认值）
Config=配置模式#Cordis 配置模式

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺席#缺席
    return getattr(对象,键,缺省)#对象属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 解析选项(上下文对象,配置):#把已解析段投影成提供方下次搜索所用的选项
    """环境回退留在这里而不是提供方里：它读到的每个值都已经完全套上默认。"""
    密钥环境名=取字段(配置,'apiKeyEnv')#配置里的引用
    if 密钥环境名 is None:#缺省
        密钥环境名=默认密钥环境#默认 DEEPSEEK_API_KEY
    密钥引用=凭证引用(密钥环境名)#规范化密钥引用
    字面量=取字段(配置,'apiKey')#字面量密钥
    字面量密钥=字面量 if (字面量 is not None and len(字面量)>0) else None#非空才采用
    def 解析密钥():#每次搜索解析密钥
        """有凭证 seam 则走凭证解析；否则环境就是整个凭证平面。"""
        凭证=上下文对象.取('credentials')#可选凭证服务
        if 凭证 is not None:#有 seam
            命中=解开(凭证.解析(密钥引用))#解析引用（承诺则等待）
            if 命中 is not None:#命中
                return 取字段(命中,'value')#返回值
            return None#未配置
        环境项=取启动环境(上下文对象).取(密钥引用)#从启动环境取
        if 环境项 is not None:#有环境项
            环境值=取字段(环境项,'value')#环境值
            if 环境值 is not None and len(环境值)>0:#非空才返回
                return 环境值#环境值
        return None#缺席
    def 记请求(请求):#把发出的 LLM 请求记入会话
        """派发前立刻记录不含密钥的精确请求。"""
        代理=上下文对象.取('agents')#可选智能体服务
        if 代理 is None:#没有 agents
            return#无法记日志
        发起方=代理.当前发起方()#当前发起方
        if 发起方 is None:#没有发起边界
            return#无法记日志
        发起方.session.追加('web/deepseek-search-llm-request',请求)#预派发日志事件
    基址=取字段(配置,'baseURL')#配置基址优先
    if 基址 is None:#配置未给
        环境项=取启动环境(上下文对象).取(搜索基址环境)#搜索专用环境变量
        基址=取字段(环境项,'value') if 环境项 is not None else None#环境值
    if 基址 is None:#再否则默认搜索基址
        基址=默认基址#默认 Messages 基址
    模型=取字段(配置,'model')#配置模型
    if 模型 is None:#缺省
        模型=默认模型#默认模型
    接口版本=取字段(配置,'apiVersion')#配置 API 版本
    if 接口版本 is None:#缺省
        接口版本=默认接口版本#默认版本
    最大令牌=取字段(配置,'maxTokens')#配置生成上限
    if 最大令牌 is None:#缺省
        最大令牌=默认最大令牌#默认上限
    最大使用=取字段(配置,'maxUses')#配置使用次数
    if 最大使用 is None:#缺省
        最大使用=默认最大使用次数#默认次数
    选项={#提供方选项
        'resolveApiKey':解析密钥,#每次搜索解析密钥
        'apiKeyEnv':密钥引用,#密钥引用名
        'baseURL':基址,#已套默认的基址
        'model':模型,#模型
        'apiVersion':接口版本,#API 版本
        'maxTokens':最大令牌,#生成上限
        'maxUses':最大使用,#使用次数
        'recordRequest':记请求,#日志钩子
    }#选项骨架
    if 字面量密钥 is not None:#有字面量才带上
        选项['apiKey']=字面量密钥#字面量密钥
    return 选项#一次搜索的选项

def 应用(上下文对象,配置):#向 ctx.web 注册 DeepSeek 搜索提供方
    """安装 DeepSeek 搜索提供方。注册不携带已解析值：提供方按次搜索投影该段，已提交的改动无需重新注册。"""
    def 读入口():#组合入口配置源
        """组合入口配置源。"""
        return 配置#入口配置
    当前=读入口#当前权威段读取器
    def 设源(源):#设置权威源
        """之后按源读取。"""
        nonlocal 当前#配置源
        当前=源#切换
    def 变更时():#提交变更时空操作
        """文档变化时没有从源派生、需要重建的东西。"""
        return#空变更钩子
    安装设置段(上下文对象,网页搜索深度求索设置命名空间,配置模式,配置,{
        'setSource':设源,#切换权威配置源
        'onChange':变更时,#空变更钩子
    })#设置段安装结束
    def 选项thunk():#按当前段投影选项
        """按当前权威段投影提供方选项。"""
        return 解析选项(上下文对象,当前())#投影
    上下文对象.web.注册搜索提供方(DeepSeek搜索提供方(选项thunk))#按当前段注册提供方

apply=应用#Cordis插件入口
default=应用#默认导出
默认=应用#中文默认导出
