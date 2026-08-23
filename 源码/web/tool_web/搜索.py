"""面向模型的 `web_search` 工具：在网上发现当前信息。执行走 `ctx.web`——本模块只负责面向模型的 schema、参数校验、结果条数上限和结果格式化，从不做提供方选择或网络访问。"""
from urllib.parse import urlparse#从URL取主机名
from ..工具 import 定义工具#定义面向模型的工具
from ...依赖 import cordis#外部依赖胶水
已兑现=cordis.工具.已兑现#立刻兑现
是否thenable=cordis.工具.是否thenable#可等待判定

__all__=[#公开面
    '网络搜索最大结果数','应用网络搜索工具','格式化搜索输出',
    '解析搜索参数','呈现搜索调用','呈现搜索结果','搜索元自值','搜索元自结果',
]#结束

网络搜索最大结果数=8#搜索返回来源的默认上限
def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 缺席(对象,键):#字段是否缺席
    """对齐字段 === undefined。"""
    if 对象 is None:#空对象
        return True#缺席
    if isinstance(对象,dict):#映射
        return 键 not in 对象#无键则缺席
    return not hasattr(对象,键)#无属性则缺席

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 解析搜索参数(参数):#把参数收成缝的请求字段
    """校验 schema DSL 表达不了的约束：`query` 不能是空白。否则抛普通 Error。"""
    if len(取字段(参数,'query').strip())==0:#空白 query
        raise Exception('query must be a non-empty string')#空白 query 抛错
    return {'query':取字段(参数,'query')}#原样返回 query

def 来源标签(网址,标题):#选出展示用标签
    """来源的展示标签：有标题用标题，否则用主机名。"""
    if 标题 is not None and len(标题)>0:#有非空标题
        return 标题#用标题
    try:#从 URL 取主机名
        主机=urlparse(网址).hostname#合法 URL 用 hostname
        if 主机 is not None and len(主机)>0:#有主机名
            return 主机#用主机名
        return 网址#无主机名用原始字符串
    except Exception:#畸形 URL 用原始字符串
        return 网址#畸形 URL 用原始字符串

def 格式化搜索输出(结果):#拼面向模型的搜索文本
    """把搜索结果格式化成一块面向模型的文本。"""
    段们=[]#按段收集输出
    内容=取字段(结果,'content')#可选回答
    if 内容 is not None and len(内容)>0:#有回答
        段们.append(内容)#先放回答
    来源们=取字段(结果,'sources')#来源列表
    if 来源们 is None:#缺席当空
        来源们=[]#空列表
    if len(来源们)>0:#有来源列表
        行们=[]#每条来源一行 markdown
        for 来源 in 来源们:#逐条
            标签=来源标签(取字段(来源,'url'),取字段(来源,'title'))#展示标签
            元=[]#摘要与日期
            摘要=取字段(来源,'snippet')#可选摘要
            if 摘要 is not None and len(摘要)>0:#非空摘要
                元.append(摘要)#收下摘要
            日期=取字段(来源,'publishedAt')#可选日期
            if 日期 is not None and len(日期)>0:#非空日期
                元.append('('+日期+')')#括号日期
            后缀=(' — '+' '.join(元)) if len(元)>0 else ''#有元数据则接在链接后
            行们.append('- ['+标签+']('+取字段(来源,'url')+')'+后缀)#一条来源的 markdown
        段们.append('Sources:\n'+'\n'.join(行们))#来源段
    elif 内容 is None or len(内容)==0:#没有来源也没有回答
        段们.append('No results found.')#空结果提示，字面量不改
    if 取字段(结果,'truncated'):#被截断
        段们.append('(Showing the first '+str(len(来源们))+' sources. Refine the query for more.)')#截断提示
    段们.append('Cite the relevant URLs above as markdown links in your answer.')#引用说明，字面量不改
    return '\n\n'.join(段们)#段与段空一行

def 呈现搜索调用(参数):#进行中搜索卡片
    """进行中调用的展示：一张以查询为标题的搜索卡片。"""
    查询=取字段(参数,'query')#搜索查询
    return {'card':'generic','title':查询,'kind':'search','rawInput':查询}#标题与原始输入都是 query

