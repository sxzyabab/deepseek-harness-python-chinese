from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块,模块节点
from ...ui_基础界面组件.icons import 图标下箭头描边常规,图标智能体预设16,图标警告16
from ...ui_基础界面组件.吐司 import 吐司
from ...ui_基础界面组件.菜单 import 菜单
from .文案 import 中文,取中文,预设展示文本
from .设置存储 import 需要编码工具

__all__=['介绍错开毫秒','预设芯片']

样式模块='agent-preset-seat'#样式隔离
介绍文字延迟毫秒=150#图标先入场
介绍字符错开毫秒=40#短名的字间距
介绍文字揭开毫秒=200#长名也在这个窗口里播完
介绍字符淡入毫秒=400#每个字淡入
拒绝保持毫秒=8000#拒绝吐司停留

def 介绍错开毫秒(字数):
    '短名按每字上限。长名压进同一个揭开窗口'
    if 字数<=1:#一个字或没有
        return 0#不需要错开
    return min(介绍字符错开毫秒,介绍文字揭开毫秒/(字数-1))#取更短的

class 预设芯片:
    '新会话画面上的预设芯片。部署没有名册时不画'
    def __init__(自身,属性):
        '记下 props 并画出'
        自身.属性=属性#props
        自身.根=None#包裹
        自身.打开=False#菜单
        自身.介绍中=False#正在播介绍
        自身.介绍定时=None#介绍结束
        自身.介绍键=None#介绍效果的依赖
        自身.吐司错误=None#正在播的那次拒绝
        自身.吐司序号=0#同一份预设连拒两次也重播
        自身.已画吐司序号=0#已经画过的那一次
        自身.吐司节点=None#吐司自己挂在 body 上
        自身.上次开发=None#上次的开发者工具
        自身.上次数量=None#上次可选数量
        自身.上次加载=None#上次 load
        自身.已订=False#是否已订阅
        自身.退订列=[]#退订
        自身.绘制中=False#防止重入
        自身.待重画=False#绘制中又脏了
        自身.渲染()#首画

    def 渲染(自身):
        '主视图才画芯片。拒绝用吐司，不挡没有芯片的情况'
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
                '预设芯片样式',
                os.path.join(os.path.dirname(__file__),'预设芯片.module.css'),
                样式模块,
            )
            会话标识=属性.get('sessionId')#当前会话

            def 读开发(值):
                '开发者工具是否开着'
                return 值#布尔

            def 读状态(快照):
                '整份芯片快照'
                return 快照#原样

            def 是主视图(信息):
                '没有会话时芯片仍在。有会话时看主视图还留不留它'
                if 会话标识 is None:#新会话还没有标识
                    return True#画
                保留=信息.get('retainedBy') if isinstance(信息,dict) else None#保留
                主=0#次数
                if isinstance(保留,dict) and 保留.get('mainView') is not None:#有计数
                    主=保留['mainView']#主视图
                return 主>0#还留着

            开发=属性['useDeveloperTools'](读开发)#开发者工具
            状态=属性['useAgentPresetSeat'](读状态)#芯片
            保留钩=属性.get('useSessionRetainInfo')#主视图保留
            if 会话标识 is None:#没有键
                主视图=是主视图(None)#选择器在没有标识时为真
            elif 保留钩 is not None:#渲染器的键控钩子要显式传入会话标识
                主视图=保留钩(会话标识,是主视图)#这场会话
            else:#没有钩子
                主视图=True#仍画
            加载=属性.get('load')#读名册
            if 加载 is not None and 加载 is not 自身.上次加载:#挂上时读一次
                自身.上次加载=加载#记下
                加载()#读
            选项=[]#菜单里看得到的
            for 项 in 状态['options']:#过滤
                if 开发 or 需要编码工具(项) is not True:#工具关着就藏起 PTC 和极简
                    选项.append(项)#留下
            if 自身.上次开发 is not None and (自身.上次开发!=开发 or 自身.上次数量!=len(选项)):#工具或数量变了
                自身.打开=False#关上菜单
            自身.上次开发=开发#记下
            自身.上次数量=len(选项)#记下
            选中=None#当前项
            for 项 in 状态['options']:#在完整名册里找，不在过滤后的菜单里找
                if 项['id']==状态['current']:#就是这份
                    选中=项#记下
                    break#停
            展示=None if 选中 is None else 预设展示文本(选中,取中文)#中文名
            标签=状态['current'] if 展示 is None else 展示['name']#按钮上的字
            就绪=len(状态['options'])>0 and 状态['current']!=''#能显示名字
            介绍键=(状态['introduce'],就绪,标签)#介绍效果依赖
            if 介绍键!=自身.介绍键:#变了才重武装
                自身.介绍键=介绍键#记下
                if 自身.介绍定时 is not None:#清掉上一次
                    窗口.clearTimeout(自身.介绍定时)#取消
                    自身.介绍定时=None#空
                if 状态['introduce'] and 就绪:#要从别的页面介绍这次选择
                    字符=list(标签)#按字
                    if len(字符)==0 or 窗口.matchMedia('(prefers-reduced-motion: reduce)').matches:#减动效或没有字
                        属性['introduced']()#立刻确认
                        自身.介绍中=False#不播
                    else:#播
                        自身.介绍中=True#播
                        时长=介绍文字延迟毫秒+(len(字符)-1)*介绍错开毫秒(len(字符))+介绍字符淡入毫秒#播完

                        def 结束():
                            '播完后确认，并回到普通文字'
                            自身.介绍中=False#结束
                            自身.介绍定时=None#空
                            属性['introduced']()#确认
                            自身.渲染()#重画
                        自身.介绍定时=窗口.setTimeout(结束,时长)#到点
            错误=状态['error']#拒绝或句子
            if isinstance(错误,dict):#对象拒绝才上吐司
                if 错误 is not 自身.吐司错误:#新的一次
                    自身.吐司序号=自身.吐司序号+1#重播
                    自身.吐司错误=错误#记下
            else:#句子或没有
                自身.吐司错误=None#收起
            旧=自身.根#上一份
            父=旧.parentNode if 旧 is not None else 属性.get('parent')#挂点
            if 旧 is not None:#拆旧
                旧.remove()#拿掉
                自身.根=None#空
            if 主视图 is not True:#不在主视图
                自身.根=None#不画
            else:#画芯片和吐司
                包裹=文档.createElement('span')#不占布局的包裹
                包裹.style.display='contents'#子级直接进父级
                if 就绪:#有名字才出芯片
                    if isinstance(错误,dict):#对象
                        标题=错误.get('reason')#原因
                    elif isinstance(错误,str):#句子
                        标题=错误#句子
                    else:#没有错误
                        标题=None#用提示
                    if 标题 is None:#没有
                        标题=中文['seatHint']#选择新任务使用的 Agent 预设
                    钮=模块节点(文档,'button',样式模块,'seat')#芯片
                    钮.type='button'#按钮
                    钮.setAttribute('aria-haspopup','menu')#会开菜单
                    开着=自身.打开 and len(选项)>0#菜单开着
                    钮.setAttribute('aria-expanded','true' if 开着 else 'false')#展开
                    钮.title=标题#提示或拒绝原因
                    钮.disabled=状态['busy'] or len(选项)==0#忙或没有可选项

                    def 点芯片(事件):
                        '开关菜单'
                        自身.打开=自身.打开 is not True#翻转
                        自身.渲染()#重画
                    钮.addEventListener('click',点芯片)#点
                    图标类='seatIcon introIcon' if 自身.介绍中 else 'seatIcon'#介绍时图标入场
                    图标=图标智能体预设16({'window':窗口,'className':图标类})#预设图标
                    if 图标 is not None:#有
                        标样式模块(图标,样式模块)#动画类
                        钮.appendChild(图标)#放进
                    字=模块节点(文档,'span',样式模块,'seatLabel')#名字
                    if 自身.介绍中:#逐字
                        字符=list(标签)#按字
                        错开=介绍错开毫秒(len(字符))#间隔
                        组=模块节点(文档,'span',样式模块,'introText')#整名一块
                        序=0#下标
                        for 字元 in 字符:#逐字
                            片=模块节点(文档,'span',样式模块,'introChar')#一字
                            片.style.animationDelay=str(介绍文字延迟毫秒+序*错开)+'ms'#错开
                            片.textContent=字元#字
                            组.appendChild(片)#放进
                            序=序+1#下一个
                        字.appendChild(组)#放进
                    else:#普通文字
                        字.textContent=标签#名字
                    钮.appendChild(字)#放进
                    箭头=图标下箭头描边常规({'window':窗口,'className':'chevron'})#下箭头
                    if 箭头 is not None:#有
                        标样式模块(箭头,样式模块)#颜色
                        钮.appendChild(箭头)#放进
                    条目=[]#菜单行
                    for 项 in 选项:#每份预设
                        文=预设展示文本(项,取中文)#中文
                        述=中文['noDescription'] if 文.get('description') is None else 文['description']#说明
                        条目.append({'id':项['id'],'label':文['name']+'\n'+述})#名称和说明。菜单只能收成一段文字

                    def 关掉():
                        '关菜单'
                        自身.打开=False#关
                        自身.渲染()#重画

                    def 选了(标识):
                        '关菜单并套用'
                        自身.打开=False#关
                        属性['select'](标识)#选定
                        自身.渲染()#重画
                    单=菜单({#锚定菜单
                        'window':窗口,
                        'open':开着,
                        'onClose':关掉,
                        'items':条目,
                        'selectedId':状态['current'],
                        'onSelect':选了,
                        'align':'start',
                        'portal':True,
                        'className':'menuAnchor',
                        'anchor':钮,
                    })
                    单节点=单.渲染()#画出
                    if 单节点 is not None:#有
                        标样式模块(单节点,样式模块)#最小宽度
                        包裹.appendChild(单节点)#放进
                if isinstance(自身.吐司错误,dict):#有拒绝要播
                    if 自身.吐司序号!=自身.已画吐司序号:#新的一次才重播，避免每次重画都重置停留
                        if 自身.吐司节点 is not None:#拆掉上一条
                            自身.吐司节点.remove()#拿掉
                        名=预设展示文本(自身.吐司错误['preset'],取中文)['name']#预设名
                        句=中文['switchRefused'].replace('{name}',名).replace('{reason}',自身.吐司错误['reason'])#无法切换
                        警告=图标警告16({'window':窗口})#警告图标
                        这次=自身.吐司错误#播完时对上这一次

                        def 播完():
                            '确认这一次拒绝'
                            属性['dismissRefusal'](这次)#确认
                        条=吐司({#顶上的拒绝
                            'window':窗口,
                            'text':句,
                            'icon':警告,
                            'holdMs':拒绝保持毫秒,
                            'anchor':文档.querySelector('[data-composer-card]'),
                            'onDone':播完,
                        })
                        自身.吐司节点=条.渲染()#画到 body
                        自身.已画吐司序号=自身.吐司序号#记下
                elif 自身.吐司节点 is not None:#拒绝已经确认
                    自身.吐司节点.remove()#拿掉
                    自身.吐司节点=None#空
                自身.根=包裹#记下
            if 父 is not None and 自身.根 is not None and 自身.根.parentNode is None:#挂回
                父.appendChild(自身.根)#挂上
            if 自身.已订 is not True:#订阅一次
                def 变更():
                    '快照变了就重画。芯片曾经挂上又被拿掉就退订'
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
                自身.退订列=[]#收集
                for 钩 in (属性.get('useDeveloperTools'),属性.get('useAgentPresetSeat'),属性.get('useSessionRetainInfo')):#三份
                    if 钩 is not None and hasattr(钩,'_subscribe') and callable(钩._subscribe):#普通钩子
                        自身.退订列.append(钩._subscribe(变更))#订
                自身.已订=True#已订
        finally:#放开
            自身.绘制中=False#结束
        if 自身.待重画:#又脏了
            自身.待重画=False#清
            return 自身.渲染()#再画
        return 自身.根#根
