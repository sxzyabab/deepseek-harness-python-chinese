import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_基础界面组件.icons import 图标上chevron14,图标下chevron14,图标接口14,图标检视12
from ...ui_基础界面组件.文字闪烁 import 文字闪烁
from ...ui_基础界面组件.命令文本 import 命令文本
from ...ui_基础界面组件.终端块 import 终端块
from .文案 import 会话命名空间,中文文案
from .终端卡模型 import (
    是后台外壳调用,是已结算持久外壳调用,是溢出外壳调用,
    本地化终端卡模型,终端块文案,终端卡模型,终端已失败,终端退出文案,
)
from .调用模型 import 格式化工具体,工具行模型
from .退出代码角标 import 退出代码角标
from .槽 import 槽名工具调用视图

__all__=['bash行','bash工具视图样例']

样式模块='dsh-tool-bash'

def 确保样式(文档):
    'bash 样例样式只插一次'
    注入模块样式文件(
        文档,
        'dsh-tool-bash',
        os.path.join(os.path.dirname(__file__),'bash样例.module.css'),
        样式模块,
    )

def 元素(文档,标签,类名=None):
    '带样式模块的节点'
    节点=文档.createElement(标签)
    if isinstance(类名,str) and 类名!='':
        节点.className=类名
        标样式模块(节点,样式模块)
    return 节点

def 状态文案(状态):
    '准备、运行、失败、停止的读屏文案'
    if 状态=='preparing':
        return 中文文案('row.preparing')
    if 状态=='running':
        return 中文文案('bash.running')
    if 状态=='error':
        return 中文文案('bash.failed')
    if 状态=='stopped':
        return 中文文案('bash.stopped')
    return None

