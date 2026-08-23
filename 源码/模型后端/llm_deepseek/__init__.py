"""在 ctx.llm 上为 deepseek-official 提供方路由注册 DeepSeek 适配器。

对齐上游 `llm-deepseek/src/index.ts`。公开面仅中文名；无英文别名。
连接事实按请求解析而不是在加载时冻结：插件把它的 cordis.yml 条目配置叠在可选的 llm-deepseek 用户设置段下，并经可选凭证 seam 解析 API 密钥。唯一在注册时捕获的事实——重试政策——在变更时就地重新注册该路由。
"""
from math import isfinite as 是否有限#有限数判断
from ...依赖 import schemastery#外部依赖胶水
模式=schemastery.模式#配置校验库
from ..llm import (
    断言可用接口密钥,#密钥判定
    大模型错误,#LLM错误
    解析重试政策,#政策解析
    重试政策模式,#政策模式
)#导入 llm 词表
from ..凭据 import 凭证引用#凭证引用工厂
from ..启动环境 import 取启动环境#启动环境快照
from ..配置 import json深度相等,安装设置段,设置命名空间#JSON相等、设置段安装与命名空间
from ..超时 import 定时器延迟上限毫秒#定时器延迟上限
from ..匿名用户标识 import 获取或创建匿名用户标识#匿名用户id（内置相对导入）
from .适配器 import (
    默认上下文窗口,#默认窗口
    默认最大令牌,#默认输出上限
    默认流空闲超时毫秒,#默认空闲超时
    深求适配器,#适配器类
)#适配器模块
from .类型 import (#再导出线路类型
    线路请求,#线路请求
    线路系统消息,#系统消息
    线路用户消息,#用户消息
    线路工具消息,#工具消息
    线路助手消息,#助手消息
    线路消息,#消息联合
    线路工具调用,#工具调用
    线路工具,#工具
    线路块,#SSE块
    线路选择,#选择
    线路增量,#增量
    线路工具调用增量,#工具增量
    线路用量,#用量
    线路错误,#错误体
)#类型再导出结束

__all__=(#仅中文公开名；无英文别名
    '名称','注入','配置','应用','默认',
    '设置空间','公开基址','解析适配器选项','解析模型目录',
    '默认上下文窗口','默认最大令牌','默认流空闲超时毫秒','深求适配器',
    '线路请求','线路系统消息','线路用户消息','线路工具消息',
    '线路助手消息','线路消息','线路工具调用','线路工具',
    '线路块','线路选择','线路增量','线路工具调用增量',
    '线路用量','线路错误',
)#公开面结束

名称='llm-deepseek'#插件名（字面量不译）
注入=['llm']#依赖 llm 服务
设置空间=设置命名空间('llm-deepseek')#设置命名空间
默认接口密钥环境='DEEPSEEK_API_KEY'#默认密钥环境变量
提供方='deepseek-official'#官方路由名
最大安全整数=9007199254740991#Number.MAX_SAFE_INTEGER
最小正数=5e-324#Number.MIN_VALUE
默认模型列表=[
    {'id':'deepseek-v4-flash','name':'DeepSeek-V4-Flash','contextWindow':默认上下文窗口},#Flash
    {'id':'deepseek-v4-pro','name':'DeepSeek-V4-Pro','contextWindow':默认上下文窗口},#Pro
]#默认建议目录
目录模型=模式.对象({
    'id':模式.字符串().必填(),#必需id
    'name':模式.字符串(),#可选名
    'description':模式.字符串(),#可选描述
    'contextWindow':模式.数字().步进(1).最小(1),#正整数窗口
    'maxTokens':模式.数字().步进(1).最小(1),#正整数上限
})#目录条目模式
配置=模式.对象({
    'apiKeyEnv':模式.字符串().角色('credential-ref').默认(默认接口密钥环境),#密钥引用
    'baseURL':模式.字符串(),#基址
    'thinking':模式.联合([模式.常量('enabled'),模式.常量('disabled')]),#思考开关
    'reasoningEffort':模式.联合([模式.常量('off'),模式.常量('high'),模式.常量('max')]),#力度
    'maxTokens':模式.数字().步进(1).最小(1).最大(最大安全整数).默认(默认最大令牌),#输出上限
    'defaultContextWindow':模式.数字().步进(1).最小(1).默认(默认上下文窗口),#默认窗口
    'models':模式.数组(目录模型).默认(默认模型列表),#目录
    'streamIdleTimeoutMs':模式.数字().最小(最小正数).最大(定时器延迟上限毫秒).默认(默认流空闲超时毫秒),#空闲超时
    'retryPolicy':重试政策模式,#重试政策
})#配置运行时模式
公开基址='https://api.deepseek.com'#公开API默认
基址环境='DEEPSEEK_BASE_URL'#基址环境变量

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 是整数(值):#对应 Number.isInteger
    """对应 Number.isInteger。"""
    if type(值) is int:#整数
        return True#整数
    if isinstance(值,float) and 值.is_integer():#整值浮点
        return True#整值浮点
    return False#非整数

