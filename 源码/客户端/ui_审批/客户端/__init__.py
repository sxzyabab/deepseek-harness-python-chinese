'浏览器里的审批：登记文案和快捷键，并消费作用域里的审批瀑布'
import threading
from ..异常 import 审批委托#委托标记
from . import 文案
from . import 审批面板
from . import 约定

__all__=['文案','审批面板','约定','依赖','应用']

命名空间='approval'#文案命名空间
依赖=['sessions','remote','uiSession','slots','locale']#所需服务


def 应用(上下文,配置=None):
    '安装审批文案、固定快捷键，以及作用域里的审批瀑布'
    def 登记词典():
        '登记中英文案表。页面上的字不走英文表'
        return 上下文.locale.register(命名空间,{'zh':文案.中文,'en':文案.英文})#登记
    上下文.副作用(登记词典,'ui-approval: dictionaries')#词典寿命

    def 装快捷键(范围):
        '快捷键服务起来之后，登记允许和拒绝的固定参考'
        def 允许标签():
            '快捷键上显示允许一次'
            return '允许一次'#中文表原文
        def 登记允许():
            '登记允许一次的固定快捷键'
            return 范围.shortcuts.registerFixed({
                'id':'approval.allow',#命令标识
                'label':允许标签,#显示名
                'keys':['Enter'],#显示键
                'bindings':[{'code':'Enter','modifiers':[]}],#物理键
                'group':'approval',#分组
            })#登记
        范围.副作用(登记允许,'ui-approval: fixed allow reference')#允许的寿命
        def 拒绝标签():
            '快捷键上显示拒绝'
            return '拒绝'#中文表原文
        def 登记拒绝():
            '登记拒绝的固定快捷键'
            return 范围.shortcuts.registerFixed({
                'id':'approval.reject',#命令标识
                'label':拒绝标签,#显示名
                'keys':['Esc'],#显示键
                'bindings':[{'code':'Escape','modifiers':[]}],#物理键
                'group':'approval',#分组
            })#登记
        范围.副作用(登记拒绝,'ui-approval: fixed reject reference')#拒绝的寿命
    上下文.依赖启动(['shortcuts'],装快捷键)#等快捷键服务

    def 优先级(_交互):
        '和其它待处理交互同一级'
        return 0#同一级
    登记待处理=上下文.uiSession.registerPendingInteraction(优先级)#发布函数

    def 选择(属性):
        '只选中待决审批'
        待=属性['pendingInteraction'] if 'pendingInteraction' in 属性 else None#当前待处理
        if isinstance(待,约定.槽.待决审批):
            return 待#命中
        return None#不是审批

    def 解析理由(理由):
        '按当前界面语言解析请求方带来的展示文案'
        return 上下文.locale.resolveText(理由)#语言服务解析

    def 注入(*位置参数):
        '槽位可能传入会话键和动作。展示理由仍按当前语言解析'
        return {'resolveReason':解析理由}#交给面板

    def 登记撰写():
        '撰写链声明之后，把审批面板登记进去'
        return 上下文.slots.register({
            'name':'conversation.composer',#撰写链
            'priority':1,#高于输入栏
            'select':选择,#只命中审批
            'locale':命名空间,#文案命名空间
            'inject':注入,#展示理由解析
            'children':{#声明可选详情
                'conversation.approval.detail':{'kind':'single','scope':'session'},
            },
        },审批面板.审批面板)#面板类
    上下文.slots.inject('conversation.composer',登记撰写)#等撰写链声明

    def 监听(拥有方,请求,下一):
        '有会话就挂上待决审批，作答、委托或取消后再把结果交回瀑布'
        会话标识=上下文.sessions.scopeOf(拥有方)#这条瀑布所属的会话
        if 会话标识 is None:
            return 下一()#没有会话就交给下一环
        呈现={'toolName':请求['toolName']}#呈现字段
        if 'callId' in 请求 and 请求['callId'] is not None:
            呈现['callId']=请求['callId']#关联调用
        if 'reason' in 请求 and 请求['reason'] is not None:
            呈现['reason']=请求['reason']#审计理由
        if 'displayReason' in 请求 and 请求['displayReason'] is not None:
            呈现['displayReason']=请求['displayReason']#展示文案
        if 'signal' in 请求 and 请求['signal'] is not None:
            呈现['signal']=请求['signal']#取消信号
        待=约定.槽.待决审批(会话标识,呈现)#这一条审批
        完成=threading.Event()#本轮收尾后门闩
        def 委托清理():
            '域卸下时把未作答的请求交给下一环，并等本轮收尾'
            待.委托()#改走下一环
            完成.wait()#等 finally
        撤销=登记待处理(待,委托清理)#发布到会话
        try:
            try:
                return 待.结果#等用户作答或取消
            except 审批委托 as 错误:
                if 待.是委托(错误):
                    return 下一()#委托给下一环
                raise#不是这次委托
        finally:
            撤销()#从会话里拿掉
            完成.set()#放行域卸下
    getattr(上下文.remote,'$on')('approval/request',监听)#消费审批瀑布

inject=依赖#框架槽
apply=应用#框架槽