class bash行:
    '可展开的命令输出。准备中只显示已经流到的描述'
    def __new__(类,属性):
        '画出命令行'
        自身=object.__new__(类)
        自身.属性=属性 if isinstance(属性,dict) else {}
        return 自身.渲染()

    def 渲染(自身):
        '终端卡或通用输入输出'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        确保样式(文档)
        模型=工具行模型(属性['toolName'],属性['block'])
        工作区=None
        if 'useSessions' in 属性 and 属性['useSessions'] is not None:
            def 取工作区(列表,会话标识=属性.get('sessionId')):
                '这一会话的工作区'
                if not isinstance(列表,dict):
                    return None
                按标识=列表.get('byId')
                if not isinstance(按标识,dict) or 会话标识 not in 按标识:
                    return None
                会话=按标识[会话标识]
                if isinstance(会话,dict):
                    return 会话.get('cwd')
                return None
            工作区=属性['useSessions'](取工作区)
        终端模型=终端卡模型(属性['block'],工作区)
        终端=None if 终端模型 is None else 本地化终端卡模型(终端模型)
        if 模型['state']=='ok' and 终端模型 is not None and 终端已失败(终端模型):
            状态='error'
        else:
            状态=模型['state']
        披露=属性['useDisclosure']()
        已展开=披露['expanded'] is True
        切换=披露['toggle']
        后台=是后台外壳调用(属性['block'])
        通用体=终端 is None and (
            模型['state']=='error'
            or 是已结算持久外壳调用(属性['block'])
            or 是溢出外壳调用(属性['block'])
            or 后台
        ) and (模型['bodyRaw'] is not None or 模型['output'] is not None)
        可展=终端 is not None or 通用体
        打开=已展开 and 可展
        体=None
        if 打开 and 通用体 and 模型['bodyRaw'] is not None:
            体=格式化工具体(模型['variant'],模型['bodyRaw'])
        if 终端 is not None and 终端.get('description') is not None:
            普通摘要=终端['description']
        else:
            普通摘要=模型['summary']
        退出文=终端退出文案(终端模型)
        if 退出文 is not None:
            结算行=None
        elif 状态=='error':
            结算行=模型['errorSummary'] if 模型['errorSummary'] is not None else 普通摘要
        elif 状态=='stopped':
            结算行=中文文案('bash.stopped')
        else:
            结算行=None
        运行=状态=='running' or 状态=='preparing'
        卡=元素(文档,'div','card')
        根=元素(文档,'div','root')
        根.setAttribute('data-sample','bash')
        根.setAttribute('data-variant','bash')
        根.setAttribute('data-state',状态)
        if 可展:
            根.setAttribute('data-expandable','')
            根.setAttribute('role','button')
            根.tabIndex=0
            根.setAttribute('aria-expanded','true' if 打开 else 'false')
            def 点行(事件,切换=切换):
                '切换展开'
                切换()
            def 键行(事件,切换=切换):
                '回车或空格切换展开'
                if 事件.key!='Enter' and 事件.key!=' ':
                    return
                事件.preventDefault()
                切换()
            根.addEventListener('click',点行)
            根.addEventListener('keydown',键行)
        前导=元素(文档,'span','leading')
        if 打开:
            前导.appendChild(图标上chevron14({'window':窗口,'className':'chevron'}))
        elif 可展:
            闲=元素(文档,'span','iconIdle')
            闲.appendChild(图标接口14({'window':窗口,'size':14}))
            前导.appendChild(闲)
            前导.appendChild(图标下chevron14({'window':窗口,'className':'chevron chevronHover'}))
        else:
            前导.appendChild(图标接口14({'window':窗口,'size':14}))
        根.appendChild(前导)
        读屏=状态文案(状态)
        if 读屏 is not None:
            隐藏=元素(文档,'span','visuallyHidden')
            隐藏.textContent=读屏
            根.appendChild(隐藏)
        根.appendChild(文字闪烁({
            'window':窗口,
            'active':运行,
            'children':中文文案(模型['titleKey']),
            'className':'title',
        }).渲染())
        点=元素(文档,'span','sep')
        点.setAttribute('data-shimmer-decoration','')
        点.setAttribute('aria-hidden','true')
        根.appendChild(点)
        类名='summary'
        if 退出文 is None and 状态=='error':
            类名=类名+' errorSummary'
        if 退出文 is None and 状态=='stopped':
            类名=类名+' stoppedSummary'
        摘=元素(文档,'span',类名)
        摘.textContent='' if 结算行 is None else 结算行
        if 结算行 is None:
            摘.textContent=普通摘要
        根.appendChild(摘)
        if 退出文 is not None:
            根.appendChild(退出代码角标({'window':窗口,'label':退出文}))
        卡.appendChild(根)
        if 打开:
            包=元素(文档,'div','bodyWrap')
            if 终端 is not None:
                卡属性=dict(终端['card'])
                卡属性['window']=窗口
                卡属性['maxLines']=None
                卡属性['labels']=终端块文案()
                卡属性['className']='terminal'
                包.appendChild(终端块(卡属性).渲染())
            else:
                盒=元素(文档,'div','ioCard')
                if 体 is not None:
                    段=元素(文档,'div','ioSection')
                    标=元素(文档,'span','ioLabel')
                    标.textContent=中文文案('row.input')
                    段.appendChild(标)
                    if 后台:
                        段.appendChild(命令文本({
                            'window':窗口,
                            'className':'commandInput',
                            'text':体,
                            'label':中文文案('row.commandArguments'),
                        }).渲染())
                    else:
                        文=元素(文档,'span','ioText')
                        文.textContent=体
                        段.appendChild(文)
                    盒.appendChild(段)
                if 体 is not None and 模型['output'] is not None:
                    盒.appendChild(元素(文档,'span','ioDivider'))
                if 模型['output'] is not None:
                    段=元素(文档,'div','ioSection')
                    标=元素(文档,'span','ioLabel')
                    标.textContent=中文文案('row.output')
                    文=元素(文档,'span','ioText')
                    if 状态=='error':
                        文.setAttribute('data-error','')
                    文.textContent=模型['output']
                    段.appendChild(标)
                    段.appendChild(文)
                    盒.appendChild(段)
                包.appendChild(盒)
            查看=属性.get('inspect')
            if 查看 is not None:
                钮=元素(文档,'button','inspectButton')
                钮.type='button'
                钮.appendChild(图标检视12({'window':窗口}))
                钮.appendChild(文档.createTextNode(中文文案('row.inspect')))
                def 点查看(事件,查看=查看):
                    '打开轨迹'
                    查看()
                钮.addEventListener('click',点查看)
                包.appendChild(钮)
            卡.appendChild(包)
        return 卡

def 应用bash工具视图(上下文,配置=None):
    '登记 bash 样例行'
    def 登记():
        '写入 bash 键'
        return 上下文.slots.register({
            'name':槽名工具调用视图,
            'key':'bash',
            'locale':会话命名空间,
        },bash行)
    上下文.slots.inject(槽名工具调用视图,登记)

bash工具视图样例={
    'name':'bash-toolview-sample',
    'inject':['slots'],
    'apply':应用bash工具视图,
}
