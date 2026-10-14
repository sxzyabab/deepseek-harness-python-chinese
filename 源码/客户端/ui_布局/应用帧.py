import os
from nicegui import ui as 界面

from ...api.会话控制器.客户端 import 客户端会话服务,会话,会话事件流,页消息数
from ..ui_主题.客户端.样式 import 主题样式合计
from ..ui_侧边栏.客户端.侧栏壳 import 侧栏壳
from ..ui_侧边栏_右侧.客户端.壳.右栏壳 import 右栏壳
from ..ui_聊天.客户端.聊天.聊天视图 import 聊天视图
from ..ui_对话.客户端.输入栏 import 输入栏
from ..ui_对话.客户端.会话根 import 会话根
from ..ui_对话.客户端.文案 import 中文 as 对话文案
from ..ui_通用设置.设置根 import 准备页面设置
from ..ui_聊天.客户端.文案 import 中文 as 聊天文案
from ..ui_聊天.异常 import 页面失败文案
from ..ui_工作区.客户端.文案 import 中文 as 工作区文案
from ..ui_工作区.客户端.树 import 主会话标识
from ..ui_工作区.客户端.浏览区 import 工作区浏览区
from .列宽 import (
    中栏下限,侧栏折叠,侧栏默认,侧栏自动折叠,
    右侧栏下限,右侧栏最大比,右侧栏默认比,
    夹紧宽度,计算列宽,
)
from .存储 import 创建布局存储,初始布局状态
from .文档标题 import 文档标题
from .异常 import 布局错误
from .样式 import 页面网格样式,页面样式已登记,记下页面样式已登记

def 产品标题(译=None):
    '环境变量优先，否则用 brand.localBuild。'
    配置=os.environ.get('DSH_CLIENT_TITLE')
    if isinstance(配置,str) and 配置!='':
        return 配置
    if callable(译):
        词=译('brand.localBuild')
        if isinstance(词,str) and 词!='' and 词!='brand.localBuild':
            return 词
    return 'DSH 本地构建'

__all__=['挂载页面','打开页面','根帧']

def 标属性(元素,名,开):
    '开着就挂上数据属性，关掉就摘掉。选择器只认有没有这个属性。'
    if 开:
        元素.props(名)
        return
    元素.props(remove=名)

def 求解帧(几何):
    '按帧宽、侧栏偏好和右栏占轨求出网格模板。窄视口默认收起左栏。'
    视口=几何['viewportWidth']
    窄=视口<侧栏自动折叠
    收起=(not 几何['narrowExpanded']) if 窄 else 几何['sidebar']==0
    侧栏偏好=0 if 收起 else (侧栏默认 if 几何['sidebar']==0 else 几何['sidebar'])
    右值=几何['rightbar']
    右偏好=视口*右侧栏默认比 if 右值 is None else 右值
    正常侧=0 if (not 几何['rightbarShown']) and 窄 else 侧栏偏好
    正常=计算列宽(视口,正常侧,右偏好,侧栏折叠)
    右请求=右偏好 if 几何['rightbarTrack'] else 0
    列=计算列宽(视口,侧栏偏好,右请求,侧栏折叠)
    右最大=0 if 列['rightbar']==0 else 夹紧宽度(右偏好,右侧栏下限,视口*右侧栏最大比)
    中最小=0 if 列['rightbar']==0 else 中栏下限
    return {
        '收起':收起,
        '视口':视口,
        '正常':正常,
        '列':列,
        '模板':f'{列["sidebar"]}px minmax({中最小}px, 1fr) minmax(0px, {右最大}px)',
        '开关':f'{收起}:{几何["rightbarTrack"]}',
    }

def 套用列(帧,左柄,右柄,布局,界面状态,上次,拖拽中=False):
    '把求解结果写到网格、拖柄和左栏收起外观。视口一起变的开关不播轨道动画。'
    几何=布局['getSnapshot']()['layoutInfo']
    解=求解帧(几何)
    帧.style('grid-template-columns:'+解['模板']+';--dsh-rightbar-width:'+str(解['正常']['rightbar'])+'px')
    标属性(帧,'data-sidebar-collapsed',解['收起'])
    标属性(帧,'data-rightbar-collapsed',解['列']['rightbar']==0)
    标属性(帧,'data-rightbar-fullscreen',几何['rightbarFullscreen'] is True)
    标属性(帧,'data-rightbar-instant',几何['rightbarInstant'] is True)
    标属性(帧,'data-dragging',拖拽中)
    视口变了=上次['视口'] is not None and 上次['视口']!=解['视口']
    开关变了=上次['开关'] is not None and 上次['开关']!=解['开关']
    上次['视口']=解['视口']
    上次['开关']=解['开关']
    if 开关变了 and not 视口变了 and not 拖拽中:
        上次['代']=上次['代']+1
        代=上次['代']
        标属性(帧,'data-animating',True)
        def 收场(代=代):
            '超时后摘掉动画属性。中途又切换过则这一轮作废。'
            if 上次['代']!=代:
                return
            标属性(帧,'data-animating',False)
        界面.timer(0.6,收场,once=True)
    elif 拖拽中 or 几何['rightbarInstant'] is True or 几何['rightbarFullscreen'] is True:
        标属性(帧,'data-animating',False)
    界面状态['左栏收起']=解['收起']
    if '同步左栏' in 界面状态:
        界面状态['同步左栏'](解['收起'])
    左柄.style('left:'+str(解['列']['sidebar'])+'px')
    左柄.set_visibility(解['收起'] is not True)
    右左=解['视口']-解['正常']['rightbar']
    右柄.style('left:'+str(右左)+'px')
    右柄可见=几何['rightbarShown'] is True and 几何['rightbarFullscreen'] is not True and 解['正常']['rightbar']>0
    右柄.set_visibility(右柄可见)

