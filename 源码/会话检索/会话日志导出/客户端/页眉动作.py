'会话页眉上的更多菜单：下载日志，反馈插件在时再多一项'
from ....客户端.模块.客户端.通告 import 取握手窗口
import os#样式路径
from ....客户端.ui_基础界面组件 import 按钮,菜单#更多按钮和菜单
from ....客户端.ui_基础界面组件.icons import 描边图标,常规描边#省略号
from ....客户端.ui_对话.异常 import 注入模块样式文件,标样式模块#模块类名
from .对话框 import 会话日志下载对话框#同一会话的状态对话框

样式模块='session-log-download'#样式隔离名
__all__=['会话日志下载页眉动作']


class 会话日志下载页眉动作:
    '页眉右侧的更多菜单，以及这一会话的导出对话框'
    def __init__(自身,属性):
        '记下份额并画出菜单和对话框'
        自身.属性=属性#props
        自身.根=None#当前根
        自身.已打开=False#菜单是否打开
        自身.对话框=None#状态对话框
        自身.已订=False#是否已订阅
        自身.退订表=[]#快照退订
        自身.绘制中=False#挡住重入
        自身.待重画=False#绘制中又来了一次
        自身.渲染()#第一次画出

    def 更新(自身,属性):
        '换成这一次的份额'
        自身.属性=属性#最新

    def 拆除(自身):
        '退掉下载和反馈可用性的订阅'
        for 退 in 自身.退订表:#逐个
            if callable(退):#是函数
                退()#退订
        自身.退订表=[]#清空
        自身.已订=False#不再订阅

    def 订上(自身,属性):
        '下载状态或反馈插件进出时重画。渲染器不订钩子，这里自己订'
        if 自身.已订:#已经订过
            return#不重复
        自身.已订=True#记下

        def 状态变了():
            '快照变了就重画菜单和对话框'
            自身.渲染()#重画

        自身.退订表.append(属性['useSessionLogDownload']._subscribe(状态变了))#下载状态
        自身.退订表.append(属性['useFeedbackAvailable']._subscribe(状态变了))#反馈是否还在

    def 渲染(自身):
        '画出更多按钮、下载和反馈菜单，以及导出对话框'
        if 自身.绘制中:#这一轮还没结束
            自身.待重画=True#结束再画
            return 自身.根#先交出现在的根
        自身.绘制中=True#占住
        try:#结束时一定放开
            属性=自身.属性#这一次份额
            if 'window' in 属性:#调用方带了窗口
                窗口=属性['window']#用它
            else:#槽位份额里没有窗口
                窗口=取握手窗口()#当前页
            文档=窗口.document#文档
            自身.订上(属性)#只订一次
            if 自身.根 is not None:#拆掉上一轮
                自身.根.remove()#连同对话框一起摘掉
            会话标识=属性['sessionId']#这一会话

            def 选条目(状态):
                '这一会话的下载条目'
                return 状态['bySession'].get(str(会话标识))#没有则是 None

            条目=属性['useSessionLogDownload'](选条目)#当前条目
            忙碌=条目 is not None and 条目.get('status')=='downloading'#正在准备

            def 原样(值):
                '反馈插件是否仍在'
                return 值#原值

            反馈可用=属性['useFeedbackAvailable'](原样) is True#在才多一项

            def 切菜单():
                '开或关更多菜单'
                自身.已打开=not 自身.已打开#翻转
                自身.渲染()#重画

            def 关闭菜单():
                '收起菜单'
                自身.已打开=False#关上
                自身.渲染()#重画

            def 选中(标识):
                '下载，或打开反馈草稿'
                自身.已打开=False#先关菜单
                if 标识=='feedback':#反馈
                    属性['openFeedback'](会话标识)#没有插件则无事
                else:#下载
                    属性['request'](会话标识)#HEAD 然后保存
                自身.渲染()#重画

            项=[{'id':'download','label':'下载 Session 日志','disabled':忙碌}]#menu.download
            if 反馈可用:#反馈插件还在
                项.append({'id':'feedback','label':'反馈'})#menu.feedback
            钮=按钮({#更多
                'window':窗口,
                'size':'sm',
                'className':'moreButton',
                'onClick':切菜单,
            }).渲染()
            注入模块样式文件(#按钮样式先插，模块样式后插，同权重时 moreButton 生效
                文档,
                'session-log-download-header',
                os.path.join(os.path.dirname(__file__),'页眉动作.module.css'),
                样式模块,
            )
            标样式模块(钮,样式模块)#接上 moreButton
            钮.setAttribute('aria-label','更多操作')#header.more
            钮.setAttribute('aria-haspopup','menu')#菜单
            钮.setAttribute('aria-expanded','true' if 自身.已打开 else 'false')#是否展开
            钮.setAttribute('aria-busy','true' if 忙碌 else 'false')#是否在准备
            图=描边图标({'window':窗口,'size':16},'0 0 16 16',[#省略号，填充不随描边变粗
                {'d':'M3 9C3.55228 9 4 8.55228 4 8C4 7.44772 3.55228 7 3 7C2.44772 7 2 7.44772 2 8C2 8.55228 2.44772 9 3 9Z','fill':'currentColor'},
                {'d':'M8 9C8.55228 9 9 8.55228 9 8C9 7.44772 8.55228 7 8 7C7.44772 7 7 7.44772 7 8C7 8.55228 7.44772 9 8 9Z','fill':'currentColor'},
                {'d':'M13 9C13.5523 9 14 8.55228 14 8C14 7.44772 13.5523 7 13 7C12.4477 7 12 7.44772 12 8C12 8.55228 12.4477 9 13 9Z','fill':'currentColor'},
            ],16,常规描边)
            钮.appendChild(图)#放进按钮
            菜单根=菜单({#对齐末端，紧凑对应上游 dense
                'window':窗口,
                'open':自身.已打开,
                'align':'end',
                'compact':True,
                'items':项,
                'onClose':关闭菜单,
                'onSelect':选中,
                'anchor':钮,
            }).渲染()
            if 自身.对话框 is None:#第一次
                自身.对话框=会话日志下载对话框(属性)#建对话框
            else:#已有
                自身.对话框.更新(属性)#换份额
            对话框根=自身.对话框.渲染()#关着则没有节点
            根=文档.createElement('div')#不占布局，对齐上游片段
            根.style.display='contents'#不产生盒子
            根.appendChild(菜单根)#菜单
            if 对话框根 is not None:#开着才挂
                根.appendChild(对话框根)#对话框
            自身.根=根#这一轮的根
        finally:#放开重入
            自身.绘制中=False#结束
        if 自身.待重画:#绘制中又脏了
            自身.待重画=False#清标记
            return 自身.渲染()#再画
        return 自身.根#根
