import threading#序列化取消与附件飞行
from ..服务 import 对话错误#本包异常
from .输入机 import 输入机,已中止,若已中止则抛出,中止控制器#提交平面
from .运行时 import 草稿编辑器运行时#作曲器编辑器

__all__=['快照存储','会话输入壳','触发档位']#仅中文公开名

空队列=()#缺席队列
空词表={}#无管道词表

class 快照存储:#简易 SnapshotStore
    """值 + 订阅；对齐 createSnapshotStore。"""
    def __init__(自身,初值):
        """记下初值。"""
        自身.状态=初值#当前
        自身.监听者=set()#订阅者

    def getSnapshot(自身):
        """返回当前值。"""
        return 自身.状态#值

    def subscribe(自身,回调):
        """登记。"""
        自身.监听者.add(回调)#加入
        def 退订():
            """取消。"""
            自身.监听者.discard(回调)#删除
        return 退订#退订器

    def set(自身,下一份):
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

def 投影内容已变(先前,下一):
    """内容是否变；选区与光标不计。"""
    if 先前['clipboardText']!=下一['clipboardText'] or 先前['detectText']!=下一['detectText']:#文本
        return True#变
    if len(先前['occurrences'])!=len(下一['occurrences']):#条数
        return True#变
    下标=0#游标
    while 下标<len(下一['occurrences']):#各出现
        旧=先前['occurrences'][下标]#旧
        新=下一['occurrences'][下标]#新
        旧无效=旧['invalid'] if 'invalid' in 旧 else None#旧旗
        新无效=新['invalid'] if 'invalid' in 新 else None#新旗
        if 旧['occurrenceId']!=新['occurrenceId'] or 旧无效!=新无效:#身份或旗
            return True#变
        下标+=1#前进
    return False#未变

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
    """作用域事件应用动词 + setDraft/submit + 发布的 InputState store。拥有作曲器编辑器。"""
    def __init__(自身,依赖):
        """斜杠/弹层面都是 thunk。依赖为 dict。"""
        自身.依赖=依赖#依赖
        自身.输入机=输入机()#提交平面
        自身.草稿编辑器=草稿编辑器运行时({#编辑器
            'onUpdate':自身.编辑器已更新,#更新
            'openReference':自身.打开引用,#打开引用
            'activeClaimToken':自身.活认领令牌,#认领令牌
            'lexicon':自身.读词表,#词表
            'resolveLexicon':自身.解析词表源,#词表源
        })#运行时结束
        自身.卸编辑器=自身.草稿编辑器.登记()#安装行为
        自身.修订=0#内容修订
        自身.通知序号=0#通知序号
        自身.上次草稿=''#上次镜像
        自身.附件标识列表=[]#本草稿附件
        自身.已拆除=False#拆除后丢迟到结算
        自身.镜像写出=None#草稿持久化
        自身.文件选择器=None#已挂载作曲器的文件选择面
        自身.脱离草稿={}#seq → 脱离快照
        自身.失败脱离={}#seq → 失败快照
        自身.失败恢复修订=None#上次自动恢复修订
        自身.正在恢复失败=False#恢复中
        自身.附件飞行序号=0#附件直送序号
        自身.附件飞行={}#序号 → 控制器与附件
        自身.notices=快照存储(None)#通知 store
        自身.state=快照存储(自身.合成())#初态
        自身.actions={#公开动作面
            'setDraft':自身.setDraft,#写草稿
            'addAttachments':自身.addAttachments,#加附件
            'removeAttachment':自身.removeAttachment,#删附件
            'pruneAttachments':自身.pruneAttachments,#修剪
            'submit':自身.以排队提交,#以 queue 提交
        }#动作结束
        自身.lexicon={#词表观察源
            'getSnapshot':自身.读词表,#读
            'subscribe':自身.订词表,#订
        }#词表结束
        自身.退订收件箱=None#收件箱退订
        收件箱=依赖['inbox'] if 'inbox' in 依赖 else None#收件箱投影
        if 收件箱 is not None:#有收件箱
            自身.退订收件箱=收件箱.subscribe(自身.发布)#收件箱变则重发

    @property
    def 编辑器(自身):
        """壳持有的编辑器。"""
        return 自身.草稿编辑器.编辑器#编辑器

    @property
    def 投影(自身):
        """已提交投影。"""
        return 自身.草稿编辑器.投影#投影

    def 以排队提交(自身):
        """公开 submit 默认 queue 模式。"""
        return 自身.submit('queue')#提交

    def 打开引用(自身,来源,引用):
        """经控制器打开预览。"""
        触发=自身.取触发()#控制器
        if 触发 is None:#无
            return False#未开
        return 触发.openReference(来源,引用) is True#打开

    def 解析词表源(自身):
        """控制器词表 store。"""
        触发=自身.取触发()#控制器
        if 触发 is None:#无
            return None#无
        return 触发.lexicon#词表

    def 读词表(自身):
        """无管道则空。"""
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

    def 编辑器已更新(自身):
        """重投影、认领监视、发布、跟踪。"""
        先前=自身.草稿编辑器.刷新投影()#旧
        if 投影内容已变(先前,自身.投影) is True:#内容变
            自身.修订+=1#前进
            if 自身.正在恢复失败 is False and 自身.失败恢复修订 is not None:#用户改了
                自身.失败脱离.clear()#丢掉失败快照
                自身.失败恢复修订=None#清
            自身.执行派发({'type':'draft-changed','draft':自身.投影['clipboardText']})#草稿已变
        光标=自身.投影['caret']#光标
        if 光标 is not None:#有
            触发=自身.取触发()#控制器
            if 触发 is not None:#可跟踪
                触发.track(自身.投影['detectText'],光标,{'tier':触发档位(自身.输入机.state['phase'])},自身.修订)#跟踪

    def setDraft(自身,文本):
        """整份草稿替换。"""
        自身.草稿编辑器.设草稿(文本)#写入

    def addAttachments(自身,标识列表):
        """忙碌准入相位拒绝。"""
        if 自身.snapshot['phase'] in ('adjudicating','submitting'):#忙碌
            return False#拒绝
        if len(标识列表)==0:#空
            return True#成功
        自身.附件标识列表=list(自身.附件标识列表)+list(标识列表)#追加
        自身.发布()#发布
        return True#已追加

    def removeAttachment(自身,标识):
        """忙碌相位拒绝，避免飞行中从栏上消失仍随发送走。"""
        if 自身.snapshot['phase'] in ('adjudicating','submitting'):#忙碌
            return False#拒绝
        下一=[项 for 项 in 自身.附件标识列表 if 项!=标识]#滤
        if len(下一)==len(自身.附件标识列表):#无变化
            return False#未摘
        自身.附件标识列表=下一#写回
        自身.发布()#发布
        return True#已摘

    def pruneAttachments(自身,可用):
        """只保留仍在册的。"""
        留=set(可用)#在册
        下一=[项 for 项 in 自身.附件标识列表 if 项 in 留]#滤
        if len(下一)==len(自身.附件标识列表):#无变化
            return#停
        自身.附件标识列表=下一#写回
        自身.发布()#发布

    def commitSend(自身,附件标识列表):
        """成功发送提交：清编辑器且切掉撤销。"""
        已送=set(附件标识列表)#已送
        自身.附件标识列表=[项 for 项 in 自身.附件标识列表 if 项 not in 已送]#去掉
        自身.执行派发({'type':'send-committed'})#机器提交

    def paste(自身,文本):
        """在当前选区插入已剥占位的纯文本。"""
        自身.草稿编辑器.粘贴(文本)#粘贴

    def submit(自身,模式='queue'):
        """空草稿有附件直送；已认领且不接受附件则通知；否则 enter。"""
        快=自身.snapshot#快照
        if 快['draft'].strip()=='' and len(自身.附件标识列表)>0:#空草稿有附件
            if 快['phase']=='plain':#明文
                附件列表=list(自身.附件标识列表)#本批
                控制器=中止控制器()#取消
                自身.附件飞行序号+=1#前进
                飞行=自身.附件飞行序号#序号
                自身.附件飞行[飞行]={'controller':控制器,'attachmentIds':附件列表}#记下
                自身.commitSend(附件列表)#先清
                def 直送():
                    """附件直送结算。"""
                    try:#发送
                        结局=自身.依赖['defaultSink']('',附件列表,模式,控制器.signal).等待()#汇
                        if 自身.已拆除 is True or 飞行 not in 自身.附件飞行:#过期
                            return#丢
                        del 自身.附件飞行[飞行]#摘
                        if 结局['kind']=='success':#成功
                            return#停
                        自身.恢复附件(附件列表)#恢复
                        if 'text' in 结局 and 结局['text'] is not None:#有文案
                            自身.notify('error',结局['text'])#通知
                    except 对话错误 as 错误:#失败
                        if 自身.已拆除 is True or 飞行 not in 自身.附件飞行:#过期
                            return#丢
                        del 自身.附件飞行[飞行]#摘
                        自身.恢复附件(附件列表)#恢复
                        自身.notify('error',str(错误))#通知
                threading.Thread(target=直送,daemon=True).start()#后台
            return#停
        前=自身.snapshot#提交前
        认领=前['claim'] if 'claim' in 前 else None#认领
        接受附件=认领 is not None and 'attachments' in 认领 and 认领['attachments'] is True#接受
        if 前['phase']=='claimed' and len(自身.附件标识列表)>0 and 接受附件 is False:#命令不收附件
            令牌=认领['token'] if 认领 is not None and 'token' in 认领 else 前['draft']#令牌
            自身.notify('error',自身.依赖['commandAttachments']['unsupportedNotice'](令牌))#通知
            return#停
        自身.执行派发({'type':'enter','mode':模式,'draft':自身.投影['clipboardText']})#回车
        相位=自身.snapshot['phase']#回车后
        if 相位 in ('adjudicating','submitting'):#已锁定
            弹=自身.取弹层()#弹层
            if 弹 is not None:#可关
                弹.dismiss()#关
            触发=自身.取触发()#触发
            if 触发 is not None:#可跟踪
                触发.track(自身.投影['detectText'],0,{'tier':'frozen'},自身.修订)#冻结档

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
        """true = 已应用认领/插入。跟踪由更新监听自己做。"""
        触发=自身.取触发()#触发
        if 触发 is None:#无
            return False#未消费
        return 触发.onSpace()#是否吃掉

    def dismissPopup(自身):
        """框外交互。"""
        弹=自身.取弹层()#弹层
        if 弹 is not None:#可
            弹.dismiss()#关

    def caretSpan(自身):
        """探测坐标上的活选区。"""
        return 自身.草稿编辑器.光标跨度()#跨度

    def bindFilePicker(自身,选择器):
        """绑定已挂载作曲器的文件动作与存活接入可用性。"""
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
            return False#未开
        if 选择器.available() is False:#不接受
            return False#未开
        选择器.open()#打开
        return True#已开

    def beginCommand(自身,认领,跨度):
        """编辑器替换 [0, span.end) 为令牌，再进入 claimed。"""
        相位=自身.输入机.state['phase']#相位
        if 相位!='plain' and 相位!='claimed':#忙碌
            return False#拒绝
        if 跨度['draftRev']!=自身.修订:#CAS
            return False#放弃
        if 自身.投影['detectText'][:跨度['start']].strip()!='':#前导非空白
            return False#放弃
        if 自身.草稿编辑器.替换文本({'start':0,'end':跨度['end']},认领['token']) is False:#未映射
            return False#放弃
        自身.执行派发({'type':'claim','claim':认领})#认领
        return True#已应用

    def insertReference(自身,引用,跨度):
        """跨度换成芯片，必要时补空格。"""
        相位=自身.输入机.state['phase']#相位
        if 相位!='plain' and 相位!='claimed':#忙碌
            return False#拒绝
        if 跨度['draftRev']!=自身.修订:#CAS
            return False#放弃
        尾=自身.投影['detectText'][跨度['end']:跨度['end']+1]#尾字符
        return 自身.草稿编辑器.插入引用(跨度,引用,尾)#插入

    def consumeToken(自身,守卫):
        """跨度 CAS 再切掉；裸令牌清空。"""
        种=守卫['kind'] if 守卫 is not None and 'kind' in 守卫 else None#种
        if 种=='span':#跨度
            跨度=守卫['span'] if 'span' in 守卫 else None#跨度
            if 跨度 is None or 跨度['draftRev']!=自身.修订 or 跨度['start']==跨度['end']:#对不上
                return False#放弃
            return 自身.草稿编辑器.替换文本(跨度,'')#切掉
        令牌=守卫['token'] if 守卫 is not None and 'token' in 守卫 else ''#令牌
        if 令牌=='' or 自身.投影['clipboardText'].strip()!=令牌:#对不上
            return False#放弃
        自身.setDraft('')#清空
        return True#已清

    def insertText(自身,文本,跨度,继续=False):
        """纯文本引用路径；完成菜单由更新监听自动重开。"""
        if 跨度['draftRev']!=自身.修订:#CAS
            return False#放弃
        return 自身.草稿编辑器.替换文本(跨度,文本)#替换

    def notify(自身,级别,正文):
        """浮出通知。"""
        自身.通知序号+=1#前进
        自身.notices.set({'level':级别,'text':正文,'seq':自身.通知序号})#写入

    def focus(自身):
        """把键盘连同上次插入符还回编写器。"""
        根=自身.编辑器.取根元素()#根
        if 根 is not None:#有根
            根.focus({'preventScroll':True})#DOM 焦点
        自身.编辑器.focus()#Lexical 恢复选区

    def dispose(自身):
        """拆除并返回仍占用的附件 id。"""
        if 自身.已拆除 is True:#已拆
            return []#空
        留=set(自身.附件标识列表)#草稿栏
        for 记录 in 自身.脱离草稿.values():#脱离
            for 标识 in 记录['attachmentIds']:#附件
                留.add(标识)#收下
        for 飞行 in 自身.附件飞行.values():#直送
            for 标识 in 飞行['attachmentIds']:#附件
                留.add(标识)#收下
            飞行['controller'].abort()#中止
        自身.已拆除=True#后续丢弃
        自身.执行派发({'type':'release'})#释放
        if 自身.退订收件箱 is not None:#有订阅
            自身.退订收件箱()#退订
        自身.卸编辑器()#卸编辑器
        自身.脱离草稿.clear()#清
        自身.失败脱离.clear()#清
        自身.附件飞行.clear()#清
        return list(留)#附件

    @property
    def snapshot(自身):
        """读现场。"""
        return 自身.state.getSnapshot()#store 快照

    def bindMirror(自身,写出):
        """绑定即采纳；返回解绑。"""
        自身.镜像写出=写出#记下
        def 解绑():
            """仍是自己才清。"""
            if 自身.镜像写出 is 写出:#仍是
                自身.镜像写出=None#清
        return 解绑#退订器

    def 活认领令牌(自身):
        """装饰用的认领令牌；未认领则 None。"""
        机=自身.输入机.state#机态
        if (机['phase']=='claimed' or 机['phase']=='submitting') and 'claim' in 机:#有令牌
            return 机['claim']['token']#令牌
        return None#无

    def 执行派发(自身,事件):
        """派发并在令牌翻转时刷新装饰。"""
        前=自身.活认领令牌()#前
        自身.执行(自身.输入机.dispatch(事件))#执行
        if 自身.活认领令牌()!=前:#翻转
            自身.草稿编辑器.刷新认领装饰()#刷新

    def 执行(自身,效应列表):
        """逐条执行后发布。"""
        for 效应 in 效应列表:#逐条
            自身.执行效应(效应)#执行
        自身.发布()#发布

    def 执行效应(自身,效应):
        """notice / adjudicate / begin-submit / default-sink / commit-draft。"""
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
            自身.序列化汇(效应['attempt'],效应['draft'],效应['mode'])#序列化后发送
            return#停
        if 种=='commit-draft':#清已提交草稿
            自身.提交草稿(效应['retainSuffixOf'])#清
            return#停

    def 提交草稿(自身,保留后缀于):
        """清已提交内容，切掉撤销。"""
        def 前缀长度(剪贴):
            """可留纯飞行中键入的后缀。"""
            if 保留后缀于 is not None and 剪贴!=保留后缀于 and 剪贴.startswith(保留后缀于):#后缀
                return len(保留后缀于)#前缀长
            return None#整根
        自身.草稿编辑器.清除已提交草稿(前缀长度)#清
        自身.草稿编辑器.清空历史()#切栈

    def 序列化汇(自身,尝试,草稿,模式):
        """芯片展开为模型形后再送汇。"""
        附件列表=list(自身.附件标识列表)#本批
        自身.附件标识列表=[]#先摘
        出现表=自身.投影['occurrences']#出现
        记录={'draft':草稿,'occurrences':出现表,'attachmentIds':附件列表}#快照
        自身.脱离草稿[尝试['seq']]=记录#记下
        if 自身.失败恢复修订==自身.修订:#新发送覆盖自动恢复
            自身.失败脱离.clear()#清
            自身.失败恢复修订=None#清
        if len(出现表)==0:#无芯片
            自身.结算汇(尝试,自身.依赖['defaultSink'](草稿.strip(),附件列表,模式,尝试['signal']))#直送任务
            return#停
        触发=自身.取触发()#控制器
        def 序列化():
            """按出现序展开。"""
            部件=[]#部件
            try:#顺序
                for 项 in 出现表:#各出现
                    if 触发 is None:#无
                        源=项['source'] if 'source' in 项 else None#源
                        raise 对话错误('no serializer for reference source "'+str(源)+'"')#失败
                    若已中止则抛出(尝试['signal'])#已取消
                    文本=触发.serializeReference(项['source'],项['ref'],尝试['signal'])#模型形
                    部件.append({'offset':项['offset'],'length':项['length'],'text':文本})#收下
                if 自身.已拆除 is True:#已拆
                    return#丢
                出=''#缓冲
                游标=0#游标
                for 部 in 部件:#按出现序
                    出+=草稿[游标:部['offset']]+部['text']#拼
                    游标=部['offset']+部['length']#跳剪贴板长
                出+=草稿[游标:]#尾
                自身.结算汇(尝试,自身.依赖['defaultSink'](出.strip(),附件列表,模式,尝试['signal']))#送汇任务
            except 对话错误 as 错误:#失败
                if 自身.已失效(尝试):#过期
                    return#丢
                自身.结算脱离失败(尝试,str(错误))#失败
        threading.Thread(target=序列化,daemon=True).start()#后台

    def 结算汇(自身,尝试,待决):
        """独立结算一次脱离发送。"""
        def 工作():
            """等汇并结算。"""
            try:#发送
                结局=待决.等待()#等汇
                if 自身.已失效(尝试):#过期
                    return#丢
                if 结局['kind']!='success':#失败
                    文=结局['text'] if 'text' in 结局 else None#文案
                    自身.结算脱离失败(尝试,文)#失败
                    return#停
                if 尝试['seq'] in 自身.脱离草稿:#有记录
                    del 自身.脱离草稿[尝试['seq']]#摘
                自身.执行派发({'type':'sink-settled','attempt':尝试,'ok':True,'outcome':结局})#成功
            except 对话错误 as 错误:#失败
                if 自身.已失效(尝试):#过期
                    return#丢
                自身.结算脱离失败(尝试,str(错误))#失败
        threading.Thread(target=工作,daemon=True).start()#后台

    def 结算脱离失败(自身,尝试,消息=None):
        """恢复一份失败脱离发送，不覆盖恢复后键入的正文。"""
        if 尝试['seq'] not in 自身.脱离草稿:#无记录
            return#停
        记录=自身.脱离草稿[尝试['seq']]#快照
        del 自身.脱离草稿[尝试['seq']]#摘
        自身.恢复附件(记录['attachmentIds'])#恢复附件
        自身.失败脱离[尝试['seq']]=记录#待恢复
        if 自身.投影['clipboardText']=='' or 自身.失败恢复修订==自身.修订:#可自动恢复
            自身.恢复失败草稿()#重建
        事件={'type':'sink-settled','attempt':尝试,'ok':False}#结算
        if 消息 is not None:#有文案
            事件['message']=消息#带上
        自身.执行派发(事件)#派发

    def 恢复失败草稿(自身):
        """按提交序重建当前失败快照。"""
        序表=sorted(自身.失败脱离.keys())#提交序
        if len(序表)==0:#无
            return#停
        分隔='\n\n'#分隔
        草稿=''#拼
        出现表=[]#出现
        for 序号 in 序表:#各份
            记录=自身.失败脱离[序号]#快照
            基=len(草稿)+(0 if 草稿=='' else len(分隔))#基
            if 草稿!='':#已有
                草稿+=分隔#隔开
            草稿+=记录['draft']#叠
            for 项 in 记录['occurrences']:#出现
                拷=dict(项)#拷
                拷['offset']=基+项['offset']#平移
                出现表.append(拷)#收下
        自身.正在恢复失败=True#恢复中
        try:#重建
            自身.草稿编辑器.恢复草稿(草稿,出现表)#写入
            自身.草稿编辑器.清空历史()#切栈
            自身.失败恢复修订=自身.修订#记下
        finally:#无论成败
            自身.正在恢复失败=False#结束

    def 恢复附件(自身,附件标识列表):
        """失败附件插回栏头；成功后才释放。"""
        if len(附件标识列表)==0:#空
            return#停
        当前=set(自身.附件标识列表)#已有
        缺=[项 for 项 in 附件标识列表 if 项 not in 当前]#缺的
        if len(缺)==0:#无
            return#停
        自身.附件标识列表=缺+list(自身.附件标识列表)#插前
        自身.发布()#发布

    def 裁决(自身,尝试,草稿):
        """未挂管道：'/' 行当普通消息。"""
        触发=自身.取触发()#控制器
        if 触发 is None:#未挂
            自身.执行派发({'type':'adjudicated','attempt':尝试,'outcome':None})#无挑选
            return#停
        def 成功(结局):
            """过期则丢。"""
            if 自身.已失效(尝试):#过期
                return#丢
            自身.执行派发({'type':'adjudicated','attempt':尝试,'outcome':结局})#喂机
        def 失败(原因):
            """过期则丢。"""
            if 自身.已失效(尝试):#过期
                return#丢
            自身.执行派发({'type':'adjudication-failed','attempt':尝试,'message':str(原因)})#失败
        附件数={'attachments':len(自身.附件标识列表)}#附件计数
        同步兑现(触发.adjudicate(草稿.strip(),尝试['signal'],附件数),成功,失败)#问控制器

    def 开始提交(自身,尝试,认领,参数):
        """对会话作用域做 claim.submit；接受附件的认领才带上序列化附件。"""
        附件列表=list(自身.附件标识列表) if 'attachments' in 认领 and 认领['attachments'] is True else []#本批
        def 工作():
            """序列化后提交。"""
            try:#提交
                附件载荷=[]#载荷
                if len(附件列表)>0:#有附件
                    附件载荷=自身.依赖['commandAttachments']['serialize'](附件列表).等待()#序列化
                if 自身.已失效(尝试):#过期
                    return#丢
                提交=认领['submit'] if 认领 is not None and 'submit' in 认领 else None#submit
                if 提交 is None:#无
                    raise 对话错误('claim.submit unavailable')#失败
                结局=提交(参数,自身.依赖['actx'],附件载荷).等待()#提交
                if 结局 is None or 自身.已失效(尝试):#过期
                    return#丢
                if 结局['kind']=='success' and len(附件列表)>0:#成功释放
                    已送=set(附件列表)#已送
                    自身.附件标识列表=[项 for 项 in 自身.附件标识列表 if 项 not in 已送]#去掉
                    自身.依赖['commandAttachments']['release'](附件列表)#释放
                事件={'type':'submit-settled','attempt':尝试,'ok':结局['kind']=='success','draft':自身.投影['clipboardText'],'outcome':结局}#结算
                if 结局['kind']=='error' and ('text' not in 结局 or 结局['text'] is None):#无文案
                    事件['message']='command failed'#缺省
                自身.执行派发(事件)#派发
            except 对话错误 as 错误:#失败
                if 自身.已失效(尝试):#过期
                    return#丢
                自身.执行派发({'type':'submit-settled','attempt':尝试,'ok':False,'draft':自身.投影['clipboardText'],'message':str(错误)})#失败
        threading.Thread(target=工作,daemon=True).start()#后台

    def 已失效(自身,尝试):
        """拆除或已中止。"""
        信号=尝试['signal'] if 尝试 is not None and 'signal' in 尝试 else None#信号
        中止=已中止(信号) if 信号 is not None else False#中止
        return 自身.已拆除 is True or 中止 is True#失效

    def 合成(自身):
        """编辑器投影叠提交平面与收件箱排队。"""
        机态=自身.输入机.state#机态
        收件箱面=自身.依赖['inbox'] if 'inbox' in 自身.依赖 else None#收件箱
        收件箱=收件箱面.getSnapshot() if 收件箱面 is not None else None#快照
        排队=收件箱['next-turn'] if 收件箱 is not None and 'next-turn' in 收件箱 else list(空队列)#排队
        快照={'draft':自身.投影['clipboardText'],'attachmentIds':list(自身.附件标识列表),'draftRev':自身.修订,'phase':机态['phase'],'occurrences':list(自身.投影['occurrences']),'queue':list(排队)}#叠好
        if 'claim' in 机态:#有认领
            快照['claim']=机态['claim']#带上
        return 快照#快照

    def 发布(自身):
        """草稿变了才镜像。"""
        下一=自身.合成()#叠好
        自身.state.set(下一)#写入
        if 下一['draft']!=自身.上次草稿:#草稿变
            自身.上次草稿=下一['draft']#记下
            if 自身.镜像写出 is not None:#有绑定
                自身.镜像写出(下一['draft'])#写出