def 绑定帧事件(帧,左柄,右柄):
    '在浏览器里量帧宽，并用指针捕获拖动两根分隔条。'
    帧号=帧.id
    左号=左柄.id
    右号=右柄.id
    界面.run_javascript(
        'const 取=(号)=>document.getElementById("c"+号)||document.getElementById(String(号));'
        f'const 帧=取({帧号!r});'
        'const 报=()=>{const 宽=Math.round(帧.getBoundingClientRect().width);if(宽>0) emitEvent("dsh-viewport",宽);};'
        '报();'
        'let 量帧=0;'
        'new ResizeObserver(()=>{if(量帧) return;量帧=requestAnimationFrame(()=>{量帧=0;报();});}).observe(帧);'
        'const 装=(号,侧)=>{'
        'const 柄=取(号);if(!柄) return;'
        'let 捕获=null;let 起点=0;let 基=0;let 拍=0;let 最新=0;'
        'const 结束=(事件)=>{'
        'if(捕获!==事件.pointerId) return;'
        'const 号针=捕获;捕获=null;'
        'if(拍){cancelAnimationFrame(拍);拍=0;}'
        'if(柄.hasPointerCapture(号针)) 柄.releasePointerCapture(号针);'
        'emitEvent("dsh-drag",{phase:"end",side:侧,px:最新});'
        '};'
        '柄.addEventListener("pointerdown",(事件)=>{'
        'if(事件.button!==0||捕获!==null) return;'
        '事件.preventDefault();'
        '柄.setPointerCapture(事件.pointerId);'
        '捕获=事件.pointerId;起点=事件.clientX;'
        'const 列=getComputedStyle(帧).gridTemplateColumns.split(" ").map(parseFloat);'
        '基=侧==="sidebar"?列[0]:列[2];最新=基;'
        'emitEvent("dsh-drag",{phase:"start",side:侧,px:基});'
        '});'
        '柄.addEventListener("pointermove",(事件)=>{'
        'if(捕获!==事件.pointerId) return;'
        'const 差=事件.clientX-起点;'
        '最新=侧==="sidebar"?基+差:基-差;'
        'if(拍) return;'
        '拍=requestAnimationFrame(()=>{拍=0;emitEvent("dsh-drag",{phase:"move",side:侧,px:最新});});'
        '});'
        '柄.addEventListener("pointerup",结束);'
        '柄.addEventListener("pointercancel",结束);'
        '柄.addEventListener("lostpointercapture",(事件)=>{if(捕获===事件.pointerId) 结束(事件);});'
        '};'
        f'装({左号!r},"sidebar");'
        f'装({右号!r},"rightbar");'
    )

def 确保样式():
    '主题令牌和页面网格用共享样式交给本进程之后的每个页面，只登记一次。'
    if 页面样式已登记():
        确保修补()
        return
    界面.add_css(主题样式合计, shared=True)
    界面.add_css(页面网格样式, shared=True)
    记下页面样式已登记()
    确保修补()

修补样式=(
    '.侧栏壳{--q-primary:#111827}'
    '.侧栏壳.收起{width:56px;max-width:56px;box-sizing:border-box;overflow:hidden;align-items:center}'
    '.侧栏壳.收起 button.q-btn:not(.设置罩 *){width:36px !important;min-width:36px !important;max-width:36px !important;padding:0 !important}'
    '.侧栏壳.收起 .设置导航 button.q-btn{width:100% !important;max-width:none !important;justify-content:flex-start}'
    '.侧栏壳 button.q-btn.text-primary,.侧栏壳 button.q-btn.text-primary .q-icon{color:#111827 !important}'
    'button.q-btn.发送钮{--q-primary:var(--dsw-alias-button-info-fill,#4176e6);width:34px !important;height:34px !important;min-width:34px !important;min-height:34px !important;padding:0 !important;background:var(--dsw-alias-button-info-fill,#4176e6) !important;color:#fff !important}'
    '.工具行{display:flex;width:100%;justify-content:flex-end;flex-wrap:nowrap}'
    '.尾组{display:flex;width:auto;margin-left:auto;justify-content:flex-end}'
    'button.q-btn.发送钮 svg,button.q-btn.发送钮 path{fill:currentColor !important;color:#fff !important}'
    'button.q-btn.浏览钮{--q-primary:#111827;width:28px !important;height:28px !important;min-height:28px !important;padding:0 !important;background:transparent !important;color:#111827 !important;box-shadow:none !important}'
)
def 确保修补():
    '按钮颜色每次挂载都写一遍。进程里旧的样式登记不会挡住这一段。'
    界面.add_css(修补样式)

