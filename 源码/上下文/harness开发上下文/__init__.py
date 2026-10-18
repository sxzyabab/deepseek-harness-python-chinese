'告诉模型当前 harness 检出位置和网页界面地址。值只走运行时上下文'
import json#检出路径与网址按 JSON 字符串写入上下文
import os#从本文件上溯到检出根

包名='@deepseek-ai/dsh-harness-dev-context'#npm 包名
名称='harness-dev-context'#Cordis 插件名
依赖=['systemPrompt','sessionProjections','webApp']#提示词、投影与网页应用
检出根=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','..'))#源码包上溯到中文仓库根
检出上下文名='harness:source'#检出说明与运行时上下文的稳定名
网页表面上下文名='app:web-surface'#网页界面说明与运行时上下文的稳定名
既往提示投影键='harnessDevLegacyPrompt'#会话已接纳段落的投影键
检出指导=('The checkout location and current working directory are separate values and may differ; '
    'never infer the working directory from the checkout path. Use pwd to determine the current working directory. '
    'Use this checkout only to inspect or extend DSH itself.')#当前检出说明，模型可见字面量
检出提示='The runtime context names the DeepSeek Harness implementation checkout. '+检出指导#不含路径的提示段
网页指导=('When the user refers to "this page", "this GUI", or "this app" without naming another target, they mean this GUI. '
    'The browser provides no implicit DOM, route, or screenshot context. '
    'The client-plugin HMR receiver is active, but client-plugin changes reload without a refresh only while '
    '`pnpm run dev:web` is also running from this same checkout to rebuild their bundles; verify that watcher before promising automatic updates. '
    'Every other change — the apps/web shell and plain packages — requires rebuilding the affected Web artifacts and verifying this existing URL after a page refresh. '
    'Starting another server does not update this GUI. '
    'The apps/web Vite entry builds the shell but is not a standalone application because only dsh web injects window.__DSH_BOOT__. '
    'Do not start a replacement server unless the user asks; if one is needed, use a managed background job and verify its exact URL.')#当前网页说明
网页提示='You are interacting with the user through the DeepSeek Harness Web GUI whose URL the runtime context names. '+网页指导#不含网址的提示段
既往检出={'prefix':'The DeepSeek Harness implementation checkout is at ',
    'suffix':'. The checkout location and current working directory are separate values and may differ; '
        'never infer the working directory from this path. Use pwd to determine the current working directory. '
        'Use this checkout only to inspect or extend DSH itself.'}#已发布会话里嵌过路径的固定前后文
既往网页={'prefix':'You are interacting with the user through the DeepSeek Harness Web GUI at ',
    'suffix':'. '+网页指导}#已发布会话里嵌过网址的固定前后文
一无所有={'source':None,'web':None}#还没有接纳过带值段落

def 既往段落(提示,前后文):
    '前后文之间的一整行，没有或跨行则空'
    起点=提示.find(前后文['prefix'])#前缀
    if 起点<0:#没有这段
        return None#空
    终点=提示.find(前后文['suffix'],起点+len(前后文['prefix']))#后缀
    if 终点<0:#不成对
        return None#空
    段落=提示[起点:终点+len(前后文['suffix'])]#整段
    if '\n' in 段落:#必须单行
        return None#跨行不算
    return 段落#命中

def 折叠既往提示(状态,事件):
    '只把单块非空系统文本折进已接纳段落，其它事件保持原状态'
    if 事件['type']!='system/message':#不是系统消息
        return 状态#原样
    内容=事件['data']['message']['content']#内容块
    if len(内容)!=1:#不是单一块
        return 状态#保持
    块=内容[0]#唯一块
    if 块['type']!='text' or 块['text']=='':#空或非文本
        return 状态#保持
    检出=既往段落(块['text'],既往检出)#检出段
    网页=既往段落(块['text'],既往网页)#网页段
    if 检出==状态['source'] and 网页==状态['web']:#没有变化
        return 状态#同一对象
    return {'source':检出,'web':网页}#新状态

def 初始既往():
    '投影初值：检出段和网页段都还没有'
    return dict(一无所有)#拷贝，避免登记方改到常量

def 应用(上下文):
    '登记两段说明、对应运行时上下文，以及会话已接纳段落的投影'
    def 已接纳(组装):
        '本会话已接纳的带值段落；没有会话则两边都空'
        智能体=组装['agent'] if isinstance(组装,dict) and 'agent' in 组装 else getattr(组装,'agent',None)#组装上的智能体
        会话=None if 智能体 is None else getattr(智能体,'session',None)#会话
        if 会话 is None:#没有会话
            return 一无所有#空
        return 上下文.sessionProjections.状态(会话,既往提示投影键)#已登记，必有状态
    def 检出段文本(组装):
        '已接纳的检出段优先，否则用不含路径的说明'
        段落=已接纳(组装)['source']#已接纳
        return 检出提示 if 段落 is None else 段落#空则说明
    def 网页段文本(组装):
        '已接纳的网页段优先，否则用不含网址的说明'
        段落=已接纳(组装)['web']#已接纳
        return 网页提示 if 段落 is None else 段落#空则说明
    def 网页地址文本():
        '当前网页界面地址'
        return 'Current DeepSeek Harness Web GUI URL: '+json.dumps(上下文.webApp.getAdvertisedUrl())+'.'#当前网址
    上下文.sessionProjections.登记({
        'key':既往提示投影键,#投影键
        'stateVersion':1,#版本
        'init':初始既往,#初值
        'apply':折叠既往提示,#折叠
    })
    上下文.systemPrompt.section({
        'name':检出上下文名,#段名
        'order':上下文.systemPrompt.getSectionOrder('HARNESS_SOURCE'),#顺序槽
        'interpolate':False,#不插值
        'text':检出段文本,#已接纳原文优先
    })
    上下文.systemPrompt.context({
        'name':检出上下文名,#上下文名
        'order':上下文.systemPrompt.getContextOrder('HARNESS_SOURCE'),#顺序槽
        'interpolate':False,#不插值
        'text':'Current DeepSeek Harness implementation checkout: '+json.dumps(检出根)+'.',#当前检出
    })
    上下文.systemPrompt.section({
        'name':网页表面上下文名,#段名
        'order':上下文.systemPrompt.getSectionOrder('WEB_SURFACE'),#顺序槽
        'interpolate':False,#不插值
        'text':网页段文本,#已接纳原文优先
    })
    上下文.systemPrompt.context({
        'name':网页表面上下文名,#上下文名
        'order':上下文.systemPrompt.getContextOrder('WEB_SURFACE'),#顺序槽
        'interpolate':False,#不插值
        'text':网页地址文本,#当前网址
    })

__all__=['包名','名称','依赖','应用','默认']
默认=应用#框架槽
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=默认#框架槽
