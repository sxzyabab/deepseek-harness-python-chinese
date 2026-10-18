from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块,模块节点
from ...ui_基础界面组件.icons import 图标智能体预设16
from .文案 import 中文,取中文,预设展示文本

__all__=['预设标签']

样式模块='agent-preset-label'#样式隔离

class 预设标签:
    '会话页眉上的预设名。会话没有预设记录时不画'
    def __init__(自身,属性):
        '记下渲染器交来的 props，并画出'
        自身.属性=属性#props
        自身.根=None#根节点
        自身.已订=False#是否已订阅
        自身.退订列=[]#退订
        自身.绘制中=False#防止订阅把重画嵌进来
        自身.待重画=False#绘制中又脏了
        自身.上次加载=None#上次调用的 load
        自身.渲染()#首画

    def 渲染(自身):
        '有预设记录才画出图标和名字'
        if 自身.绘制中:#嵌套
            自身.待重画=True#等这次结束再画
            return 自身.根#旧根
        自身.绘制中=True#占住
        try:#整次绘制
            属性=自身.属性#props
            窗口=属性['window'] if 'window' in 属性 else 取握手窗口()#浏览器窗口
            文档=窗口.document#文档
            注入模块样式文件(#样式只插一次
                文档,
                '预设标签样式',
                os.path.join(os.path.dirname(__file__),'预设标签.module.css'),
                样式模块,
            )
            会话标识=属性.get('sessionId')#当前会话

            def 读预设(状态):
                '列表里这场会话的 agentPreset。只有字符串才算'
                行=状态.get('byId',{}).get(会话标识) if isinstance(状态,dict) else None#摘要
                if 行 is None:#没有
                    return None#无
                投影=行.get('projectionValues')#投影
                if not isinstance(投影,dict):#没有
                    return None#无
                值=投影.get('agentPreset')#预设
                if isinstance(值,str):#字符串
                    return 值#标识
                return None#不算

            def 读选项(状态):
                '名册选项'
                return 状态['options']#选项

            预设=属性['useSessions'](读预设)#这场会话的预设
            选项列=属性['useAgentPresets'](读选项)#名册
            加载=属性.get('load')#读名册
            if 预设 is not None and 加载 is not None and 加载 is not 自身.上次加载:#有预设才请求
                自身.上次加载=加载#记下
                加载()#读
            旧=自身.根#上一份
            父=旧.parentNode if 旧 is not None else 属性.get('parent')#挂点
            if 旧 is not None:#拆旧
                旧.remove()#拿掉
                自身.根=None#空
            if 预设 is None:#会话没记预设
                自身.根=None#不画
            else:#画出标签
                选项=None#命中的选项
                for 项 in 选项列:#找
                    if 项['id']==预设:#就是这份
                        选项=项#记下
                        break#停
                展示=None if 选项 is None else 预设展示文本(选项,取中文)#中文名
                说明=中文['headerHint']#没有说明时的提示
                if 展示 is not None and 展示.get('description') is not None:#有说明
                    说明=展示['description']#用说明
                名字=预设 if 展示 is None else 展示['name']#名字或标识
                根=模块节点(文档,'span',样式模块,'label')#标签
                根.title=说明#悬停
                图标=图标智能体预设16({'window':窗口,'size':14,'className':'icon'})#图标
                if 图标 is not None:#有
                    标样式模块(图标,样式模块)#接上本页样式
                    根.appendChild(图标)#放进
                根.appendChild(文档.createTextNode(名字))#名字
                自身.根=根#记下
            if 父 is not None and 自身.根 is not None and 自身.根.parentNode is None:#挂回
                父.appendChild(自身.根)#挂上
            if 自身.已订 is not True:#订阅一次
                def 变更():
                    '快照变了就重画。根曾经挂上又被拿掉就退订'
                    if 自身.绘制中:#还在画
                        自身.待重画=True#等
                        return#停
                    根=自身.根#当前
                    if 根 is not None and 根.parentNode is None:#已从页面拿掉
                        for 退 in 自身.退订列:#退订
                            退()#拆
                        自身.退订列=[]#空
                        自身.已订=False#可再订
                        return#停
                    自身.渲染()#重画
                自身.退订列=[]#收集
                for 钩 in (属性.get('useSessions'),属性.get('useAgentPresets')):#两份快照
                    if 钩 is not None and hasattr(钩,'_subscribe') and callable(钩._subscribe):#渲染器钩子
                        自身.退订列.append(钩._subscribe(变更))#订
                自身.已订=True#已订
        finally:#放开
            自身.绘制中=False#结束
        if 自身.待重画:#绘制中又脏了
            自身.待重画=False#清
            return 自身.渲染()#再画
        return 自身.根#根