def 是正整数(值):#正整数
    """正整数（含整值浮点）。"""
    return 是整数(值) and 值>0#正

def 是正安全整数(值):#正安全整数
    """对应 Number.isSafeInteger 且为正。"""
    return 是正整数(值) and int(值)<=最大安全整数#正安全整数

def 解析模型目录(模型列表):#解析建议目录
    """解析、校验并拆离建议模型目录。"""
    已见=set()#已见id
    结果=[]#拆离后的目录
    for 模型 in (模型列表 if 模型列表 is not None else 默认模型列表):#逐条
        if len(模型['id'])==0:#id空
            raise Exception('llm-deepseek: catalog model ids must be non-empty')#id不得空
        if 取字段(模型,'name') is not None and len(模型['name'])==0:#名给了但是空
            raise Exception('llm-deepseek: catalog model "'+模型['id']+'" has an empty name')#名非法
        if 取字段(模型,'contextWindow') is not None and not 是正整数(模型['contextWindow']):#窗口非法
            raise Exception('llm-deepseek: catalog model "'+模型['id']+'" contextWindow must be a positive integer')#窗口非法
        if 取字段(模型,'maxTokens') is not None and not 是正整数(模型['maxTokens']):#上限非法
            raise Exception('llm-deepseek: catalog model "'+模型['id']+'" maxTokens must be a positive integer')#上限非法
        if 模型['id'] in 已见:#id重复
            raise Exception('llm-deepseek: duplicate catalog model "'+模型['id']+'"')#id重复
        已见.add(模型['id'])#记下已见
        条目={'id':模型['id']}#拆离条目
        if 取字段(模型,'name') is not None:#有名
            条目['name']=模型['name']#有名才带上
        if 取字段(模型,'description') is not None:#有描述
            条目['description']=模型['description']#有描述才带上
        if 取字段(模型,'contextWindow') is not None:#有窗口
            条目['contextWindow']=模型['contextWindow']#有窗口才带上
        if 取字段(模型,'maxTokens') is not None:#有上限
            条目['maxTokens']=模型['maxTokens']#有上限才带上
        结果.append(条目)#收下
    return 结果#已校验目录

def 解析适配器选项(原始配置,环境=None):#解析连接事实
    """从原始配置到已校验连接事实的那一次显式解析步骤。"""
    if 取字段(原始配置,'thinking')=='disabled' and 取字段(原始配置,'reasoningEffort') is not None and 取字段(原始配置,'reasoningEffort')!='off':#禁用思考却给了非off力度
        raise Exception('llm-deepseek: only reasoningEffort "off" can be configured when thinking is disabled')#禁用思考时只能off
    if 取字段(原始配置,'defaultContextWindow') is not None and not 是正整数(原始配置['defaultContextWindow']):#窗口非法
        raise Exception('llm-deepseek: defaultContextWindow must be a positive integer')#窗口非法
    if 取字段(原始配置,'maxTokens') is not None and not 是正安全整数(原始配置['maxTokens']):#上限非法
        raise Exception('llm-deepseek: maxTokens must be a positive safe integer')#上限非法
    空闲超时=原始配置['streamIdleTimeoutMs'] if 取字段(原始配置,'streamIdleTimeoutMs') is not None else 默认流空闲超时毫秒#空闲超时或默认
    if not 是否有限(空闲超时) or 空闲超时<=0 or 空闲超时>定时器延迟上限毫秒:#空闲超时非法
        raise Exception('llm-deepseek: streamIdleTimeoutMs must be a positive finite number no greater than '+str(定时器延迟上限毫秒))#空闲超时非法
    if 取字段(原始配置,'baseURL') is not None:#配置基址
        基址=原始配置['baseURL']#配置基址
    else:#回落环境或公开
        环境项=环境.取(基址环境) if 环境 is not None else None#受信环境
        if 环境项 is not None:#有环境项
            基址=环境项['value']#环境基址
        else:#公开默认
            基址=公开基址#公开默认
    return {
        'apiKeyEnv':凭证引用(原始配置['apiKeyEnv'] if 取字段(原始配置,'apiKeyEnv') is not None else 默认接口密钥环境),#凭证引用
        'baseURL':基址,#基址
        'defaults':{
            'thinking':取字段(原始配置,'thinking'),#开关
            'reasoningEffort':取字段(原始配置,'reasoningEffort'),#力度
        },#思考默认
        'maxTokens':原始配置['maxTokens'] if 取字段(原始配置,'maxTokens') is not None else 默认最大令牌,#输出上限
        'defaultContextWindow':原始配置['defaultContextWindow'] if 取字段(原始配置,'defaultContextWindow') is not None else 默认上下文窗口,#默认窗口
        'models':解析模型目录(取字段(原始配置,'models')),#目录
        'streamIdleTimeoutMs':空闲超时,#空闲超时
        'retryPolicy':解析重试政策(取字段(原始配置,'retryPolicy'),'llm-deepseek: retryPolicy'),#解析政策
    }#已校验事实