def 套文案(词表,键,参数=None):
    '词表里有的句子才格式化。缺键时把键本身留在页面上。'
    文=词表[键] if isinstance(词表,dict) and 键 in 词表 else 键
    if not isinstance(文,str):
        return 键
    if isinstance(参数,dict) and '{' in 文:
        try:
            return 文.format(**参数)
        except (KeyError,ValueError,IndexError):
            return 文
    return 文

def 记录成节点(记录,序号):
    '一条会话日志变成聊天节点。键用序号和种类，同一次投递不会画出两行。'
    事件=None
    if isinstance(记录,dict) and isinstance(记录.get('event'),dict):
        事件=记录['event']
    elif isinstance(记录,dict):
        事件=记录
    else:
        事件={}
    序值=事件['seq'] if 'seq' in 事件 else 序号
    种类=事件['type'] if isinstance(事件.get('type'),str) and 事件['type']!='' else 'unknown'
    键=str(序值)+':'+种类
    锚=序值 if isinstance(序值,int) and not isinstance(序值,bool) else 序号
    return 键,{
        'key':键,
        'kind':种类,
        'visibility':'visible',
        'anchorSeq':锚,
        'data':事件['data'] if 'data' in 事件 else 事件,
    }

def 浏览器会话行(标识,行):
    '浏览区要的摘要。缺来源时按普通会话，避免子槽在读 origin 时崩掉。'
    源=行 if isinstance(行,dict) else {}
    标题=源['displayTitle'] if 'displayTitle' in 源 and isinstance(源['displayTitle'],str) and 源['displayTitle']!='' else 标识
    更新=源['updatedAt'] if 'updatedAt' in 源 and isinstance(源['updatedAt'],(int,float)) and not isinstance(源['updatedAt'],bool) else 0
    结果={
        'id':源['id'] if 'id' in 源 else 标识,
        'displayTitle':标题,
        'blank':源['blank'] is True if 'blank' in 源 else False,
        'running':源['running'] is True if 'running' in 源 else False,
        'updatedAt':更新,
        'origin':源['origin'] if 'origin' in 源 else 'user',
    }
    for 键 in ('retainedBy','projectionValues','parentId','cwd','title'):
        if 键 in 源:
            结果[键]=源[键]
    return 结果

def 取出会话服务(上下文):
    '取已经安装的客户端会话服务。没有上下文时页面仍可打开，不另造会话。'
    if 上下文 is None:
        return None
    已装=getattr(上下文,'sessions',None)
    if isinstance(已装,客户端会话服务):
        return 已装
    远程=getattr(上下文,'remote',None)
    if 远程 is None:
        raise 布局错误('会话服务没有远程面')
    return 客户端会话服务(上下文,远程)

def 读取会话列表(服务):
    '只读列表快照。快照缺 ids 或 byId 视为服务没接上。'
    if not isinstance(服务,客户端会话服务):
        raise 布局错误('会话服务没有接上')
    列表=服务.list.getSnapshot()
    if not isinstance(列表,dict) or 'ids' not in 列表 or 'byId' not in 列表:
        raise 布局错误('会话服务没有给出列表')
    return 列表

def 读取已绑定会话(服务,列表):
    '只读取已经绑定的会话。不调用创建，也不补一条假会话。'
    会话类型=会话
    结果=[]
    标识列表=列表['ids'] if isinstance(列表.get('ids'),list) else []
    for 标识 in 标识列表:
        绑定=服务.binding(标识)
        if not isinstance(绑定,dict) or 'session' not in 绑定:
            continue
        面=绑定['session']
        if isinstance(面,会话类型):
            面.getSnapshot()
            结果.append(面)
    return 结果

def 取远程(上下文):
    '事件流要的远程面。没有上下文就没有远程。'
    if 上下文 is None:
        return None
    return getattr(上下文,'remote',None)

