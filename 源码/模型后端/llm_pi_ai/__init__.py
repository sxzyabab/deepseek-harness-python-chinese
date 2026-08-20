"""通用 pi-ai 后端 LLM 适配器插件。

对齐上游 `llm-pi-ai/src/index.ts`。公开面仅中文名；无英文别名。
一个插件实例拥有一份提供方路由字典；点名已安装 pi-ai 提供方的路由继承该提供方的端点、协议与模型目录作为默认，pi-ai 没有运来的路由则直接声明。
"""
import llm#语言模型服务
from launch_environment import 取启动环境#启动环境快照
from settings import json深度相等,安装设置段,设置命名空间#JSON 相等、设置段安装与命名空间
from .适配器 import 派爱适配器#适配器类
from .目录 import 目录提供方标识列表,目录提供方接受密钥#目录路由与密钥方法判定
from .配置 import 配置模式,断言可服务,解析配置表#配置模式、可服务断言与解析
from .发现 import 发现模型#模型发现
from .提供方 import 受支持协议#受支持协议

__all__=(#仅中文公开名；无英文别名
    '名称','注入','设置空间','配置模式','派爱适配器','受支持协议',
    '路由键','登记事实','目录条目','应用','默认',
)#公开面结束

名称='llm-pi-ai'#插件名（字面量不译）
注入=['llm']#依赖 llm 服务
设置空间=设置命名空间('llm-pi-ai')#设置命名空间

def 路由键(项):#取出可比较事实上的路由键
    """取出可比较事实上的路由键。"""
    return 项['provider']#路由

def 登记事实(配置表):#注册表按路由捕获的可比较事实
    """注册表按路由捕获这些；这里的变更必须重新注册。"""
    条目=[]#可比较事实
    for 提供方,配置项 in 配置表.items():#按路由收展示名与重试政策，这两项变了必须重新注册
        条目.append({
            'provider':提供方,#路由
            'displayName':配置项['displayName'],#展示名
            'retryPolicy':配置项['retryPolicy'],#重试政策
        })#一条事实
    条目.sort(key=路由键)#按路由排序
    return 条目#已排序事实

def 目录条目(配置表):#可配置提供方目录
    """可配置提供方目录：能认证的已安装目录路由，加上当前配置声明的每条路由。"""
    目录路由=list(目录提供方标识列表())#已安装目录路由
    目录集合=set(目录路由)#成员资格
    条目表={}#去重后的条目
    def 声明(提供方,展示名):#声明一条目录条目
        """声明一条目录条目。"""
        条目表[提供方]={
            'provider':提供方,#路由键
            'displayName':展示名,#展示名
            'settingsNs':设置空间,#设置命名空间
            'settingsPath':['providers',提供方],#设置路径
            'declared':提供方 not in 目录集合,#是否仅因配置而认识
        }#目录条目
    for 提供方 in 目录路由:#已安装目录路由：只有声明了密钥方法的才广告到配置面
        if 目录提供方接受密钥(提供方):#仅 OAuth、不接受密钥的路由不予广告
            声明(提供方,提供方)#声明
    for 提供方,配置项 in 配置表.items():#配置已声明的路由一律进目录，覆盖同名目录项的展示名
        声明(提供方,配置项['displayName'])#声明
    return list(条目表.values())#目录条目

