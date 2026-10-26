from ....客户端.存储 import 创建快照存储
from ...模块.客户端.通告 import 取握手窗口
from . import 传递,反馈,文案
from .传递 import 文件传递
from .反馈 import 文件拖拽反馈
from .文案 import 中文,中文句,俄文,德文,日文,法文,英文,西班牙文,葡萄牙文

__all__=['传递','反馈','文案','名称','依赖','应用']

名称='ui-file-drag'
命名空间='fileDrag'
依赖=['slots','locale']

def 应用(上下文,配置=None):
    '拥有这一次激活的文件传递，并把失败提示挂到壳的覆盖层'
    窗口=取握手窗口()
    桥=getattr(窗口,'dshDesktop',None)
    桌面=None
    if 桥 is not None and getattr(桥,'protocolVersion',None)==1:
        桌面=getattr(桥,'fileDrag',None)
    失败=创建快照存储(None)
    def 登记词典():
        '挂上各语言文案。看得见的字走中文表'
        return 上下文.locale.register(命名空间,{
            'zh':中文,'en':英文,'ja':日文,'es':西班牙文,'fr':法文,'de':德文,'ru':俄文,'pt':葡萄牙文,
        })
    上下文.副作用(登记词典)
    序号盒={'值':0}
    def 报告失败():
        '用中文失败句换一条新提示'
        序号盒['值']=序号盒['值']+1
        失败.set({'text':中文句('failed'),'sequence':序号盒['值']})
    传递器=文件传递(桌面,报告失败)
    def 关掉():
        '清掉当前失败提示'
        失败.set(None)
    上下文.反射.提供服务('fileDrag',{
        'actions':{'prepare':传递器.准备,'reportFailure':报告失败},
        'read':传递器.读取,
    })
    def 登记寿命():
        '卸下时结束传递并清掉提示'
        def 清理():
            '结束传递，并清掉提示'
            传递器.拆除()
            关掉()
        return 清理
    上下文.副作用(登记寿命)
    def 注入():
        '覆盖层只拿失败源和关掉动作'
        return {'hooks':{'failure':失败},'dismiss':关掉}
    def 挂反馈():
        '登记失败提示'
        return 上下文.slots.register({
            'name':'shell.overlay',
            'id':'file-drag.feedback',
            'inject':注入,
        },文件拖拽反馈)
    上下文.slots.inject('shell.overlay',挂反馈)

inject=依赖
name=名称
apply=应用
default=应用