def 投影来源(来源):#省略缺席可选字段的来源投影
    """把一条缝来源投影成普通对象，省略所有缺席的可选字段。"""
    出={'url':取字段(来源,'url')}#URL 必带
    if not 缺席(来源,'title'):#有标题才带
        出['title']=取字段(来源,'title')#标题
    if not 缺席(来源,'snippet'):#有摘要才带
        出['snippet']=取字段(来源,'snippet')#摘要
    if not 缺席(来源,'publishedAt'):#有日期才带
        出['publishedAt']=取字段(来源,'publishedAt')#日期
    return 出#投影对象

def 搜索元自值(值):#从结果值抽出展示 meta
    """把已校验的 `web_search` 输出值投影成可回放的展示 meta。"""
    投影们=[]#投影后的来源
    for 来源 in 取字段(值,'sources'):#逐条投影
        投影们.append(投影来源(来源))#收下
    出={#meta 对象
        'sources':投影们,#投影后的来源
        'truncated':取字段(值,'truncated'),#截断标记
    }#骨架
    if not 缺席(值,'content'):#有回答才带 answer
        出['answer']=取字段(值,'content')#回答
    return 出#meta

def 是否网络来源(值):#校验一条来源
    """`value` 是否为合法 WebSource（从不透明 `meta` 做收窄）。"""
    if not isinstance(值,dict) or 值 is None:#非普通对象
        return False#非法
    网址=取字段(值,'url')#url
    if not isinstance(网址,str):#url 必须是字符串
        return False#非法
    标题=取字段(值,'title') if not 缺席(值,'title') else None#可选标题
    摘要=取字段(值,'snippet') if not 缺席(值,'snippet') else None#可选摘要
    日期=取字段(值,'publishedAt') if not 缺席(值,'publishedAt') else None#可选日期
    if 标题 is not None and not isinstance(标题,str):#title 缺席或字符串
        return False#非法
    if 摘要 is not None and not isinstance(摘要,str):#snippet 缺席或字符串
        return False#非法
    if 日期 is not None and not isinstance(日期,str):#publishedAt 缺席或字符串
        return False#非法
    return True#合法来源

def 搜索元自结果(元):#校验回放 meta
    """把不透明的现场或回放结果元数据收窄为 WebSearchMeta。畸形元数据返回 None，展示可回退到通用卡片。"""
    if not isinstance(元,dict) or 元 is None:#非普通对象
        return None#畸形
    来源们=取字段(元,'sources')#来源列表
    截断=取字段(元,'truncated')#截断标记
    if not isinstance(来源们,list):#来源必须是列表
        return None#畸形
    for 项 in 来源们:#逐条校验
        if not 是否网络来源(项):#来源不合法
            return None#畸形
    if not isinstance(截断,bool):#truncated 必须是布尔
        return None#畸形
    if (not 缺席(元,'answer')) and (not isinstance(取字段(元,'answer'),str)):#answer 若在必须是字符串
        return None#畸形
    出={'sources':来源们,'truncated':截断}#已校验 meta
    if not 缺席(元,'answer'):#有回答才带
        出['answer']=取字段(元,'answer')#回答
    return 出#WebSearchMeta

def 呈现搜索结果(参数,结果):#完成态搜索卡片
    """已完成调用的展示：一张 `web` 搜索卡片，携带 `meta` 里忠实的结构化来源。"""
    if 取字段(结果,'isError'):#错误结果不画专用卡
        return None#通用卡
    元=搜索元自结果(取字段(结果,'meta'))#校验 meta
    if 元 is None:#畸形则交给通用卡
        return None#通用卡
    出={#专用 web 搜索卡
        'card':'web',#走 web 卡片
        'kind':'search',#搜索种类
        'title':取字段(参数,'query'),#查询作标题
        'sources':取字段(元,'sources'),#结构化来源
        'truncated':取字段(元,'truncated'),#截断标记
    }#骨架
    if not 缺席(元,'answer'):#有回答才带
        出['answer']=取字段(元,'answer')#回答
    return 出#视图对象