def 挂上已有会话的事件流(远程,会话面列表,画布):
    '已经绑定的会话才打开事件流。投递写进画布，由聊天视图读取。'
    流类型=会话事件流
    if len(会话面列表)==0:
        return []
    if 远程 is None:
        raise 布局错误('会话事件流没有远程面')
    结果=[]
    for 面 in 会话面列表:
        快照=面.getSnapshot()
        标识=快照['sessionId'] if isinstance(快照,dict) else None
        if not isinstance(标识,str) or 标识=='':
            raise 布局错误('会话快照缺少会话标识')
        def 发布(变更,会话标识=标识):
            '宿主投递写入当前页的聊天窗口'
            画布.纳入(会话标识,变更)
        def 失败(错误):
            '流失败原样抛出，页面不改写成固定说明'
            raise 错误
        流=流类型(远程,{'kind':'session','sessionId':标识},{'publish':发布,'failed':失败})
        流.open({'maxMessages':页消息数})
        结果.append(流)
    return 结果

def 会话视图(服务):
    '供 useSessions 读取的列表。current 只取主视图占用，不用第一条冒充。'
    空={
        'current':None,
        'byId':{},
        'ids':[],
        'phase':None,
        'subagentsByParent':{},
        'jobsBySession':{},
    }
    if 服务 is None:
        return 空
    列表=服务.list.getSnapshot()
    源表=列表['byId'] if isinstance(列表.get('byId'),dict) else {}
    标识列表=列表['ids'] if isinstance(列表.get('ids'),list) else []
    按标识={}
    for 标识 in 标识列表:
        if 标识 in 源表:
            按标识[标识]=浏览器会话行(标识,源表[标识])
    视图={
        'current':None,
        'byId':按标识,
        'ids':标识列表,
        'phase':列表['phase'] if 'phase' in 列表 else None,
        'subagentsByParent':列表['subagentsByParent'] if 'subagentsByParent' in 列表 else {},
        'jobsBySession':列表['jobsBySession'] if 'jobsBySession' in 列表 else {},
    }
    视图['current']=主会话标识(视图)
    if 视图['current'] is None:
        选中=选聊天会话(视图)
        if isinstance(选中,str) and 选中 in 按标识:
            行=dict(按标识[选中])
            占用=dict(行['retainedBy']) if isinstance(行.get('retainedBy'),dict) else {}
            占用['mainView']=1
            行['retainedBy']=占用
            按标识[选中]=行
            视图['current']=选中
    return 视图

class 页内聊天:
    '把已绑定会话的事件流收成 useChat 能读的窗口。'

    def __init__(自身,服务):
        '服务用来补 running 和打开态。窗口按会话标识分开。'
        自身.服务=服务
        自身.窗口={}
        自身.节点={}
        自身.还有更多={}
        自身.听者=[]
        自身.当前=None
        自身.代=0
        自身.已派=0
        def 用聊天(投影):
            '投影当前会话的聊天快照'
            return 投影(自身.快照())
        def 订阅(回调):
            '聊天视图在投递或换会话时重画'
            自身.听者.append(回调)
            def 取消():
                if 回调 in 自身.听者:
                    自身.听者.remove(回调)
            return 取消
        用聊天._subscribe=订阅
        自身.用聊天=用聊天

    def 放上(自身,标识):
        '挂载时选定要画的会话，此时还没有读者。'
        自身.当前=标识 if isinstance(标识,str) and 标识!='' else None

    def 选定(自身,标识):
        '侧栏点开会话后，主栏改读这一条的窗口。'
        下一=标识 if isinstance(标识,str) and 标识!='' else None
        if 下一==自身.当前:
            return
        自身.当前=下一
        自身.通知()
        自身.派发()

    def 通知(自身):
        '投递线程只推进代际。界面线程再派发重画。'
        自身.代+=1

    def 派发(自身):
        '界面计时器调用。代际没变则不重画。单个听众失败留在页面上，不拆掉连接。'
        if 自身.代==自身.已派:
            return
        自身.已派=自身.代
        for 回调 in list(自身.听者):
            try:
                回调()
            except Exception as 错误:
                界面.label(页面失败文案(错误))

    def 纳入(自身,标识,变更):
        'replace 和 prepend 换窗口，append 追加，助手流按修订号占一行。'
        if not isinstance(标识,str) or 标识=='' or not isinstance(变更,dict) or 'type' not in 变更:
            return
        类型=变更['type']
        if 类型=='replace' or 类型=='prepend':
            条目=变更['entries'] if isinstance(变更.get('entries'),list) else []
            新序=[]
            新表={}
            for 下标,记录 in enumerate(条目):
                键,节点=记录成节点(记录,下标)
                新序.append(键)
                新表[键]=节点
            if 类型=='replace':
                自身.窗口[标识]=新序
                自身.节点[标识]=新表
            else:
                自身.窗口[标识]=新序+自身.窗口.get(标识,[])
                旧表=自身.节点.get(标识,{})
                旧表.update(新表)
                自身.节点[标识]=旧表
            自身.还有更多[标识]=变更.get('hasMore') is True
        elif 类型=='append' and 'entry' in 变更:
            键,节点=记录成节点(变更['entry'],len(自身.窗口.get(标识,[])))
            表=自身.节点.setdefault(标识,{})
            序=自身.窗口.setdefault(标识,[])
            if 键 not in 表:
                序.append(键)
            表[键]=节点
        elif 类型=='assistant-stream':
            帧=变更['frame'] if 'frame' in 变更 else {}
            修订=帧['revision'] if isinstance(帧,dict) and 'revision' in 帧 else 'live'
            键=标识+':assistant:'+str(修订)
            锚=修订 if isinstance(修订,int) and not isinstance(修订,bool) else 0
            节点={'key':键,'kind':'assistant-stream','visibility':'visible','anchorSeq':锚,'data':帧}
            表=自身.节点.setdefault(标识,{})
            序=自身.窗口.setdefault(标识,[])
            if 键 not in 表:
                序.append(键)
            表[键]=节点
        else:
            return
        if 标识==自身.当前:
            自身.通知()

    def 快照(自身):
        'useChat 读到的窗口。nodes.get 按这次快照里的表取节点。'
        标识=自身.当前
        序=list(自身.窗口.get(标识,[])) if 标识 is not None else []
        表=dict(自身.节点.get(标识,{})) if 标识 is not None else {}
        面=自身._会话面(标识)
        return {
            'order':序,
            'nodes':{'get':lambda 键,表=表: 表[键] if 键 in 表 else None},
            'timeline':None,
            'turnNavigation':[],
            'running':面['running'],
            'openState':面['openState'],
            'openError':面['openError'],
            'hasMore':自身.还有更多.get(标识,False) if 标识 is not None else False,
            'loadingOlder':False,
        }

    def _会话面(自身,标识):
        '绑定会话上的运行和打开态。没有绑定时按冷启动。'
        缺={'running':False,'openState':'cold','openError':None}
        if not isinstance(标识,str) or 标识=='' or 自身.服务 is None:
            return 缺
        绑定=自身.服务.binding(标识)
        if not isinstance(绑定,dict) or 'session' not in 绑定:
            return 缺
        读=getattr(绑定['session'],'getSnapshot',None)
        快照=读() if callable(读) else None
        if not isinstance(快照,dict):
            return 缺
        return {
            'running':快照['running'] is True if 'running' in 快照 else False,
            'openState':快照['openState'] if 'openState' in 快照 else 'cold',
            'openError':快照['openError'] if 'openError' in 快照 else None,
        }

