from ...模块.客户端.通告 import 取握手窗口
import os
from ....工具.惰性导入 import 创建惰性导入
from ...ui_对话.异常 import 注入模块样式文件,模块节点
from ...ui_基础界面组件.按钮 import 按钮
from .文案 import 中文
from .终端主题 import 终端主题
from .终端光标 import 观察终端光标

__all__=['适配屏幕','终端屏幕','终端体']

样式路径=os.path.join(os.path.dirname(__file__),'终端体.module.css')
样式模块='terminal'
加载仿真=创建惰性导入('@xterm/xterm',__file__)
加载适配=创建惰性导入('@xterm/addon-fit',__file__)

def 适配屏幕(仿真,适配,状态,模型):
    '按视口与环境上限调整列行'
    尺寸=适配.proposeDimensions()
    if 尺寸 is None:
        return
    if isinstance(尺寸,dict):
        列数=尺寸['cols']
        行数=尺寸['rows']
    else:
        列数=尺寸.cols
        行数=尺寸.rows
    环境=状态['environment'] if isinstance(状态,dict) and isinstance(状态.get('environment'),dict) else None
    if 环境 is None:
        return
    列数=min(列数,环境['maxCols'])
    行数=min(行数,环境['maxRows'])
    if 列数<2 or 行数<1:
        return
    仿真.resize(列数,行数)
    模型.调整尺寸(列数,行数)