def 应用网络搜索工具(上下文,最大结果数,超时毫秒,抓取已启用):#注册 web_search 与提示词
    """注册 `web_search` 工具及其系统提示词指引。"""
    if 抓取已启用:#有 fetch 时推荐跟进 web_fetch
        指引='Use the web_search tool to discover current information on the web. It returns an optional answer plus a list of source URLs. Follow up with web_fetch when you need the full content of a specific result, and cite the relevant URLs as markdown links.'#有 fetch 的英文指引，字面量不改
    else:#无 fetch
        指引='Use the web_search tool to discover current information on the web. It returns an optional answer plus a list of source URLs. Use the returned source snippets when available, and cite the relevant URLs as markdown links.'#无 fetch 的英文指引，字面量不改
    上下文.systemPrompt.段落({#写入系统提示词段落
        'name':'tool:web_search',#段落名
        'order':110,#排序
        'text':指引,#面向模型指引
    })#提示词段落结束
    def 渲染(参数,值):#面向模型的文本块
        """把结构化结果渲染成文本块。"""
        return [{'type':'text','text':格式化搜索输出(值)}]#单个文本块
    def 展示元(参数,值):#回放用 meta
        """投影可回放展示 meta。"""
        return 搜索元自值(值)#展示 meta
    def 并发安全():#提供方读取不改变父 agent 状态
        """始终可并发。"""
        return True#安全
    def 执行(参数,执行上下文):#真正搜索
        """校验后交给 ctx.web.search。"""
        输入=解析搜索参数(参数)#校验 query 非空
        结果=解开(上下文.web.搜索(#交给能力缝
            {'query':取字段(输入,'query'),'maxResults':最大结果数},#查询与上限
            取字段(执行上下文,'signal'),#工具调用取消信号
        ))#search 结束
        投影们=[]#投影后的来源
        for 来源 in 取字段(结果,'sources'):#逐条投影
            投影们.append(投影来源(来源))#收下
        出={#规范输出值
            'sources':投影们,#投影后的来源
            'truncated':取字段(结果,'truncated'),#截断标记
        }#骨架
        if not 缺席(结果,'content'):#有回答才带 content
            出['content']=取字段(结果,'content')#回答
        return 已兑现(出)#兑现规范输出
    def 呈现结果(参数,结果):#完成态卡片
        """委托呈现搜索结果。"""
        return 呈现搜索结果(参数,结果)#完成态卡片
    上下文.tools.登记(定义工具({#注册 web_search 工具
        'name':'web_search',#工具名
        'description':'Search the web for current information. Returns an optional summary answer and a list of source URLs.',#工具描述，字面量不改
        'parameters':{#入参 schema
            'query':{'type':'string','required':True,'description':'The search query.'},#搜索查询
        },#parameters 结束
        'output':{#输出 schema 与渲染
            'schema':{#结果值 schema
                'type':'object',#对象
                'additionalProperties':False,#禁止多余字段
                'properties':{#字段
                    'content':{'type':'string'},#可选回答
                    'sources':{#来源数组
                        'type':'array',#数组
                        'required':True,#必填
                        'items':{#一条来源
                            'type':'object',#对象
                            'additionalProperties':False,#禁止多余字段
                            'properties':{#字段
                                'url':{'type':'string','required':True},#URL
                                'title':{'type':'string'},#可选标题
                                'snippet':{'type':'string'},#可选摘要
                                'publishedAt':{'type':'string'},#可选发布日期
                            },#properties 结束
                        },#items 结束
                    },#sources 结束
                    'truncated':{'type':'boolean','required':True},#是否截断
                },#properties 结束
            },#schema 结束
            'render':渲染,#面向模型的文本块
            'presentationMeta':展示元,#回放用 meta
        },#output 结束
        'timeoutMs':超时毫秒,#协作超时预算
        'isConcurrencySafe':并发安全,#提供方读取不改变父 agent 状态
        'execute':执行,#真正搜索
        'presentCall':呈现搜索调用,#进行中卡片
        'presentResult':呈现结果,#完成态卡片
    }))#register 结束
