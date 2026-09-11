"""纯输入机上的会话输入外壳：唯一机器调用方与效果执行器。

对齐上游 `ui-conversation/src/client/input/facade.ts`。公开面仅中文名。
拥有输入状态存储（机器状态 + 队列叠加）、通知通道与提交事务管道。
依赖为 dict；触发器与弹层为本包对象；机事件与效应为 dict。
"""
import threading#序列化取消标志
import time#缺省墙钟
from ..服务 import 对话错误#本包异常
from .输入机 import 输入机,已中止,若已中止则抛出#纯输入状态机与中止

__all__=['快照存储','会话输入壳','触发档位']#仅中文公开名

空队列=()#缺席队列
空词表={}#无管道词表

class 快照存储:#简易 SnapshotStore
    """值 + 订阅；对齐 createSnapshotStore。"""
    def __init__(自身,初值):#播种
        """记下初值。"""
        自身.状态=初值#当前
        自身.监听者=set()#订阅者

    def getSnapshot(自身):#读
        """返回当前值。"""
        return 自身.状态#值

    def subscribe(自身,回调):#订阅
        """登记。"""
        自身.监听者.add(回调)#加入
        def 退订():#退订
            """取消。"""
            自身.监听者.discard(回调)#删除
        return 退订#退订器

    def set(自身,下一份):#替换
        """写入并通知。"""
        自身.状态=下一份#覆盖
        for 回调 in list(自身.监听者):#通知
            回调()#触发

def 触发档位(相位):
    """plain / claimed / frozen。"""
    if 相位=='plain':#明文
        return 'plain'#可编
    if 相位=='claimed':#已认领
        return 'claimed'#认领档
    return 'frozen'#裁决/提交中

def 空退订():
    """无管道时的退订器。"""
    return None#无事

def 同步兑现(结果,成功,失败=None):
    """翻译时已确定为同步值，直接走成功臂。"""
    try:#同步
        成功(结果)#当即
    except 对话错误 as 错误:#本包失败
        if 失败 is not None:#有失败臂
            失败(错误)#走失败