def 布局选择器(存储):
    'useStore 选择器。_subscribe 供根帧在收起或主面板变化时重画。'
    def 选择(投影):
        return 投影(存储['getSnapshot']())
    def 订阅(回调):
        return 存储['subscribe'](回调)
    选择._subscribe=订阅
    return 选择

def 选聊天会话(视图):
    '主栏先读主视图占用的会话，否则读第一条有内容的，再否则读第一条。'
    当前=视图['current'] if isinstance(视图,dict) else None
    if isinstance(当前,str) and 当前!='':
        return 当前
    按标识=视图['byId'] if isinstance(视图,dict) and isinstance(视图.get('byId'),dict) else {}
    标识列表=视图['ids'] if isinstance(视图,dict) and isinstance(视图.get('ids'),list) else []
    for 标识 in 标识列表:
        行=按标识[标识] if 标识 in 按标识 else None
        if isinstance(行,dict) and 行.get('blank') is not True:
            return 标识
    if len(标识列表)>0:
        return 标识列表[0]
    return None

def 造页面绘制槽(服务,画布,工作区=None):
    '侧栏浏览区读会话列表，主栏读事件流收成的 useChat。'
    def 开新(工作区标识=None):
        '新建走会话服务。未分组桶没有工作区标识。没有服务时不造假会话，也不把页面打成 500。'
        if 服务 is None:
            try:
                界面.notify('当前进程没有会话服务')
            except Exception as 错误:
                页面失败文案(错误)
            return
        选项={}
        if isinstance(工作区标识,str) and 工作区标识!='':
            选项['workspaceId']=工作区标识
        return 服务.create(选项)
    def 选择会话(投影):
        '每次读取都回到服务列表，不另造会话。'
        return 投影(会话视图(服务))
    if 服务 is not None:
        选择会话._subscribe=服务.list.subscribe
    def 读工作区(投影):
        '有宿主账本时交 items 和归档标识。没有则会话进未分组，不另造工作区。'
        if 工作区 is None:
            return 投影({'items':[],'archivedSessionIds':[]})
        快照=工作区.getSnapshot()
        if not isinstance(快照,dict):
            return 投影({'items':[],'archivedSessionIds':[]})
        项=快照['items'] if 'items' in 快照 and 快照['items'] is not None else []
        归档=快照['archivedSessionIds'] if 'archivedSessionIds' in 快照 and 快照['archivedSessionIds'] is not None else []
        return 投影({'items':项,'archivedSessionIds':归档})
    if 工作区 is not None and callable(getattr(工作区,'subscribe',None)):
        读工作区._subscribe=工作区.subscribe
    def 浏览快照(投影):
        '分组默认 workspace。组没收开时会话行不出现。'
        return 投影({'groupBy':'workspace','orderBy':'updated','groupExpansion':{},'sessionOrderByAccount':{}})
    def 工作区文(键,参数=None):
        '浏览区词表'
        return 套文案(工作区文案,键,参数)
    def 聊天文(键,参数=None):
        '聊天词表'
        return 套文案(聊天文案,键,参数)
    def 对话文(键,参数=None):
        '输入栏词表'
        return 套文案(对话文案,键,参数)
    画出设置=准备页面设置()
    def 页会话(投影):
        '打开态和撰写相位给会话根。没有消息时是空白，英雄区才会出来。'
        面=画布._会话面(画布.当前)
        序=画布.窗口.get(画布.当前,[]) if 画布.当前 is not None else []
        空白=len(序)==0
        return 投影({
            'promptError':None,
            'running':面['running'] if isinstance(面,dict) and 'running' in 面 else False,
            'openState':面['openState'] if isinstance(面,dict) and 'openState' in 面 else 'cold',
            'composerPhase':'blank' if 空白 else 'active',
            'blank':空白,
            'pending':[],
        })
    def 页输入(投影):
        '空草稿。调用方把 useInput 交齐时，占位才不是「会话不可用」。'
        return 投影({'draft':'','imageIds':[],'phase':'idle','queue':[]})
    def 页提交():
        '没有会话服务时发送只提示，不再抛进页面函数。'
        if 服务 is not None:
            return
        try:
            界面.notify('当前进程没有会话服务')
        except Exception as 错误:
            页面失败文案(错误)
    def 页面绘制槽(名,拥有方=None,选项=None):
        属性=dict(拥有方) if isinstance(拥有方,dict) else {}
        属性['renderSlot']=页面绘制槽
        if 选项 is not None:
            属性['slotOptions']=选项
        if 名=='sidebar':
            属性['startSession']=开新
            属性['useSessions']=选择会话
            return 侧栏壳(属性)
        if 名=='sidebar.workspaces':
            return 工作区浏览区({
                't':工作区文,
                'wide':属性['wide'] if 'wide' in 属性 else True,
                'useSessions':选择会话,
                'useWorkspaces':读工作区,
                'useStore':浏览快照,
                'startSession':开新,
                'open':画布.选定,
                'expandSidebar':属性['expandSidebar'] if 'expandSidebar' in 属性 else None,
            })
        if 名=='sidebar.settings':
            return 画出设置(页面绘制槽,属性['wide'] if 'wide' in 属性 else True)
        if 名=='main':
            键=选项['entryKey'] if isinstance(选项,dict) and 'entryKey' in 选项 else 'conversation'
            if 键!='conversation':
                return None
            根=会话根({
                't':对话文,
                'renderSlot':页面绘制槽,
                'useSessions':选择会话,
                'useWorkspaces':读工作区,
                'useSession':页会话,
                'useInput':页输入,
                'inputActions':{'submit':页提交},
                'sessionId':画布.当前,
            })
            def 换会话():
                '侧栏换会话后重画英雄或聊天。'
                新=dict(根.属性)
                新['sessionId']=画布.当前
                根.更新(新)
                根.渲染()
            画布.听者.append(换会话)
            return 根
        if 名=='conversation.session':
            快照=画布.快照()
            if not isinstance(快照.get('order'),list) or len(快照['order'])==0:
                return None
            return 聊天视图({'useChat':画布.用聊天,'t':聊天文,'renderSlot':页面绘制槽})
        if 名=='conversation.composer.bar':
            栏={
                't':对话文,
                'renderSlot':页面绘制槽,
                'useSession':页会话,
                'useInput':页输入,
                'keyboard':{},
                'inputActions':{'submit':页提交},
            }
            栏.update(属性)
            return 输入栏(栏)
        if 名=='conversation.chat.node':
            if isinstance(选项,dict) and 'fallback' in 选项:
                return 选项['fallback']
            return None
        if 名=='rightbar':
            return 右栏壳(属性)
        return None
    return 页面绘制槽

