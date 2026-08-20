"""输入机：纯的每会话输入状态机。

对齐上游 `ui-conversation/src/client/input/machine.ts`。公开面仅中文名。
事件进、效应出；零 DOM / 环境时钟。包私有——会话输入壳是唯一调用方。
草稿真相：每个芯片持有一个 U+FFFC；出现表携带身份与投影。
"""
import re#裸令牌后分隔判定
from .约定 import 占位符#U+FFFC 占位

__all__=['占位符','投影剪贴板','输入机']#仅中文公开名

空队列=()#本层队列恒空
日志上限=100#撤销环深度

def 不可达(值):#漏分支则抛
    """封闭输入事件的穷尽性兜底。"""
    raise Exception('unreachable input event: '+repr(值))#不可能到达

def 令牌后参数(草稿,令牌):#从草稿剥掉认领令牌得到提交参数
    """容忍前导空白；裸令牌缺尾部分隔则空参数；恰吃一个分隔字符。"""
    文本=草稿.lstrip()#去掉前导空白
    if 文本.startswith(令牌):#完整令牌命中
        return 文本[len(令牌):]#切掉令牌
    基=令牌.rstrip()#去掉令牌尾部分隔
    if 文本.startswith(基):#裸令牌前缀命中
        余=文本[len(基):]#令牌后的余下
        return 余[1:] if 余 and re.match(r'\s',余[0]) else 余#有分隔则再吃一个空白
    return ''#对不上则空参数

def 差分编辑(旧草稿,新草稿):#两份草稿之间的编辑范围
    """前缀/后缀公共扫描，恢复编辑范围。"""
    前=0#前缀公共长度
    公共=min(len(旧草稿),len(新草稿))#最多可比较
    while 前<公共 and 旧草稿[前]==新草稿[前]:#扫前缀
        前+=1#前进
    后=0#后缀公共长度
    可后=公共-前#去掉前缀后剩余
    while 后<可后 and 旧草稿[len(旧草稿)-1-后]==新草稿[len(新草稿)-1-后]:#扫后缀
        后+=1#前进
    return {'start':前,'end':len(旧草稿)-后,'insertedLength':len(新草稿)-后-前}#范围

def 投影剪贴板(状态):#草稿的纯文本投影
    """把占位符展开成各出现的剪贴板文本；U+FFFC 永不离开机。"""
    草稿=状态.get('draft','') if isinstance(状态,dict) else getattr(状态,'draft','')#草稿
    出现表=状态.get('occurrences') if isinstance(状态,dict) else getattr(状态,'occurrences',None)#出现
    出现表=出现表 or []#缺省空
    if len(出现表)==0:#无芯片
        return 草稿#原文即投影
    出=''#组装
    游标=0#已消费偏移
    for 项 in 出现表:#按 offset 序
        偏移=项.get('offset') if isinstance(项,dict) else getattr(项,'offset',0)#偏移
        剪贴=项.get('clipboardText') if isinstance(项,dict) else getattr(项,'clipboardText','')#投影
        出+=草稿[游标:偏移]+剪贴#中间原文+投影
        游标=偏移+1#跳过 U+FFFC
    return 出+草稿[游标:]#尾部

class 中止信号:#取消信号
    """对齐 AbortSignal.aborted。"""
    def __init__(自身):#初值未中止
        """未中止。"""
        自身.aborted=False#否

class 中止控制器:#取消控制器
    """对齐 AbortController；机在进入时铸造。"""
    def __init__(自身):#造信号
        """绑定信号。"""
        自身.signal=中止信号()#信号

    def abort(自身):#中止
        """标 aborted。"""
        自身.signal.aborted=True#是