class 会话输入壳:#每会话输入外壳
    """作用域事件应用动词 + setDraft/submit + 发布的 InputState store。"""
    def __init__(自身,依赖):#注入依赖并发布初态
        """斜杠/弹层面都是 thunk。依赖为 dict。"""
        自身.依赖=依赖#依赖
        时钟=依赖['now'] if 'now' in 依赖 and 依赖['now'] is not None else time.time#真实 now；可注入
        自身.输入机=输入机({'now':时钟})#机
        自身.通知序号=0#通知序号
        自身.上次草稿=''#上次镜像
        自身.图片标识列表=[]#本草稿图 id
        自身.已拆除=False#拆除后丢迟到结算
        自身.镜像写出=None#草稿持久化
        自身.文件选择器=None#已挂载作曲器的文件选择面
        自身.notices=快照存储(None)#通知 store
        自身.state=快照存储(自身.合成())#初态
        自身.actions={#公开动作面
            'setDraft':自身.setDraft,#写草稿
            'addImages':自身.addImages,#加图
            'removeImage':自身.removeImage,#删图
            'pruneImages':自身.pruneImages,#修剪
            'submit':自身.以排队提交,#以 queue 提交
        }#动作结束
        队列=依赖['queue'] if 'queue' in 依赖 else None#队列读面
        if 队列 is not None:#有队列
            队列.subscribe(自身.发布)#队列变则重发
        自身.lexicon={#词表观察源
            'getSnapshot':自身.读词表,#读
            'subscribe':自身.订词表,#订
        }#词表结束

    def 以排队提交(自身):
        """公开 submit 默认 queue 模式。"""
        return 自身.submit('queue')#提交

    def 读词表(自身):
        """无管道则空。词表面为对象。"""
        触发=自身.取触发()#控制器
        if 触发 is None:#无
            return 空词表#空
        词=触发.lexicon#词表
        if 词 is None:#无
            return 空词表#空
        return 词.getSnapshot()#快照

    def 订词表(自身,回调):
        """无管道则空订阅。"""
        触发=自身.取触发()#控制器
        if 触发 is None:#无
            return 空退订#空退订
        词=触发.lexicon#词表
        if 词 is None:#无
            return 空退订#空退订
        return 词.subscribe(回调)#退订器

    def 取触发(自身):
        """thunk 惰性解析。"""
        解析=自身.依赖['inputTriggers'] if 'inputTriggers' in 自身.依赖 else None#thunk
        if 解析 is None:#无
            return None#无
        return 解析()#结果

    def 取弹层(自身):
        """thunk 惰性解析。"""
        解析=自身.依赖['popup'] if 'popup' in 自身.依赖 else None#thunk
        if 解析 is None:#无
            return None#无
        return 解析()#结果

    def setDraft(自身,文本,编辑范围=None):
        """唯一草稿写入路径。"""
        事件={'type':'draft-changed','draft':文本}#事件
        if 编辑范围 is not None:#有形态
            事件['editRange']=编辑范围#带上
        自身.执行(自身.输入机.dispatch(事件))#派发

    def addImages(自身,标识列表):
        """忙碌准入相位拒绝。"""
        if 自身.snapshot['phase'] in ('adjudicating','submitting'):#忙碌
            return False#拒绝
        if len(标识列表)==0:#空；判 length
            return True#成功
        自身.图片标识列表=list(自身.图片标识列表)+list(标识列表)#追加
        自身.发布()#发布
        return True#已追加

    def removeImage(自身,标识):
        """滤掉该 id。"""
        下一=[项 for 项 in 自身.图片标识列表 if 项!=标识]#滤
        if len(下一)==len(自身.图片标识列表):#无变化；判 length
            return#停
        自身.图片标识列表=下一#写回
        自身.发布()#发布

    def pruneImages(自身,可用):
        """只保留仍在册的。"""
        留=set(可用)#在册
        下一=[项 for 项 in 自身.图片标识列表 if 项 in 留]#滤
        if len(下一)==len(自身.图片标识列表):#无变化；判 length
            return#停
        自身.图片标识列表=下一#写回
        自身.发布()#发布

    def restoreImages(自身,标识列表):
        """缺的插到前面。"""
        当前=set(自身.图片标识列表)#已有
        缺=[项 for 项 in 标识列表 if 项 not in 当前]#缺的
        自身.图片标识列表=缺+list(自身.图片标识列表)#插前
        自身.发布()#发布

    def commitSend(自身,图片标识列表):
        """不记撤销；去掉已送图。"""
        已送=set(图片标识列表)#已送
        自身.图片标识列表=[项 for 项 in 自身.图片标识列表 if 项 not in 已送]#去掉
        自身.执行(自身.输入机.dispatch({'type':'send-committed'}))#机器提交

    def undo(自身):
        """派发撤销。"""
        自身.执行(自身.输入机.dispatch({'type':'undo'}))#撤销

    def redo(自身):
        """派发重做。"""
        自身.执行(自身.输入机.dispatch({'type':'redo'}))#重做

    def pasteBegin(自身,文本,选区,分量=None,代数=None):
        """一次事务贴选区。"""
        事件={'type':'paste-begin','text':文本,'selection':选区}#事件
        if 分量 is not None:#有分量
            事件['components']=分量#带上
        if 代数 is not None:#有代数
            事件['generation']=代数#带上
        自身.执行(自身.输入机.dispatch(事件))#派发

    def invalidatePaste(自身):
        """结束粘贴尝试。"""
        自身.执行(自身.输入机.dispatch({'type':'invalidate-paste'}))#作废

    def submit(自身,模式='queue'):
        """空草稿有图直送；否则 enter。"""
        快=自身.snapshot#快照
        if 快['draft'].strip()=='' and len(自身.图片标识列表)>0:#空草稿有图；判 length
            if 快['phase']=='plain':#明文
                自身.依赖['defaultSink']('',list(自身.图片标识列表),模式)#直送
            return#停
        自身.执行(自身.输入机.dispatch({'type':'enter','mode':模式}))#回车
        相位=自身.snapshot['phase']#回车后
        if 相位 in ('adjudicating','submitting'):#已锁定
            弹=自身.取弹层()#弹层
            if 弹 is not None:#可关
                弹.dismiss()#关
            触发=自身.取触发()#触发
            if 触发 is not None:#可跟踪
                下=自身.snapshot#替换后
                触发.track(下['draft'],0,{'tier':'frozen'},下['draftRev'])#冻结档

    def track(自身,草稿,光标):
        """守卫由相位导出。"""
        触发=自身.取触发()#触发
        if 触发 is not None:#可
            触发.track(草稿,光标,{'tier':触发档位(自身.snapshot['phase'])},自身.snapshot['draftRev'])#跟踪

    def arbitrate(自身,键,合成中):
        """无管道则 pass。"""
        触发=自身.取触发()#触发
        if 触发 is None:#无
            return 'pass'#放行
        return 触发.arbitrate(键,合成中)#裁决

    def steerQueue(自身):
        """有依赖才执行。"""
        转向=自身.依赖['steerQueue'] if 'steerQueue' in 自身.依赖 else None#thunk
        if 转向 is not None:#有
            转向()#执行

    def space(自身):
        """true = 已应用认领/插入。"""
        触发=自身.取触发()#触发
        if 触发 is None:#无
            return False#未消费
        已吃=触发.onSpace()#是否吃掉
        if 已吃 is True:#已应用
            下=自身.snapshot#替换后
            触发.track(下['draft'],len(下['draft']),{'tier':触发档位(下['phase'])},下['draftRev'])#再跟踪
        return 已吃#是否消费

    def dismissPopup(自身):
        """框外交互。"""
        弹=自身.取弹层()#弹层
        if 弹 is not None:#可
            弹.dismiss()#关

    def bindFilePicker(自身,选择器):
        """绑定已挂载作曲器的文件动作与存活接入可用性。选择器为对象，含 available/open。"""
        自身.文件选择器=选择器#记下
        def 解绑():
            """仍是自己才清。"""
            if 自身.文件选择器 is 选择器:#同
                自身.文件选择器=None#清
        return 解绑#拆除器

    def canPickFiles(自身):
        """已绑且当前接受文件。"""
        选择器=自身.文件选择器#面
        if 选择器 is None:#未绑
            return False#不接受
        return 选择器.available() is True#可用性

    def pickFiles(自身):
        """按存活接入策略打开原生文件对话框。"""
        选择器=自身.文件选择器#面
        if 选择器 is None:#未绑
            return#停
        if 选择器.available() is False:#不接受
            return#停
        选择器.open()#打开

    def beginCommand(自身,认领,跨度):
        """机器是否接受。"""
        前=自身.输入机.state['draftRev']#派发前
        自身.执行(自身.输入机.dispatch({'type':'begin-command','claim':认领,'span':跨度}))#派发
        后=自身.输入机.state#派发后
        return 后['phase']=='claimed' and 后['draftRev']!=前#已认领且修订前进

    def insertReference(自身,引用,跨度):
        """机器是否接受。"""
        前=自身.输入机.state['draftRev']#派发前
        自身.执行(自身.输入机.dispatch({'type':'insert-ref','reference':引用,'span':跨度}))#派发
        return 自身.输入机.state['draftRev']!=前#修订前进

    def consumeToken(自身,守卫):
        """跨度 CAS 再拼接；裸令牌清空。守卫为线协议 dict。"""
        快=自身.输入机.state#机态
        种=守卫['kind'] if 守卫 is not None and 'kind' in 守卫 else None#种
        if 种=='span':#跨度
            跨度=守卫['span'] if 'span' in 守卫 else None#跨度
            if 跨度 is None or 跨度['draftRev']!=快['draftRev']:#对不上
                return False#放弃
            草稿=快['draft']#草稿
            自身.setDraft(草稿[:跨度['start']]+草稿[跨度['end']:])#切掉
            return True#已拼
        令牌=守卫['token'] if 守卫 is not None and 'token' in 守卫 else ''#令牌
        if 快['draft'].strip()!=令牌:#对不上
            return False#放弃
        自身.setDraft('')#清空
        return True#已清

    def insertText(自身,文本,跨度):
        """CAS 再拼接；不铸造出现。跨度为 dict。"""
        快=自身.输入机.state#机态
        if 跨度['draftRev']!=快['draftRev']:#对不上
            return False#放弃
        草稿=快['draft']#草稿
        自身.setDraft(草稿[:跨度['start']]+文本+草稿[跨度['end']:])#替换
        return True#已拼

    def notify(自身,级别,正文):
        """浮出通知。"""
        自身.通知序号+=1#前进
        自身.notices.set({'level':级别,'text':正文,'seq':自身.通知序号})#写入

    def dispose(自身):
        """中止进行中尝试。"""
        自身.已拆除=True#后续丢弃
        自身.执行(自身.输入机.dispatch({'type':'release'}))#释放

    @property
    def snapshot(自身):
        """读现场。"""
        return 自身.state.getSnapshot()#store 快照

    def bindMirror(自身,写出):
        """绑定即采纳；返回解绑。"""
        自身.镜像写出=写出#记下
        def 解绑():#解绑
            """仍是自己才清。"""
            if 自身.镜像写出 is 写出:#仍是
                自身.镜像写出=None#清
        return 解绑#退订器

    def 执行(自身,效应列表):
        """逐条执行后叠队列发布。"""
        for 效应 in 效应列表:#逐条
            自身.执行效应(效应)#执行
        自身.发布()#发布

    def 执行效应(自身,效应):
        """notice / adjudicate / begin-submit / default-sink。效应为 dict。"""
        种=效应['type'] if 'type' in 效应 else None#标签
        if 种=='notice':#通知
            自身.通知序号+=1#前进
            自身.notices.set({'level':效应['level'],'text':效应['text'],'seq':自身.通知序号})#写
            return#停
        if 种=='adjudicate':#裁决
            自身.裁决(效应['attempt'],效应['draft'])#问控制器
            return#停
        if 种=='begin-submit':#开始提交
            自身.开始提交(效应['attempt'],效应['claim'],效应['args'])#claim.submit
            return#停
        if 种=='default-sink':#默认汇
            自身.序列化汇(效应['draft'],效应['mode'])#序列化后发送
            return#停

    def 序列化汇(自身,草稿,模式):
        """无芯片同步直送；有芯片经控制器序列化引用。"""
        图列表=list(自身.图片标识列表)#本批图
        出现表=自身.输入机.state['occurrences']#出现
        if len(出现表)==0:#无芯片；判 length
            自身.依赖['defaultSink'](草稿.strip(),图列表,模式)#直送
            return#停
        触发=自身.取触发()#控制器
        中止标志=threading.Event()#取消其余序列化
        def 序列化一项(项):
            """无控制器则抛。项为 dict。"""
            if 触发 is None:#无
                源=项['source'] if 'source' in 项 else None#源
                raise 对话错误('no serializer for reference source "'+str(源)+'"')#失败
            若已中止则抛出(中止标志)#已取消
            return {'offset':项['offset'],'text':触发.serializeReference(项['source'],项['ref'],中止标志)}#偏移与模型形
        try:#顺序执行（禁止 async）
            部件=[序列化一项(项) for 项 in 出现表]#全部
            if 自身.已拆除 is True:#已拆
                return#丢
            出=''#缓冲
            游标=0#游标
            for 部 in 部件:#按出现序
                出+=草稿[游标:部['offset']]+部['text']#拼
                游标=部['offset']+1#跳占位
            出+=草稿[游标:]#尾
            自身.依赖['defaultSink'](出.strip(),图列表,模式)#送汇
        except 对话错误 as 错误:#任一失败
            中止标志.set()#取消其余
            if 自身.已拆除 is True:#已拆
                return#丢
            自身.notify('error',str(错误))#浮出，草稿保留

    def 裁决(自身,尝试,草稿):
        """未挂管道：'/' 行当普通消息。尝试为 dict。"""
        触发=自身.取触发()#控制器
        if 触发 is None:#未挂
            自身.执行(自身.输入机.dispatch({'type':'adjudicated','attempt':尝试,'outcome':None}))#无挑选
            return#停
        def 成功(结局):
            """过期则丢。"""
            if 自身.已失效(尝试):#过期
                return#丢
            自身.执行(自身.输入机.dispatch({'type':'adjudicated','attempt':尝试,'outcome':结局}))#喂机
        def 失败(原因):
            """过期则丢。"""
            if 自身.已失效(尝试):#过期
                return#丢
            自身.执行(自身.输入机.dispatch({'type':'adjudication-failed','attempt':尝试,'message':str(原因)}))#失败
        同步兑现(触发.adjudicate(草稿.strip(),尝试['signal']),成功,失败)#问控制器；同步值

    def 开始提交(自身,尝试,认领,参数):
        """对会话作用域做 claim.submit。认领为 dict。"""
        def 成功(结局):
            """过期则丢。结局为 dict。"""
            if 自身.已失效(尝试):#过期
                return#丢
            好=结局['kind']=='success' if 结局 is not None and 'kind' in 结局 else False#成功否
            自身.执行(自身.输入机.dispatch({'type':'submit-settled','attempt':尝试,'ok':好,'outcome':结局}))#结算
        def 失败(原因):
            """过期则丢。"""
            if 自身.已失效(尝试):#过期
                return#丢
            自身.执行(自身.输入机.dispatch({'type':'submit-settled','attempt':尝试,'ok':False,'message':str(原因)}))#失败结算
        提交=认领['submit'] if 认领 is not None and 'submit' in 认领 else None#submit
        if 提交 is None:#无
            失败(对话错误('claim.submit unavailable'))#失败
            return#停
        同步兑现(提交(参数,自身.依赖['actx']),成功,失败)#在会话作用域提交；同步值

    def 已失效(自身,尝试):
        """拆除或已中止。尝试为 dict。"""
        信号=尝试['signal'] if 尝试 is not None and 'signal' in 尝试 else None#信号
        中止=已中止(信号) if 信号 is not None else False#中止
        return 自身.已拆除 is True or 中止 is True#失效

    def 合成(自身):
        """机器状态叠图片与队列。"""
        机态=自身.输入机.state#机态
        队列面=自身.依赖['queue'] if 'queue' in 自身.依赖 else None#队列
        队列=队列面.getSnapshot() if 队列面 is not None else list(空队列)#队列
        return {**机态,'imageIds':list(自身.图片标识列表),'queue':list(队列)}#叠好

    def 发布(自身):
        """草稿变了才镜像。"""
        下一=自身.合成()#叠好
        自身.state.set(下一)#写入
        if 下一['draft']!=自身.上次草稿:#草稿变
            自身.上次草稿=下一['draft']#记下
            if 自身.镜像写出 is not None:#有绑定
                自身.镜像写出(下一['draft'])#写出