def 取出工作区(上下文):
    '取宿主工作区账本。没有上下文或没有 list 快照时返回空，不另造工作区。'
    if 上下文 is None:
        return None
    已装=getattr(上下文,'workspaces',None)
    清单=getattr(已装,'list',None) if 已装 is not None else None
    if 清单 is None or not callable(getattr(清单,'getSnapshot',None)):
        return None
    return 清单

def 根帧属性(服务,画布,工作区=None):
    '根帧要的布局存储、会话选择器和三栏绘制函数。'
    存储=创建布局存储()
    def 选择会话(投影):
        return 投影(会话视图(服务))
    if 服务 is not None:
        选择会话._subscribe=服务.list.subscribe
    return {
        'useStore':布局选择器(存储),
        'actions':存储['actions'],
        'useSessions':选择会话,
        'renderSlot':造页面绘制槽(服务,画布,工作区),
    }

def 挂载页面(上下文=None):
    '只挂根帧。有会话服务时把列表和事件流交给三栏；没有时仍画出壳，不另造会话。'
    确保样式()
    try:
        服务=取出会话服务(上下文)
        画布=页内聊天(服务)
        流列表=[]
        if 服务 is not None:
            列表=读取会话列表(服务)
            面列表=读取已绑定会话(服务,列表)
            画布.放上(选聊天会话(会话视图(服务)))
            流列表=挂上已有会话的事件流(取远程(上下文),面列表,画布)
        帧=根帧(根帧属性(服务,画布,取出工作区(上下文)))
        帧.会话事件流=流列表
        界面.timer(0.05,画布.派发)
    except Exception as 错误:
        界面.label(页面失败文案(错误))

