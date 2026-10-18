'按会话保留输入壳，并在第一次查找前读入已存草稿'
from ..存储 import 读会话草稿
from .外壳 import 会话输入壳

__all__=['输入枢纽']

class 输入枢纽:
    '每个仍在的会话绑定一份壳'
    def __init__(自身,上下文,翻译):
        '空表'
        自身.上下文=上下文
        自身.翻译=翻译
        自身.壳表={}

    def shellFor(自身,绑定):
        '按绑定取壳。第一次把存下的草稿放进去'
        已有=自身.壳表.get(id(绑定))
        if 已有 is not None:
            return 已有
        会话=绑定.session
        def 读触发():
            '当前作用域上的输入触发器'
            服务=绑定.ctx.get('inputTriggers') if hasattr(绑定.ctx,'get') else None
            if 服务 is None:
                return None
            if hasattr(服务,'sessionOf'):
                return 服务.sessionOf(绑定.ctx)
            return 服务
        def 读弹层():
            '当前作用域上可关掉的弹层'
            服务=绑定.ctx.get('commandUi') if hasattr(绑定.ctx,'get') else None
            if 服务 is None:
                return None
            if hasattr(服务,'popupFor'):
                return 服务.popupFor(绑定.ctx)
            return 服务
        def 发送(文本,附件,方式):
            '交给会话服务做一次带附件的发送'
            控制器=自身.上下文.get('conversation')
            if 控制器 is None:
                raise Exception('ui-conversation: conversation service unavailable')
            return 控制器.sendSession(会话,文本,附件,方式)
        壳=会话输入壳(会话,自身.翻译,读触发,读弹层,发送)
        存下=读会话草稿(绑定.sessionId)
        if 存下['text']!='' or len(存下['references'])>0:
            壳.setDraft(存下)
        自身.壳表[id(绑定)]=壳
        def 拆():
            '作用域结束时放掉壳'
            def 摘():
                '中止并忘掉'
                if 自身.壳表.get(id(绑定)) is 壳:
                    壳.释放()
                    del 自身.壳表[id(绑定)]
            return 摘
        if hasattr(绑定.ctx,'effect'):
            绑定.ctx.effect(拆,'ui-conversation: input shell')
        return 壳

    def shell(自身,会话标识):
        '按会话标识取壳。绑定必须还在'
        绑定=自身.上下文.sessions.binding(会话标识)
        if 绑定 is None:
            raise Exception('ui-conversation: session "'+str(会话标识)+'" resolved no binding')
        return 自身.shellFor(绑定)

    def canPickFiles(自身,会话标识):
        '壳不在裁决或提交中就可以选文件'
        try:
            壳=自身.shell(会话标识)
        except Exception:
            return False
        return 壳.snapshot['phase'] not in ('adjudicating','submitting')

    def pickFiles(自身,会话标识):
        '让编辑器打开文件选择'
        壳=自身.shell(会话标识)
        if 壳.editor is not None and hasattr(壳.editor,'pickFiles'):
            壳.editor.pickFiles()

    def inputTriggers(自身,会话标识):
        '这份会话的输入触发器'
        绑定=自身.上下文.sessions.binding(会话标识)
        if 绑定 is None:
            return None
        壳=自身.shellFor(绑定)
        return 壳.读触发()

    def 供(自身,作用域):
        '队列停靠按作用域找到壳，用来发通知'
        标识=None
        if hasattr(作用域,'sessionId'):
            标识=作用域.sessionId
        elif hasattr(作用域,'get'):
            标识=作用域.get('sessionId')
        return 自身.shell(标识)
