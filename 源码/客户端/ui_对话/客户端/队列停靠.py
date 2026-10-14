from ..异常 import 对话错误
from .文案 import 命名空间

__all__=['队列停靠','队列停靠条目']

from nicegui import ui as 界面
from .文案 import 中文 as 对话文案
from ..异常 import 页面失败文案,贴出失败

def 恒等翻译(键,参数=None):
    '无宿主文案时用本包中文词典，没有则返回键本身。'
    if 键 not in 对话文案:#词典没有
        return 键#键
    文本=对话文案[键]#词条
    if 参数 is None:#无参数
        return 文本#原文
    for 名 in 参数:#替换占位
        文本=文本.replace('{'+名+'}',str(参数[名]))#替换
    return 文本#译完

def 取队列(快照):
    '会话 queue 字段'
    队列=快照['queue'] if 快照 is not None and 'queue' in 快照 else None#队列
    return 队列 if 队列 is not None else []#空容器仍返回

def 取可改(快照):
    '无 subagent 才可改'
    return 快照 is None or 'subagent' not in 快照 or 快照['subagent'] is None#可改

def 取文本(内容):
    '从 content 块拼文本'
    if isinstance(内容,str):#已是串
        return 内容#串
    if not isinstance(内容,(list,tuple)):#非列表
        return ''#空
    段=[]#段
    for 块 in 内容:#块
        种=块['type'] if isinstance(块,dict) and 'type' in 块 else None#种
        文=块['text'] if isinstance(块,dict) and 'text' in 块 else None#文
        if 种=='text' and isinstance(文,str):#文本块
            段.append(文)#收
    return ''.join(段)#拼

