from ....ui_基础界面组件.icons import 图标,图标下箭头描边常规,图标右chevron14
from ....ui_基础界面组件.markdown.Markdown文本 import Markdown文本
from ....ui_对话.异常 import 标样式模块
from ..markdown标签 import markdown标签
from .用披露 import 注入聊天样式

__all__=['压缩项']

样式模块='message-item'


class 压缩项:
    '历史压缩标记。当前窗口有摘要才能展开'
    def __init__(自身,属性=None):
        '记下压缩节点'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.展开=False
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '有计数就写完成文案，否则用命令结算或不可用'
        if 自身.根 is not None:
            自身.根.remove()
            自身.根=None
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        注入聊天样式(文档,样式模块,'消息项.module.css')
        节点=属性.get('node') if isinstance(属性.get('node'),dict) else {}
        翻译=属性.get('t')
        if not callable(翻译):
            def 翻译(键,参数=None):
                '没有文案表时返回键'
                return 键
        可展=节点.get('summary') is not None
        打开=可展 and 自身.展开
        if 节点.get('shadowedItemCount') is not None and 节点.get('shadowedTokenCount') is not None:
            摘要=翻译('message.compaction.completed',{
                'items':节点.get('shadowedItemCount'),
                'tokens':节点.get('shadowedTokenCount'),
            })
        elif isinstance(属性.get('fallbackSummary'),str):
            摘要=属性['fallbackSummary']
        elif 可展:
            摘要=翻译('message.compaction.expand')
        else:
            摘要=翻译('message.compaction.unavailable')
        根=文档.createElement('div')
        根.className='compactionRow'
        标样式模块(根,样式模块)
        钮=文档.createElement('button')
        钮.type='button'
        钮.className='compactionButton'
        标样式模块(钮,样式模块)
        钮.disabled=not 可展
        if 可展:
            钮.setAttribute('aria-expanded','true' if 打开 else 'false')

        def 切换(事件=None):
            '有摘要才翻转'
            if not 可展:
                return
            自身.展开=not 自身.展开
            自身.渲染()

        钮.addEventListener('click',切换)
        前=文档.createElement('span')
        前.className='compactionLeading'
        标样式模块(前,样式模块)
        前.setAttribute('aria-hidden','true')
        图盒=文档.createElement('span')
        图盒.className='compactionContextIcon'
        标样式模块(图盒,样式模块)
        图盒.setAttribute('data-compaction-icon','context')
        图=图标('api-14',{'window':窗口})
        if 图 is not None:
            图盒.appendChild(图)
        折盒=文档.createElement('span')
        折盒.className='compactionDisclosureIcon'
        标样式模块(折盒,样式模块)
        折盒.setAttribute('data-compaction-disclosure','expanded' if 打开 else 'collapsed')
        折=图标下箭头描边常规({'window':窗口}) if 打开 else 图标右chevron14({'window':窗口})
        if 折 is not None:
            折盒.appendChild(折)
        前.appendChild(图盒)
        前.appendChild(折盒)
        钮.appendChild(前)
        题=文档.createElement('span')
        题.className='compactionTitle'
        标样式模块(题,样式模块)
        题.textContent=属性.get('title') if isinstance(属性.get('title'),str) else 翻译('message.compaction')
        钮.appendChild(题)
        隔=文档.createElement('span')
        隔.className='compactionSep'
        标样式模块(隔,样式模块)
        隔.setAttribute('aria-hidden','true')
        钮.appendChild(隔)
        摘=文档.createElement('span')
        摘.className='compactionSummary'
        标样式模块(摘,样式模块)
        摘.textContent=摘要
        钮.appendChild(摘)
        根.appendChild(钮)
        if 打开 and isinstance(节点.get('summary'),str):
            体=文档.createElement('div')
            体.className='compactionBody'
            标样式模块(体,样式模块)
            文=Markdown文本({'window':窗口,'text':节点['summary'],'labels':markdown标签(翻译)})
            画出=文.渲染()
            if 画出 is not None:
                体.appendChild(画出)
            根.appendChild(体)
        自身.根=根
        if 属性.get('parent') is not None:
            属性['parent'].appendChild(根)
        return 根
