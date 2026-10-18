'一场会话的反馈对话框，以及记下之后和失败时的轻提示'
import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_基础界面组件.按钮 import 处理按钮
from ...ui_基础界面组件.模态 import 处理模态
from ...ui_基础界面组件.吐司 import 处理吐司
from ...ui_基础界面组件.icons import 描边图标
from .文案 import 中文

__all__=['反馈对话框']

样式模块='feedback-dialog'
反馈类别=(
    'task-result',
    'instruction-following',
    'product-interaction',
    'service-stability',
    'resource-cost',
    'security-privacy-permission',
    'other',
)
警告路径=(
    'M8 14.5C11.5899 14.5 14.5 11.5899 14.5 8C14.5 4.41015 11.5899 1.5 8 1.5C4.41015 1.5 1.5 4.41015 1.5 8C1.5 11.5899 4.41015 14.5 8 14.5Z',
    'M8 4.29199V9.79199',
    'M8 10.708V11.708',
)

class 反馈对话框:
    '对话框和两条轻提示。探针留在撰写栏里，用来对齐轻提示'
    活={}

    def __init__(自身,属性):
        '记下 props。同一场已有实例时把浮层让出来，不退役轻提示'
        自身.属性=属性
        自身.根=None
        自身.探针=None
        自身.窗口=None
        自身.状态快照=None
        自身.显示序号=0
        自身.罩=None
        自身.分类钮=()
        自身.正文框=None
        自身.提交钮=None
        自身.确认条=None
        自身.确认序号=0
        自身.确认锚=None
        自身.确认代=0
        自身.失败条=None
        自身.失败码=None
        自身.失败锚=None
        自身.失败代=0
        自身.卡片=None
        自身.已量=False
        自身.已约量=False
        自身.已订=False
        自身.退订=None
        自身.观察=None
        自身.移交=False
        自身.已卸=False
        自身.绘制中=False
        自身.待重画=False
        自身.曾挂上=False
        键=id(属性['useDialog'])
        自身.键=键
        旧=反馈对话框.活.get(键)
        if 旧 is not None and 旧 is not 自身:
            旧.移交=True
            旧.拆监听()
            旧.拆浮层()
        反馈对话框.活[键]=自身
        自身.渲染()

    def 拆监听(自身):
        '卸掉状态订阅和拆除观察'
        if 自身.观察 is not None:
            自身.观察.disconnect()
            自身.观察=None
        if 自身.退订 is not None:
            退=自身.退订
            自身.退订=None
            自身.已订=False
            退()

    def 拆浮层(自身):
        '拿掉门户上的对话框和轻提示'
        if 自身.罩 is not None:
            自身.罩.remove()
            自身.罩=None
        if 自身.确认条 is not None:
            自身.确认条.remove()
            自身.确认条=None
            自身.确认代+=1
        if 自身.失败条 is not None:
            自身.失败条.remove()
            自身.失败条=None
            自身.失败代+=1
        自身.分类钮=()
        自身.正文框=None
        自身.提交钮=None
        自身.确认序号=0
        自身.失败码=None

    def 卸下(自身):
        '入口真正离开、且没有新实例接上时，退役当前轻提示'
        if 自身.已卸:
            return
        if 自身.移交:
            自身.拆监听()
            return
        自身.已卸=True
        序号=自身.显示序号
        自身.拆监听()
        自身.拆浮层()
        自身.属性['dismissToast'](序号)

    def 点分类(自身,事件):
        '再点已选中的分类就清掉'
        类别=事件.currentTarget.getAttribute('data-category')
        if 自身.状态快照['category']==类别:
            自身.属性['edit']({'category':None})
        else:
            自身.属性['edit']({'category':类别})

    def 改文(自身,事件):
        '把输入框里的文字交回草稿'
        自身.属性['edit']({'text':事件.target.value})

    def 点提交(自身,事件=None):
        '提交当前草稿'
        自身.属性['submit']()

    def 渲染(自身):
        '按当前草稿画对话框。确认和失败轻提示对着撰写卡'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        画完=False
        try:
            属性=自身.属性
            窗口=属性['window']
            自身.窗口=窗口
            文档=窗口.document
            注入模块样式文件(
                文档,
                '反馈对话框样式',
                os.path.join(os.path.dirname(__file__),'反馈对话框.module.css'),
                样式模块,
            )
            def 全量(快照):
                '对话框整份状态。上游选择器原样返回'
                return 快照
            状态=属性['useDialog'](全量)
            自身.状态快照=状态
            自身.显示序号=状态['toast']
            if 自身.根 is None:
                根=文档.createElement('span')
                根.style.display='contents'
                探针=文档.createElement('span')
                探针.setAttribute('hidden','')
                根.appendChild(探针)
                自身.根=根
                自身.探针=探针
            失败码=状态['failure']
            if 失败码 is None:
                失败文=None
            elif 失败码=='version-conflict':
                失败文=中文['error.conflict']
            elif 失败码=='note-too-large':
                失败文=中文['error.noteTooLarge']
            else:
                失败文=中文['error.generic']
            要确认=状态['toast']>0 and 失败文 is None
            要失败=失败文 is not None
            if 要确认:
                换确认=自身.确认条 is None or 自身.确认序号!=状态['toast'] or 自身.确认锚 is not 自身.卡片
                if 换确认:
                    自身.确认代+=1
                    if 自身.确认条 is not None:
                        自身.确认条.remove()
                        自身.确认条=None
                    序号=状态['toast']
                    代=自身.确认代
                    def 结束确认():
                        '这条确认轻提示淡出完了。换过一条的旧计时不再退役'
                        if 代!=自身.确认代:
                            return
                        属性['dismissToast'](序号)
                    自身.确认条=处理吐司(窗口,{
                        'text':中文['toast.recorded'],
                        'tone':'success',
                        'anchor':自身.卡片,
                        'onDone':结束确认,
                        'window':窗口,
                    })
                    自身.确认序号=序号
                    自身.确认锚=自身.卡片
            elif 自身.确认条 is not None:
                自身.确认代+=1
                自身.确认条.remove()
                自身.确认条=None
                自身.确认序号=0
            if 要失败:
                换失败=自身.失败条 is None or 自身.失败码!=失败码 or 自身.失败锚 is not 自身.卡片
                if 换失败:
                    自身.失败代+=1
                    if 自身.失败条 is not None:
                        自身.失败条.remove()
                        自身.失败条=None
                    图=描边图标({'window':窗口},'0 0 16 16',list(警告路径))
                    代=自身.失败代
                    def 结束失败():
                        '失败轻提示淡出完了。换过一条的旧计时不再关掉失败'
                        if 代!=自身.失败代:
                            return
                        属性['dismissFailure']()
                    自身.失败条=处理吐司(窗口,{
                        'text':失败文,
                        'icon':图,
                        'anchor':自身.卡片,
                        'holdMs':6000,
                        'onDone':结束失败,
                        'window':窗口,
                    })
                    自身.失败码=失败码
                    自身.失败锚=自身.卡片
            elif 自身.失败条 is not None:
                自身.失败代+=1
                自身.失败条.remove()
                自身.失败条=None
                自身.失败码=None
            if 状态['target'] is None:
                if 自身.罩 is not None:
                    自身.罩.remove()
                    自身.罩=None
                    自身.分类钮=()
                    自身.正文框=None
                    自身.提交钮=None
            elif 自身.罩 is None:
                分类盒=文档.createElement('div')
                分类盒.className='categories'
                标样式模块(分类盒,样式模块)
                分类盒.setAttribute('role','group')
                分类盒.setAttribute('aria-label',中文['dialog.categories'])
                钮列=[]
                for 类别 in 反馈类别:
                    选中=状态['category']==类别
                    芯片=文档.createElement('button')
                    芯片.type='button'
                    芯片.className='chip chipActive' if 选中 else 'chip'
                    标样式模块(芯片,样式模块)
                    芯片.setAttribute('data-category',类别)
                    芯片.setAttribute('aria-pressed','true' if 选中 else 'false')
                    芯片.disabled=状态['submitting'] is True
                    芯片.textContent=中文['category.'+类别]
                    芯片.addEventListener('click',自身.点分类)
                    分类盒.appendChild(芯片)
                    钮列.append(芯片)
                自身.分类钮=tuple(钮列)
                框=文档.createElement('textarea')
                框.className='detail'
                标样式模块(框,样式模块)
                框.setAttribute('aria-label',中文['dialog.detail'])
                框.setAttribute('placeholder',中文['dialog.hint'])
                框.value=状态['text']
                框.readOnly=状态['submitting'] is True
                框.addEventListener('input',自身.改文)
                自身.正文框=框
                提交文='正在提交…' if 状态['submitting'] else '提交'
                提交钮=处理按钮(窗口,{
                    'variant':'primary',
                    'className':'submit',
                    'disabled':状态['submitting'] is True,
                    'onClick':自身.点提交,
                    'children':提交文,
                    'window':窗口,
                })
                标样式模块(提交钮,样式模块)
                自身.提交钮=提交钮
                罩=处理模态(窗口,{
                    'open':True,
                    'title':中文['dialog.title'],
                    'closeLabel':'关闭',
                    'onClose':属性['dismiss'],
                    'className':'dialog',
                    'footer':提交钮,
                    'children':[分类盒,框],
                    'window':窗口,
                    'parent':文档.body,
                })
                if 罩 is not None:
                    卡=罩.querySelector('.dialog')
                    if 卡 is not None:
                        标样式模块(卡,样式模块)
                自身.罩=罩
            else:
                for 芯片 in 自身.分类钮:
                    类别=芯片.getAttribute('data-category')
                    选中=状态['category']==类别
                    芯片.className='chip chipActive' if 选中 else 'chip'
                    标样式模块(芯片,样式模块)
                    芯片.setAttribute('aria-pressed','true' if 选中 else 'false')
                    芯片.disabled=状态['submitting'] is True
                if 自身.正文框.value!=状态['text']:
                    自身.正文框.value=状态['text']
                自身.正文框.readOnly=状态['submitting'] is True
                提交文='正在提交…' if 状态['submitting'] else '提交'
                字=自身.提交钮.querySelector('span')
                if 字 is not None and 字.textContent!=提交文:
                    字.textContent=提交文
                自身.提交钮.disabled=状态['submitting'] is True
            if 自身.根 is not None and 自身.根.parentNode is not None:
                自身.曾挂上=True
            钩=属性['useDialog']
            if 自身.已订 is False and hasattr(钩,'_subscribe') and callable(钩._subscribe):
                def 变更():
                    '对话框状态变了就重画。根已经离开页面就卸下'
                    if 自身.绘制中:
                        自身.待重画=True
                        return
                    if 自身.移交:
                        return
                    if 自身.根 is not None and 自身.根.parentNode is not None:
                        自身.曾挂上=True
                    if 自身.曾挂上 and (自身.根 is None or 自身.根.parentNode is None):
                        自身.卸下()
                        return
                    自身.渲染()
                自身.退订=钩._subscribe(变更)
                自身.已订=True
            if 自身.已约量 is False:
                自身.已约量=True
                def 量卡片():
                    '探针挂进撰写栏之后，读一次最近的撰写卡'
                    if 自身.已卸 or 自身.移交:
                        return
                    if 自身.根 is None or 自身.根.parentNode is None:
                        return
                    if 自身.已量 is False:
                        自身.已量=True
                        下一=自身.探针.closest('[data-composer-card]')
                        if 下一 is not 自身.卡片:
                            自身.卡片=下一
                            自身.渲染()
                    if 自身.观察 is None and 自身.根 is not None and 自身.根.parentNode is not None:
                        父=自身.根.parentNode
                        def 看(记录,观察者):
                            '根被从撰写栏拿掉'
                            if 自身.根 is not None and 自身.根.parentNode is not None:
                                return
                            自身.卸下()
                        自身.观察=窗口.MutationObserver(看)
                        自身.观察.observe(父,{'childList':True})
                窗口.setTimeout(量卡片,0)
            画完=True
        finally:
            自身.绘制中=False
        if 画完 and 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根
