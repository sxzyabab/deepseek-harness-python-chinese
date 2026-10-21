import os
import re

def 页面失败文案(错误):
    '页面上给调用方看的失败句。去掉绝对路径、用户名和环境变量，其余原文保留。'
    if isinstance(错误,BaseException):
        名=type(错误).__name__
        原文=str(错误.args[0]) if len(错误.args)>0 else ''
    else:
        名=''
        原文=str(错误)
    屏蔽名=set(os.environ)
    屏蔽值=set()
    for 键 in ('USERNAME','USER','LOGNAME','USERPROFILE','HOME'):
        值=os.environ.get(键)
        if isinstance(值,str) and 值!='':
            屏蔽值.add(值)
            基=os.path.basename(值.rstrip('\\/'))
            if 基!='':
                屏蔽值.add(基)
    for 值 in os.environ.values():
        if isinstance(值,str) and (len(值)>=8 or '\\' in 值 or '/' in 值):
            屏蔽值.add(值)
    留下=[]
    for 词 in 原文.split():
        裸=词.strip('\'"')
        统一=裸.replace('\\','/')
        if 统一.startswith('/') or 统一.startswith('~/') or (len(统一)>2 and 统一[0].isalpha() and 统一[1]==':' and 统一[2]=='/'):
            continue
        if 裸.startswith('$') and len(裸)>1:
            continue
        if len(裸)>2 and 裸.startswith('%') and 裸.endswith('%'):
            continue
        if '=' in 裸 and 裸.split('=',1)[0] in 屏蔽名:
            continue
        if 裸 in 屏蔽名 or 裸 in 屏蔽值 or 统一 in 屏蔽值:
            continue
        含敏感=False
        for 项 in 屏蔽值:
            if len(项)>=3 and 项 in 裸:
                含敏感=True
                break
        if 含敏感:
            continue
        留下.append(词)
    说明=' '.join(留下).strip()
    if 说明=='':
        return 名 if 名!='' else '失败'
    return 说明

def 贴出失败(自身,文档,父节点):
    '父级拆掉旧画面时，把失败句留在当前容器里。'
    文=getattr(自身,'画面失败',None)
    if isinstance(文,str) and 文!='' and 文档 is not None and 父节点 is not None:
        标签=文档.createElement('div')
        标签.textContent=文
        父节点.appendChild(标签)
        自身.画面失败=None

def 清空子(节点):
    '拆掉全部子节点'
    while 节点.firstElementChild is not None:
        节点.firstElementChild.remove()

def 是页面节点(值):
    '桥上的节点。缺属性会给出 undefined，不能拿来判断有没有根'
    if 值 is None or isinstance(值,(str,int,float,bool,dict,list,tuple)):
        return False
    模块=getattr(type(值),'__module__','')
    return isinstance(模块,str) and 模块.startswith('pywebbridge')

def 挂上(父,结果):
    '组件挂根，官方槽位树展开后再挂。节点直接挂'
    if 父 is None or 结果 is None:
        return 结果
    if isinstance(结果,dict):
        种类=结果.get('type')
        if 种类 in ('slot-outlet','root-outlet','slot-renderer-root'):
            内容=结果.get('content')
            if 内容 is None:
                内容=结果.get('body')
            if 内容 is None:
                内容=结果.get('tree')
            return 挂上(父,内容)
        if 种类 in ('root-entry','strict-session-entry','session-maybe-wrap','session-maybe-entry'):
            return 挂上(父,结果.get('body'))
        if 种类=='slot-list':
            for 项 in 结果.get('items') or []:
                挂上(父,项)
            return 结果
        if 种类=='chain-overlay':
            选=结果.get('elected')
            if 选 is None:
                选=结果.get('fallback')
            return 挂上(父,选)
        return 结果
    模块=getattr(type(结果),'__module__','')
    if isinstance(模块,str) and 模块.startswith('pywebbridge'):
        父.appendChild(结果)
        return 结果
    try:
        根=object.__getattribute__(结果,'根')
    except AttributeError:
        根=None
    if 根 is not None:
        if getattr(根,'parentNode',None) is not 父:
            父.appendChild(根)
        return 结果
    try:
        实现=object.__getattribute__(结果,'实现')
    except AttributeError:
        实现=None
    if 实现 is not None:
        try:
            实现根=object.__getattribute__(实现,'根')
        except AttributeError:
            实现根=None
        if 实现根 is not None:
            父.appendChild(实现根)
    return 结果

