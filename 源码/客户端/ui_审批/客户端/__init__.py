"""浏览器审批消费者，叠在既有作用域 Remote Event waterfall 上。

对齐上游 `ui-approval/src/client/index.ts`。公开面仅中文名。
"""
from .审批面板 import 审批面板#审批面板
from .约定.槽 import 待决审批#待处理审批面
from .文案 import 中文,英文,NS,zh,en#中英文词典

__all__=[#仅中文公开名
    '注入','应用','回答审批','审批面板','待决审批','中文','英文','NS','zh','en',
]#公开面结束

注入=['sessions','remote','uiSession','slots','locale']#所需服务
命名空间=NS#本地化命名空间

def 回答审批(上下文,拥有方,请求,下一,登记待处理):#呈现一个请求直到作答或寿命结束
    """无会话则下放；委托则下放；其它错误上抛。"""
    会话标识=上下文.sessions.scopeOf(拥有方)#解析所属会话
    if 会话标识 is None:#无会话
        return 下一()#下放
    载荷={#呈现用请求
        'toolName':请求.get('toolName') if isinstance(请求,dict) else getattr(请求,'toolName',None),#工具名
    }#载荷起点
    调用=请求.get('callId') if isinstance(请求,dict) else getattr(请求,'callId',None)#可选调用 id
    if 调用 is not None:#有
        载荷['callId']=调用#写入
    理由=请求.get('reason') if isinstance(请求,dict) else getattr(请求,'reason',None)#可选原因
    if 理由 is not None:#有
        载荷['reason']=理由#写入
    信号=请求.get('signal') if isinstance(请求,dict) else getattr(请求,'signal',None)#可选取消
    if 信号 is not None:#有
        载荷['signal']=信号#写入
    待=待决审批(会话标识,载荷)#物化待处理面
    完成箱={'done':False}#拆卸结算门闩

    def 委托清理():#拆卸时委托 waterfall
        """委托并等本轮 finally。"""
        待.delegate()#拆卸时委托
        while not 完成箱['done']:#等本轮 finally
            break#同步宿主半无需自旋

    撤销=登记待处理(待,委托清理)#发布并登记委托
    try:#等待作答
        try:#内层捕获委托
            return 待.result#等用户作答
        except Exception as 错误:#作答失败或委托
            if 待.isDelegation(错误):#委托
                return 下一()#下放
            raise#其它错误上抛
    finally:#无论成败清理
        撤销()#撤销待处理投影
        完成箱['done']=True#放行拆卸委托

def 应用(上下文):#浏览器侧安装入口
    """安装审批文案与作用域 waterfall 消费者。"""
    上下文.effect(lambda:上下文.locale.register(命名空间,{'zh':zh,'en':en}),'ui-approval: dictionaries')#登记词典
    登记待处理=上下文.uiSession.registerPendingInteraction(lambda _交互:0)#同优先级域

    def 选择(属性):#链选择器
        """仅命中审批。"""
        待=属性.get('pendingInteraction') if isinstance(属性,dict) else getattr(属性,'pendingInteraction',None)#待处理
        return 待 if isinstance(待,待决审批) else None#仅审批

    上下文.slots.inject('conversation.composer',lambda:上下文.slots.register({#登记 composer 链条目
        'name':'conversation.composer',#槽名
        'priority':1,#高于输入栏
        'select':选择,#仅命中审批
        'locale':命名空间,#词典命名空间
        'children':{#子槽声明
            'conversation.approval.detail':{'kind':'single','scope':'session'},#声明可选详情子槽
        },#子槽结束
    },审批面板))#登记结束

    def 监听(请求,下一):#挂 waterfall
        """作用域 waterfall 消费。"""
        return 回答审批(上下文,上下文,请求,下一,登记待处理)#消费

    上下文.remote.$on('approval/request',监听)#挂载监听