class 终端屏幕:
    '挂上仿真器，并跟上主题、字体、画面和尺寸'
    def __init__(自身,窗):
        '先留下屏幕节点。仿真等模型到了再开'
        自身.窗=窗
        自身.节点=模块节点(窗.document,'div',样式模块,'screen')
        自身.仿真=None
        自身.适配=None
        自身.调色=None
        自身.光标拆=None
        自身.输入拆=None
        自身.观察=None
        自身.上次修订=0
        自身.上次模型=None
        自身.上次字体=None
        自身.上次标签=None
        自身.上次焦点=None
        自身.上次尺寸=None
        自身.最新=None

    def 卸下(自身):
        '拆掉观察、输入、光标、调色和仿真'
        if 自身.观察 is not None:
            自身.观察.disconnect()
            自身.观察=None
        if 自身.输入拆 is not None:
            自身.输入拆.dispose()
            自身.输入拆=None
        if 自身.光标拆 is not None:
            自身.光标拆.dispose()
            自身.光标拆=None
        if 自身.调色 is not None:
            自身.调色.拆除()
            自身.调色=None
        if 自身.仿真 is not None:
            自身.仿真.dispose()
            自身.仿真=None
            自身.适配=None
        自身.上次模型=None
        自身.上次修订=0
        自身.上次尺寸=None
        自身.上次焦点=None

    def 挂仿真(自身,状态,模型,字体族,字号,标签):
        '按这一模型打开仿真，并接上输入和尺寸观察'
        自身.卸下()
        环境=状态['environment'] if isinstance(状态,dict) and isinstance(状态.get('environment'),dict) else None
        回滚=0
        if 环境 is not None and 环境.get('scrollback') is not None:
            回滚=环境['scrollback']
        仿真=加载仿真().Terminal({
            'minimumContrastRatio':4.5,
            'cursorBlink':True,
            'fontSize':字号,
            'fontFamily':字体族,
            'scrollback':回滚,
        })
        适配=加载适配().FitAddon()
        仿真.loadAddon(适配)
        仿真.open(自身.节点)
        调色=终端主题(仿真)
        样式=自身.窗.getComputedStyle(自身.节点)
        调色.更新(样式.backgroundColor,样式.color)

        def 优先光标():
            '当前光标色'
            return 调色.光标()

        自身.仿真=仿真
        自身.适配=适配
        自身.调色=调色
        自身.光标拆=观察终端光标(仿真,自身.节点,优先光标)
        输入区=仿真.textarea
        if 输入区 is not None:
            输入区.setAttribute('aria-label',标签)
        自身.上次标签=标签

        def 收到(数据):
            '把按键写进模型'
            模型.写入(数据)

        自身.输入拆=仿真.onData(收到)
        自身.上次修订=0

        def 测量():
            '可见且可写、节点有尺寸时才适配'
            现=自身.最新
            if 现 is None:
                return
            if 现['可见'] is not True or 现['状态'].get('writable') is not True:
                return
            if 自身.节点.clientWidth==0 or 自身.节点.clientHeight==0:
                return
            适配屏幕(仿真,适配,现['状态'],现['模型'])

        观察=自身.窗.ResizeObserver(测量)
        观察.observe(自身.节点)
        自身.观察=观察
        自身.上次模型=模型
        自身.上次字体=(字体族,字号)

    def 同步(自身,状态,模型,可见,标签,主题):
        '模型变了就重开仿真，其余只跟上变化'
        字体表=''
        字号=None
        if isinstance(主题,dict):
            族表=主题['fontFamilies'] if isinstance(主题.get('fontFamilies'),dict) else {}
            号表=主题['fontSizes'] if isinstance(主题.get('fontSizes'),dict) else {}
            if isinstance(族表.get('terminal'),str):
                字体表=族表['terminal']
            if 'terminal' in 号表:
                字号=号表['terminal']
        栈='ui-monospace, SFMono-Regular, Menlo, Consolas, monospace'
        if 字体表=='':
            字体族=栈
        else:
            字体族=字体表+', '+栈
        自身.最新={'状态':状态,'模型':模型,'可见':可见}
        if 自身.仿真 is None or 自身.上次模型 is not 模型:
            自身.挂仿真(状态,模型,字体族,字号,标签)
        仿真=自身.仿真
        if 标签!=自身.上次标签:
            输入区=仿真.textarea
            if 输入区 is not None:
                输入区.setAttribute('aria-label',标签)
            自身.上次标签=标签
        if 自身.上次字体!=(字体族,字号):
            if 仿真.options.fontFamily!=字体族 or 仿真.options.fontSize!=字号:
                仿真.options.fontFamily=字体族
                仿真.options.fontSize=字号
                if 可见 is True and 状态.get('writable') is True and 自身.节点.clientWidth and 自身.节点.clientHeight:
                    适配屏幕(仿真,自身.适配,状态,模型)
            自身.上次字体=(字体族,字号)
        if 自身.调色 is not None:
            样式=自身.窗.getComputedStyle(自身.节点)
            自身.调色.更新(样式.backgroundColor,样式.color)
        渲染帧=状态['render'] if isinstance(状态.get('render'),dict) else None
        if 渲染帧 is not None and 渲染帧.get('revision') is not None and 渲染帧['revision']>自身.上次修订:
            自身.上次修订=渲染帧['revision']
            帧=渲染帧['frame']
            if 帧['type']=='snapshot':
                仿真.reset()
                仿真.resize(帧['info']['cols'],帧['info']['rows'])
                数据=帧['screen']
            else:
                数据=帧['data']

            def 确认写完(修订=渲染帧['revision']):
                '画面写入完成后确认修订'
                模型.确认(修订)

            仿真.write(数据,确认写完)
        可写=状态.get('writable') is True
        仿真.options.disableStdin=可写 is not True
        信息=状态['info'] if isinstance(状态.get('info'),dict) else None
        列=None if 信息 is None else 信息.get('cols')
        行=None if 信息 is None else 信息.get('rows')
        尺寸键=(可见,可写,列,行,模型)
        if 尺寸键!=自身.上次尺寸:
            if 可见 is True and 可写 and 自身.节点.clientWidth and 自身.节点.clientHeight:
                适配屏幕(仿真,自身.适配,状态,模型)
            elif 信息 is not None and 可写 is not True:
                仿真.resize(信息['cols'],信息['rows'])
            自身.上次尺寸=尺寸键
        焦点=可见 is True and 可写
        if 焦点 and 自身.上次焦点 is not True:
            仿真.focus()
        自身.上次焦点=焦点