def 应用(上下文,配置):#为所有已配置提供方路由注册通用 pi-ai 适配器
    """为所有已配置提供方路由注册一个通用 pi-ai 适配器。"""
    def 读入口():#组合入口配置源
        """组合入口配置源。"""
        return 配置#入口配置
    当前=读入口#当前配置源
    上次原始=None#上次原始快照
    已记住=None#记住的已解析配置
    def 配置表():#当前配置的已解析配置，按原始快照身份记住
        """当前配置的已解析配置，按原始快照身份记住。"""
        nonlocal 上次原始,已记住#缓存
        原始=当前()#当前原始配置
        if 原始 is 上次原始 and 已记住 is not None:#同一份原始快照则复用已解析结果，避免每请求重解析
            return 已记住#复用
        提供方们=原始.get('providers') if isinstance(原始,dict) else None#原始路由字典
        下一份=解析配置表(提供方们)#显式解析
        上次原始=原始#记下原始
        已记住=下一份#记下成功
        return 下一份#新配置
    配置表()#加载时先解析一次
    def 解析密钥(提供方,配置项):#按配置解析密钥
        """按配置解析密钥。"""
        引用=配置项.get('apiKeyEnv')#本配置的引用
        if 引用 is None:#不点名 apiKeyEnv 则交还 pi-ai 自己的环境发现
            return None#回落
        凭证=上下文.取('credentials')#可选凭证服务
        if 凭证 is not None:#有凭证缝则只走凭证服务，不再读启动环境
            命中=凭证.解析(引用)#解析引用
            if 命中 is None:#引用未写入凭证平面
                值=None#没有值
            elif isinstance(命中,dict):#命中是映射，读 value 键
                值=命中.get('value')#引用值
            else:#命中是对象，读 value 属性
                值=getattr(命中,'value',None)#引用值
        else:#没有凭证缝，启动环境就是整块凭证平面
            环境项=取启动环境(上下文).取(引用)#环境层
            if 环境项 is None:#环境里没有这个引用
                值=None#没有值
            elif isinstance(环境项,dict):#环境项是映射
                值=环境项.get('value')#环境值
            else:#环境项是对象
                值=getattr(环境项,'value',None)#环境值
        if 值 is not None and len(值)>0:#拿到非空值才判定可用；空串当缺失
            return llm.断言可用接口密钥(值,'llm-pi-ai',引用)#判定
        raise llm.大模型错误(
            'llm-pi-ai: no credential for provider route "'+提供方+'"; its profile resolves '+str(引用)+', which is not'
            +' set — store '+str(引用)+' through the credentials service (the web Models page writes it) or export it,'
            +' and remove apiKeyEnv only if this provider should authenticate from pi-ai\'s own environment discovery',
            'MISSING_CREDENTIAL',
        )#缺失凭证
    def 解析附件():#可选附件服务
        """可选附件服务。"""
        return 上下文.取('attachments')#附件
    适配器=派爱适配器({
        'profiles':配置表,#按请求解析配置
        'resolveApiKey':解析密钥,#按配置解析密钥
        'resolveAttachments':解析附件,#可选附件服务
    })#构造适配器
    目录句柄=None#目录句柄
    目录事实=None#上次目录事实
    def 确保目录():#目录变了则就地替换
        """目录变了则就地替换。"""
        nonlocal 目录句柄,目录事实#句柄与事实
        条目=目录条目(配置表())#当前目录
        if json深度相等(条目,目录事实):#目录内容没变则不换句柄
            return#不替换
        if 目录句柄 is None:#第一次挂可配置提供方目录
            目录句柄=上下文.llm.注册可配置提供方(条目)#初次注册
        else:#已有句柄则原子替换，避免先拆后挂的空窗
            目录句柄.替换(条目)#原子替换
        目录事实=条目#记下新事实
    确保目录()#加载时先挂目录
    def 已存密钥(提供方):#已点名路由已经解析到的凭证
        """已点名路由已经解析到的凭证。"""
        if 提供方 is None:#发现请求没点名路由，没有已存密钥可回落
            return None#没有
        配置项=配置表().get(提供方)#当前配置
        if 配置项 is None:#当前配置没有这条路由
            return None#没有
        return 解析密钥(提供方,配置项)#按配置解析
    def 发现回调(请求):#询问端点是针对草稿的配置时动作
        """询问端点是针对草稿的配置时动作。"""
        if isinstance(请求,dict):#发现请求是映射，读 provider 键
            提供方=请求.get('provider')#草稿路由
        else:#发现请求是对象，读 provider 属性
            提供方=getattr(请求,'provider',None)#草稿路由
        def 取已存():#已存密钥闭包
            """已存密钥闭包。"""
            return 已存密钥(提供方)#按路由
        return 发现模型(请求,取已存)#发现
    上下文.llm.注册模型发现(设置空间,发现回调)#注册发现
    登记=None#适配器句柄
    已登记事实=None#上次注册事实
    def 确保登记事实():#路由或政策变了则就地替换
        """路由或政策变了则就地替换。"""
        nonlocal 登记,已登记事实#句柄与事实
        事实=登记事实(配置表())#当前捕获事实
        if json深度相等(事实,已登记事实):#路由集与政策都没变则不换句柄
            return#不替换
        路由=list(配置表().keys())#当前路由
        if 登记 is None:#尚未注册过适配器
            if len(路由)==0:#空路由集不注册空适配器，只记住空事实
                已登记事实=事实#记下空事实
                return#不注册
            登记=上下文.llm.注册适配器(路由,适配器)#初次注册
        else:#已有句柄则就地替换路由集
            登记.替换(路由)#原子替换
        已登记事实=事实#记下新事实
    确保登记事实()#加载时先挂路由
    def 设源(源):#替换配置源
        """替换配置源。"""
        nonlocal 当前#配置源
        当前=源#此后配置表()读设置
    def 变更时():#变更时刷新注册
        """变更时刷新注册。"""
        try:#刷新已注册路由；失败则保住先前路由，不把半截替换留给调用方
            确保登记事实()#就地替换
        except Exception as 错误:#交换被拒绝
            上下文.logger.error('llm-pi-ai: keeping the previously registered routes after a refused update')#保住先前路由
            上下文.logger.error(错误)#附带错误
        try:#刷新可配置提供方目录；失败同样保住先前目录
            确保目录()#就地替换
        except Exception as 错误:#交换被拒绝
            上下文.logger.error('llm-pi-ai: keeping the previous configurable-provider directory after a refused update')#保住先前目录
            上下文.logger.error(错误)#附带错误
    安装设置段(上下文,设置空间,配置模式,配置,{
        'validate':断言可服务,#设置缝钩子字段字面量；写入时校验可服务
        'setSource':设源,#设置缝钩子字段字面量
        'onChange':变更时,#设置缝钩子字段字面量；变更时刷新注册
    })#安装设置段

默认=应用#中文默认导出
