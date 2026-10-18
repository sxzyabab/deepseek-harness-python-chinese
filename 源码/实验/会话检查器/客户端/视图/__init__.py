'登记会话检查器侧栏页，以及按会话复用的日志和对话来源'

import weakref#模型按会话实例回收
from ..文案 import 命名空间#文案命名空间
from .聊天节点.文档对象 import 主聊天根#主对话列
from .聊天节点.定位目标 import 解析聊天定位目标#精确和附近坐标
from .聊天节点.模型 import 聊天节点模型#对话表
from .聊天节点.选取器 import 检查器聊天选取器#点选罩子
from .会话日志.聊天目标 import 会话日志聊天目标#日志坐标
from .会话日志.模型 import 会话日志模型#日志表
from .视图 import 会话检查器视图#侧栏页

__all__=[
    '登记检查器标签','类型筛选','表格模型','表格布局','对象值','对象','原始json','格式',
    '视图','类型筛选器','检查器表格','检查器对象树','检查器详情','会话日志','聊天节点',
]#同目录模块都导出

from . import (
    类型筛选,表格模型,表格布局,对象值,对象,原始json,格式,视图,
    类型筛选器,检查器表格,检查器对象树,检查器详情,会话日志,聊天节点,
)#执行同目录顶层

def 登记检查器标签(上下文):
    '登记侧栏页。每个会话绑定只建一套模型'
    活动={'选取器':None}#当前选取
    已释放={'值':False}#插件是否已卸

    def 拆选取():
        '卸下时拆掉自己的选取器，不调用面板回调'
        def 拆除():
            '标记已释放并拆当前选取'
            已释放['值']=True#不再开始新的
            if 活动['选取器'] is not None:#还有罩子
                活动['选取器'].拆除()#只拆资源
        return 拆除#副作用的清理

    上下文.副作用(拆选取,'session-inspector: chat picker')#插件寿命

    def 标题():
        '侧栏和引导用的标题'
        return '会话数据诊断'#中文原文

    def 说明():
        '引导说明'
        return '在侧边栏分析当前会话原始日志和聊天分组数据'#中文原文

    def 登记标签():
        '登记侧栏种类和引导'
        return 上下文.sidebarRightTabs.登记({
            'id':'@deepseek-ai/dsh-experimental-session-inspector',#插件标识
            'kind':'session-inspector-log',#种类
            'title':标题,#标题函数
            'guide':[{'id':'open','order':60,'title':标题,'description':说明}],#引导
        })#拆除器

    上下文.副作用(登记标签,'session-inspector: sidebar tab')#标签寿命
    模型表=weakref.WeakKeyDictionary()#会话实例到注入面

    def 注入(会话标识):
        '按会话复用模型。绑定是字典，弱键用里面的会话实例'
        绑定=上下文.sessions.binding(会话标识)#会话绑定
        if 绑定 is None:#没有这个会话
            raise Exception('session-inspector: unknown Session '+str(会话标识))#上游原文
        会话=绑定['session']#可弱引用的实例
        来源=模型表.get(会话)#已建
        if 来源 is None:#第一次
            对话=上下文.uiConversation.binding(绑定)#对话绑定
            聊天=聊天节点模型(对话)#对话表
            日志=会话日志模型(绑定['eventSource'])#日志表

            def 聊天根(标识=会话标识):
                '主区当前会话就是这一份时才返回主对话列'
                当前=上下文.uiSession.adapter['current']['getSnapshot']()#主视图
                键=当前.get('key') if isinstance(当前,dict) else None#会话键
                if 键!=标识:#不是这个会话
                    return None#不选取、不定位
                return 主聊天根()#主对话列

            def 选取聊天(所有者,已选取,已取消,取根=聊天根):
                '插件已卸或主对话不可用时不开始'
                if 已释放['值']:#已经卸了
                    return None#不开始
                if 活动['选取器'] is not None:#换一次选取
                    活动['选取器'].取消()#取消上一次
                持有={'选取器':None}#这一次

                def 释放():
                    '这一次结束时清掉活动引用'
                    if 活动['选取器'] is 持有['选取器']:#还是这一次
                        活动['选取器']=None#清空

                选取器=检查器聊天选取器(取根,所有者,已选取,已取消,释放)#罩子
                持有['选取器']=选取器#记住
                if not 选取器.开始():#没有可见对话
                    return None#不开始
                活动['选取器']=选取器#当前

                def 停止():
                    '卸掉这一次选取'
                    选取器.拆除()#拆资源
                return 停止#表格卸载时调用

            def 解析目标(目标,对话绑定=对话):
                '从当前对话快照解析定位坐标'
                快照=对话绑定.snapshot.getSnapshot()#对话快照
                视图=快照.get('views') if isinstance(快照,dict) else 快照.views#视图
                聊天视图=视图.get('chat')#聊天
                节点仓=None if not isinstance(聊天视图,dict) else 聊天视图.get('nodes')#节点
                节点=() if 节点仓 is None else 节点仓.values()#已加载节点
                return 解析聊天定位目标(目标,节点 or [])#主目标和邻居

            def 记录类型(键,模式,聊天模型=聊天,日志模型=日志):
                '不额外订阅，只读当前类型'
                源=聊天模型.行(键) if 模式=='chat-node' else 日志模型.行(键)#记录源
                if 源 is None:#行不在
                    return None#没有类型
                快照=源.getSnapshot()#当前记录
                if not isinstance(快照,dict):#空
                    return None#没有类型
                return 快照.get('type')#原始类型

            def 日志目标(键,日志模型=日志):
                '选中日志行在主对话里的位置'
                锚=日志模型.聊天锚(键)#事件和可选增量
                if 锚 is None:#行没了
                    return None#没有坐标
                return 会话日志聊天目标(锚)#坐标

            def 选取行(目标,模式,聊天模型=聊天,日志模型=日志,对话绑定=对话):
                '对话分组直接匹配。日志再补上锚点和回合步骤'
                if 模式=='chat-node':#对话表
                    return 聊天模型.选取(目标)#最近的行
                快照=对话绑定.snapshot.getSnapshot()#对话快照
                视图=快照.get('views') if isinstance(快照,dict) else 快照.views#视图
                分组=视图.grouped('chat')#分组
                引用=None#分组条目
                if 目标.get('groupKey') is not None and 分组 is not None:#点了分组
                    for 条目 in 分组.entries or []:#根条目
                        if isinstance(条目,dict) and 条目.get('kind')=='group' and 条目.get('key')==目标.get('groupKey'):#同一组
                            引用=条目#记下
                            break#停
                组=None#分组快照
                if isinstance(引用,dict) and 引用.get('kind')=='group':#找到了组
                    组=分组.组源(引用.get('key'))['getSnapshot']()#当前组
                节点键=目标.get('nodeKey')#节点
                if 节点键 is None and isinstance(组,dict):#用组的第一个成员
                    成员=组.get('members') or []#成员
                    if len(成员)>0 and isinstance(成员[0],dict):#有成员
                        节点键=成员[0].get('key')#第一个
                节点=None#节点快照
                if 节点键 is not None:#有键
                    聊天视图=视图.get('chat')#聊天
                    仓=None if not isinstance(聊天视图,dict) else 聊天视图.get('nodes')#仓库
                    if 仓 is not None:#有仓库
                        节点=仓.get(节点键)#节点
                位置=节点.get('location') if isinstance(节点,dict) else None#位置
                补={}#补进日志选取的字段
                if isinstance(节点,dict):#有节点
                    补['anchorSeq']=节点.get('anchorSeq')#锚
                    补['nodeKind']=节点.get('kind')#种类
                种类=位置.get('kind') if isinstance(位置,dict) else None#位置种类
                if 种类 in ('turn','step') and isinstance(位置.get('turn'),dict):#有回合
                    补['turn']=位置['turn'].get('turn')#回合号
                if 种类=='step' and isinstance(位置.get('step'),dict):#有步骤
                    补['step']=位置['step'].get('step')#步骤号
                合并=dict(目标)#原身份
                合并.update(补)#补上日志需要的字段
                return 日志模型.选取(合并)#日志行

            def 加载更早(会话=绑定['session']):
                '向更早的页翻。会话现在同步返回'
                会话.loadOlder()#翻页

            来源={
                'hooks':{'chatRows':聊天,'logRows':日志},#两份行顺序
                'keyedHooks':{'chatRecord':聊天.行,'logRecord':日志.行},#单行记录
                'chatRoot':聊天根,#主对话
                'pickChat':选取聊天,#点选
                'resolveChatTargets':解析目标,#定位坐标
                'recordType':记录类型,#筛选用的类型
                'loadOlder':加载更早,#翻页
                'objects':聊天.对象(会话标识),#对象树
                'logChatTarget':日志目标,#日志行的对话坐标
                'pickRow':选取行,#点选对到行
            }#注入面
            模型表[会话]=来源#复用
        return 来源#这一会话的注入

    def 登记页():
        '等右栏标签槽声明后再登记这一页'
        return 上下文.slots.register({
            'name':'sidebar.right.pane.tab',#右栏页
            'key':'@deepseek-ai/dsh-experimental-session-inspector',#和标签同一标识
            'locale':命名空间,#文案命名空间
            'inject':注入,#按会话注入
        },会话检查器视图)#页面类

    上下文.slots.inject('sidebar.right.pane.tab',登记页)#等槽声明
