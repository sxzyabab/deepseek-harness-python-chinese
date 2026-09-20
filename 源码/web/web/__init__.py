"""web 访问服务：搜索与抓取注册表，及按提供方选择的执行。"""
import os
from ...依赖.schemastery import 字符串字段
from ...依赖 import cordis
服务=cordis.服务
from .类型 import (
    网络错误,
    网络搜索请求字段,
    网络搜索结果字段,
    网络搜索来源字段,
    网络抓取请求字段,
    网络抓取结果字段,
    网络抓取正文种类,
    网络搜索提供方字段,
    网络抓取提供方字段,
)

__all__=[
    '包名','名称','默认','网络','网络错误',
    '网络搜索请求字段','网络搜索结果字段','网络搜索来源字段',
    '网络抓取请求字段','网络抓取结果字段','网络抓取正文种类',
    '网络搜索提供方字段','网络抓取提供方字段',
    '搜索提供方环境键','抓取提供方环境键','网络运行时配置字段',
]

搜索提供方环境键='DSH_WEB_SEARCH_PROVIDER'
抓取提供方环境键='DSH_WEB_FETCH_PROVIDER'
网络运行时配置字段=('searchProvider','fetchProvider')
包名='@deepseek-ai/dsh-web'
名称='web'

def 解析提供方(选择):
    """解析出选定提供方，或抛出对应的网络错误。选择从不依赖注册顺序。"""
    配置标识=选择['configuredId'] if 'configuredId' in 选择 else None
    注册表=选择['providers']
    if 配置标识 is not None:
        提供方=注册表[配置标识] if 配置标识 in 注册表 else None
        if 提供方 is None:
            raise 网络错误('configured web provider "'+str(配置标识)+'" is not registered','WEB_PROVIDER_CONFIGURED_MISSING')
        if 提供方.available() is not True:
            raise 网络错误('configured web provider "'+str(配置标识)+'" is registered but unavailable','WEB_PROVIDER_CONFIGURED_UNAVAILABLE')
        return 提供方
    可用列表=[]
    for 提供方 in 注册表.values():
        if 提供方.available() is True:
            可用列表.append(提供方)
    if len(可用列表)==0:
        raise 网络错误('no usable web provider is registered','WEB_PROVIDER_UNAVAILABLE')
    if len(可用列表)>1:
        标识拼接=', '.join([str(方.id) for 方 in 可用列表])
        raise 网络错误('multiple usable web providers are registered ('+标识拼接+'); configure one explicitly','WEB_PROVIDER_AMBIGUOUS')
    return 可用列表[0]

def 截断来源(结果,上限):
    """对搜索结果强制 maxResults：截断 sources[] 并打标记。"""
    来源列表=list(结果['sources'])
    if 上限 is None or len(来源列表)<=上限:
        return 结果
    下一={'sources':来源列表[:上限],'truncated':True}
    if 'content' in 结果:#有内容则保留，缺席不加键
        下一['content']=结果['content']
    return 下一

class 网络运行时(服务):
    """web 访问服务（每个上下文一个实例）。

选择语义（执行时解析，从不依赖顺序）：
- 已配置 id 且已注册且 available() → 该提供方
- 已配置 id 未注册 → WEB_PROVIDER_CONFIGURED_MISSING
- 已配置 id 已注册但不可用 → WEB_PROVIDER_CONFIGURED_UNAVAILABLE
- 未配置 id，恰好一个已注册可用提供方 → 该提供方
- 未配置 id，多个可用提供方 → WEB_PROVIDER_AMBIGUOUS
- 未配置 id，没有可用提供方 → WEB_PROVIDER_UNAVAILABLE
"""
    Config={
        'searchProvider':字符串字段(),
        'fetchProvider':字符串字段(),
    }

    def __init__(自身,ctx,配置=None):
        """以 web 名注册服务。环境变量 DSH_WEB_*_PROVIDER 与配置字段等价，不是隐藏优先级链。"""
        super().__init__(ctx,'web')
        if 配置 is None:
            配置={}
        搜索标识=配置['searchProvider'] if 'searchProvider' in 配置 else None
        if 搜索标识 is None:
            搜索标识=os.environ[搜索提供方环境键] if 搜索提供方环境键 in os.environ else None
        抓取标识=配置['fetchProvider'] if 'fetchProvider' in 配置 else None
        if 抓取标识 is None:
            抓取标识=os.environ[抓取提供方环境键] if 抓取提供方环境键 in os.environ else None
        自身.搜索提供方标识=搜索标识
        自身.抓取提供方标识=抓取标识
        自身.搜索提供方表={}
        自身.抓取提供方表={}

    def 注册搜索提供方(自身,提供方):
        """注册搜索提供方。id 已占用则抛 WEB_DUPLICATE_PROVIDER。返回拆除器。"""
        return 自身.注册提供方(自身.搜索提供方表,提供方)

    def 注册抓取提供方(自身,提供方):
        """注册抓取提供方。id 已占用则抛 WEB_DUPLICATE_PROVIDER。返回拆除器。"""
        return 自身.注册提供方(自身.抓取提供方表,提供方)

    def 注册提供方(自身,表,提供方):
        """写入一张提供方注册表。id 已占用则拒绝；纤程销毁时注销。"""
        标识=提供方.id
        if 标识 in 表:
            raise 网络错误('a web provider with id "'+str(标识)+'" is already registered','WEB_DUPLICATE_PROVIDER')
        def 挂上():
            """写入注册表并在拆除时删除。"""
            表[标识]=提供方
            def 摘掉():
                """销毁时从注册表删除。"""
                表.pop(标识,None)
            return 摘掉
        释放=自身.ctx.副作用(挂上,'web.registerProvider()')
        def 同步拆除():
            """丢掉副作用返回值的同步拆除。"""
            释放()
        return 同步拆除

    def 搜索(自身,请求,信号=None):
        """经选定提供方跑一次搜索；强制 request.maxResults，多返回则截断 sources[] 并置 truncated。"""
        选择={'providers':自身.搜索提供方表}
        if 自身.搜索提供方标识 is not None:
            选择['configuredId']=自身.搜索提供方标识
        提供方=解析提供方(选择)
        结果=提供方.search(请求,信号)
        return 截断来源(结果,请求['maxResults'] if 'maxResults' in 请求 else None)

    def 抓取(自身,请求,信号=None):
        """经选定提供方检索一个 URL。非 2xx 响应是结果，不是抛错。"""
        选择={'providers':自身.抓取提供方表}
        if 自身.抓取提供方标识 is not None:
            选择['configuredId']=自身.抓取提供方标识
        提供方=解析提供方(选择)
        return 提供方.fetch(请求,信号)

网络=网络运行时
默认=网络运行时
name=名称#框架槽
default=默认#框架槽
