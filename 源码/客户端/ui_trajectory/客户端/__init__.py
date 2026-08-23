"""浏览器轨迹插件：向会话视图槽贡献一条条目。



对齐上游 `ui-trajectory/src/client/index.ts`。公开面仅中文名。

React 像素半以结构树 `轨迹视图` 接线；完整 DOM/CSS 仍以上游为准。

"""

from ....依赖 import cordis#外部依赖胶水
是否thenable=cordis.工具.是否thenable#可等待判定

from .文案 import 命名空间,中文,英文#词典

from .时长存储 import 创建轨迹时长存储#时长偏好

from .消息定义 import 登记轨迹消息定义#消息定义

from .请求头定义 import 登记轨迹请求头定义#请求头定义

from .助手定义 import 登记轨迹助手定义#助手定义

from .工具定义 import 登记轨迹工具定义#工具定义

from .压缩定义 import 登记轨迹压缩定义#压缩定义

from .快照构建 import 登记轨迹会话视图#会话轨迹视图

from .布局 import 派生轨迹布局,追加轨迹流式布局#布局

from .时间线 import 派生轨迹时间线,轨迹时间线焦点下标,格式化时间线偏移#时间线

from .搜索索引 import 轨迹搜索索引#搜索

from .虚拟行 import 编组轨迹虚拟行,轨迹虚拟记录键#虚拟行

from .轨迹记录 import 轨迹记录身份,格式化已用秒数,格式化毫秒时长,取字段#记录

from .轨迹视图 import 轨迹视图#视图结构树

from .轨迹工具栏 import 轨迹工具栏,样式表 as 工具栏样式表,样式文件 as 工具栏样式文件#工具栏

from .轨迹格 import 轨迹格,种类标签,样式表 as 格样式表,样式文件 as 格样式文件#格

from .轨迹轮次 import 轨迹轮次,轨迹轮次头,列标签,轮次样式表,轮次头样式表,轮次样式文件,轮次头样式文件#轮次

from .轨迹表实现 import 轨迹表,样式表 as 表样式表,样式分块 as 表样式分块#权威实现

from . import 轨迹表投影#纯投影面（上游 TrajectoryTable 非 DOM）

from . import 轨迹表视图#账本/检查器兼容入口

from .轨迹表视图 import 种类样式类#种类修饰

from .轨迹时间线 import 轨迹时间线,样式表 as 时间线样式表,样式文件 as 时间线样式文件#时间线视图+样式

from .轨迹组头 import 轨迹组头,样式表 as 组头样式表,样式文件 as 组头样式文件#组头行

from .轨迹预览 import 轨迹预览文本#有界预览



__all__=[#仅中文公开名

    '注入',

    '应用',

    '命名空间',

    '中文',

    '英文',

    '派生轨迹布局',

    '追加轨迹流式布局',

    '派生轨迹时间线',

    '轨迹搜索索引',

    '编组轨迹虚拟行',

    '轨迹记录身份',

    '轨迹视图',

    '轨迹工具栏',

    '轨迹格',

    '种类标签',

    '轨迹轮次',

    '轨迹轮次头',

    '列标签',

    '轨迹组头',

    '轨迹预览文本',

    '工具栏样式表',

    '工具栏样式文件',

    '格样式表',

    '格样式文件',

    '轮次样式表',

    '轮次头样式表',

    '轮次样式文件',

    '轮次头样式文件',

    '组头样式表',

    '组头样式文件',

    '表样式表',

    '表样式分块',

    '轨迹表',

    '轨迹表投影',

    '轨迹表视图',

    '种类样式类',

    '轨迹时间线',

    '时间线样式表',

    '时间线样式文件',

]#公开面结束



注入=['slots','conversationEvents','conversationViews','sessions','locale']#槽位、会话事件、视图、会话、文案



def 解开(值):#承诺则等待否则原样

    """承诺则等待，否则原样返回。"""

    if 是否thenable(值):#可等待

        return 值.等待()#等待承诺

    return 值#同步值



def 应用(上下文):#安装轨迹视图浏览器半边

    """登记轨迹视图标签、词表与各 Definition。"""

    上下文.effect(lambda:上下文.locale.register(命名空间,{'zh':中文,'en':英文}),'ui-trajectory: dictionaries')#登记中英文案

    翻译=上下文.locale.bind(命名空间)#绑定本命名空间的翻译

    时长=创建轨迹时长存储()#本插件共享的实测时长偏好句柄

    登记轨迹消息定义(上下文)#登记消息块定义

    登记轨迹请求头定义(上下文)#登记请求头定义

    登记轨迹助手定义(上下文)#登记助手消息定义

    登记轨迹工具定义(上下文)#登记工具调用定义

    登记轨迹压缩定义(上下文)#登记压缩块定义

    登记轨迹会话视图(上下文)#登记会话轨迹视图投影

    def 登记视图():#等会话视图槽出现再登记轨迹标签

        """登记 conversation.view 轨迹贡献。"""

        def 注入面(会话标识):#按会话组装轨迹视图注入面

            """会话不可用则硬失败。"""

            绑定=上下文.sessions.binding(会话标识)#取出该会话绑定

            会话=取字段(绑定,'session') if 绑定 is not None else None#会话面

            if 会话 is None:#会话不可用则硬失败

                raise Exception(f'ui-trajectory: session "{会话标识}" is unavailable')#会话绑定缺失

            def 加载更早():#再向更早分页

                """是否真的多出轨迹。"""

                快照=解开(会话.getSnapshot())#当前快照

                视图=取字段(快照,'views')#视图表

                之前=视图.get('trajectory') if isinstance(视图,dict) else 取字段(视图,'trajectory')#分页前

                解开(会话.loadOlder())#向更早一页

                之后快照=解开(会话.getSnapshot())#分页后

                之后视图=取字段(之后快照,'views')#视图表

                之后=之后视图.get('trajectory') if isinstance(之后视图,dict) else 取字段(之后视图,'trajectory')#分页后轨迹

                return 之后 is not 之前#轨迹视图是否因分页而变

            def 设实测时长(值):#记下实测时长

                """写入时长偏好句柄。"""

                时长['set'](值)#写入

            return {#组装注入面

                'hooks':{'duration':时长},#把时长句柄注入视图钩子

                'loadOlder':加载更早,#向更早分页

                'setActualDuration':设实测时长,#实测时长

                'deriveLayout':派生轨迹布局,#布局折叠

                'appendPartial':追加轨迹流式布局,#流式拼接

                'deriveTimeline':派生轨迹时间线,#时间线

                'timelineFocus':轨迹时间线焦点下标,#焦点下标

                'formatOffset':格式化时间线偏移,#偏移标签

                'formatElapsed':格式化已用秒数,#秒标签

                'formatMillis':格式化毫秒时长,#毫秒标签

                'recordId':轨迹记录身份,#稳定身份

                'SearchIndex':轨迹搜索索引,#搜索索引类

                'groupVirtualRows':编组轨迹虚拟行,#虚拟行

                'virtualRecordKey':轨迹虚拟记录键,#虚拟行键

            }#注入面结束

        return 上下文.slots.register({#登记

            'name':'conversation.view',#槽名

            'id':'trajectory',#贡献 id

            'order':10,#排序

            'locale':命名空间,#文案命名空间

            'label':lambda:翻译('view.trajectory'),#标签走绑定翻译

            'inject':注入面,#注入工厂

        },轨迹视图)#结构树视图

    上下文.slots.inject('conversation.view',登记视图)#依赖槽位声明


