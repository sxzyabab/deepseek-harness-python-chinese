'一条助手消息上的赞和踩。已记下的评分再点一次就撤回，其余打开反馈对话框'
import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_基础界面组件.icons import 描边图标
from ...ui_基础界面组件.提示泡 import 提示泡
from .文案 import 中文

__all__=['消息反馈动作']

样式模块='message-feedback-actions'
赞路径='M13.537 8.12098L12.3983 12.8455C12.1818 13.7438 11.378 14.3769 10.454 14.3769L9.35595 14.3769H7.43799H5.16577C3.50892 14.3769 2.16577 13.0337 2.16577 11.3769V7.88668C2.16577 7.33439 2.61349 6.88668 3.16577 6.88668H4.02665C5.84943 6.88668 7.38083 3.28711 7.67689 2.54578C7.71259 2.45639 7.73501 2.36373 7.77922 2.27824C7.86506 2.11221 8.08228 1.87578 8.59039 2.07775C10.3291 2.76886 9.23144 6.04071 8.96955 6.75058C8.94502 6.81707 8.99495 6.88668 9.06581 6.88668H12.5648C13.2119 6.88668 13.6886 7.49192 13.537 8.12098Z'
踩路径='M2.46302 8.06749L3.60171 3.34299C3.81822 2.44467 4.62196 1.81162 5.546 1.8116L6.64406 1.81158L8.56202 1.81158L10.8342 1.81158C12.4911 1.81158 13.8342 3.15473 13.8342 4.81158L13.8342 8.3018C13.8342 8.85408 13.3865 9.3018 12.8342 9.3018L11.9734 9.3018C10.1506 9.3018 8.61918 12.9014 8.32311 13.6427C8.28741 13.7321 8.26499 13.8247 8.22078 13.9102C8.13494 14.0763 7.91772 14.3127 7.40961 14.1107C5.67089 13.4196 6.76856 10.1478 7.03045 9.43789C7.05498 9.37141 7.00505 9.3018 6.93419 9.3018L3.43519 9.3018C2.78811 9.3018 2.31141 8.69656 2.46302 8.06749Z'

