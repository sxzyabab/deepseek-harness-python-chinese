from ....ui_基础界面组件.icons import 图标分支16,图标勾16,图标复制16
from ....ui_基础界面组件.剪贴板 import 写剪贴板
from ....ui_对话.异常 import 标样式模块
from .消息铬 import 格式化消息时钟
from .用披露 import 注入聊天样式,真属性
from .用日历日 import 用日历日

__all__=['消息图标动作']

样式模块='message-icon-actions'


class 消息图标动作:
    '复制、可选的分叉，以及日期时钟'
    def __init__(自身,属性=None):
        '记下要复制的文本'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.已复制=False
        自身.复制中=False
        自身.复制代=0
        自身.定时=None
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 拆除(自身):
        '卸掉复制成功的定时器'
        自身.复制代+=1
        自身.复制中=False
        if 自身.定时 is not None:
            窗=自身.属性['window']
            if hasattr(窗,'clearTimeout'):
                窗.clearTimeout(自身.定时)
            自身.定时=None

    def 渲染(自身):
        '时钟在用户侧排前面，在助手侧排到图标后面'
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        注入聊天样式(文档,样式模块,'消息图标动作.module.css')
        翻译=属性.get('t')
        if not callable(翻译):
            def 翻译(键,参数=None):
                '没有文案表时返回键'
                return 键
        日=用日历日()
        时钟侧=属性.get('clock') or 'end'
        时刻=属性.get('time')
        根=文档.createElement('div')
        类名='actions'
        if isinstance(属性.get('className'),str) and 属性['className']!='':
            类名=类名+' '+属性['className']
        根.className=类名
        标样式模块(根,样式模块)
        根.setAttribute('data-clock',时钟侧)
        时钟=None
        if isinstance(时刻,(int,float)) and not isinstance(时刻,bool):
            时钟=文档.createElement('span')
            时钟.className='timeStart' if 时钟侧=='start' else 'timeEnd'
            标样式模块(时钟,样式模块)
            时钟.textContent=格式化消息时钟(时刻,翻译,日)
        if 时钟侧=='start' and 时钟 is not None:
            根.appendChild(时钟)
        复制钮=文档.createElement('button')
        复制钮.type='button'
        复制钮.className='action'
        标样式模块(复制钮,样式模块)
        复制文=翻译('copied') if 自身.已复制 else 翻译('copy')
        复制钮.setAttribute('aria-label',复制文)
        复制钮.setAttribute('title',复制文)
        图=图标勾16({'window':窗口}) if 自身.已复制 else 图标复制16({'window':窗口})
        if 图 is not None:
            复制钮.appendChild(图)

        def 复制(事件=None):
            '成功后一秒换回复制图标。这段时间不再写一次'
            if 自身.已复制 or 自身.复制中:
                return
            代=自身.复制代
            自身.复制中=True
            好=False
            try:
                好=写剪贴板(属性.get('text') or '') is not False
            except Exception:
                好=False
            if 代!=自身.复制代:
                return
            自身.复制中=False
            if not 好:
                return
            自身.已复制=True
            def 还原():
                '一秒后恢复'
                自身.定时=None
                自身.已复制=False
                自身.渲染()
            自身.定时=窗口.setTimeout(还原,1000)
            自身.渲染()

        复制钮.addEventListener('click',复制)
        根.appendChild(复制钮)
        额外=属性.get('extraActions')
        if 额外 is not None and hasattr(额外,'tagName'):
            根.appendChild(额外)
        elif 额外 is not None and hasattr(额外,'渲染'):
            画出=额外.渲染()
            if 画出 is not None:
                根.appendChild(画出)
        分叉=属性.get('onBranch')
        不可用=属性.get('branchUnavailable') is True
        if callable(分叉):
            原因号='branch-reason-'+str(id(自身))
            叉钮=文档.createElement('button')
            叉钮.type='button'
            叉钮.className='action'
            标样式模块(叉钮,样式模块)
            叉钮.setAttribute('aria-label',翻译('message.branch'))
            叉钮.setAttribute('title',翻译('message.branchUnavailable') if 不可用 else 翻译('message.branch'))
            真属性(叉钮,'aria-disabled',不可用)
            真属性(叉钮,'data-unavailable',不可用)
            if 不可用:
                叉钮.setAttribute('aria-describedby',原因号)
            叉图=图标分支16({'window':窗口})
            if 叉图 is not None:
                叉钮.appendChild(叉图)
            if not 不可用:
                def 点叉(事件=None):
                    '从这条消息分叉'
                    分叉()
                叉钮.addEventListener('click',点叉)
            根.appendChild(叉钮)
            if 不可用:
                原因=文档.createElement('span')
                原因.id=原因号
                原因.className='visuallyHidden'
                标样式模块(原因,样式模块)
                原因.textContent=翻译('message.branchUnavailable')
                根.appendChild(原因)
        用量=属性.get('usageAction')
        if 时钟侧=='end':
            尾=文档.createElement('span')
            尾.className='endInfo'
            标样式模块(尾,样式模块)
            if 用量 is not None and hasattr(用量,'tagName'):
                尾.appendChild(用量)
            elif 用量 is not None and hasattr(用量,'渲染'):
                画出=用量.渲染()
                if 画出 is not None:
                    尾.appendChild(画出)
            if 时钟 is not None:
                尾.appendChild(时钟)
            根.appendChild(尾)
        elif 用量 is not None and hasattr(用量,'tagName'):
            根.appendChild(用量)
        自身.根=根
        if 属性.get('parent') is not None:
            属性['parent'].appendChild(根)
        return 根
