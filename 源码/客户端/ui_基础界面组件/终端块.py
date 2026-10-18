from ..模块.客户端.通告 import 取握手窗口
import os
from ...基础设施.通用工具 import 路径转正斜杠
from ..ui_对话.异常 import 注入模块样式文件,标样式模块
from .头尾封顶 import 头尾封顶
from .复制反馈 import 复制反馈
from .ansi import 解析ansi行
from .命令文本 import 命令文本
from .状态点 import 处理状态点
from .胶囊 import 处理胶囊

__all__=['终端块','处理终端块','默认终端最大行','默认标签','提示标签','状态文案','运行态']

默认终端最大行=16
样式模块='terminal'
未传=object()

def 信号文案(信号):
    '信号胶囊'
    return '信号 '+str(信号)

def 退出码文案(码):
    '退出码胶囊'
    return '退出码 '+str(码)

def 展开其余无障碍(隐):
    '展开其余 N 行的无障碍名'
    return '展开其余 '+str(隐)+' 行输出'

def 展开其余标(隐):
    '展开其余 N 行'
    return '… 其余 '+str(隐)+' 行'

def 命令行文案(行号):
    '溢出命令行的无障碍名，从 1 计'
    return '第 '+str(行号)+' 行命令'

默认标签={
    'signal':信号文案,
    'exitCode':退出码文案,
    'noExitCode':'无退出码',
    'running':'运行中',
    'failed':'失败',
    'done':'已完成',
    'copy':'复制',
    'copied':'复制成功',
    'noOutput':'无输出',
    'collapseAria':'收起输出',
    'collapse':'收起',
    'expandAria':展开其余无障碍,
    'expand':展开其余标,
    'commandLine':命令行文案,
}

def 剥尾分隔(路径):
    '去掉路径尾部的斜杠'
    if isinstance(路径,str) is False:
        return ''
    return 路径.rstrip('/\\')

def 切末段(路径):
    '正反斜杠都认，取最后一段'
    片=路径转正斜杠(路径).split('/')
    if len(片)>0:
        return 片[-1]
    return ''

def 提示标签(工作目录,家目录):
    '家目录收成 ~，否则取末段'
    修=剥尾分隔(工作目录)
    if 家目录 is not None and 修==剥尾分隔(家目录):
        return '~'
    段=切末段(修)
    if 段=='':
        return 工作目录
    return 段

def 状态文案(退出码,信号,标签):
    '信号优先。exitCode 为 None 表示没有退出码。缺省且无信号则干净退出'
    if 信号 is not 未传:
        return 标签['signal'](信号)
    if 退出码 is None:
        return 标签['noExitCode']
    if 退出码 is not 未传 and 退出码!=0:
        return 标签['exitCode'](退出码)
    return None

def 运行态(运行中,退出码,信号,标签):
    'ongoing、error 或 done'
    if 运行中 is True:
        return {'state':'ongoing','label':标签['running']}
    if 状态文案(退出码,信号,标签) is not None:
        return {'state':'error','label':标签['failed']}
    return {'state':'done','label':标签['done']}

def 段文(段):
    'span.text，缺则空串'
    if 'text' in 段 and 段['text'] is not None:
        return 段['text']
    return ''

def 取键(属性,键):
    '缺键用未传，显式 None 保留'
    if 键 not in 属性:
        return 未传
    return 属性[键]

