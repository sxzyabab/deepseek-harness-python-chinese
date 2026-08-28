"""web 访问能力缝（`ctx.web`）的 Service Definition：搜索与抓取的注册表以及按提供方选择的执行。重复 id 会被拒绝。执行时必须有已配置且可用的提供方；没有配置时恰好需要一个可用提供方，选择从不依赖注册顺序。"""
import os#读取运行覆盖环境变量
from ...依赖.schemastery import 路径上节点,字符串字段,枚举字段#配置字段
from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#导入Cordis服务基类
是否thenable=cordis.工具.是否thenable#可等待判定
from .类型 import (
    网络错误,#结构化web错误
    网络搜索请求字段,#搜索请求词汇
    网络搜索结果字段,#搜索结果词汇
    网络搜索来源字段,#搜索来源词汇
    网络抓取请求字段,#抓取请求词汇
    网络抓取结果字段,#抓取结果词汇
    网络抓取正文种类,#抓取正文种类
    网络搜索提供方字段,#搜索提供方词汇
    网络抓取提供方字段,#抓取提供方词汇
)#再导出公开类型

__all__=[#公开面
    '网络','默认','网络错误',
    '网络搜索请求字段','网络搜索结果字段','网络搜索来源字段',
    '网络抓取请求字段','网络抓取结果字段','网络抓取正文种类',
    '网络搜索提供方字段','网络抓取提供方字段',
    '搜索提供方环境键','抓取提供方环境键','网络运行时配置字段',
]#结束

搜索提供方环境键='DSH_WEB_SEARCH_PROVIDER'#搜索提供方运行覆盖环境变量
抓取提供方环境键='DSH_WEB_FETCH_PROVIDER'#抓取提供方运行覆盖环境变量
网络运行时配置字段=('searchProvider','fetchProvider')#缝配置：显式搜索/抓取提供方id，省略则恰好一个可用时自动选

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 解析提供方(选择):#按选择规则解析出选定提供方
    """解析出选定提供方，或抛出对应的网络错误。已配置 id 且已注册且 available() 为真则用该提供方；已配置未注册抛 WEB_PROVIDER_CONFIGURED_MISSING；已配置不可用抛 WEB_PROVIDER_CONFIGURED_UNAVAILABLE；未配置且恰好一个可用则自动选；未配置且多个可用抛 WEB_PROVIDER_AMBIGUOUS；未配置且没有可用抛 WEB_PROVIDER_UNAVAILABLE。"""
    配置标识=取字段(选择,'configuredId')#钉死的提供方id，缺席表示未配置
    注册表=取字段(选择,'providers')#该能力种类已注册的提供方映射
    if 配置标识 is not None:#钉死了id
        提供方=注册表.get(配置标识)#按id查找
        if 提供方 is None:#未注册
            raise 网络错误('configured web provider "'+str(配置标识)+'" is not registered','WEB_PROVIDER_CONFIGURED_MISSING')#配置了但不在表里
        检查=取字段(提供方,'available')#本地可用性检查
        if not 检查():#不可用
            raise 网络错误('configured web provider "'+str(配置标识)+'" is registered but unavailable','WEB_PROVIDER_CONFIGURED_UNAVAILABLE')#在表里但available为假
        return 提供方#用钉死的提供方
    可用们=[]#当前可用的提供方
    for 提供方 in 注册表.values():#遍历注册表，不依赖顺序做选择，仅收集可用集合
        检查=取字段(提供方,'available')#本地可用性检查
        if 检查():#当前可用
            可用们.append(提供方)#收入可用集合
    if len(可用们)==0:#一个都没有
        raise 网络错误('no usable web provider is registered','WEB_PROVIDER_UNAVAILABLE')#没有可用提供方
    if len(可用们)>1:#多于一个，不能靠注册顺序猜
        标识们=', '.join([str(取字段(方,'id')) for 方 in 可用们])#列出id
        raise 网络错误('multiple usable web providers are registered ('+标识们+'); configure one explicitly','WEB_PROVIDER_AMBIGUOUS')#要求显式配置
    return 可用们[0]#恰好一个，自动选这一个

def 截断来源(结果,上限):#按上限截断搜索来源
    """对搜索结果强制 maxResults：截断 sources[] 并打标记。没有上限或未超则原样返回；切开时置 truncated 为真。"""
    来源们=list(取字段(结果,'sources'))#可引用来源列表
    if 上限 is None or len(来源们)<=上限:#没有上限或未超
        return 结果#原样返回
    下一={'sources':来源们[:上限],'truncated':True}#切开并标截断
    内容=取字段(结果,'content')#可选提供方生成文本
    if 内容 is not None:#有内容则保留
        下一['content']=内容#写入内容
    return 下一#截断后的结果