class 输入机:#纯输入机，每会话一份
    """事件进、效应出；零副作用。"""
    def __init__(自身,选项=None):#可注入合并窗口与时钟
        """默认常量时钟，连续打字总会合并。"""
        选项=选项 or {}#缺省
        自身.草稿=''#当前草稿
        自身.草稿修订=0#草稿修订号
        自身.相位='plain'#当前相位
        自身.认领=None#活认领
        自身.出现表=[]#出现表
        自身.出现序号=0#出现身份计数
        自身.序号=0#提交尝试序号
        自身.飞行=None#飞行中提交槽
        自身.日志=[]#撤销日志
        自身.重做栈=[]#重做栈
        自身.打字游程=None#打开的打字游程
        自身.粘贴=None#活着的粘贴匹配尝试
        自身.粘贴序号=0#粘贴尝试序号
        自身.合并窗口毫秒=选项.get('mergeWindowMs',1000)#默认 1000ms
        自身.现在=选项.get('now') or (lambda:0)#默认常量时钟

    @property
    def state(自身):#只读快照（本层队列恒空）
        """已发布输入状态。"""
        态={#快照
            'draft':自身.草稿,#草稿
            'imageIds':[],#本层不持图
            'draftRev':自身.草稿修订,#修订
            'phase':自身.相位,#相位
            'occurrences':list(自身.出现表),#出现表拷贝
            'queue':list(空队列),#本层队列恒空
        }#结束
        if 自身.认领 is not None:#有认领
            令牌=自身.认领['token'] if isinstance(自身.认领,dict) else getattr(自身.认领,'token')#令牌
            认={'token':令牌}#快照
            提示=自身.认领.get('hint') if isinstance(自身.认领,dict) else getattr(自身.认领,'hint',None)#hint
            if 提示 is not None:#有 hint
                认['hint']=提示#带上
            态['claim']=认#写入
        if 自身.粘贴 is not None:#有粘贴尝试
            态['paste']=dict(自身.粘贴)#带上
        return 态#快照

    def dispatch(自身,事件):#唯一写路径
        """按事件判别标签分发；空操作/锁定/过期返回空效应表。"""
        种=事件.get('type') if isinstance(事件,dict) else getattr(事件,'type',None)#标签
        if 种=='draft-changed':#草稿已变
            return 自身.草稿已变(事件.get('draft'),事件.get('editRange'))#派发
        if 种=='begin-command':#开始认领
            return 自身.开始命令(事件.get('claim'),事件.get('span'))#派发
        if 种=='insert-ref':#插入引用
            return 自身.插入引用(事件.get('reference'),事件.get('span'))#派发
        if 种=='consume-token':#消费令牌
            return 自身.消费令牌(事件.get('guard'))#派发
        if 种=='set-invalid':#标无效
            return 自身.标无效(事件.get('invalidIds') or [])#派发
        if 种=='undo':#撤销
            return 自身.撤销()#派发
        if 种=='redo':#重做
            return 自身.重做()#派发
        if 种=='paste-begin':#开始粘贴
            return 自身.粘贴开始(事件.get('text'),事件.get('selection'),事件.get('components') or [],事件.get('generation',0))#派发
        if 种=='paste-upgrade':#升级粘贴
            return 自身.粘贴升级(事件.get('attemptId'),事件.get('span'),事件.get('reference'))#派发
        if 种=='invalidate-paste':#作废粘贴
            自身.粘贴=None#清
            return []#无效应
        if 种=='enter':#进入提交
            return 自身.进入(事件.get('mode'))#派发
        if 种=='adjudicated':#裁决完成
            return 自身.裁决完成(事件.get('attempt'),事件.get('outcome'))#派发
        if 种=='adjudication-failed':#裁决失败
            return 自身.裁决失败(事件.get('attempt'),事件.get('message'))#派发
        if 种=='submit-settled':#提交已结算
            return 自身.提交结算(事件)#派发
        if 种=='send-committed':#发送已提交
            return 自身.发送已提交()#派发
        if 种=='release':#释放
            return 自身.释放()#派发
        return 不可达(事件)#穷尽兜底

    def 采纳(自身,草稿):#采纳新草稿
        """前进修订号。"""
        自身.草稿=草稿#写入
        自身.草稿修订+=1#前进

    def 推事务(自身,选区前=None):#推入撤销单元
        """事前快照；修剪环；切断重做链。"""
        单元={'draftBefore':自身.草稿,'occurrencesBefore':list(自身.出现表)}#事前
        if 选区前 is not None:#有选区
            单元['selectionBefore']=选区前#带上
        自身.日志.append(单元)#推入
        if len(自身.日志)>日志上限:#超深
            自身.日志.pop(0)#丢掉最旧
        自身.重做栈=[]#切断重做

    def 对账(自身,范围):#按一次编辑对账出现表
        """范围后平移；落在被替换范围内的消失。"""
        差=范围['insertedLength']-(范围['end']-范围['start'])#长度差
        保留=[]#保留
        for 项 in 自身.出现表:#逐条
            偏移=项['offset']#偏移
            if 偏移<范围['start']:#范围前
                保留.append(项)#不动
            elif 偏移>=范围['end']:#范围后
                if 差==0:#无平移
                    保留.append(项)#原样
                else:#平移
                    新=dict(项)#拷
                    新['offset']=偏移+差#新偏移
                    保留.append(新)#收下
        自身.出现表=保留#写回

    def 监视认领(自身):#认领完整性监视
        """破坏令牌前缀则释放认领。"""
        if 自身.相位=='claimed' and 自身.认领 is not None:#认领相位
            令牌=自身.认领['token'] if isinstance(自身.认领,dict) else 自身.认领['token']#令牌
            if not 自身.草稿.startswith(令牌):#前缀已破
                自身.相位='plain'#退回
                自身.认领=None#丢掉

    def 铸造(自身,引用,偏移):#铸造一次出现
        """在草稿偏移处铸造。"""
        自身.出现序号+=1#前进身份
        return {#出现
            'occurrenceId':自身.出现序号,#身份
            'source':引用.get('source') if isinstance(引用,dict) else getattr(引用,'source',''),#源
            'ref':引用.get('ref') if isinstance(引用,dict) else getattr(引用,'ref',''),#引用 id
            'offset':偏移,#偏移
            'label':引用.get('label') if isinstance(引用,dict) else getattr(引用,'label',''),#标签
            'clipboardText':引用.get('clipboardText') if isinstance(引用,dict) else getattr(引用,'clipboardText',''),#剪贴板
        }#结束

    def 拼入铸造(自身,铸出):#拼入铸出的出现
        """拼入后按 offset 排序。"""
        if not 铸出:#没有
            return#停
        自身.出现表=sorted(list(自身.出现表)+list(铸出),key=lambda 项:项['offset'])#排序

    def 草稿已变(自身,草稿,编辑范围=None):#草稿已变
        """单字符打字可合并进打开游程。"""
        if 草稿==自身.草稿:#未变
            return []#空
        范围=编辑范围 if 编辑范围 is not None else 差分编辑(自身.草稿,草稿)#形态
        打字=范围['start']==范围['end'] and 范围['insertedLength']==1#单字符插入
        时刻=自身.现在()#时钟
        游程=自身.打字游程#打开游程
        合并=打字 and 游程 is not None and 游程['end']==范围['start'] and 时刻-游程['at']<=自身.合并窗口毫秒#连续且窗口内
        if not 合并:#不合并
            自身.推事务({'start':范围['start'],'end':范围['end']})#新开事务
        自身.打字游程={'end':范围['start']+1,'at':时刻} if 打字 else None#延长或关掉
        自身.对账(范围)#对账
        自身.采纳(草稿)#采纳
        自身.监视认领()#监视
        自身.粘贴=None#结束粘贴
        return []#无效应

    def 跨度可用(自身,跨度):#跨度 CAS
        """修订号相等且边界健全。"""
        return (跨度.get('draftRev')==自身.草稿修订#修订相等
            and 跨度.get('start',0)>=0 and 跨度.get('start',0)<=跨度.get('end',0)
            and 跨度.get('end',0)<=len(自身.草稿))#落在草稿内

    def 开始命令(自身,认领,跨度):#开始认领命令
        """前导触发：跨度前只许空白。"""
        if 自身.相位 not in ('plain','claimed'):#忙碌
            return []#拒绝
        if not 自身.跨度可用(跨度) or 自身.草稿[:跨度['start']].strip()!='':#CAS 失败或前有非空白
            return []#拒绝
        自身.推事务()#开事务
        自身.打字游程=None#打断打字
        令牌=认领['token'] if isinstance(认领,dict) else 认领['token']#令牌
        自身.对账({'start':0,'end':跨度['end'],'insertedLength':len(令牌)})#对账
        自身.采纳(令牌+自身.草稿[跨度['end']:])#令牌+跨度后
        自身.认领=认领 if isinstance(认领,dict) else dict(认领)#记下
        自身.相位='claimed'#进入
        自身.粘贴=None#结束粘贴
        return []#无效应

    def 插入引用(自身,引用,跨度):#插入引用
        """用芯片替换跨度。"""
        if 自身.相位 not in ('plain','claimed'):#忙碌
            return []#拒绝
        if not 自身.跨度可用(跨度):#CAS 失败
            return []#拒绝
        自身.用芯片替换跨度(引用,跨度)#共用事务
        自身.粘贴=None#结束粘贴
        return []#无效应

    def 用芯片替换跨度(自身,引用,跨度):#用芯片替换跨度
        """芯片后跟分隔空格，除非后面已有。返回插入长度。"""
        自身.推事务()#开事务
        自身.打字游程=None#打断
        尾=自身.草稿[跨度['end']:]#跨度后
        空隙=' ' if (len(尾)==0 or 尾[0]!=' ') else ''#补空格
        插入=占位符+空隙#占位+空隙
        自身.对账({'start':跨度['start'],'end':跨度['end'],'insertedLength':len(插入)})#对账
        自身.拼入铸造([自身.铸造(引用,跨度['start'])])#铸造
        自身.采纳(自身.草稿[:跨度['start']]+插入+尾)#拼回
        自身.监视认领()#监视
        return len(插入)#插入长

    def 消费令牌(自身,守卫):#消费令牌
        """业务成功后的守卫令牌删除。"""
        if 自身.相位 not in ('plain','claimed'):#忙碌
            return []#拒绝
        种=守卫.get('kind') if isinstance(守卫,dict) else getattr(守卫,'kind',None)#种类
        if 种=='span':#按跨度
            跨度=守卫.get('span') if isinstance(守卫,dict) else getattr(守卫,'span',None)#跨度
            if 跨度 is None or not 自身.跨度可用(跨度) or 跨度['start']==跨度['end']:#失败或空
                return []#拒绝
            自身.推事务()#开事务
            自身.打字游程=None#打断
            自身.对账({'start':跨度['start'],'end':跨度['end'],'insertedLength':0})#删除
            自身.采纳(自身.草稿[:跨度['start']]+自身.草稿[跨度['end']:])#拼回
            自身.监视认领()#监视
            自身.粘贴=None#结束
            return []#无效应
        if 种=='bare-token':#裸令牌
            令牌=守卫.get('token') if isinstance(守卫,dict) else getattr(守卫,'token','')#令牌
            if 令牌=='' or 自身.草稿.strip()!=令牌:#不匹配
                return []#拒绝
            自身.推事务()#开事务
            自身.打字游程=None#打断
            自身.出现表=[]#清空芯片
            自身.采纳('')#清空
            自身.监视认领()#监视
            自身.粘贴=None#结束
            return []#无效应
        return 不可达(守卫)#穷尽

    def 标无效(自身,无效标识们):#标无效出现
        """样式位；不是事务。"""
        标识集=set(无效标识们)#集
        需改=False#是否要改
        for 项 in 自身.出现表:#检查
            曾=项.get('invalid') is True#旧位
            要=项['occurrenceId'] in 标识集#新位
            if 曾!=要:#不一致
                需改=True#要改
                break#停
        if not 需改:#已一致
            return []#空
        新表=[]#新表
        for 项 in 自身.出现表:#翻位
            要=项['occurrenceId'] in 标识集#是否无效
            拷=dict(项)#拷
            拷.pop('invalid',None)#剥旧
            if 要:#要无效
                拷['invalid']=True#写
            新表.append(拷)#收下
        自身.出现表=新表#写回
        return []#无效应

    def 撤销(自身):#撤销
        """弹出最近事务。"""
        if not 自身.日志:#没有
            return []#空
        条目=自身.日志.pop()#弹出
        自身.重做栈.append({'draftBefore':自身.草稿,'occurrencesBefore':list(自身.出现表)})#推进重做
        自身.出现表=list(条目['occurrencesBefore'])#恢复出现
        自身.采纳(条目['draftBefore'])#恢复草稿
        自身.监视认领()#监视
        自身.打字游程=None#打断
        自身.粘贴=None#结束
        return []#无效应

    def 重做(自身):#重做
        """弹出最近重做。"""
        if not 自身.重做栈:#没有
            return []#空
        条目=自身.重做栈.pop()#弹出
        自身.日志.append({'draftBefore':自身.草稿,'occurrencesBefore':list(自身.出现表)})#手工推日志
        if len(自身.日志)>日志上限:#超深
            自身.日志.pop(0)#丢最旧
        自身.出现表=list(条目['occurrencesBefore'])#恢复
        自身.采纳(条目['draftBefore'])#恢复
        自身.监视认领()#监视
        自身.打字游程=None#打断
        自身.粘贴=None#结束
        return []#无效应

    def 粘贴开始(自身,原文,选区,分量=None,代数=0):#粘贴开始
        """一次事务替换选区；同步分量同事务分量化。"""
        分量=分量 or []#缺省
        起=选区['start']#起
        止=选区['end']#止
        if 起<0 or 起>止 or 止>len(自身.草稿):#不健全
            return []#拒绝
        文本=原文.replace(占位符,'')#洗掉 U+FFFC
        自身.推事务(选区)#开事务
        自身.打字游程=None#打断
        排序=sorted(分量,key=lambda 项:项['start'])#按起点
        铸出=[]#本事务出现
        插入=''#插入串
        游标=0#粘贴文本偏移
        for 项 in 排序:#同步分量
            插入+=文本[游标:项['start']]#分量前原文
            铸出.append(自身.铸造(项['reference'],起+len(插入)))#铸造
            插入+=占位符#占位
            游标=项['end']#跳过
        插入+=文本[游标:]#尾部
        自身.对账({'start':起,'end':止,'insertedLength':len(插入)})#对账
        自身.拼入铸造(铸出)#拼入
        自身.采纳(自身.草稿[:起]+插入+自身.草稿[止:])#拼回
        自身.监视认领()#监视
        if 自身.相位 in ('plain','claimed'):#仍接受引用
            自身.粘贴序号+=1#铸造尝试
            自身.粘贴={'attemptId':自身.粘贴序号,'insertedRange':{'start':起,'end':起+len(插入)},'generation':代数}#打开
        else:#忙碌
            自身.粘贴=None#不打开
        return []#无效应

    def 粘贴升级(自身,尝试标识,跨度,引用):#升级粘贴令牌
        """异步匹配落地：独立芯片事务。"""
        尝试=自身.粘贴#活尝试
        if 尝试 is None or 尝试['attemptId']!=尝试标识:#过期
            return []#拒绝
        if 自身.相位 not in ('plain','claimed'):#忙碌
            return []#拒绝
        if not 自身.跨度可用(跨度) or 跨度['start']==跨度['end']:#CAS/空
            return []#拒绝
        插入长=自身.用芯片替换跨度(引用,跨度)#芯片事务
        自身.粘贴={#保持尝试
            **尝试,#沿用
            'insertedRange':{#调整范围
                'start':尝试['insertedRange']['start'],#起
                'end':尝试['insertedRange']['end']+插入长-(跨度['end']-跨度['start']),#终点平移
            },#范围结束
        }#粘贴结束
        return []#无效应

    def 开尝试(自身,模式):#铸造提交尝试
        """占据飞行槽。"""
        控制器=中止控制器()#取消控制器
        自身.序号+=1#前进
        尝试={'seq':自身.序号,'signal':控制器.signal,'draftSnapshot':自身.草稿,'mode':模式}#铸造
        自身.飞行={'attempt':尝试,'controller':控制器}#占槽
        return 尝试#载荷

    def 进入(自身,模式):#进入提交
        """认领直提；斜杠走裁决；否则默认汇。"""
        if 自身.相位 in ('adjudicating','submitting'):#已锁定
            return []#拒绝
        if 自身.相位=='claimed' and 自身.认领 is not None:#已认领
            尝试=自身.开尝试(模式)#铸造
            自身.相位='submitting'#进入提交
            自身.粘贴=None#结束粘贴
            令牌=自身.认领['token'] if isinstance(自身.认领,dict) else 自身.认领['token']#令牌
            return [{'type':'begin-submit','attempt':尝试,'claim':自身.认领,'args':令牌后参数(自身.草稿,令牌)}]#开始提交
        修剪=自身.草稿.strip()#去两端
        if 修剪=='':#空草稿
            return []#不提交
        自身.粘贴=None#结束粘贴
        if 修剪.startswith('/'):#斜杠裁决
            尝试=自身.开尝试(模式)#铸造
            自身.相位='adjudicating'#进入裁决
            return [{'type':'adjudicate','attempt':尝试,'draft':自身.草稿}]#去裁决
        return [{'type':'default-sink','draft':自身.草稿,'mode':模式}]#默认汇

    def 裁决完成(自身,尝试,结局):#裁决完成
        """过期丢掉；认领则 begin-submit；未命中流向汇点。"""
        飞行=自身.飞行#飞行槽
        if 自身.相位!='adjudicating' or 飞行 is None or 飞行['attempt']['seq']!=尝试['seq']:#过期
            return []#丢掉
        if 结局 is not None and 结局!='handled' and isinstance(结局,dict) and 'claim' in 结局:#给出认领
            自身.认领=结局['claim']#记下
            自身.相位='submitting'#进入提交
            令牌=结局['claim']['token']#令牌
            return [{'type':'begin-submit','attempt':尝试,'claim':结局['claim'],'args':令牌后参数(尝试['draftSnapshot'],令牌)}]#认领提交
        自身.飞行=None#清槽
        自身.相位='plain'#回到 plain
        if 结局 is None:#未命中
            return [{'type':'default-sink','draft':尝试['draftSnapshot'],'mode':尝试['mode']}]#默认汇
        return []#handled/insert：无效应

    def 裁决失败(自身,尝试,消息):#裁决失败
        """草稿保留；错误通知。"""
        if 自身.相位!='adjudicating' or 自身.飞行 is None or 自身.飞行['attempt']['seq']!=尝试['seq']:#过期
            return []#丢掉
        自身.飞行=None#清槽
        自身.相位='plain'#回到
        return [{'type':'notice','level':'error','text':消息}]#错误通知

    def 提交结算(自身,事件):#提交已结算
        """成功则清空且切断撤销；失败按漂移守卫重入 claimed 或退 plain。"""
        飞行=自身.飞行#飞行槽
        if 自身.相位!='submitting' or 飞行 is None or 飞行['attempt']['seq']!=事件['attempt']['seq']:#过期
            return []#丢掉
        自身.飞行=None#清槽
        if 事件.get('ok'):#成功
            自身.相位='plain'#回到
            自身.认领=None#丢掉
            自身.出现表=[]#清空
            自身.采纳('')#清空
            自身.日志=[]#丢撤销
            自身.重做栈=[]#丢重做
            自身.打字游程=None#关掉
            自身.粘贴=None#结束
            结局=事件.get('outcome')#结算文案
            文=结局.get('text') if isinstance(结局,dict) else None#文案
            if 文 is not None:#有文案
                级='error' if isinstance(结局,dict) and 结局.get('kind')=='error' else 'info'#级别
                return [{'type':'notice','level':级,'text':文}]#通知
            return []#静默成功
        文=事件.get('message')#失败消息
        if 文 is None:#无消息
            结局=事件.get('outcome')#结局
            文=结局.get('text') if isinstance(结局,dict) else None#文案
        if 文 is None:#仍无
            文='command failed'#默认
        if (自身.草稿==飞行['attempt']['draftSnapshot']#活草稿仍等于快照
            and 自身.认领 is not None and 自身.草稿.startswith(自身.认领['token'])):#认领仍在
            自身.相位='claimed'#回到 claimed
            return [{'type':'notice','level':'error','text':文}]#错误
        自身.相位='plain'#草稿已漂移
        自身.认领=None#丢掉
        return [{'type':'notice','level':'error','text':文}]#错误

    def 发送已提交(自身):#发送已提交
        """COMMIT 清空；撤销不得复活。"""
        自身.认领=None#丢掉
        自身.出现表=[]#清空
        自身.采纳('')#清空
        自身.日志=[]#丢撤销
        自身.重做栈=[]#丢重做
        自身.打字游程=None#关掉
        自身.粘贴=None#结束
        return []#无效应

    def 释放(自身):#释放
        """中止飞行；回到 plain。"""
        if 自身.飞行 is not None:#有飞行
            自身.飞行['controller'].abort()#机自己 abort
            自身.飞行=None#清槽
        自身.相位='plain'#回到
        自身.认领=None#丢掉
        自身.打字游程=None#关掉
        自身.粘贴=None#结束
        return []#无效应
