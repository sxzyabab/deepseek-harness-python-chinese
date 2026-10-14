from .消息铬 import 格式化延迟秒,格式化运行时长,格式化每秒令牌#时长与吞吐
from .令牌格式 import 格式化缓存命中百分比,格式化精确令牌,格式化令牌#token 格式
from .消息项 import 打开列

__all__=['回合用量面板','回合时间面板']#仅中文公开名

面板边距=12#视口边距
面板间隙=8#触发器间隙

from nicegui import ui as 界面

def 恒等翻译(键,参数=None):
    '无文案表时返回键本身'
    return 键#键即文案

def 紧凑计数(值,翻译):
    'message.turnUsage.count'
    return 翻译('message.turnUsage.count',{'count':格式化令牌(值,翻译)})#紧凑

def 精确计数(值,翻译):
    '精确模板'
    return 翻译('message.turnUsage.count',{'count':格式化精确令牌(值,翻译)})#精确

def 路由标签(路由):
    'provider/model。路由为 dict'
    供应=路由['provider'] if 'provider' in 路由 else None#供应
    模型=路由['model'] if 'model' in 路由 else None#模型
    return str(供应)+'/'+str(模型)#串

class 回合用量面板:
    '数据库胶囊 + 锚定对话框结构'
    def __init__(自身,属性=None):
        '记下合成 props'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.打开=False#开合
        自身.根=None#列

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性 if 属性 is not None else {}#新

    def 切换(自身):
        '翻转开合'
        自身.打开=not 自身.打开#翻

    def 渲染(自身):
        '用量面板'
        属性=自身.属性#props
        用量=属性['usage'] if 'usage' in 属性 and 属性['usage'] is not None else {}#用量
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        总量令牌=用量['totalTokens'] if 'totalTokens' in 用量 and 用量['totalTokens'] is not None else 0#总量
        输出=用量['outputTokens'] if 'outputTokens' in 用量 and 用量['outputTokens'] is not None else 0#输出
        缓存读=用量['cacheReadTokens'] if 'cacheReadTokens' in 用量 else None#缓存读
        命中=None if 缓存读 is None else 格式化缓存命中百分比(缓存读,总量令牌-输出,1)#命中
        路由列表=用量['routes'] if 'routes' in 用量 and 用量['routes'] is not None else []#路由
        路由段=[]
        for 路由 in 路由列表:
            路由段.append(路由标签(路由))
        路由串=', '.join(路由段)#串
        未=用量['uncachedInputTokens'] if 'uncachedInputTokens' in 用量 and 用量['uncachedInputTokens'] is not None else 0#未
        读=用量['cacheReadTokens'] if 'cacheReadTokens' in 用量 and 用量['cacheReadTokens'] is not None else 0#读
        写=用量['cacheWriteTokens'] if 'cacheWriteTokens' in 用量 and 用量['cacheWriteTokens'] is not None else 0#写
        行列表=[
            {'label':翻译('message.turnUsage.input'),'value':精确计数(未+读+写,翻译)},
            {'label':翻译('message.turnUsage.output'),'value':精确计数(输出,翻译)},
        ]
        def 点切换():
            '展开或收起用量明细。'
            自身.切换()
            自身.渲染()
        with 打开列(自身,'回合用量面板'):
            自身.根.style(f'margin-top:{面板间隙}px')
            界面.button(翻译('message.turnUsage.consumed',{'total':紧凑计数(总量令牌,翻译)}),on_click=点切换)
            if 自身.打开 is not True:
                return
            with 界面.card().classes('用量卡').style(f'margin:{面板边距}px'):
                界面.label(翻译('message.turnUsage.title')).classes('标题')
                if 命中 is not None:
                    界面.label(翻译('message.turnUsage.cacheHit')+' '+str(命中))
                if 路由串=='':
                    界面.label(翻译('message.turnUsage.model'))
                else:
                    界面.label(翻译('message.turnUsage.model')+' '+路由串)
                for 行 in 行列表:
                    with 界面.row():
                        界面.label(行['label'])
                        界面.label(行['value'])

    def __call__(自身,属性=None):
        '对齐'
        if 属性 is not None:
            自身.更新(属性)#刷
        自身.渲染()#画

class 回合时间面板:
    '墙钟 + TTFT/吞吐详情'
    def __init__(自身,属性=None):
        '记下合成 props'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.打开=False#开合
        自身.根=None#列

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性 if 属性 is not None else {}#新

    def 切换(自身):
        '翻转开合'
        自身.打开=not 自身.打开#翻

    def 渲染(自身):
        '时间面板'
        属性=自身.属性#props
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        运行毫秒=属性['runMs'] if 'runMs' in 属性 and 属性['runMs'] is not None else 0#墙钟
        吞吐=属性['tokensPerSecond'] if 'tokensPerSecond' in 属性 else None#吞吐
        首令=属性['ttftMs'] if 'ttftMs' in 属性 else None#TTFT
        行列表=[{'label':翻译('message.turnTime.duration'),'value':格式化运行时长(运行毫秒,翻译)}]
        if 首令 is not None:#有 TTFT
            行列表.append({'label':翻译('message.turnTime.ttft'),'value':格式化延迟秒(首令)})
        if 吞吐 is not None:#有吞吐
            行列表.append({'label':翻译('message.turnTime.speed'),'value':格式化每秒令牌(吞吐)})
        def 点切换():
            '展开或收起用时明细。'
            自身.切换()
            自身.渲染()
        with 打开列(自身,'回合时间面板'):
            界面.button(格式化运行时长(运行毫秒,翻译),on_click=点切换)
            if 自身.打开 is not True:
                return
            with 界面.card().classes('时间卡'):
                界面.label(翻译('message.turnTime.title')).classes('标题')
                for 行 in 行列表:
                    with 界面.row():
                        界面.label(行['label'])
                        界面.label(行['value'])

    def __call__(自身,属性=None):
        '对齐'
        if 属性 is not None:
            自身.更新(属性)#刷
        自身.渲染()#画