class 终端体:
    '保留终端、主题和状态条'
    def __init__(自身,属性=None):
        '记下份额并画出'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.屏幕=None
        自身.模型=None
        自身.挂载拆=None
        自身.拆=[]
        自身.已订=None
        自身.绘制中=False
        自身.待再画=False
        自身.页标识=None
        自身.渲染()

    def 更新(自身,属性):
        '换上一份份额'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 退订(自身):
        '摘掉状态和主题订阅'
        副本=list(自身.拆)
        自身.拆=[]
        自身.已订=None
        for 卸 in 副本:
            卸()

    def 卸下(自身):
        '卸挂模型并拆掉仿真'
        if 自身.挂载拆 is not None:
            自身.挂载拆()
            自身.挂载拆=None
        if 自身.屏幕 is not None:
            自身.屏幕.卸下()
            自身.屏幕=None
        自身.退订()
        if 自身.根 is not None:
            自身.根.remove()
            自身.根=None
        自身.模型=None
        if 自身.页标识 is not None:
            from .惰性终端体 import _实例
            if _实例.get(自身.页标识) is 自身:
                del _实例[自身.页标识]

    def 换模型(自身,模型,标签):
        '同一个模型只挂一次。出现结束时卸掉'
        if 自身.模型 is 模型:
            return
        if 自身.挂载拆 is not None:
            自身.挂载拆()
            自身.挂载拆=None
        自身.退订()
        自身.模型=模型
        自身.挂载拆=模型.挂载()

        def 变更(*参数):
            '状态或主题变了就重画。节点已被摘掉则退订'
            if 自身.根 is not None and getattr(自身.根,'isConnected',True) is False:
                自身.退订()
                return
            自身.渲染()

        自身.拆.append(模型.状态.subscribe(变更))
        用主题=自身.属性.get('useTheme')
        if callable(getattr(用主题,'_subscribe',None)):
            自身.拆.append(用主题._subscribe(变更))
        自身.已订=模型
        信号=标签.get('signal')
        if 信号 is not None:
            def 结束():
                '这一次出现结束'
                自身.卸下()
            信号.addEventListener('abort',结束)

    def 渲染(自身):
        '画出状态条、屏幕和错误。绘制中再来的通知等这一次结束'
        if 自身.绘制中:
            自身.待再画=True
            return 自身.根
        自身.绘制中=True
        try:
            自身.画出()
        finally:
            自身.绘制中=False
        if 自身.待再画:
            自身.待再画=False
            自身.渲染()
        return 自身.根

    def 画出(自身):
        '按当前状态填这一节'
        属性=自身.属性
        if isinstance(属性,dict) and 属性.get('window') is not None:
            窗=属性['window']
        else:
            窗=取握手窗口()
        文档=窗.document
        注入模块样式文件(文档,'终端体样式',样式路径,样式模块)
        标签=属性['useTabInfo']()['tab']
        自身.页标识=标签['id']
        模型=属性['view'](标签['id'])
        自身.换模型(模型,标签)
        状态=属性['useTerminal'](标签['id'])
        if 自身.根 is None:
            自身.根=模块节点(文档,'section',样式模块,'root')
            自身.根.setAttribute('data-sidebar-terminal','')
        while 自身.根.firstChild is not None:
            自身.根.firstChild.remove()
        if 状态 is None:
            return
        可见=标签.get('visible') is True

        def 造新建(尺寸):
            '新建终端按钮'
            def 打开():
                '用新终端替换当前页签'
                标签['actions']['openTab']('terminal',{'replaceTab':True})

            钮=按钮({
                'window':窗,
                'variant':'primary',
                'size':尺寸,
                'children':'新建终端',
                'onClick':打开,
            }).渲染()
            标=模块节点(文档,'span',样式模块,'actionIcon')
            标.setAttribute('aria-hidden','true')
            图=文档.createElementNS('http://www.w3.org/2000/svg','svg')
            图.setAttribute('width','16')
            图.setAttribute('height','16')
            图.setAttribute('viewBox','0 0 16 16')
            图.setAttribute('fill','none')
            图.setAttribute('stroke-width','1')
            图.setAttribute('aria-hidden','true')
            for 路径 in ('M8 2V14','M2 8H14'):
                笔=文档.createElementNS('http://www.w3.org/2000/svg','path')
                笔.setAttribute('d',路径)
                笔.setAttribute('stroke','currentColor')
                图.appendChild(笔)
            标.appendChild(图)
            if 钮.firstChild is not None:
                钮.insertBefore(标,钮.firstChild)
            else:
                钮.appendChild(标)
            return 钮

        if 状态.get('issue')=='missingTerminal':
            if 自身.屏幕 is not None:
                自身.屏幕.卸下()
                自身.屏幕=None
            空=模块节点(文档,'div',样式模块,'empty')
            图=文档.createElementNS('http://www.w3.org/2000/svg','svg')
            图.setAttribute('width','36')
            图.setAttribute('height','36')
            图.setAttribute('viewBox','0 0 28 28')
            图.setAttribute('fill','none')
            图.setAttribute('aria-hidden','true')
            框=文档.createElementNS('http://www.w3.org/2000/svg','rect')
            框.setAttribute('x','3')
            框.setAttribute('y','5')
            框.setAttribute('width','22')
            框.setAttribute('height','19')
            框.setAttribute('rx','3')
            框.setAttribute('fill','#17191d')
            线=文档.createElementNS('http://www.w3.org/2000/svg','path')
            线.setAttribute('d','m8 10 4 4-4 4M15 18h5')
            线.setAttribute('stroke','#fff')
            线.setAttribute('stroke-width','1.7')
            线.setAttribute('stroke-linecap','round')
            线.setAttribute('stroke-linejoin','round')
            图.appendChild(框)
            图.appendChild(线)
            空.appendChild(图)
            讯=模块节点(文档,'p',样式模块,'emptyMessage')
            讯.setAttribute('role','alert')
            讯.textContent='此终端已不存在，请新建终端。'
            空.appendChild(讯)
            空.appendChild(造新建('md'))
            自身.根.appendChild(空)
            return
        阶段=状态.get('phase')
        信息=状态['info'] if isinstance(状态.get('info'),dict) else None
        状态文=None
        if 阶段=='idle' or 阶段=='loading':
            状态文='正在读取终端环境…'
        elif 阶段=='creating':
            状态文='正在启动…'
        elif 阶段=='connecting':
            状态文='正在连接…'
        elif 阶段=='disconnected':
            状态文='连接已断开。'
        elif 信息 is not None and 信息.get('state')=='exited':
            码=信息['exitCode'] if 'exitCode' in 信息 and 信息['exitCode'] is not None else '—'
            状态文='进程已退出（'+str(码)+'）'
        elif 信息 is not None and 信息.get('state')=='failed':
            状态文='不可用'
        elif 阶段=='closed':
            状态文='终端已关闭。'
        结束=阶段=='closed' or (信息 is not None and 信息.get('state')=='exited')
        可重试=结束 is not True and (阶段=='failed' or 阶段=='disconnected')
        只读=阶段=='connected' and 信息 is not None and 信息.get('state')=='running' and 状态.get('writable') is not True
        if 状态文 is not None or 可重试 or 只读 or 结束:
            条=模块节点(文档,'div',样式模块,'status')
            条.setAttribute('role','status')
            if 状态文 is not None:
                条.appendChild(文档.createTextNode(状态文))

            def 造钮(文案,点击):
                '描边小按钮'
                return 按钮({
                    'window':窗,
                    'variant':'outline',
                    'size':'sm',
                    'children':文案,
                    'onClick':点击,
                }).渲染()

            if 只读:
                条.appendChild(文档.createTextNode('此页面当前只读。'))

                def 接管():
                    '接管输入'
                    模型.连接()

                条.appendChild(造钮('接管输入',接管))
            if 可重试:
                if 信息 is None:
                    文案='重新连接' if 阶段=='disconnected' else '重试'

                    def 刷新():
                        '重新读取终端'
                        模型.刷新()

                    条.appendChild(造钮(文案,刷新))
                else:
                    def 重连():
                        '重新连接'
                        模型.连接()

                    条.appendChild(造钮('重新连接',重连))
            if 结束:
                条.appendChild(造新建('sm'))
            自身.根.appendChild(条)
        if 信息 is not None:
            if 自身.屏幕 is None:
                自身.屏幕=终端屏幕(窗)
            自身.根.appendChild(自身.屏幕.节点)

            def 原样(值):
                '主题快照'
                return 值

            主题=属性['useTheme'](原样)
            自身.屏幕.同步(状态,模型,可见,'终端',主题)
        elif 自身.屏幕 is not None:
            自身.屏幕.卸下()
            自身.屏幕=None
        错误=None
        if 阶段!='disconnected':
            if 状态.get('issue') is not None:
                错误=中文[状态['issue']]
            elif 状态.get('error') is not None:
                错误=状态['error']
            elif 信息 is not None and 信息.get('error') is not None:
                错误=信息['error']
        if 错误 is not None:
            败=模块节点(文档,'p',样式模块,'error')
            败.setAttribute('role','alert')
            败.textContent='终端错误：'+str(错误)
            自身.根.appendChild(败)
        父=属性.get('parent')
        if 父 is not None and getattr(自身.根,'parentNode',None) is None:
            父.appendChild(自身.根)

    def __call__(自身,属性=None):
        '有新属性先更新，再画出'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
