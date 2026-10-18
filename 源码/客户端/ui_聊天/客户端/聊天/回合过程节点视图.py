from ....ui_基础界面组件.icons import 图标下箭头描边常规
from ....ui_对话.异常 import 标样式模块
from ..约定.回合过程 import 回合过程始终打开
from .消息铬 import 格式化运行时长
from .用披露 import 注入聊天样式,真属性

__all__=['回合过程节点视图']

样式模块='turn-process'
无障碍模块='a11y'


class 回合过程节点视图:
    '回合收束后的用时和过程折叠'
    def __init__(自身,属性=None):
        '记下过程节点'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '还没结束的回合不画。停止和失败不显示用时'
        if 自身.根 is not None:
            自身.根.remove()
            自身.根=None
        属性=自身.属性
        过程=属性.get('turnProcess')
        if not isinstance(过程,dict):
            from ...异常 import 聊天错误
            raise 聊天错误('turn-process node requires Turn process owner state')
        窗口=属性['window']
        文档=窗口.document
        注入聊天样式(文档,样式模块,'回合过程节点视图.module.css')
        注入聊天样式(文档,无障碍模块,'无障碍.module.css')
        翻译=属性.get('t')
        if not callable(翻译):
            def 翻译(键,参数=None):
                '没有文案表时返回键'
                return 键
        节点=属性.get('node') if isinstance(属性.get('node'),dict) else {}
        打开=(not 过程.get('foldable')) or 过程.get('open') is True
        位置=节点.get('location') if isinstance(节点.get('location'),dict) else {}
        回合=位置.get('turn') if 位置.get('kind') in ('turn','step') and isinstance(位置.get('turn'),dict) else None
        if not isinstance(回合,dict) or 回合.get('status')!='closed':
            return None
        可收=过程.get('foldable') is True and 过程.get('hasContent') is True and not 回合过程始终打开(节点)
        结束=回合.get('end') if isinstance(回合.get('end'),dict) else {}
        原因数据=结束.get('data') if isinstance(结束.get('data'),dict) else {}
        原因=原因数据.get('reason') if isinstance(原因数据.get('reason'),dict) else {}
        种类=原因.get('kind')
        已停=种类 in ('aborted','interrupted')
        经过=None
        if isinstance(回合.get('start'),dict) and isinstance(回合.get('end'),dict):
            经过=max(1000,回合['end'].get('time',0)-回合['start'].get('time',0))
        时长=None
        if 经过 is not None and not 已停 and 种类!='error':
            时长=格式化运行时长(经过,翻译)
        if 已停:
            标签=翻译('message.stopped')
        elif 种类=='error':
            标签=翻译('message.turnProcess.failed')
        elif 时长 is None:
            标签=翻译('message.turnProcess.worked')
        else:
            标签=翻译('message.turnProcess.took')
        if 已停:
            播报=翻译('message.stopped')
        elif 种类=='error':
            播报=翻译('message.turnProcess.failed')
        else:
            播报=翻译('message.turnProcess.worked')
        根=文档.createDocumentFragment()
        隐=文档.createElement('span')
        隐.className='visuallyHidden'
        标样式模块(隐,无障碍模块)
        隐.setAttribute('role','status')
        隐.setAttribute('aria-live','polite')
        隐.setAttribute('aria-atomic','true')
        隐.textContent=播报
        根.appendChild(隐)
        钮=文档.createElement('button')
        钮.type='button'
        钮.className='root'
        标样式模块(钮,样式模块)
        真属性(钮,'data-open',打开)
        数据=节点.get('data') if isinstance(节点.get('data'),dict) else {}
        钮.setAttribute('data-turn-process',str(数据.get('turn')))
        钮.setAttribute('data-turn-process-messages',str(数据.get('messageCount')))
        钮.setAttribute('data-turn-process-tool-calls',str(数据.get('toolCallCount')))
        钮.setAttribute('data-turn-process-subagents',str(数据.get('subagentCount')))
        钮.disabled=not 可收
        if 过程.get('hasContent') is True:
            钮.setAttribute('aria-expanded','true' if 打开 else 'false')
        文=文档.createElement('span')
        文.className='label'
        标样式模块(文,样式模块)
        文.appendChild(文档.createTextNode(标签))
        if isinstance(时长,list):
            for 段 in 时长:
                片=文档.createElement('span')
                if 段.get('numeric') is True:
                    片.className='durationNumber'
                    标样式模块(片,样式模块)
                片.textContent=段.get('text') or ''
                文.appendChild(片)
        钮.appendChild(文)
        if 可收:
            箭头=图标下箭头描边常规({'window':窗口,'className':'chevron'})
            if 箭头 is not None:
                标样式模块(箭头,样式模块)
                钮.appendChild(箭头)

        def 点击(事件=None):
            '先聚焦，再翻转过程开合'
            if hasattr(钮,'focus'):
                钮.focus()
            设开=过程.get('setOpen')
            if callable(设开):
                设开(not 打开)

        钮.addEventListener('click',点击)
        根.appendChild(钮)
        自身.根=根
        if 属性.get('parent') is not None:
            属性['parent'].appendChild(根)
        return 根
