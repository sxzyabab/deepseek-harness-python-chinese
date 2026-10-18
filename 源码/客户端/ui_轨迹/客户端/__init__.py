from .文案 import 命名空间,中文,英文#中英词表，显示不走英文表
from .时长存储 import 创建轨迹时长存储#实测时长
from .字符串换行存储 import 创建轨迹字符串换行存储#JSON 折行
from . import 复制代码#压缩打断标记
from . import 约定#贡献字段说明
from . import 轨迹记录#记录身份
from . import 轨迹预览#有界预览
from . import 轨迹节点#目标信封
from . import 虚拟行#虚拟行
from . import 代码程序#PTC 程序
from . import 时间线#时间线投影
from . import 搜索索引#全文索引
from . import 轨迹表投影#事件投影
from . import 布局#轮次折叠
from . import 消息定义#消息定义
from . import 请求头定义#请求头
from . import 助手定义#助手定义
from . import 工具定义#工具定义
from . import 压缩定义#压缩定义
from .快照构建 import 空轨迹快照#空目标
from . import 快照构建#轨迹目标
from . import 轨迹视图#视图
from . import 轨迹工具栏#工具栏
from . import 轨迹时间线#时间线画面
from . import 轨迹表实现#账本
from . import 轨迹格#独立格
from . import 轨迹轮次#轮次
from . import 轨迹轮次头#轮次头
from . import 轨迹组头#组头

__all__=[
    '依赖','应用',
    '文案','时长存储','字符串换行存储','复制代码','约定',
    '轨迹记录','轨迹预览','轨迹节点','虚拟行','代码程序',
    '时间线','搜索索引','轨迹表投影','布局',
    '消息定义','请求头定义','助手定义','工具定义','压缩定义','快照构建',
    '轨迹视图','轨迹工具栏','轨迹时间线','轨迹表实现','轨迹格',
    '轨迹轮次','轨迹轮次头','轨迹组头',
]

依赖=['slots','sessions','uiSession','uiConversation','locale']#槽位、会话、会话标准源、对话、文案

def 应用(上下文,配置=None):
    '登记轨迹词表、定义、会话钩子和 conversation.view 页签'
    轨迹源缓存={}#同一绑定只包一次。绑定是字典，不能做弱键

    def 登记词典():
        '把中英词表写进 locale，卸下时由副作用拆掉'
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})

    上下文.副作用(登记词典,'ui-trajectory: dictionaries')#词典寿命
    时长=创建轨迹时长存储()#本插件共享的实测时长
    折行=创建轨迹字符串换行存储()#本插件共享的 JSON 折行

    def 轨迹源(绑定):
        '同一绑定只包一次。读的是 trajectory 目标'
        键=id(绑定)#对象身份。字典不能当弱键
        if 键 in 轨迹源缓存:
            return 轨迹源缓存[键]
        if isinstance(绑定,dict):
            标识=绑定.get('sessionId')
        elif isinstance(绑定,str):
            标识=绑定
        else:
            标识=绑定.sessionId
        目标=上下文.uiConversation.binding(标识).target('trajectory')#按会话标识取目标

        def 取快照():
            '目标还没有快照时用空轨迹'
            照=目标.getSnapshot()
            if 照 is None:
                return 空轨迹快照
            return 照

        def 订阅(监听):
            '把监听交给轨迹目标'
            return 目标.subscribe(监听)

        源={'getSnapshot':取快照,'subscribe':订阅}
        轨迹源缓存[键]=源
        return 源

    def 解析轨迹钩(绑定):
        '向会话标准源提供 trajectory'
        return {'hooks':{'trajectory':轨迹源(绑定)}}

    上下文.uiSession.provide({
        'hooks':['trajectory'],
        'resolve':解析轨迹钩,
    })
    消息定义.登记轨迹消息定义(上下文)#消息
    请求头定义.登记轨迹请求头定义(上下文)#请求头
    助手定义.登记轨迹助手定义(上下文)#助手
    工具定义.登记轨迹工具定义(上下文)#工具
    压缩定义.登记轨迹压缩定义(上下文)#压缩
    快照构建.登记轨迹会话视图(上下文)#目标构建器

    def 登记视图():
        '等会话视图槽出现再登记轨迹页签'

        def 视图标签():
            '页签固定为中文'
            return '轨迹'

        def 注入面(会话标识):
            '按会话组装轨迹视图注入面'
            绑定=上下文.sessions.binding(会话标识)
            会话=None if not isinstance(绑定,dict) else 绑定.get('session')
            if 会话 is None:
                raise Exception('ui-trajectory: session "'+str(会话标识)+'" is unavailable')
            目标=上下文.uiConversation.binding(会话标识).target('trajectory')

            def 加载更早():
                '分页后轨迹目标快照是否换成另一份'
                之前=目标.getSnapshot()
                会话.loadOlder()
                return 目标.getSnapshot() is not 之前

            def 设实测时长(值):
                '写入时长偏好'
                时长.set(值)

            def 加载图(附件):
                '该会话的图片地址'
                return 上下文.uiConversation.imageUrl(会话标识,附件)

            def 窥视图(附件):
                '缓存里已有的图片地址'
                return 上下文.uiConversation.peekImageUrl(会话标识,附件)

            def 读折行():
                '读 JSON 折行默认'
                return 折行.getSnapshot()

            def 写折行(值):
                '写 JSON 折行默认'
                折行.set(值)

            加载图.peek=窥视图#同步窥视
            return {
                'hooks':{'duration':时长},
                'jsonStringWrapping':{'getDefault':读折行,'setDefault':写折行},
                'loadOlder':加载更早,
                'loadImage':加载图,
                'setActualDuration':设实测时长,
            }

        return 上下文.slots.register({
            'name':'conversation.view',
            'id':'trajectory',
            'order':10,
            'locale':命名空间,
            'label':视图标签,
            'children':{
                'conversation.trajectory.images':{'kind':'single','scope':'session'},
            },
            'inject':注入面,
        },轨迹视图.轨迹视图)

    上下文.slots.inject('conversation.view',登记视图)#等槽位声明

inject=依赖#框架槽
apply=应用#框架槽
