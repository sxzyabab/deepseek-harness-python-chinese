'插件页上的翻译服务、目标语言和对外发送说明'
from ....客户端.模块.客户端.通告 import 取握手窗口
import os#样式文件
from ....客户端.ui_基础界面组件.按钮 import 按钮#复位
from ....客户端.ui_基础界面组件.标签 import 标签#已覆盖
from ....客户端.ui_插件设置.字段 import 取值字段,画出设置表单,跳过离开丢弃#共享表单
from ....客户端.ui_对话.异常 import 注入模块样式文件,标样式模块#模块类名
from .文案 import 中文#界面用中文表原文

__all__=['思考设置']

样式模块='思考翻译'#与样式文件对应


def 服务名(提供方):
    '提供方在选项里的中文'
    if 提供方=='bing':
        return 中文['bing']#Bing
    if 提供方=='google':
        return 中文['google']#Google
    if 提供方=='deepseek-account':
        return 中文['deepseekAccount']#账号付费
    if 提供方=='deepseek-official':
        return 中文['deepseekOfficial']#官方 API 付费
    return 提供方#不认识的原样显示


class 思考设置:
    '暂存的翻译偏好，并写明哪些文本会离开宿主'
    def __init__(自身,属性):
        '记下份额，并画出这一页'
        自身.属性=属性#渲染器交来的 props
        自身.根=None#当前根节点
        自身.已订=False#是否已订阅
        自身.退订表=[]#快照退订
        自身.绘制中=False#挡住重入
        自身.待重画=False#绘制中又来了一次
        自身.已刷新=None#上次调用的刷新函数
        自身.服务标识='cot-translation-provider-'+str(id(自身))#选择框
        自身.语言标识='cot-translation-language-'+str(id(自身))#语言框
        自身.渲染()#第一次画出

    def 更新(自身,属性):
        '换成这一次的份额'
        自身.属性=属性#新 props

    def 拆除(自身):
        '退掉快照订阅'
        for 退 in 自身.退订表:
            if callable(退):
                退()#退订
        自身.退订表=[]#清空
        自身.已订=False#不再订阅

    def 渲染(自身):
        '隐私说明、服务选择和目标语言'
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

            def 全量表单(快照):
                '整份表单快照'
                return 快照

            def 全部可用(快照):
                '整份合格路由'
                return 快照

            状态=属性['useTranslationForm'](全量表单)#草稿
            可用=属性['useAvailableProviders'](全部可用)#合格提供方
            活动=文档.activeElement#重画前的焦点
            焦点标识=None#要恢复的 id
            选起=None#语言框选区
            选止=None#语言框选区
            if 活动 is not None and isinstance(getattr(活动,'id',None),str) and 活动.id!='':
                焦点标识=活动.id#记下
                if 焦点标识==自身.语言标识:
                    选起=活动['selectionStart']#起点
                    选止=活动['selectionEnd']#终点
            父=None#挂回哪里
            if 自身.根 is not None:
                跳过离开丢弃(自身.根)#重画不是离开页面
                父=自身.根.parentNode#原父节点
                自身.根.remove()#拆掉旧根
                自身.根=None#清空
            elif 'parent' in 属性:
                父=属性['parent']#调用方给的父节点
            禁用=(not 状态['writable']) or 状态['saving']#只读或正在保存
            提供方文本=状态['provider']['text']#草稿
            缺这个=提供方文本!='' and not any(项==提供方文本 for 项 in 可用)#不在合格名单
            付费=提供方文本=='deepseek-account' or 提供方文本=='deepseek-official'#付费路由

            def 改服务(事件):
                '写入 provider 草稿'
                目标=None if 事件 is None else getattr(事件,'target',None)#选择框
                值='' if 目标 is None else 目标.value#当前选项
                属性['edit']('provider',值)#暂存

            def 复位服务():
                '把 provider 恢复成默认'
                属性['resetField']('provider')#复位

            def 改语言(值):
                '写入 targetLanguage 草稿'
                属性['edit']('targetLanguage',值)#暂存

            def 复位语言():
                '把 targetLanguage 恢复成默认'
                属性['resetField']('targetLanguage')#复位

            def 画控件(容器):
                '说明、服务和目标语言'
                隐私=文档.createElement('p')#对外发送说明
                隐私.className='notice'#说明
                标样式模块(隐私,样式模块)#接上模块
                隐私.textContent=中文['privacy']#展开的思考会送出
                容器.appendChild(隐私)#放进表单
                费用=文档.createElement('p')#付费或匿名说明
                费用.className='notice'#说明
                标样式模块(费用,样式模块)#接上模块
                if 付费:
                    费用.textContent=中文['paidNotice']#每个片段单独付费
                else:
                    费用.textContent=中文['anonymousNotice']#匿名端点可能拒绝
                容器.appendChild(费用)#放进表单
                字段=文档.createElement('div')#服务字段
                字段.className='field'#纵向
                标样式模块(字段,样式模块)#接上模块
                工具条=文档.createElement('div')#标签和复位
                工具条.className='toolbar'#横排
                标样式模块(工具条,样式模块)#接上模块
                题=文档.createElement('label')#服务标签
                题.htmlFor=自身.服务标识#指向选择框
                题.textContent=中文['provider']#翻译服务
                工具条.appendChild(题)#放进工具条
                if 状态['provider']['overridden'] is True:
                    牌=标签({
                        'window':窗口,
                        'tone':'neutral',
                        'children':中文['overridden'],#已覆盖
                    }).渲染()#徽章
                    if 牌 is not None:
                        工具条.appendChild(牌)#放进工具条
                    复位钮=按钮({
                        'window':窗口,
                        'size':'sm',
                        'disabled':禁用,
                        'children':中文['reset'],#恢复默认
                        'onClick':复位服务,
                    }).渲染()#复位按钮
                    if 复位钮 is not None:
                        工具条.appendChild(复位钮)#放进工具条
                字段.appendChild(工具条)#标签行
                选择=文档.createElement('select')#提供方
                选择.id=自身.服务标识#稳定 id
                选择.disabled=禁用#不可改
                if 状态['provider']['invalid'] is True:
                    选择.setAttribute('aria-invalid','true')#非法
                def 变更(事件):
                    '选择变了就写入草稿'
                    改服务(事件)#读当前值
                选择.addEventListener('change',变更)#原生变更
                if 缺这个:
                    缺项=文档.createElement('option')#当前值不在名单里
                    缺项.value=提供方文本#仍显示这个值
                    缺项.disabled=True#不能再选
                    缺项.textContent=中文['providerUnavailableOption'].replace(
                        '{provider}',服务名(提供方文本),
                    )#服务名加不可用
                    选择.appendChild(缺项)#放进列表
                for 项 in 可用:
                    选项=文档.createElement('option')#一个合格提供方
                    选项.value=项#协议值
                    选项.textContent=服务名(项)#中文名
                    选择.appendChild(选项)#放进列表
                选择.value=提供方文本#选项齐了再写入当前草稿
                字段.appendChild(选择)#选择框
                if 状态['provider']['invalid'] is True:
                    非法=文档.createElement('p')#校验说明
                    非法.setAttribute('role','status')#状态
                    非法.textContent=中文['invalidProvider']#请选择翻译服务
                    字段.appendChild(非法)#放进字段
                elif 缺这个:
                    不可用=文档.createElement('p')#服务不可用
                    不可用.setAttribute('role','status')#状态
                    不可用.className='notice'#次要说明
                    标样式模块(不可用,样式模块)#接上模块
                    不可用.textContent=中文['providerUnavailable']#请改配置或换服务
                    字段.appendChild(不可用)#放进字段
                容器.appendChild(字段)#服务整块
                语言=取值字段({
                    'window':窗口,
                    'id':自身.语言标识,
                    'label':中文['targetLanguage'],#目标语言
                    'hint':中文['targetLanguageHint'],#auto 或语言代码
                    'overriddenLabel':中文['overridden'],#已覆盖
                    'resetLabel':中文['reset'],#恢复默认
                    'invalidLabel':中文['invalidLanguage'],#请填写 auto 或语言代码
                    **状态['targetLanguage'],#草稿、覆盖、非法
                    'disabled':禁用,
                    'onEdit':改语言,
                    'onReset':复位语言,
                }).渲染()#目标语言字段
                if 语言 is not None:
                    容器.appendChild(语言)#放进表单

            自身.根=画出设置表单(窗口,{
                'unavailable':中文['unavailable'],#翻译设置暂不可用
                'readOnly':中文['readOnly'],#本部署只读
                'saveFailed':中文['saveFailed'],#没有接受这些值
                'save':中文['save'],#保存
                'saving':中文['saving'],#保存中
            },状态,属性['discard'],属性['save'],画控件)#共享表单铬
            if 父 is not None and 自身.根 is not None:
                父.appendChild(自身.根)#挂回原处
            if 焦点标识 is not None and 自身.根 is not None:
                框=文档.getElementById(焦点标识)#找回焦点
                if 框 is not None:
                    框.focus()#还放在原控件
                    if type(选起) in (int,float) and type(选止) in (int,float):
                        框.setSelectionRange(int(选起),int(选止))#恢复选区
            if not 自身.已订:
                def 变更():
                    '快照变了就重画。节点已经不在页面上就退订'
                    if 自身.绘制中:
                        自身.待重画=True#这一轮结束再画
                        return
                    根=自身.根#当前根
                    if 根 is None or 根.parentNode is None:
                        自身.拆除()#离开页面
                        return
                    自身.渲染()#重画
                for 钩 in (属性.get('useTranslationForm'),属性.get('useAvailableProviders')):
                    if 钩 is not None and hasattr(钩,'_subscribe') and callable(钩._subscribe):
                        自身.退订表.append(钩._subscribe(变更))#订上
                自身.已订=True#只订一次
            刷新=属性.get('refreshProviders')#合格路由刷新
            if 刷新 is not 自身.已刷新:
                自身.已刷新=刷新#记下身份
                if callable(刷新):
                    刷新()#不发送思考，只重读路由
        finally:
            自身.绘制中=False#放开
        if 自身.待重画:
            自身.待重画=False#消化这一次
            return 自身.渲染()#用最新快照再画
        return 自身.根
