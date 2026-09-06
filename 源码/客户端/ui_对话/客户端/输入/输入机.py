"""输入机：纯的每会话输入状态机。

对齐上游 `ui-conversation/src/client/input/machine.ts`。公开面仅中文名。
事件进、效应出；零 DOM / 环境时钟。包私有——会话输入壳是唯一调用方。
草稿真相：每个芯片持有一个 U+FFFC；出现表携带身份与投影。
"""
import re#裸令牌后分隔判定
import threading#中止 Event
from ..服务 import 对话错误#本包异常
from .约定 import 占位符#U+FFFC 占位

__all__=['占位符','投影剪贴板','输入机','已中止','若已中止则抛出','中止控制器']#仅中文公开名

空队列=()#本层队列恒空
日志上限=100#撤销环深度

def 零时钟():
    """缺省常量时钟。"""
    return 0#零

def 出现偏移(项):
    """按 offset 排序。"""
    return 项['offset']#偏移

def 粘贴起点(项):
    """按 start 排序。"""
    return 项['start']#起点

def 不可达(值):
    """封闭输入事件的穷尽性兜底。"""
    raise 对话错误('unreachable input event: '+repr(值))#不可能到达

def 令牌后参数(草稿,令牌):#从草稿剥掉认领令牌得到提交参数
    """容忍前导空白；裸令牌缺尾部分隔则空参数；恰吃一个分隔字符。"""
    文本=草稿.lstrip()#去掉前导空白
    if 文本.startswith(令牌):#完整令牌命中
        return 文本[len(令牌):]#切掉令牌
    基名=令牌.rstrip()#去掉令牌尾部分隔
    if 文本.startswith(基名):#裸令牌前缀命中
        余下=文本[len(基名):]#令牌后的余下
        return 余下[1:] if len(余下)>0 and re.match(r'\s',余下[0],re.ASCII) is not None else 余下#有分隔则再吃一个空白
    return ''#对不上则空参数

def 差分编辑(旧草稿,新草稿):#两份草稿之间的编辑范围
    """前缀/后缀公共扫描，恢复编辑范围。"""
    前缀长=0#前缀公共长度
    公共=min(len(旧草稿),len(新草稿))#最多可比较
    while 前缀长<公共 and 旧草稿[前缀长]==新草稿[前缀长]:#扫前缀
        前缀长+=1#前进
    后缀长=0#后缀公共长度
    可后=公共-前缀长#去掉前缀后剩余
    while 后缀长<可后 and 旧草稿[len(旧草稿)-1-后缀长]==新草稿[len(新草稿)-1-后缀长]:#扫后缀
        后缀长+=1#前进
    return {'start':前缀长,'end':len(旧草稿)-后缀长,'insertedLength':len(新草稿)-后缀长-前缀长}#范围

def 投影剪贴板(状态):
    """把占位符展开成各出现的剪贴板文本；U+FFFC 永不离开机。"""
    草稿=状态['draft'] if 状态 is not None and 'draft' in 状态 and 状态['draft'] is not None else ''#草稿
    出现表=状态['occurrences'] if 状态 is not None and 'occurrences' in 状态 and 状态['occurrences'] is not None else []#出现
    if len(出现表)==0:#无芯片
        return 草稿#原文即投影
    投影=''#组装
    游标=0#已消费偏移
    for 项 in 出现表:#按 offset 序
        偏移=项['offset'] if 'offset' in 项 else 0#偏移
        剪贴=项['clipboardText'] if 'clipboardText' in 项 and 项['clipboardText'] is not None else ''#投影
        投影+=草稿[游标:偏移]+剪贴#中间原文+投影
        游标=偏移+1#跳过 U+FFFC
    return 投影+草稿[游标:]#尾部

def 已中止(信号):
    """Event 已置位。"""
    return 信号.is_set()#已中止

def 若已中止则抛出(信号):
    """已置位则抛本包异常。"""
    if 已中止(信号):#已中止
        raise 对话错误('The operation was aborted.')#中止