class 网络运行时(服务):#web访问服务，注册为ctx.web
    """web 访问服务。注册为 `ctx.web`（每个上下文一个实例）。

选择语义（执行时解析，从不依赖顺序）：
- 已配置 id 且已注册且 available() → 该提供方
- 已配置 id 未注册 → WEB_PROVIDER_CONFIGURED_MISSING
- 已配置 id 已注册但不可用 → WEB_PROVIDER_CONFIGURED_UNAVAILABLE
- 未配置 id，恰好一个已注册可用提供方 → 该提供方
- 未配置 id，多个可用提供方 → WEB_PROVIDER_AMBIGUOUS
- 未配置 id，没有可用提供方 → WEB_PROVIDER_UNAVAILABLE
"""
    Config=路径上节点({#提供方选择配置schema，无默认值
        'searchProvider':字符串字段(),#可选搜索提供方id
        'fetchProvider':字符串字段(),#可选抓取提供方id
    })#schema结束

    def __init__(自身,ctx,配置=None):#构造运行时
        """以 web 名注册服务。运行环境覆盖喂进同一组字段：`$DSH_WEB_SEARCH_PROVIDER` / `$DSH_WEB_FETCH_PROVIDER` 等价于 searchProvider / fetchProvider，不是隐藏的优先级链。"""
        super().__init__(ctx,'web')#以web名注册服务
        if 配置 is None:#缺省空配置
            配置={}#空配置
        搜索标识=取字段(配置,'searchProvider')#配置里的搜索提供方id
        if 搜索标识 is None:#配置未给出
            搜索标识=os.environ.get(搜索提供方环境键)#否则读环境变量
        抓取标识=取字段(配置,'fetchProvider')#配置里的抓取提供方id
        if 抓取标识 is None:#配置未给出
            抓取标识=os.environ.get(抓取提供方环境键)#否则读环境变量
        自身.搜索提供方标识=搜索标识#钉死的搜索id，可为None
        自身.抓取提供方标识=抓取标识#钉死的抓取id，可为None
        自身.搜索提供方们={}#搜索提供方注册表
        自身.抓取提供方们={}#抓取提供方注册表

    def 登记搜索提供方(自身,提供方):#注册搜索提供方
        """注册搜索提供方。id 已为搜索注册过则抛网络错误 WEB_DUPLICATE_PROVIDER。返回 disposer；随调用 fiber 销毁。"""
        return 自身.登记提供方(自身.搜索提供方们,提供方)#写入搜索表

    def 登记抓取提供方(自身,提供方):#注册抓取提供方
        """注册抓取提供方。id 已为抓取注册过则抛网络错误 WEB_DUPLICATE_PROVIDER。返回 disposer；随调用 fiber 销毁。"""
        return 自身.登记提供方(自身.抓取提供方们,提供方)#写入抓取表

    def 登记提供方(自身,表,提供方):#写入一张注册表
        """写入一张提供方注册表。id 已占用则拒绝；按 effect 注册，fiber 销毁时注销。"""
        标识=取字段(提供方,'id')#提供方稳定id，作注册表键
        if 标识 in 表:#id已占用
            raise 网络错误('a web provider with id "'+str(标识)+'" is already registered','WEB_DUPLICATE_PROVIDER')#拒绝重复
        def 挂上():#按effect注册
            """写入注册表并在拆除时删除。"""
            表[标识]=提供方#写入
            def 摘掉():#销毁时删除
                """销毁时从注册表删除。"""
                表.pop(标识,None)#删除
            return 摘掉#拆除器
        释放=自身.ctx.effect(挂上,'web.registerProvider()')#effect名
        def 同步拆除():#同步即发即忘的disposer
            """丢掉 effect 返回值的同步拆除。"""
            释放()#拆除
        return 同步拆除#对外disposer

    def 搜索(自身,请求,信号=None):#执行搜索
        """经选定提供方跑一次搜索。调用时按选择规则解析提供方；能力跑不了则抛网络错误。缝对结果强制 request.maxResults：提供方多返回则截断 sources[] 并置 truncated。"""
        选择={'providers':自身.搜索提供方们}#选择输入：搜索表
        if 自身.搜索提供方标识 is not None:#有配置才带id
            选择['configuredId']=自身.搜索提供方标识#钉死的搜索id
        提供方=解析提供方(选择)#解析搜索提供方
        搜索函数=取字段(提供方,'search')#提供方搜索入口
        结果=解开(搜索函数(请求,信号))#交给提供方并解开承诺
        return 截断来源(结果,取字段(请求,'maxResults'))#按上限截断来源

    def 抓取(自身,请求,信号=None):#执行抓取
        """经选定提供方检索一个 URL。调用时按选择规则解析提供方；能力跑不了则抛网络错误。非 2xx 响应是结果，不是抛错。"""
        选择={'providers':自身.抓取提供方们}#选择输入：抓取表
        if 自身.抓取提供方标识 is not None:#有配置才带id
            选择['configuredId']=自身.抓取提供方标识#钉死的抓取id
        提供方=解析提供方(选择)#解析抓取提供方
        抓取函数=取字段(提供方,'fetch')#提供方抓取入口
        return 解开(抓取函数(请求,信号))#交给提供方并解开承诺

默认=网络运行时#默认导出服务类
default=网络运行时#Cordis默认导出