def 接上(旧,新,父=None):
    '新节点画完后再换到旧位置。旧节点留到这一次替换，不先拆空'
    if 新 is not None and 旧 is not None and getattr(旧,'parentNode',None) is not None:
        旧.parentNode.replaceChild(新,旧)
        return 新
    if 旧 is not None and 旧 is not 新 and getattr(旧,'parentNode',None) is not None:
        旧.remove()
    if 新 is not None and 父 is not None and getattr(新,'parentNode',None) is None:
        父.appendChild(新)
    return 新

def 换根(自身,处理,属性=None):
    '只换这个组件自己的根。先画好再替换，不拆整页'
    自身.画面失败=None
    用=自身.属性 if 属性 is None else 属性
    if isinstance(用,dict) is False or 'window' not in 用:
        return None
    父=用['parent'] if 'parent' in 用 else None
    画用=dict(用)
    if 'parent' in 画用:
        del 画用['parent']
    try:
        新=处理(画用['window'],画用)
    except Exception as 错误:
        自身.画面失败=页面失败文案(错误)
        return None
    旧=getattr(自身,'根',None)
    if 新 is not None and 旧 is not None and getattr(旧,'parentNode',None) is not None:
        旧.parentNode.replaceChild(新,旧)
    elif 新 is not None and 父 is not None and getattr(新,'parentNode',None) is None:
        父.appendChild(新)
        if 旧 is not None:
            旧.remove()
    elif 旧 is not None and 新 is None:
        旧.remove()
    自身.根=新
    return 新

def 卸根(自身):
    '不画时拆掉旧根'
    if getattr(自身,'根',None) is not None:
        try:
            自身.根.remove()
        except Exception as 错误:
            自身.画面失败=页面失败文案(错误)
        自身.根=None

def 带窗(window,基础=None):
    '子组件只收 window，不收 parent'
    出=dict(基础) if isinstance(基础,dict) else {}
    出['window']=window
    if 'parent' in 出:
        del 出['parent']
    return 出

def 叫槽(渲染槽,名,属主,window,选项=None):
    '把 window 交给槽位'
    子=带窗(window,属主)
    if 选项 is None:
        return 渲染槽(名,子)
    return 渲染槽(名,子,选项)

def 列(文档,类名):
    '纵向盒子'
    节点=文档.createElement('div')
    节点.className=类名
    节点.style.display='flex'
    节点.style.flexDirection='column'
    return 节点

def 行盒(文档,类名):
    '横向盒子'
    节点=文档.createElement('div')
    节点.className=类名
    节点.style.display='flex'
    节点.style.flexDirection='row'
    return 节点

def 文(文档,文字,类名=None):
    '文本节点'
    节点=文档.createElement('div')
    if 类名 not in (None,''):
        节点.className=类名
    节点.textContent='' if 文字 is None else str(文字)
    return 节点

def 钮(文档,文字,点击,类名=None):
    '按钮。点击函数第一个参数是事件'
    节点=文档.createElement('button')
    节点.type='button'
    if 类名 not in (None,''):
        节点.className=类名
    if 文字 is not None:
        节点.textContent=str(文字)
    if 点击 is not None:
        节点.addEventListener('click',点击)
    return 节点

def 注入样式(文档,标识,文本):
    '固定 id，已有就不再插'
    if 文档.getElementById(标识) is not None:
        return
    样式=文档.createElement('style')
    样式.id=标识
    样式.textContent=文本
    文档.head.appendChild(样式)

def 注入样式文件(文档,标识,路径):
    '样式文件只读，由这里插进 head'
    if 文档.getElementById(标识) is not None:
        return
    句柄=open(路径,encoding='utf-8')
    文本=句柄.read()
    句柄.close()
    注入样式(文档,标识,文本)

def 去掉样式注释(原文):
    '去掉块注释，避免注释里的花括号打断规则'
    出=[]
    下标=0
    长度=len(原文)
    while 下标<长度:
        if 原文.startswith('/*',下标):
            止=原文.find('*/',下标+2)
            if 止<0:
                break
            下标=止+2
            continue
        出.append(原文[下标])
        下标+=1
    return ''.join(出)

