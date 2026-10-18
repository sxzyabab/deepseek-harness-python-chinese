'一个会话的输入壳：草稿、提交机、通知和持久化'
from ....存储 import 创建快照存储
from ..草稿 import 快照草稿,解析草稿输入
from .输入机 import 提交机

__all__=['会话输入壳']

class 会话输入壳:
    '编辑器真相和提交平面之间的编排'
    def __init__(自身,会话,翻译,读触发,读弹层,发送=None):
        '空草稿，普通阶段'
        自身.会话=会话
        自身.翻译=翻译
        自身.发送=发送
        自身.读触发=读触发
        自身.读弹层=读弹层
        自身.机=提交机()
        自身.文本=''
        自身.引用=[]
        自身.命令=None
        自身.附件=[]
        自身.修订=0
        自身.通知值=None
        自身.通知=创建快照存储(None)
        自身.词表值={}
        自身.词表=创建快照存储({})
        自身.写出=None
        自身.编辑器=None
        自身.状态仓=创建快照存储(自身.投影())

    def 投影(自身):
        '发布给界面的输入状态'
        提交=自身.机.状态()
        出={
            'phase':提交['phase'],
            'draft':自身.文本,
            'draftRev':自身.修订,
            'attachmentIds':list(自身.附件),
            'queue':[],
        }
        if 'claim' in 提交:
            出['claim']=提交['claim']
        return 出

    def 发布(自身):
        '状态变了就写快照，并镜像草稿'
        自身.状态仓.set(自身.投影())
        if 自身.写出 is not None:
            自身.写出(自身.draftSnapshot)

    @property
    def snapshot(自身):
        '当前输入快照'
        return 自身.状态仓.getSnapshot()

    @property
    def state(自身):
        '可观察的输入状态'
        return 自身.状态仓

    @property
    def notices(自身):
        '通知通道'
        return 自身.通知

    @property
    def lexicon(自身):
        '斜杠和提及词表'
        return 自身.词表

    @property
    def draftSnapshot(自身):
        '语义草稿'
        return 快照草稿(自身.文本,自身.引用,None if 自身.命令 is None else 自身.命令.get('token'))

    @property
    def actions(自身):
        '界面可调用的输入动作'
        return {
            'persistDraft':自身.persistDraft,
            'pruneAttachments':自身.pruneAttachments,
        }

    @property
    def editor(自身):
        '栏绑定的编辑器。没有时为 None'
        return 自身.编辑器

    def 绑定编辑器(自身,编辑器):
        '输入栏挂上内容可编辑区'
        自身.编辑器=编辑器

    def caretSpan(自身):
        '当前光标。没有编辑器时落在文末'
        if 自身.编辑器 is not None and hasattr(自身.编辑器,'caretSpan'):
            return 自身.编辑器.caretSpan()
        return {'start':len(自身.文本),'end':len(自身.文本)}

    def setDraft(自身,输入):
        '换成这份草稿'
        快照=解析草稿输入(输入 if not isinstance(输入,str) else 输入)
        if isinstance(输入,str):
            快照={'text':输入,'references':[]}
        elif isinstance(输入,dict) and 'text' in 输入 and 'references' not in 输入:
            快照={'text':输入['text'],'references':[]}
        else:
            快照=解析草稿输入(输入)
        自身.文本=快照['text']
        自身.引用=快照['references']
        自身.命令=快照.get('command')
        自身.修订+=1
        自身.机.派发({'type':'draft-changed','command':自身.命令})
        自身.发布()

    def addAttachments(自身,标识列):
        '收下附件标识。裁决或提交中拒绝'
        if 自身.snapshot['phase'] in ('adjudicating','submitting'):
            return False
        for 标识 in 标识列:
            if 标识 not in 自身.附件:
                自身.附件.append(标识)
        自身.发布()
        return True

    def addFiles(自身,引用列,标识列):
        '引用和附件一起收下'
        if not 自身.addAttachments(标识列):
            return False
        return True

    def removeAttachment(自身,标识):
        '从壳里拿掉一个附件'
        if 标识 not in 自身.附件:
            return False
        自身.附件=[项 for 项 in 自身.附件 if 项!=标识]
        自身.发布()
        return True

    def dismissPopup(自身):
        '关掉当前弹层'
        弹层=自身.读弹层()
        if 弹层 is not None and hasattr(弹层,'dismiss'):
            弹层.dismiss()

    def bindDraftPersistence(自身,写出):
        '草稿变化时写到存储。返回拆除'
        自身.写出=写出
        def 拆():
            '不再镜像'
            if 自身.写出 is 写出:
                自身.写出=None
        return 拆

    def bindMirror(自身,写出):
        '旧名。仍把草稿镜像到写出'
        return 自身.bindDraftPersistence(写出)

    def persistDraft(自身):
        '立刻写一次当前草稿'
        if 自身.写出 is not None:
            自身.写出(自身.draftSnapshot)

    def pruneAttachments(自身,仍在):
        '拿掉界面已经不认的附件'
        留=set(仍在)
        自身.附件=[项 for 项 in 自身.附件 if 项 in 留]
        自身.发布()

    def notify(自身,级别,文本):
        '发布一条通知'
        自身.通知值={'level':级别,'text':文本}
        自身.通知.set(自身.通知值)

    def setLexicon(自身,词表):
        '替换斜杠和提及词表'
        自身.词表值=词表
        自身.词表.set(词表)

    def submit(自身,方式,来源):
        '从按钮或键盘提交'
        效果=自身.机.派发({'type':'enter','mode':方式,'draft':自身.文本})
        自身.执行(效果)

    def 执行(自身,效果列):
        '按顺序执行提交机给出的效果'
        for 效果 in 效果列:
            类型=效果['type']
            if 类型=='notice':
                自身.notify(效果['level'],效果['text'])
            elif 类型=='commit-draft':
                保留=效果.get('retainSuffixOf')
                if 保留 is None:
                    自身.文本=''
                    自身.引用=[]
                自身.修订+=1
            elif 类型=='default-sink':
                自身.默认汇(效果)
            elif 类型=='adjudicate':
                自身.裁决(效果)
            elif 类型=='begin-submit':
                自身.开始提交(效果)
        自身.发布()

    def 默认汇(自身,效果):
        '把普通消息交给会话发送'
        try:
            if 自身.发送 is None:
                raise Exception('ui-conversation: conversation service unavailable')
            结果=自身.发送(效果['draft'],list(自身.附件),效果['mode'])
            if hasattr(结果,'等待'):
                结果=结果.等待()
            成功=isinstance(结果,dict) and 结果.get('kind')=='success'
            自身.机.派发({'type':'sink-settled','attempt':效果['attempt'],'ok':成功,'outcome':结果 if isinstance(结果,dict) else None})
            if 成功:
                自身.文本=''
                自身.引用=[]
                自身.附件=[]
        except Exception as 错误:
            自身.机.派发({'type':'sink-settled','attempt':效果['attempt'],'ok':False,'message':str(错误)})

    def 裁决(自身,效果):
        '问输入触发器这条斜杠怎么处理'
        触发=自身.读触发()
        if 触发 is None or not hasattr(触发,'adjudicate'):
            自身.执行(自身.机.派发({'type':'adjudicated','attempt':效果['attempt'],'outcome':None}))
            return
        try:
            结局=触发.adjudicate(效果['draft'])
            if hasattr(结局,'等待'):
                结局=结局.等待()
            自身.执行(自身.机.派发({'type':'adjudicated','attempt':效果['attempt'],'outcome':结局}))
        except Exception as 错误:
            自身.执行(自身.机.派发({'type':'adjudication-failed','attempt':效果['attempt'],'message':str(错误)}))

    def 开始提交(自身,效果):
        '已认领命令交给 claim.submit'
        认领=效果['claim']
        try:
            提交=认领['submit']
            结局=提交(效果['args'],自身.附件)
            if hasattr(结局,'等待'):
                结局=结局.等待()
            自身.执行(自身.机.派发({'type':'submit-settled','attempt':效果['attempt'],'ok':True,'outcome':结局,'command':自身.命令}))
        except Exception as 错误:
            自身.执行(自身.机.派发({'type':'submit-settled','attempt':效果['attempt'],'ok':False,'message':str(错误),'command':自身.命令}))

    def 释放(自身):
        '会话结束时中止在途提交'
        自身.执行(自身.机.派发({'type':'release'}))