def 打开页面(主机='127.0.0.1',端口=8080,上下文=None):
    '在调用本函数的进程里监听网页。0.0.0.0 直接拒绝。'
    if 主机=='0.0.0.0':
        raise ValueError('网页只监听本机')
    def 页面():
        '根路径只挂根帧'
        挂载页面(上下文)
    界面.page('/')(页面)
    界面.run(host=主机,port=端口,title=产品标题(),reload=False,show=False)


class 根帧:
    'root 槽的三栏壳。左栏收起变化时清空左列，再按 sidebar 槽重画。'

    def __init__(自身,属性):
        '保存槽位份额。构造时即画出三栏。'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身._已订=False
        自身._面板=None
        自身._收起=None
        自身.侧栏盒=None
        自身.渲染()

    def 快照(自身):
        '读布局存储。没有 useStore，或读到的值不含 layoutInfo 时，用冷启动几何。'
        用=自身.属性['useStore'] if 'useStore' in 自身.属性 else None
        if callable(用):
            def 原样(快照):
                return 快照
            值=用(原样)
            if isinstance(值,dict) and 'layoutInfo' in 值:
                return 值
        return 初始布局状态()

    def 布局面(自身):
        '套用列要的 getSnapshot 和 actions。actions 缺席时按空动作表处理。'
        动作=自身.属性['actions'] if 'actions' in 自身.属性 and isinstance(自身.属性['actions'],dict) else {}
        return {'getSnapshot':自身.快照,'actions':动作}

    def 画槽(自身,名,拥有方=None,选项=None):
        '有 renderSlot 才画子槽。名是框架槽位名。'
        画=自身.属性['renderSlot'] if 'renderSlot' in 自身.属性 else None
        if callable(画) is not True:
            return
        try:
            if 选项 is None:
                画(名,{} if 拥有方 is None else 拥有方)
                return
            画(名,{} if 拥有方 is None else 拥有方,选项)
        except Exception as 错误:
            界面.label(页面失败文案(错误))

    def 渲染(自身):
        '网格、四块子槽和两根拖柄。样式已登记过就不再追加。'
        确保样式()
        快照=自身.快照()
        几何=快照['layoutInfo']
        面板=快照['panelInfo']['activePanelId'] if 'panelInfo' in 快照 else None
        自身._面板=面板
        译=自身.属性['t'] if 't' in 自身.属性 and callable(自身.属性['t']) else None
        标题属性={'productTitle':产品标题(译)}
        if 'useSessions' in 自身.属性:
            标题属性['useSessions']=自身.属性['useSessions']
        def 面板信息(投影):
            '布局存储里的活动面板。没有面板时主面是会话。'
            快照=自身.快照()
            标识=快照['panelInfo']['activePanelId'] if 'panelInfo' in 快照 and 'activePanelId' in 快照['panelInfo'] else None
            return 投影({'activePanelId':标识})
        标题属性['usePanelInfo']=面板信息
        自身._标题属性=标题属性
        def 写标题():
            '会话或主面板变化后重写文档标题'
            try:
                文档标题(自身._标题属性).渲染()
            except Exception as 错误:
                页面失败文案(错误)
        写标题()
        解=求解帧(几何)
        收起=解['收起']
        自身._收起=收起
        布局=自身.布局面()
        动作=布局['actions']
        def 侧栏份额(收起态,列宽):
            '把折叠动作交给侧栏壳。存储里没有这个动作时按钮仍画出，只是点了不改列宽。'
            份额={'collapsed':收起态,'width':列宽}
            if 'toggleSidebar' in 动作:
                份额['toggleSidebar']=动作['toggleSidebar']
            return 份额
        with 界面.element('div').classes('根帧') as 帧:
            自身.侧栏盒=界面.element('div').classes('根帧列')
            with 自身.侧栏盒:
                自身.画槽('sidebar',侧栏份额(收起,解['列']['sidebar']))
            自身.主盒=界面.element('div').classes('根帧列')
            with 自身.主盒:
                键=面板 if 面板 is not None else 'conversation'
                自身.画槽('main',{},{'entryKey':键})
            with 界面.element('div').classes('根帧列') as 右列:
                自身.右栏盒=右列
                自身.画槽('rightbar',{
                    'width':解['正常']['rightbar'],
                    'viewportWidth':解['视口'],
                    'canShow':解['正常']['rightbar']>0,
                    'usePanelInfo':面板信息,
                })
            with 界面.element('div').classes('根帧底'):
                自身.画槽('shell.bottom',{})
            with 界面.element('div').classes('根帧罩'):
                自身.画槽('shell.overlay',{})
            左柄=界面.element('div').classes('拖柄')
            右柄=界面.element('div').classes('拖柄')
        左柄.props('data-side=sidebar')
        右柄.props('data-side=rightbar')
        上次={'视口':None,'开关':None,'代':0}
        界面状态={}
        def 套用(拖拽中=False):
            '只改列宽，不重画子槽'
            套用列(帧,左柄,右柄,布局,界面状态,上次,拖拽中)
        套用()
        绑定帧事件(帧,左柄,右柄)
        def 收到视口(事件):
            '把帧宽写进存储后再套列。布尔值和其它非数字宽度丢掉。'
            宽=事件.args
            if isinstance(宽,bool) or not isinstance(宽,(int,float)):
                return
            动作=布局['actions']
            if 'setViewportWidth' not in 动作:
                return
            动作前=自身.快照()['layoutInfo']['viewportWidth']
            动作['setViewportWidth'](int(宽))
            if 自身.快照()['layoutInfo']['viewportWidth']==动作前:
                return
            套用()
        def 收到拖(事件):
            '拖分隔条时改偏好宽。按下时停掉轨道动画，松开后再套一次。'
            载荷=事件.args
            if not isinstance(载荷,dict) or 'phase' not in 载荷 or 'side' not in 载荷 or 'px' not in 载荷:
                return
            像素=载荷['px']
            if isinstance(像素,bool) or not isinstance(像素,(int,float)):
                return
            动作=布局['actions']
            if 载荷['phase']=='move':
                if 载荷['side']=='sidebar' and 'setSidebar' in 动作:
                    动作['setSidebar'](像素)
                elif 'setRightbar' in 动作:
                    动作['setRightbar'](像素)
                套用(True)
                return
            if 载荷['phase']=='start':
                套用(True)
                return
            套用(False)
        界面.on('dsh-viewport',收到视口)
        界面.on('dsh-drag',收到拖)
        if 自身._已订 is not True:
            用=自身.属性['useStore'] if 'useStore' in 自身.属性 else None
            订=getattr(用,'_subscribe',None) if 用 is not None else None
            if callable(订):
                def 变更():
                    '主面板换了重画主列；左栏收起变了重画左列'
                    新=自身.快照()
                    新面板=新['panelInfo']['activePanelId'] if 'panelInfo' in 新 else None
                    几何=新['layoutInfo'] if 'layoutInfo' in 新 else {}
                    新收起=求解帧(几何)['收起']
                    if 新收起!=自身._收起 and 自身.侧栏盒 is not None:
                        自身._收起=新收起
                        列宽=求解帧(几何)['列']['sidebar']
                        自身.侧栏盒.clear()
                        with 自身.侧栏盒:
                            自身.画槽('sidebar',侧栏份额(新收起,列宽))
                    if 新面板==自身._面板:
                        套用()
                        return
                    自身._面板=新面板
                    自身.主盒.clear()
                    with 自身.主盒:
                        键=新面板 if 新面板 is not None else 'conversation'
                        自身.画槽('main',{},{'entryKey':键})
                    if 自身.右栏盒 is not None:
                        自身.右栏盒.clear()
                        右解=求解帧(几何)
                        with 自身.右栏盒:
                            自身.画槽('rightbar',{
                                'width':右解['正常']['rightbar'],
                                'viewportWidth':右解['视口'],
                                'canShow':右解['正常']['rightbar']>0,
                                'usePanelInfo':面板信息,
                            })
                    套用()
                    写标题()
                订(变更)
                自身._已订=True
            用会话=自身.属性['useSessions'] if 'useSessions' in 自身.属性 else None
            订会话=getattr(用会话,'_subscribe',None) if 用会话 is not None else None
            if callable(订会话) and getattr(自身,'_已订标题',False) is not True:
                订会话(写标题)
                自身._已订标题=True

    def __call__(自身):
        '再画一次'
        return 自身.渲染()
