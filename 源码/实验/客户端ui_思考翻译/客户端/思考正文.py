'一块展开的思考：译文、原文切换和失败重试'
from ....客户端.模块.客户端.通告 import 取握手窗口
import os#样式文件
from ....客户端.ui_基础界面组件.按钮 import 按钮#切换和重试
from ....客户端.ui_基础界面组件.icons import 图标加载描边常规#正在翻译
from ....客户端.ui_对话.异常 import 注入模块样式文件,标样式模块#模块类名
from .文案 import 中文#界面用中文表原文
from .翻译 import 思考翻译#这一展开区的请求

__all__=['思考正文']

样式模块='思考翻译'#与样式文件对应


class 思考正文:
    '渲染译文。失败重试前保留完整原文'
    def __init__(自身,属性):
        '记下份额，并画出这一块'
        自身.属性=属性#渲染器交来的 props
        自身.根=None#当前根节点
        自身.状态={'文本':'','待定':False,'失败':False}#还没译
        自身.看原文=False#读者要看原文
        自身.控制器=None#这一展开区
        自身.选择键=None#提供方、语言、上限、翻译函数
        自身.已订=False#是否已订阅
        自身.退订表=[]#快照退订
        自身.绘制中=False#挡住重入
        自身.待重画=False#绘制中又来了一次
        自身.渲染()#第一次画出

    def 更新(自身,属性):
        '换成这一次的份额'
        自身.属性=属性#新 props

    def 拆除(自身):
        '退掉订阅并中止这一展开区的请求'
        if 自身.控制器 is not None:
            自身.控制器.拆除()#取消在途
            自身.控制器=None#不再用
        for 退 in 自身.退订表:
            if callable(退):
                退()#退订
        自身.退订表=[]#清空
        自身.已订=False#不再订阅

    def 渲染(自身):
        '工具栏和原文或译文'
        if 自身.绘制中:
            自身.待重画=True#这一轮结束再画
            return 自身.根
        自身.绘制中=True#占住
        try:
            属性=自身.属性#这一次份额
            if 'window' in 属性:
                窗口=属性['window']#调用方窗口
            else:
                窗口=取握手窗口()#当前页
            文档=窗口.document#文档
            注入模块样式文件(
                文档,
                '思考翻译样式',
                os.path.join(os.path.dirname(__file__),'思考翻译.module.css'),
                样式模块,
            )#模块样式只插一次

            def 全量偏好(快照):
                '整份偏好'
                return 快照

            def 当前语言(快照):
                '当前界面语言'
                return 快照['active']

            def 上限值(快照):
                '请求上限'
                return 快照

            偏好=属性['usePreferences'](全量偏好)#已接受偏好
            界面语言=属性['useTranslationLocale'](当前语言)#auto 跟随它
            最大字符=属性['useTranslationLimit'](上限值)#UTF-16 上限
            if 偏好['targetLanguage']=='auto':
                目标语言=界面语言#跟随界面
            else:
                目标语言=偏好['targetLanguage']#显式语言
            文本='' if 属性.get('text') is None else 属性['text']#原文
            进行中=属性.get('running') is True#尾段还在增长
            if not 自身.已订:
                def 变更():
                    '偏好、语言或上限变了就重画。节点不在页面上就退订'
                    if 自身.绘制中:
                        自身.待重画=True#这一轮结束再画
                        return
                    根节点=自身.根#当前根
                    if 根节点 is None or 根节点.parentNode is None:
                        自身.拆除()#离开页面
                        return
                    自身.渲染()#重画
                for 钩 in (
                    属性.get('usePreferences'),
                    属性.get('useTranslationLocale'),
                    属性.get('useTranslationLimit'),
                ):
                    if 钩 is not None and hasattr(钩,'_subscribe') and callable(钩._subscribe):
                        自身.退订表.append(钩._subscribe(变更))#订上
                自身.已订=True#只订一次
            选择键=(偏好['provider'],目标语言,最大字符,属性.get('translate'))#控制器寿命
            if 选择键!=自身.选择键:
                if 自身.控制器 is not None:
                    自身.控制器.拆除()#旧请求作废
                自身.状态={'文本':文本,'待定':False,'失败':False}#先显示原文

                def 发布(状态):
                    '控制器交出的展示状态'
                    自身.状态=状态#记下
                    if 自身.绘制中:
                        return#这一轮画的就是最新状态
                    自身.渲染()#状态变了就重画

                自身.控制器=思考翻译(
                    {'provider':偏好['provider'],'targetLanguage':目标语言},
                    最大字符,
                    属性['translate'],
                    发布,
                )#新的展开区
                自身.选择键=选择键#记下这一组
            if 自身.控制器 is not None:
                自身.控制器.更新(文本,进行中)#采用当前原文
            显示原文=自身.看原文 or 自身.状态['失败']#失败时只能看原文
            if 显示原文:
                动作文案=中文['translation']#查看译文
                正文=文本#完整原文
                视图='original'#数据视图
            else:
                动作文案=中文['original']#查看原文
                正文=自身.状态['文本']#译文或尚未译完的原文
                视图='translated'#数据视图
            if 自身.状态['失败']:
                阶段='failed'#失败
            elif 自身.状态['待定']:
                阶段='pending'#正在翻译
            else:
                阶段='ready'#已就绪
            父=None#挂回哪里
            if 自身.根 is not None:
                父=自身.根.parentNode#原父节点
                自身.根.remove()#拆掉旧根
                自身.根=None#清空
            elif 'parent' in 属性:
                父=属性['parent']#调用方给的父节点
            根=文档.createElement('div')#这一块
            根.setAttribute('data-cot-translation','true')#思考翻译
            根.setAttribute('data-translation-state',阶段)#失败、在途或就绪
            根.setAttribute('data-translation-view',视图)#原文或译文
            工具条=文档.createElement('div')#切换和状态
            工具条.className='toolbar'#横排
            标样式模块(工具条,样式模块)#接上模块

            def 切换():
                '在原文和译文之间切换'
                自身.看原文=not 显示原文#失败时按钮不可用
                自身.渲染()#换正文

            切换钮=按钮({
                'window':窗口,
                'className':'viewToggle',#对齐正文
                'size':'sm',
                'variant':'ghost',
                'disabled':自身.状态['失败'],#失败不能切换
                'children':动作文案,#查看译文或查看原文
                'onClick':切换,
            }).渲染()#切换按钮
            if 切换钮 is not None:
                标样式模块(切换钮,样式模块)#模块里的 viewToggle
                工具条.appendChild(切换钮)#放进工具条
            if 自身.状态['待定']:
                状态=文档.createElement('span')#正在翻译
                状态.setAttribute('role','status')#状态
                状态.setAttribute('aria-label',中文['translating'])#正在翻译思考内容
                图=图标加载描边常规({
                    'window':窗口,
                    'size':14,
                    'className':'spinner',#旋转
                })#加载弧
                if 图 is not None:
                    标样式模块(图,样式模块)#接上旋转
                    状态.appendChild(图)#放进状态
                工具条.appendChild(状态)#放进工具条
            if 自身.状态['失败']:
                失败=文档.createElement('span')#失败说明
                失败.className='failure'#主色
                标样式模块(失败,样式模块)#接上模块
                失败.setAttribute('role','status')#状态
                失败.textContent=中文['failed']#翻译暂不可用，已显示原文
                工具条.appendChild(失败)#放进工具条

                def 重试():
                    '重试尚未翻译的片段'
                    if 自身.控制器 is not None:
                        自身.控制器.重试()#清掉失败再译

                重试钮=按钮({
                    'window':窗口,
                    'size':'sm',
                    'variant':'ghost',
                    'children':中文['retry'],#重试
                    'onClick':重试,
                }).渲染()#重试按钮
                if 重试钮 is not None:
                    工具条.appendChild(重试钮)#放进工具条
            根.appendChild(工具条)#工具条
            标签={
                'code':{
                    'copyLabel':中文['copy'],#复制
                    'copiedLabel':中文['copied'],#已复制
                    'toolbarLabels':{
                        'codeLabel':中文['codeTitle'],#代码块
                        'wrapLabel':中文['wrap'],#自动换行
                        'unwrapLabel':中文['unwrap'],#不换行
                    },
                },
                'footnotes':中文['footnotes'],#脚注
            }#交给思考正文工厂
            内容=属性['renderFactorySlot']('conversation.chat.reasoning.content',{
                'text':正文,#原文或译文
                'running':进行中,#尾段是否还在增长
                'labels':标签,#中文表原文
                'window':窗口,#子树用同一窗口
            })#官方推理内容
            if 内容 is not None and hasattr(内容,'tagName'):
                根.appendChild(内容)#放进这一块
            自身.根=根#记下
            if 父 is not None:
                父.appendChild(根)#挂回原处
        finally:
            自身.绘制中=False#放开
        if 自身.待重画:
            自身.待重画=False#消化这一次
            return 自身.渲染()#用最新状态再画
        return 自身.根