class 队列停靠:
    '单条直出；多条默认可折叠计数头'

    def __init__(自身,属性=None):
        '记下 props 与本地态'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.折叠=True#折叠
        自身.编辑=None#编辑 {id,text}
        自身.忙碌=None#忙碌 id
        自身.画面=None#可反复清空的画面
        自身.渲染()#槽位只调用构造，这里就要画

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if 属性 is not None else {}#新

    def 开编(自身,标识,正文,可改):
        '开始编辑一行'
        if 可改 is True:#可
            自身.编辑={'id':标识,'text':正文}#开

    def 取消编(自身):
        '取消编辑'
        自身.编辑=None#清

    def 改编(自身,标识,文):
        '改编辑正文'
        自身.编辑={'id':标识,'text':文}#改

    def 切换折叠(自身,交互中):
        '非交互才翻转'
        if 交互中 is False:#闲
            自身.折叠=not 自身.折叠#翻

    def 渲染(自身):
        '空队列返回 None'
        属性=自身.属性#props
        用会话=属性['useSession'] if 'useSession' in 属性 else None#会话
        更新队列=属性['updateQueue'] if 'updateQueue' in 属性 else None#更新
        通知=属性['notify'] if 'notify' in 属性 else None#通知
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        收件=用会话(取队列) if 用会话 is not None else []#收件
        队列=[行 for 行 in 收件 if 'placement' in 行 and 行['placement']=='queued']#排队
        可改=用会话(取可改) if 用会话 is not None else True#可改
        if len(队列)==0:#空
            return#不画
        编标识=自身.编辑['id'] if 自身.编辑 is not None and 'id' in 自身.编辑 else None#编 id
        仍在=False#是否仍在队列
        for 行 in 队列:#扫
            if 'id' in 行 and 行['id']==编标识:#命中
                仍在=True#在
                break#停
        if 自身.编辑 is not None and (可改 is False or 仍在 is False):#编辑失效
            自身.编辑=None#清
        if len(队列)==0 and 自身.折叠 is False:#空则折
            自身.折叠=True#折
        自身.画面失败=None
        if 自身.画面 is not None:
            try:
                自身.画面.clear()
            except Exception as 错误:
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.column().classes('队列停靠')#停靠
        def 重画():
            '按折叠和编辑态重画排队消息。'
            自身.画面.clear()#清空
            现编=自身.编辑['id'] if 自身.编辑 is not None and 'id' in 自身.编辑 else None#编 id
            现交互=可改 is True and (自身.编辑 is not None or 自身.忙碌 is not None)#交互
            现展开=自身.折叠 is False or 现交互 is True#展开
            现列表=len(队列)==1 or 现展开 is True#列表
            with 自身.画面:#停靠
                贴出失败(自身)
                if len(队列)>1:#多条才折叠
                    def 点折():
                        '翻转折叠。'
                        自身.切换折叠(现交互)#翻
                        重画()#重画
                    界面.button(翻译('queue.count',{'n':len(队列)}),on_click=点折)#计数
                else:#单条
                    界面.label(翻译('queue.count',{'n':len(队列)}))#计数
                if 现列表 is False:#折叠
                    return#只留计数
                for 行 in 队列:#逐行
                    标识=行['id'] if 'id' in 行 else None#id
                    正文=取文本(行['content'] if 'content' in 行 else None)#正文
                    在编=自身.编辑 is not None and 现编==标识#编辑中
                    编文=自身.编辑['text'] if 在编 is True and 'text' in 自身.编辑 else ''#编文
                    if 自身.忙碌==标识:#忙
                        界面.label(翻译('queue.sending'))#发送中
                    if 在编 is True:#编辑
                        框=界面.textarea(value=编文 if 编文 is not None else '').classes('排队编辑')#编辑
                        def 改文(钉标识=标识,钉框=框):
                            '记下编辑正文。'
                            值=钉框.value if 钉框.value is not None else ''#文
                            自身.改编(钉标识,值)#改
                        框.on_value_change(改文)#改
                        def 点存(钉标识=标识):
                            '保存。'
                            自身._存编辑(钉标识,更新队列,通知,翻译)#存
                            重画()#重画
                        def 点消():
                            '取消编辑。'
                            自身.取消编()#取消
                            重画()#重画
                        界面.button(翻译('queue.save'),on_click=点存)#保存
                        界面.button(翻译('queue.cancelEdit'),on_click=点消)#取消
                    else:#阅读
                        if 正文=='':#没有文本
                            界面.label(翻译('queue.edit.unsupported'))#不可编辑
                        else:#正文
                            界面.label(正文)#文
                        if 可改 is True:#可改
                            def 点编(钉标识=标识,钉正文=正文):
                                '开始编辑。'
                                自身.开编(钉标识,钉正文,可改)#开
                                重画()#重画
                            def 点发(钉标识=标识):
                                '发送这一条。'
                                自身._动作(钉标识,{'kind':'send'},翻译('queue.sendFailed'),更新队列,通知)#发
                                重画()#重画
                            def 点删(钉标识=标识):
                                '删除这一条。'
                                自身._动作(钉标识,{'kind':'delete'},翻译('queue.removeFailed'),更新队列,通知)#删
                                重画()#重画
                            界面.button(翻译('queue.edit'),on_click=点编)#编辑
                            界面.button(翻译('input.send'),on_click=点发)#发送
                            界面.button(翻译('queue.remove'),on_click=点删)#删除
        重画()#画

    def _动作(自身,标识,动作,失败文,更新队列,通知):
        '忙态围栏'
        自身.忙碌=标识#忙
        try:#派
            if 更新队列 is not None:#有
                更新队列(标识,动作)#派
            return True#成
        except 对话错误:#败
            if 通知 is not None:#有
                通知('error',失败文)#报
            return False#败
        finally:#清忙
            if 自身.忙碌==标识:#本项
                自身.忙碌=None#清

    def _存编辑(自身,标识,更新队列,通知,翻译):
        '写 edit 动作'
        if 自身.编辑 is None:#无
            return#停
        文=自身.编辑['text'] if 'text' in 自身.编辑 else ''#文
        if str(文).strip()=='':#无效
            return#停
        if 自身._动作(标识,{'kind':'edit','content':[{'type':'text','text':文}]},翻译('queue.editFailed'),更新队列,通知) is True:#成
            自身.编辑=None#清

    def __call__(自身,属性=None):
        '对齐 React'
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

def 队列停靠条目():
    '对齐 queueDockEntry：独立激活边界的 plain registrant'
    def 应用(上下文):
        '终端 input-dock 条目（order 20）'
        def 注入(会话标识):
            'updateQueue + notify'
            作用域=上下文.sessions.scope(会话标识)#作用域
            if 作用域 is None:#无
                raise 对话错误('排队停靠: 会话 "'+str(会话标识)+'" 没有作用域')
            会话=作用域.获取服务('conversation')#conversation
            if 会话 is None:#无
                raise 对话错误('排队停靠: conversation 服务不可用')
            def 通知(级别,正文):
                'input.for(actx).notify'
                会话.input.按作用域取门面(作用域).notify(级别,正文)#通知
            def 改队列(项标识,动作):
                '改队列'
                return 会话.updateQueue(项标识,动作)#改
            return {#注入面
                'updateQueue':改队列,#改队列
                'notify':通知,#通知
            }#结束
        def 登记():
            'register'
            return 上下文.slots.register({#条目
                'name':'conversation.input.dock',#停靠
                'id':'queue',#id
                'order':20,#序
                'locale':命名空间,#文案
                'inject':注入,#注入
            },队列停靠)#组件
        上下文.slots.inject('conversation.input.dock',登记)#等槽
    return {'name':'conversation-queue-dock','inject':['slots','conversation','sessions'],'apply':应用}#插件