def 应用(上下文对象,原始配置=None):#加载插件
    """加载插件：按请求解析连接事实并注册路由。"""
    if 原始配置 is None:#未传配置
        原始配置={}#空配置
    def 读入口():#组合入口配置源
        """组合入口配置源。"""
        return 原始配置#入口配置
    当前=读入口#当前配置源
    上次原始=None#上次原始快照
    上次成功=None#上次成功解析
    def 选项():#按请求解析连接事实
        """按请求解析连接事实。"""
        nonlocal 上次原始,上次成功#缓存
        原始=当前()#当前原始配置
        if 原始 is 上次原始 and 上次成功 is not None:#同一快照则复用
            return 上次成功#复用
        try:#解析
            下一份=解析适配器选项(原始,取启动环境(上下文对象))#显式解析
            上次原始=原始#记下原始
            上次成功=下一份#记下成功
            return 下一份#新事实
        except Exception as 错误:#解析失败
            if 上次成功 is None:#加载时没有上次成功则失败
                raise 错误#失败
            上次原始=原始#记下坏快照以免每请求都报
            上下文对象.logger.error('llm-deepseek: keeping the last good configuration after an invalid settings section')#保留上次成功
            上下文对象.logger.error(错误)#附带错误
            return 上次成功#继续用上次成功
    选项()#加载时先解析一次，失败则大声
    def 解析接口密钥(连接):#按快照解析密钥
        """按快照解析密钥。"""
        引用=连接['apiKeyEnv']#本快照的引用
        凭证=上下文对象.获取服务('credentials')#可选凭证服务
        if 凭证 is not None:#有seam
            命中=凭证.解析(引用)#解析引用
            if 命中 is not None:#命中
                return 断言可用接口密钥(命中['value'],'llm-deepseek',引用)#命中则判定
        else:#没有seam
            环境项=取启动环境(上下文对象).取(引用)#环境层
            if 环境项 is not None and len(环境项['value'])>0:#有非空值
                return 断言可用接口密钥(环境项['value'],'llm-deepseek',引用)#判定
        缺密钥文案='llm-deepseek: no API key for provider route "'+提供方+'"; store '+str(引用)+' through the credentials service (the web Models page writes it), or export '+str(引用)+' in the launching environment'#缺失凭证文案
        raise 大模型错误(缺密钥文案,'MISSING_CREDENTIAL')#缺失凭证
    用户标识=None#惰性匿名id
    def 解析用户标识():#首次签发后复用
        """首次签发后复用。"""
        nonlocal 用户标识#惰性
        if 用户标识 is None:#尚未签发
            用户标识=获取或创建匿名用户标识()#签发
        return 用户标识#匿名id
    适配器=深求适配器({'选项':选项,'解析接口密钥':解析接口密钥,'解析用户标识':解析用户标识})#构造适配器
    上下文对象.llm.注册可配置提供方([
        {'provider':提供方,'displayName':'DeepSeek','settingsNs':设置空间,'settingsPath':[]},#官方路由
    ])#声明可配置提供方
    登记=上下文对象.llm.注册适配器([提供方],适配器)#注册路由
    已登记政策=选项()['retryPolicy']#注册时捕获的政策
    def 确保登记事实():#政策变了则就地替换
        """政策变了则就地替换。"""
        nonlocal 已登记政策#捕获的政策
        政策=选项()['retryPolicy']#当前政策
        if json深度相等(政策,已登记政策):#没变
            return#没变
        登记.替换([提供方])#就地替换同一路由
        已登记政策=政策#记下新政策
    def 设源(源):#替换配置源
        """替换配置源。"""
        nonlocal 当前#配置源
        当前=源#此后选项()读设置
    安装设置段(上下文对象,设置空间,配置,原始配置,{
        'setSource':设源,#设置缝钩子字段字面量
        'onChange':确保登记事实,#变更时刷新注册捕获的政策
    })#安装设置段

默认=应用#默认导出该插件入口（中文名；无英文 default 别名）