class 中止控制器:#取消控制器
    """对齐 AbortController；机在进入时铸造。信号为 threading.Event。"""
    def __init__(自身):#造信号
        """绑定 Event。"""
        自身.signal=threading.Event()#信号

    def abort(自身):#中止
        """置位 Event。"""
        自身.signal.set()#是

class 输入机:#纯输入机，每会话一份
    """事件进、效应出；零副作用。"""
    def __init__(自身,选项=None):#可注入合并窗口与时钟
        """默认常量时钟，连续打字总会合并。"""
        选项=选项 if 选项 is not None else {}#缺省
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
        自身.合并窗口毫秒=选项['mergeWindowMs'] if 'mergeWindowMs' in 选项 else 1000#默认 1000ms
        自身.现在=选项['now'] if 'now' in 选项 and 选项['now'] is not None else 零时钟#默认常量时钟

    @property
    def state(自身):#只读快照（本层队列恒空）
        """已发布输入状态。"""
        快照={#快照
            'draft':自身.草稿,#草稿
            'imageIds':[],#本层不持图
            'draftRev':自身.草稿修订,#修订
            'phase':自身.相位,#相位
            'occurrences':list(自身.出现表),#出现表拷贝
            'queue':list(空队列),#本层队列恒空
        }#结束
        if 自身.认领 is not None:#有认领
            令牌=自身.认领['token']#令牌
            认领快照={'token':令牌}#快照
            提示=自身.认领['hint'] if 'hint' in 自身.认领 else None#hint
            if 提示 is not None:#有 hint
                认领快照['hint']=提示#带上
            快照['claim']=认领快照#写入
        if 自身.粘贴 is not None:#有粘贴尝试
            快照['paste']=dict(自身.粘贴)#带上
        return 快照#快照

    def dispatch(自身,事件):#唯一写路径
        """按事件判别标签分发；空操作/锁定/过期返回空效应表。"""
        种类=事件['type'] if 'type' in 事件 else None#标签
        if 种类=='draft-changed':#草稿已变
            return 自身.草稿已变(事件['draft'] if 'draft' in 事件 else None,事件['editRange'] if 'editRange' in 事件 else None)#派发
        if 种类=='begin-command':#开始认领
            return 自身.开始命令(事件['claim'] if 'claim' in 事件 else None,事件['span'] if 'span' in 事件 else None)#派发
        if 种类=='insert-ref':#插入引用
            return 自身.插入引用(事件['reference'] if 'reference' in 事件 else None,事件['span'] if 'span' in 事件 else None)#派发
        if 种类=='consume-token':#消费令牌
            return 自身.消费令牌(事件['guard'] if 'guard' in 事件 else None)#派发
        if 种类=='set-invalid':#标无效
            无效=事件['invalidIds'] if 'invalidIds' in 事件 and 事件['invalidIds'] is not None else []#标识
            return 自身.标无效(无效)#派发
        if 种类=='undo':#撤销
            return 自身.撤销()#派发
        if 种类=='redo':#重做
            return 自身.重做()#派发
        if 种类=='paste-begin':#开始粘贴
            分量=事件['components'] if 'components' in 事件 and 事件['components'] is not None else []#分量
            代数=事件['generation'] if 'generation' in 事件 else 0#代数
            return 自身.粘贴开始(事件['text'] if 'text' in 事件 else None,事件['selection'] if 'selection' in 事件 else None,分量,代数)#派发
        if 种类=='paste-upgrade':#升级粘贴
            return 自身.粘贴升级(事件['attemptId'] if 'attemptId' in 事件 else None,事件['span'] if 'span' in 事件 else None,事件['reference'] if 'reference' in 事件 else None)#派发
        if 种类=='invalidate-paste':#作废粘贴
            自身.粘贴=None#清
            return []#无效应
        if 种类=='enter':#进入提交
            return 自身.进入(事件['mode'] if 'mode' in 事件 else None)#派发
        if 种类=='adjudicated':#裁决完成
            return 自身.裁决完成(事件['attempt'] if 'attempt' in 事件 else None,事件['outcome'] if 'outcome' in 事件 else None)#派发
        if 种类=='adjudication-failed':#裁决失败
            return 自身.裁决失败(事件['attempt'] if 'attempt' in 事件 else None,事件['message'] if 'message' in 事件 else None)#派发
        if 种类=='submit-settled':#提交已结算
            return 自身.提交结算(事件)#派发
        if 种类=='send-committed':#发送已提交
            return 自身.发送已提交()#派发
        if 种类=='release':#拆除
            return 自身.拆除()#派发
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
        长度差=范围['insertedLength']-(范围['end']-范围['start'])#长度差
        保留=[]#保留
        for 项 in 自身.出现表:#逐条
            偏移=项['offset']#偏移
            if 偏移<范围['start']:#范围前
                保留.append(项)#不动
            elif 偏移>=范围['end']:#范围后
                if 长度差==0:#无平移
                    保留.append(项)#原样
                else:#平移
                    新项=dict(项)#拷
                    新项['offset']=偏移+长度差#新偏移
                    保留.append(新项)#收下
        自身.出现表=保留#写回

    def 监视认领(自身):#认领完整性监视
        """破坏令牌前缀则释放认领。"""
        if 自身.相位=='claimed' and 自身.认领 is not None:#认领相位
            令牌=自身.认领['token']#令牌
            if 自身.草稿.startswith(令牌) is False:#前缀已破
                自身.相位='plain'#退回
                自身.认领=None#丢掉

    def 铸造(自身,引用,偏移):#铸造一次出现
        """在草稿偏移处铸造。"""
        自身.出现序号+=1#前进身份
        return {#出现
            'occurrenceId':自身.出现序号,#身份
            'source':引用['source'] if 'source' in 引用 else '',#源
            'ref':引用['ref'] if 'ref' in 引用 else '',#引用 id
            'offset':偏移,#偏移
            'label':引用['label'] if 'label' in 引用 else '',#标签
            'clipboardText':引用['clipboardText'] if 'clipboardText' in 引用 else '',#剪贴板
        }#结束

    def 拼入铸造(自身,铸出):#拼入铸出的出现
        """拼入后按 offset 排序。"""
        if len(铸出)==0:#没有
            return#停
        自身.出现表=sorted(list(自身.出现表)+list(铸出),key=出现偏移)#排序

    def 草稿已变(自身,草稿,编辑范围=None):#草稿已变
        """单字符打字可合并进打开游程。"""
        if 草稿==自身.草稿:#未变
            return []#空
        范围=编辑范围 if 编辑范围 is not None else 差分编辑(自身.草稿,草稿)#形态
        打字=范围['start']==范围['end'] and 范围['insertedLength']==1#单字符插入
        时刻=自身.现在()#时钟
        游程=自身.打字游程#打开游程
        合并=打字 and 游程 is not None and 游程['end']==范围['start'] and 时刻-游程['at']<=自身.合并窗口毫秒#连续且窗口内
        if 合并 is False:#不合并
            自身.推事务({'start':范围['start'],'end':范围['end']})#新开事务
        自身.打字游程={'end':范围['start']+1,'at':时刻} if 打字 else None#延长或关掉
        自身.对账(范围)#对账
        自身.采纳(草稿)#采纳
        自身.监视认领()#监视
        自身.粘贴=None#结束粘贴
        return []#无效应

    def 跨度可用(自身,跨度):#跨度 CAS
        """修订号相等且边界健全。"""
        起点=跨度['start'] if 'start' in 跨度 else 0#起
        终点=跨度['end'] if 'end' in 跨度 else 0#止
        修订=跨度['draftRev'] if 'draftRev' in 跨度 else None#修订
        return (修订==自身.草稿修订#修订相等
            and 起点>=0 and 起点<=终点
            and 终点<=len(自身.草稿))#落在草稿内

    def 开始命令(自身,认领,跨度):#开始认领命令
        """前导触发：跨度前只许空白。"""
        if 自身.相位 not in ('plain','claimed'):#忙碌
            return []#拒绝
        if 自身.跨度可用(跨度) is False or 自身.草稿[:跨度['start']].strip()!='':#CAS 失败或前有非空白
            return []#拒绝
        自身.推事务()#开事务
        自身.打字游程=None#打断打字
        令牌=认领['token']#令牌
        自身.对账({'start':0,'end':跨度['end'],'insertedLength':len(令牌)})#对账
        自身.采纳(令牌+自身.草稿[跨度['end']:])#令牌+跨度后
        自身.认领=认领#记下
        自身.相位='claimed'#进入
        自身.粘贴=None#结束粘贴
        return []#无效应

    def 插入引用(自身,引用,跨度):#插入引用
        """用芯片替换跨度。"""
        if 自身.相位 not in ('plain','claimed'):#忙碌
            return []#拒绝
        if 自身.跨度可用(跨度) is False:#CAS 失败
            return []#拒绝
        自身.用芯片替换跨度(引用,跨度)#共用事务
        自身.粘贴=None#结束粘贴
        return []#无效应

    def 用芯片替换跨度(自身,引用,跨度):#用芯片替换跨度
        """芯片后跟分隔空格，除非后面已有。返回插入长度。"""
        自身.推事务()#开事务
        自身.打字游程=None#打断
        尾部=自身.草稿[跨度['end']:]#跨度后
        空隙=' ' if (len(尾部)==0 or 尾部[0]!=' ') else ''#补空格
        插入=占位符+空隙#占位+空隙
        自身.对账({'start':跨度['start'],'end':跨度['end'],'insertedLength':len(插入)})#对账
        自身.拼入铸造([自身.铸造(引用,跨度['start'])])#铸造
        自身.采纳(自身.草稿[:跨度['start']]+插入+尾部)#拼回
        自身.监视认领()#监视
        return len(插入)#插入长

    def 消费令牌(自身,消费条件):#消费令牌
        """业务成功后的条件令牌删除。"""
        if 自身.相位 not in ('plain','claimed'):#忙碌
            return []#拒绝
        种类=消费条件['kind'] if 消费条件 is not None and 'kind' in 消费条件 else None#种类
        if 种类=='span':#按跨度
            跨度=消费条件['span'] if 'span' in 消费条件 else None#跨度
            if 跨度 is None or 自身.跨度可用(跨度) is False or 跨度['start']==跨度['end']:#失败或空
                return []#拒绝
            自身.推事务()#开事务
            自身.打字游程=None#打断
            自身.对账({'start':跨度['start'],'end':跨度['end'],'insertedLength':0})#删除
            自身.采纳(自身.草稿[:跨度['start']]+自身.草稿[跨度['end']:])#拼回
            自身.监视认领()#监视
            自身.粘贴=None#结束
            return []#无效应
        if 种类=='bare-token':#裸令牌
            令牌=消费条件['token'] if 消费条件 is not None and 'token' in 消费条件 else ''#令牌
            if 令牌=='' or 自身.草稿.strip()!=令牌:#不匹配
                return []#拒绝
            自身.推事务()#开事务
            自身.打字游程=None#打断
            自身.出现表=[]#清空芯片
            自身.采纳('')#清空
            自身.监视认领()#监视
            自身.粘贴=None#结束
            return []#无效应
        return 不可达(消费条件)#穷尽

    def 标无效(自身,无效标识列表):#标无效出现
        """样式位；不是事务。"""
        标识集=set(无效标识列表)#集
        需改=False#是否要改
        for 项 in 自身.出现表:#检查
            曾无效='invalid' in 项 and 项['invalid'] is True#旧位
            要无效=项['occurrenceId'] in 标识集#新位
            if 曾无效!=要无效:#不一致
                需改=True#要改
                break#停
        if 需改 is False:#已一致
            return []#空
        新表=[]#新表
        for 项 in 自身.出现表:#翻位
            要无效=项['occurrenceId'] in 标识集#是否无效
            拷=dict(项)#拷
            拷.pop('invalid',None)#剥旧
            if 要无效:#要无效
                拷['invalid']=True#写
            新表.append(拷)#收下
        自身.出现表=新表#写回
        return []#无效应

    def 撤销(自身):#撤销
        """弹出最近事务。"""
        if len(自身.日志)==0:#没有
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
        if len(自身.重做栈)==0:#没有
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
        分量=分量 if 分量 is not None else []#缺省
        起点=选区['start']#起
        终点=选区['end']#止
        if 起点<0 or 起点>终点 or 终点>len(自身.草稿):#不健全
            return []#拒绝
        文本=原文.replace(占位符,'')#洗掉 U+FFFC
        自身.推事务(选区)#开事务
        自身.打字游程=None#打断
        排序=sorted(分量,key=粘贴起点)#按起点
        铸出=[]#本事务出现
        插入=''#插入串
        游标=0#粘贴文本偏移
        for 项 in 排序:#同步分量
            插入+=文本[游标:项['start']]#分量前原文
            铸出.append(自身.铸造(项['reference'],起点+len(插入)))#铸造
            插入+=占位符#占位
            游标=项['end']#跳过
        插入+=文本[游标:]#尾部
        自身.对账({'start':起点,'end':终点,'insertedLength':len(插入)})#对账
        自身.拼入铸造(铸出)#拼入
        自身.采纳(自身.草稿[:起点]+插入+自身.草稿[终点:])#拼回
        自身.监视认领()#监视
        if 自身.相位 in ('plain','claimed'):#仍接受引用
            自身.粘贴序号+=1#铸造尝试
            自身.粘贴={'attemptId':自身.粘贴序号,'insertedRange':{'start':起点,'end':起点+len(插入)},'generation':代数}#打开
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
        if 自身.跨度可用(跨度) is False or 跨度['start']==跨度['end']:#CAS/空
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
            令牌=自身.认领['token']#令牌
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
        if 结局 is not None and 结局!='handled' and 'claim' in 结局:#给出认领
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
        if 'ok' in 事件 and 事件['ok'] is True:#成功
            自身.相位='plain'#回到
            自身.认领=None#丢掉
            自身.出现表=[]#清空
            自身.采纳('')#清空
            自身.日志=[]#丢撤销
            自身.重做栈=[]#丢重做
            自身.打字游程=None#关掉
            自身.粘贴=None#结束
            结局=事件['outcome'] if 'outcome' in 事件 else None#结算文案
            文案=结局['text'] if 结局 is not None and 'text' in 结局 else None#文案
            if 文案 is not None:#有文案
                级别='error' if 结局 is not None and 'kind' in 结局 and 结局['kind']=='error' else 'info'#级别
                return [{'type':'notice','level':级别,'text':文案}]#通知
            return []#静默成功
        文案=事件['message'] if 'message' in 事件 else None#失败消息
        if 文案 is None:#无消息
            结局=事件['outcome'] if 'outcome' in 事件 else None#结局
            文案=结局['text'] if 结局 is not None and 'text' in 结局 else None#文案
        if 文案 is None:#仍无
            文案='command failed'#默认
        if (自身.草稿==飞行['attempt']['draftSnapshot']#活草稿仍等于快照
            and 自身.认领 is not None and 自身.草稿.startswith(自身.认领['token'])):#认领仍在
            自身.相位='claimed'#回到 claimed
            return [{'type':'notice','level':'error','text':文案}]#错误
        自身.相位='plain'#草稿已漂移
        自身.认领=None#丢掉
        return [{'type':'notice','level':'error','text':文案}]#错误

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

    def 拆除(自身):#拆除飞行
        """中止飞行；回到 plain。"""
        if 自身.飞行 is not None:#有飞行
            自身.飞行['controller'].abort()#机自己 abort
            自身.飞行=None#清槽
        自身.相位='plain'#回到
        自身.认领=None#丢掉
        自身.打字游程=None#关掉
        自身.粘贴=None#结束
        return []#无效应
