from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块,模块节点
from ...ui_基础界面组件.icons import 图标智能体预设16
from .文案 import 中文

__all__=['创建插件菜单项']

样式模块='create-plugin-menu-item'#样式隔离

class 创建插件菜单项:
    '添加插件菜单里进入创造模式的一行。创造模式不在名册上时说明原因'
    def __init__(自身,属性):
        '记下 props 并画出'
        自身.属性=属性#props
        自身.根=None#根节点
        自身.已订=False#是否已订阅
        自身.退订列=[]#退订
        自身.绘制中=False#防止重入
        自身.待重画=False#绘制中又脏了
        自身.上次加载=None#上次 load
        自身.渲染()#首画

    def 渲染(自身):
        '按名册状态换说明。创造模式在册上才能点'
        if 自身.绘制中:#嵌套
            自身.待重画=True#等
            return 自身.根#旧根
        自身.绘制中=True#占住
        try:#整次绘制
            属性=自身.属性#props
            窗口=属性['window'] if 'window' in 属性 else 取握手窗口()#窗口
            文档=窗口.document#文档
            注入模块样式文件(#样式
                文档,
                '创建插件菜单项样式',
                os.path.join(os.path.dirname(__file__),'创建插件菜单项.module.css'),
                样式模块,
            )

            def 读名册(状态):
                '整份名册快照'
                return 状态#原样

            名册=属性['useAgentPresets'](读名册)#名册
            加载=属性.get('load')#读名册
            if 加载 is not None and 加载 is not 自身.上次加载:#换了就再读
                自身.上次加载=加载#记下
                加载()#读
            可用=名册['status']=='ready' and any(项['id']=='cordis' for 项 in 名册['options'])#创造模式在册
            说明=中文['createPluginDescription']#默认可点时的说明
            if 名册['status']=='idle' or 名册['status']=='loading':#还在确认
                说明=中文['createPluginChecking']#检查中
            elif 名册['status']=='error' or 名册['status']=='unavailable':#读失败或没有名册
                说明=中文['createPluginUnavailable']#稍后再开
            elif 可用 is not True:#名册里没有创造模式
                说明=中文['createPluginMissing']#这份配置没有
            旧=自身.根#上一份
            父=旧.parentNode if 旧 is not None else 属性.get('parent')#挂点
            if 旧 is not None:#拆旧
                旧.remove()#拿掉
            钮=文档.createElement('button')#菜单行。基础界面组件没有菜单项按钮
            钮.type='button'#按钮
            钮.setAttribute('role','menuitem')#菜单项
            钮.disabled=可用 is not True#不可用就禁用
            def 选定(事件):
                '先关添加菜单，再开创造模式，不发消息'
                卸=属性.get('onDismiss')#关菜单
                if 卸 is not None:#有
                    卸()#关
                属性['startCreatorDraft']()#进入创造模式
            钮.addEventListener('click',选定)#点
            图标=图标智能体预设16({'window':窗口,'size':14})#前导图标
            if 图标 is not None:#有
                钮.appendChild(图标)#放进
            文=模块节点(文档,'span',样式模块,'copy')#标题和说明
            题=文档.createElement('span')#标题
            题.textContent=中文['createPlugin']#让 Agent 创建插件
            文.appendChild(题)#放进
            述=模块节点(文档,'span',样式模块,'description')#说明
            述.title=说明#放不下时悬停看全文
            述.textContent=说明#说明
            文.appendChild(述)#放进
            钮.appendChild(文)#放进
            自身.根=钮#记下
            if 父 is not None:#挂回
                父.appendChild(自身.根)#挂上
            if 自身.已订 is not True:#订阅一次
                def 变更():
                    '名册变了就重画。行已经不在页面上就退订'
                    if 自身.绘制中:#还在画
                        自身.待重画=True#等
                        return#停
                    根=自身.根#当前
                    if 根 is not None and 根.parentNode is None:#已拿掉
                        for 退 in 自身.退订列:#退订
                            退()#拆
                        自身.退订列=[]#空
                        自身.已订=False#可再订
                        return#停
                    自身.渲染()#重画
                钩=属性.get('useAgentPresets')#名册钩子
                if 钩 is not None and hasattr(钩,'_subscribe') and callable(钩._subscribe):#有订阅
                    自身.退订列=[钩._subscribe(变更)]#订
                自身.已订=True#已订
        finally:#放开
            自身.绘制中=False#结束
        if 自身.待重画:#又脏了
            自身.待重画=False#清
            return 自身.渲染()#再画
        return 自身.根#根