class 消息反馈动作:
    '赞和踩。点已记下的评分就撤回，其余打开对话框'
    活={}
    现场表={}

    def __init__(自身,属性):
        '记下渲染器交来的 props，并接上这一条消息的现场'
        自身.属性=属性
        自身.根=None
        自身.提示列=[]
        自身.已订=False
        自身.退订=None
        自身.绘制中=False
        自身.待重画=False
        自身.曾挂上=False
        钩=属性['useFeedback']
        键=(id(钩),属性['messageId'])
        自身.键=键
        现场=消息反馈动作.现场表.get(键)
        if 现场 is None:
            现场={'进行中':False,'失败':None,'已播种':False,'存活':True}
            消息反馈动作.现场表[键]=现场
        现场['存活']=True
        自身.现场=现场
        旧=消息反馈动作.活.get(键)
        if 旧 is not None and 旧 is not 自身:
            旧.停下(False)
        消息反馈动作.活[键]=自身
        自身.渲染()

    def 停下(自身,标死):
        '卸掉提示和订阅。换实例时不把现场标死'
        if 标死:
            自身.现场['存活']=False
        for 泡 in 自身.提示列:
            if 泡.卸 is not None:
                泡.卸()
        自身.提示列=[]
        if 自身.退订 is not None:
            退=自身.退订
            自身.退订=None
            自身.已订=False
            退()

    def 播种(自身,事件=None):
        '第一次悬停或聚焦才读这一场的反馈'
        if 自身.现场['已播种']:
            return
        自身.现场['已播种']=True
        自身.属性['ensure']()

    def 选择(自身,下一评价):
        '先读已存评分。对得上就撤回，否则打开对话框'
        自身.现场['进行中']=True
        自身.现场['失败']=None
        自身.渲染()
        已加载=自身.属性['ensure']()
        if 自身.现场['存活'] is not True:
            return
        当前=自身.属性['current'](自身.属性['messageId'])
        当前评价=None if 当前 is None else 当前['rating']
        if 已加载['ok'] is not True or 当前评价!=下一评价:
            自身.现场['进行中']=False
            自身.属性['openDialog'](自身.属性['messageId'],下一评价)
            自身.渲染()
            return
        结果=自身.属性['retract'](自身.属性['messageId'],下一评价)
        if 自身.现场['存活'] is not True:
            return
        自身.现场['进行中']=False
        if 结果['ok'] is not True:
            if 结果['error']['code']=='version-conflict':
                自身.现场['失败']=中文['error.conflict']
            else:
                自身.现场['失败']=中文['error.generic']
        自身.渲染()

    def 选赞(自身,事件=None):
        '点赞这一条'
        自身.选择('positive')

    def 选踩(自身,事件=None):
        '点踩这一条'
        自身.选择('negative')

    def 渲染(自身):
        '画出赞、踩，以及加载失败或这一次动作的失败'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        画完=False
        try:
            for 泡 in 自身.提示列:
                if 泡.卸 is not None:
                    泡.卸()
            自身.提示列=[]
            属性=自身.属性
            窗口=属性['window']
            文档=窗口.document
            注入模块样式文件(
                文档,
                '反馈动作样式',
                os.path.join(os.path.dirname(__file__),'反馈动作.module.css'),
                样式模块,
            )
            消息标识=属性['messageId']
            def 取条目(视图):
                '只要这一条消息的已提交项'
                表=视图['items']
                if 消息标识 in 表:
                    return 表[消息标识]
                return None
            def 是否加载失败(视图):
                '只看这次列表是不是失败'
                return 视图['status']=='error'
            条目=属性['useFeedback'](取条目)
            加载失败=属性['useFeedback'](是否加载失败) is True
            评价=None if 条目 is None else 条目['rating']
            赞文案=中文['action.likeActive'] if 评价=='positive' else 中文['action.like']
            踩文案=中文['action.dislikeActive'] if 评价=='negative' else 中文['action.dislike']
            def 画按钮(文案,按下,点下,是赞):
                '一颗评分按钮。按下时用填色字形'
                钮=文档.createElement('button')
                钮.type='button'
                钮.className='action'
                标样式模块(钮,样式模块)
                钮.setAttribute('aria-label',文案)
                钮.setAttribute('aria-pressed','true' if 按下 else 'false')
                if 按下:
                    钮.setAttribute('data-active','true')
                钮.disabled=自身.现场['进行中'] is True
                钮.addEventListener('focus',自身.播种)
                钮.addEventListener('pointerenter',自身.播种)
                钮.addEventListener('click',点下)
                路径=赞路径 if 是赞 else 踩路径
                if 按下:
                    图=描边图标(
                        {'window':窗口},
                        '0 0 16 16',
                        [{'d':路径,'fill':'currentColor','stroke':'currentColor'}],
                    )
                else:
                    图=描边图标({'window':窗口},'0 0 16 16',[路径])
                钮.appendChild(图)
                泡=提示泡({
                    'window':窗口,
                    'label':文案,
                    'side':'bottom',
                    'children':钮,
                })
                锚=泡.渲染()
                自身.提示列.append(泡)
                return 锚
            新=文档.createElement('span')
            新.style.display='contents'
            新.appendChild(画按钮(赞文案,评价=='positive',自身.选赞,True))
            新.appendChild(画按钮(踩文案,评价=='negative',自身.选踩,False))
            失败文=自身.现场['失败']
            if 失败文 is not None or 加载失败:
                失败=文档.createElement('span')
                失败.className='failure'
                标样式模块(失败,样式模块)
                失败.setAttribute('role','status')
                if 失败文 is not None:
                    失败.textContent=失败文
                else:
                    失败.textContent=中文['error.load']
                新.appendChild(失败)
            旧=自身.根
            if 旧 is not None and 旧.parentNode is not None:
                旧.parentNode.replaceChild(新,旧)
            自身.根=新
            if 新.parentNode is not None:
                自身.曾挂上=True
            钩=属性['useFeedback']
            if 自身.已订 is False and hasattr(钩,'_subscribe') and callable(钩._subscribe):
                def 变更():
                    '视图变了就重画。节点已经离开页面就退订'
                    if 自身.绘制中:
                        自身.待重画=True
                        return
                    if 自身.根 is not None and 自身.根.parentNode is not None:
                        自身.曾挂上=True
                    if 自身.曾挂上 and (自身.根 is None or 自身.根.parentNode is None):
                        自身.停下(True)
                        return
                    自身.渲染()
                自身.退订=钩._subscribe(变更)
                自身.已订=True
            画完=True
        finally:
            自身.绘制中=False
        if 画完 and 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根