def 挂上模块类(选择器,模块):
    '类名留在元素上。选择器改成带 data-dsh-css，避免各模块的 .root 互相盖住。:global 里的类名不改'
    保护=[]
    暂=选择器
    下标=0
    拼=[]
    while True:
        起=暂.find(':global(',下标)
        if 起<0:
            拼.append(暂[下标:])
            break
        拼.append(暂[下标:起])
        深度=1
        游=起+len(':global(')
        内起=游
        while 游<len(暂) and 深度>0:
            if 暂[游]=='(':
                深度+=1
            elif 暂[游]==')':
                深度-=1
                if 深度==0:
                    break
            游+=1
        保护.append(暂[内起:游])
        拼.append('\u0000'+str(len(保护)-1)+'\u0000')
        下标=游+1 if 游<len(暂) else 游
    文=''.join(拼)
    def 换(匹配):
        return '[data-dsh-css="'+模块+'"].'+匹配.group(1)
    文=re.sub(r'\.([A-Za-z_][\w-]*)',换,文)
    for 序,内 in enumerate(保护):
        文=文.replace('\u0000'+str(序)+'\u0000',内)
    return 文

def 编译模块规则(文,模块):
    '普通规则改类选择器。媒体查询往里走。关键帧和字体保持原样'
    出=[]
    下标=0
    长度=len(文)
    while 下标<长度:
        while 下标<长度 and 文[下标].isspace():
            下标+=1
        if 下标>=长度:
            break
        起=下标
        while 下标<长度 and 文[下标]!='{':
            下标+=1
        if 下标>=长度:
            break
        选择器=文[起:下标].strip()
        下标+=1
        深度=1
        体起=下标
        while 下标<长度 and 深度>0:
            if 文[下标]=='{':
                深度+=1
            elif 文[下标]=='}':
                深度-=1
            下标+=1
        体=文[体起:下标-1]
        if 选择器.startswith('@keyframes') or 选择器.startswith('@font-face'):
            出.append(选择器+'{'+体+'}')
        elif 选择器.startswith('@media') or 选择器.startswith('@container') or 选择器.startswith('@supports'):
            出.append(选择器+'{'+编译模块规则(体,模块)+'}')
        elif 选择器!='':
            出.append(挂上模块类(选择器,模块)+'{'+体+'}')
    return '\n'.join(出)

def 编译模块样式(原文,模块):
    '官方 CSS 模块按类名生效，并用 data-dsh-css 把同一类名隔开'
    return 编译模块规则(去掉样式注释(原文),模块)

def 注入模块样式(文档,标识,文本,模块):
    '同一 id 只插一次。文本是官方模块原文'
    if 文档.getElementById(标识) is not None:
        return
    注入样式(文档,标识,编译模块样式(文本,模块))

def 注入模块样式文件(文档,标识,路径,模块):
    '读官方模块文件，编译后插进 head'
    if 文档.getElementById(标识) is not None:
        return
    句柄=open(路径,encoding='utf-8')
    文本=句柄.read()
    句柄.close()
    注入模块样式(文档,标识,文本,模块)

def 标样式模块(节点,模块):
    '元素用官方类名，再用这个属性接上编译后的选择器'
    节点.setAttribute('data-dsh-css',模块)
    return 节点

def 模块节点(文档,标签,模块,类名):
    '造一个挂了官方类名和样式模块的节点'
    节点=文档.createElement(标签)
    if isinstance(类名,str) and 类名!='':
        节点.className=类名
    return 标样式模块(节点,模块)

def 可画(属性):
    '构造时有 window 才画'
    return isinstance(属性,dict) and 'window' in 属性

class 对话错误(Exception):
    '审批回执与槽面失败'
    def __init__(自身,消息,原因=None):
        '记下英文消息与可选结构原因'
        super().__init__(消息)
        自身.reason=原因

class 不支持图片媒体类型(Exception):
    '浏览器声明了不支持的图片类型，由 UI 边界本地化'
    def __init__(自身,媒体类型):
        '保存声明值'
        super().__init__('unsupported image media type: '+(媒体类型 or '(empty)'))
        自身.mediaType=媒体类型

class 用户文本变换错误(Exception):
    '一条用户文本规则求值失败。原文整段保留，错误交给登记的上报'
    def __init__(自身,规则标识,原因):
        '记下规则标识和原因'
        super().__init__('user-text rule "'+str(规则标识)+'" failed to evaluate')
        自身.ruleId=规则标识
        自身.__cause__=原因 if isinstance(原因,BaseException) else None