def 处理终端块(window,属性):
    '画出 data-terminal 卡片。可关掉状态点、复制指定文本、用 Infinity 不封顶'
    文档=window.document
    注入模块样式文件(
        文档,
        '终端块样式',
        os.path.join(os.path.dirname(__file__),'终端块.module.css'),
        样式模块,
    )
    组件=属性['组件']
    标签=dict(默认标签)
    覆=属性.get('labels')
    if isinstance(覆,dict):
        标签.update(覆)
    输出=属性['output'] if 'output' in 属性 and 属性['output'] is not None else ''
    行列表=解析ansi行(输出)
    if len(行列表)>1:
        末=行列表[-1]
        全空=True
        for 段 in 末:
            if 段文(段)!='':
                全空=False
                break
        if 全空 is True:
            行列表=行列表[:-1]
    运行中=属性.get('running') is True
    后台=属性.get('background') is True
    画点=True
    if 'runStateDot' in 属性 and 属性['runStateDot'] is False:
        画点=False
    退出码=取键(属性,'exitCode')
    信号=取键(属性,'signal')
    最大=属性['maxLines'] if 'maxLines' in 属性 and 属性['maxLines'] is not None else 默认终端最大行
    命令=属性['command'] if 'command' in 属性 and 属性['command'] is not None else ''
    令体=命令[:-1] if 命令.endswith('\n') else 命令
    命令行=令体.split('\n') if 令体!='' else ['']
    空=True
    for 线 in 行列表:
        for 段 in 线:
            if 段文(段).strip()!='':
                空=False
                break
        if 空 is False:
            break
    复制原文=输出
    if 'copyText' in 属性 and 属性['copyText'] is not None:
        复制原文=属性['copyText']
    组件.反馈.置文本(复制原文)
    工作目录=属性.get('cwd')
    家=属性.get('home')
    态=运行态(运行中,退出码,信号,标签)
    状=None if 后台 else 状态文案(退出码,信号,标签)
    显示状态=画点 and (后台 is False or 运行中 is True)
    有体=后台 is False and (运行中 is False or 空 is False)
    根=文档.createElement('div')
    类名='block'
    附加=属性.get('className')
    if isinstance(附加,str) and 附加!='':
        类名=类名+' '+附加
    根.className=类名
    标样式模块(根,样式模块)
    根.setAttribute('data-terminal','')
    if 运行中:
        根.setAttribute('data-running','')
    if 有体:
        根.setAttribute('data-body','')
    def 样式串(样式):
        'ANSI 样式写成行内样式'
        if 样式 is None:
            return ''
        名={
            'backgroundColor':'background-color',
            'fontWeight':'font-weight',
            'fontStyle':'font-style',
            'textDecoration':'text-decoration',
            'visibility':'visibility',
            'opacity':'opacity',
            'color':'color',
        }
        段=[]
        for 键,值 in 样式.items():
            css=名[键] if 键 in 名 else 键
            段.append(str(css)+':'+str(值))
        return ';'.join(段)
    def 画行(线):
        '一行。没有样式的段直接用文本'
        行盒=文档.createElement('div')
        行盒.className='line'
        标样式模块(行盒,样式模块)
        if len(线)==0:
            行盒.appendChild(文档.createTextNode(''))
        else:
            for 段 in 线:
                文=段文(段)
                样式=段['style'] if 'style' in 段 else None
                if 样式 is None:
                    行盒.appendChild(文档.createTextNode(文))
                else:
                    标=文档.createElement('span')
                    标.textContent=文
                    串=样式串(样式)
                    if 串!='':
                        标.style.cssText=串
                    行盒.appendChild(标)
        return 行盒
    头=文档.createElement('div')
    头.className='header'
    标样式模块(头,样式模块)
    提示=文档.createElement('div')
    提示.className='prompt'
    标样式模块(提示,样式模块)
    if 显示状态:
        读=文档.createElement('span')
        读.className='runStateLabel'
        标样式模块(读,样式模块)
        读.textContent=态['label']
        提示.appendChild(读)
    序=0
    for 行文 in 命令行:
        行盒=文档.createElement('div')
        行盒.className='promptLine'
        标样式模块(行盒,样式模块)
        if 序==0 and 显示状态:
            点=处理状态点(window,{
                'state':态['state'],
                'className':'runState',
            })
            if 点 is not None:
                标样式模块(点,样式模块)
                行盒.appendChild(点)
        目录=文档.createElement('span')
        目录.className='cwd'
        标样式模块(目录,样式模块)
        if 序>0 or 工作目录 is None:
            目录.textContent='$'
        else:
            目录.textContent=提示标签(工作目录,家)
        行盒.appendChild(目录)
        名函=标签['commandLine'] if 'commandLine' in 标签 and callable(标签['commandLine']) else 命令行文案
        命令节点=命令文本({
            'window':window,
            'text':行文,
            'label':名函(序+1),
            'className':'command',
        }).渲染()
        if 命令节点 is not None:
            标样式模块(命令节点,样式模块)
            行盒.appendChild(命令节点)
        提示.appendChild(行盒)
        序=序+1
    头.appendChild(提示)
    if 状 is not None:
        丸=处理胶囊(window,{'children':状,'className':'status'})
        if 丸 is not None:
            标样式模块(丸,样式模块)
            头.appendChild(丸)
    可复制='copyText' in 属性 and 属性['copyText'] is not None
    if 可复制 is False and 后台 is False and 运行中 is False and 空 is False:
        可复制=True
    if 可复制:
        复制钮=文档.createElement('button')
        复制钮.type='button'
        复制钮.className='copyButton'
        标样式模块(复制钮,样式模块)
        复制钮.textContent=标签['copied'] if 组件.反馈.已复制 else 标签['copy']
        def 点复制(事件):
            '写入剪贴板。成功后的一秒钟由复制反馈自己熄灭并重画'
            组件.反馈.刷新=组件.渲染
            组件.反馈.复制()
            组件.渲染()
        复制钮.addEventListener('click',点复制)
        头.appendChild(复制钮)
    根.appendChild(头)
    if 有体:
        if 空:
            空盒=文档.createElement('div')
            空盒.className='empty'
            标样式模块(空盒,样式模块)
            空盒.textContent=标签['noOutput']
            根.appendChild(空盒)
        else:
            度量=头尾封顶(len(行列表),最大,组件.已展开)
            出=文档.createElement('div')
            出.className='output'
            标样式模块(出,样式模块)
            头行=行列表[:度量['headLines']] if 度量['capped'] is True else 行列表
            for 线 in 头行:
                出.appendChild(画行(线))
            if 度量['hidden']>0:
                展钮=文档.createElement('button')
                展钮.type='button'
                展钮.className='expand'
                标样式模块(展钮,样式模块)
                展钮.setAttribute('aria-expanded','true' if 组件.已展开 else 'false')
                if 组件.已展开:
                    展钮.setAttribute('aria-label',标签['collapseAria'])
                    展钮.textContent=标签['collapse']
                else:
                    展文=标签['expandAria']
                    展钮.setAttribute('aria-label',展文(度量['hidden']) if callable(展文) else 展文)
                    正文=标签['expand']
                    展钮.textContent=正文(度量['hidden']) if callable(正文) else 正文
                def 点展开(事件):
                    '翻转封顶'
                    组件.切换展开()
                    组件.渲染()
                展钮.addEventListener('click',点展开)
                出.appendChild(展钮)
            if 度量['capped'] is True:
                尾=行列表[len(行列表)-度量['tailLines']:]
                for 线 in 尾:
                    出.appendChild(画行(线))
            根.appendChild(出)
    if 'parent' in 属性 and 属性['parent'] is not None:
        属性['parent'].appendChild(根)
    return 根

class 终端块:
    '终端卡。本地展开，复制写原始输出或 copyText'
    def __init__(自身,属性=None,**关键字参数):
        '合并 props。构造不画'
        自身.属性=dict(属性 if 属性 is not None else {})
        自身.属性.update(关键字参数)
        自身.已展开=False
        自身.反馈=复制反馈()
        自身.根=None

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=dict(属性)

    def 切换展开(自身):
        '翻转封顶'
        自身.已展开=not 自身.已展开

    def 渲染(自身):
        '拆掉旧卡，再画一次'
        if 自身.根 is not None:
            自身.根.remove()
        绘制=dict(自身.属性)
        绘制['组件']=自身
        窗口=自身.属性['window'] if 'window' in 自身.属性 else 取握手窗口()
        自身.根=处理终端块(窗口,绘制)
        return 自身.根

    def __call__(自身,属性=None,**关键字参数):
        '对齐 React 调用'
        if 属性 is not None or len(关键字参数)>0:
            合并=dict(属性 if 属性 is not None else {})
            合并.update(关键字参数)
            自身.更新(合并)
        return 自身.渲染()
