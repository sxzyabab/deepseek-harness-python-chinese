"""经审计的 V2 迁移准入与 V3 载荷校验，独立于已安装的核心会话类型。"""
import json,re#JSON诊断与修复标识后缀
from ..会话格式 import (#从会话格式导入
    会话格式错误,#格式错误
    会话格式不支持迁移错误,#不支持迁移
    是否会话格式json对象,#是否JSON对象
    会话格式计数,#格式计数
    会话格式安全整数,#安全整数
)#从会话格式导入
from ..会话格式_v0到v1 import 断言已发布载荷语义,断言已发布表面元数据#从v0到v1导入
from ..会话格式_v1到v2 import 已发布v2事件处置#从v1到v2导入

#经审计的 surface 事件名；其余已接纳事件为仅日志。
表面类型=frozenset(['system/message','user/message','assistant/message','tool/result'])#表面类型
来源种类=frozenset(['user','plugin','model','tool','agent-instructions','session-reference','team-message','goal','skill-invocation','skill-catalog','coordinator','subagent-report','subagent-settled','webhook','agent-message'])#消息来源种类
内容种类=frozenset(['text','reasoning','image','file','tool-call','tool-result'])#内容种类

def 记录(值,标签):#记录对象
    """在持久输入边界要求 JSON 对象。"""
    if not 是否会话格式json对象(值):#须对象
        raise 会话格式错误(标签+' must be an object')#错误
    return 值#返回

def 精确键(值,必填,可选,标签):#精确键
    """拒绝缺失与未经审计的成员，而非猜测它们是否含坐标。"""
    缺=None#缺必填
    for 键 in 必填:#找缺
        if 键 not in 值:#缺
            缺=键#记下
            break#找到
    意外=None#意外键
    for 键 in 值.keys():#找意外
        if 键 not in 必填 and 键 not in 可选:#意外
            意外=键#记下
            break#找到
    if 缺 is not None:#缺字段
        raise 会话格式错误(标签+' lacks required field '+缺)#错误
    if 意外 is not None:#意外字段
        raise 会话格式错误(标签+' has unexpected field '+意外)#错误

def 断言事件(事件,版本):#断言事件
    """在迁移前校验已分类载荷，或校验原生 V3 的 system/header 载荷。"""
    if 版本==3:#目标代
        断言v3事件(事件)#委托v3
        return#返回
    处置=已发布v2事件处置.get(事件['type'])#处置
    反馈=事件['type']=='feedback/message-put' or 事件['type']=='feedback/message-delete'#反馈事件
    if 处置 is None and not 反馈:#未分类
        raise 会话格式不支持迁移错误('format v2 to v3 cannot safely transform unclassified event '+事件['type'])#拒绝
    表面=事件['type'] in 表面类型#是否表面
    精确键(事件,['type','seq','time','data'],['ignorable','sourceEventSeqs','surfaceOp'] if 表面 else ['ignorable'],事件['type'])#信封键
    会话格式计数(事件['seq'],'event seq')#序号
    会话格式安全整数(事件['time'],'event time')#时间
    if 'ignorable' in 事件 and 事件['ignorable'] is not True:#ignorable须为true
        raise 会话格式错误('ignorable must be true')#错误
    if 表面:#表面事件
        断言已发布表面元数据(事件,事件['seq'],事件['type'],'forbid-assistant')#表面元数据
        if 'surfaceOp' not in 事件:#须有surfaceOp
            raise 会话格式错误(事件['type']+' requires surfaceOp')#错误
    数据=记录(事件['data'],事件['type']+' data')#载荷
    if 反馈:#反馈
        断言反馈(事件['type'],数据)#断言反馈
        return#返回
    #非清单反馈事件已在上方返回。
    精确键(数据,处置['required'],处置['optional'],事件['type']+' data')#载荷键
    断言自有内容(事件,数据)#自有内容审计
    #助手 attempt 由 V2 引入；V0 助手无对应分支。
    if 事件['type']!='assistant/attempt':#非attempt
        断言已发布载荷语义(事件,版本)#语义校验
    if 事件['type']=='assistant/message' or 事件['type']=='assistant/attempt':#助手坐标
        for 坐标 in ('turn','step'):#回合与步骤
            if 会话格式计数(数据[坐标],坐标)==0:#须为正
                raise 会话格式错误(坐标+' must be positive')#错误
    if 事件['type']=='session/end-seed' and 'inherited' in 数据 and 数据['inherited'] is not True:#继承标记非法
        raise 会话格式错误('session/end-seed inherited must be true')#错误
    #来源分类仅适用于 Harness 消息，不适用于团队投递信封。
    if 事件['type']=='user/message':#用户消息来源
        断言来源(数据)#来源
    if 事件['type']=='assistant/message' or 事件['type']=='tool/result':#嵌套消息来源
        断言来源(记录(数据['message'],'message'))#来源
    if 事件['type']=='tool/result' and 是否会话格式json对象(数据.get('error')) and 数据['error'].get('code')=='TOOL_NOT_STARTED':#修复标识
        消息=记录(数据['message'],'tool result message')#消息
        来源=记录(消息['source'],'tool result source')#来源
        if not 是否修复标识(消息.get('id'),来源.get('callId')):#非规范修复标识
            raise 会话格式错误('TOOL_NOT_STARTED repair requires its canonical historical message id')#错误
    if 事件['type']=='agent/inbox/spliced' or 事件['type']=='session/title-llm-request':#多消息位置
        消息列表=数据['inserted' if 事件['type']=='agent/inbox/spliced' else 'messages']#消息列表
        for 消息 in 消息列表:#逐条来源
            断言来源(消息)#来源

def 是否修复标识(标识,调用标识):#是否修复标识
    """识别稳定的生成修复标识，且不把其历史后缀解释为当前坐标。"""
    if not isinstance(调用标识,str):#callId须串
        return False#否
    前缀='interrupted-tool-result-'+调用标识+'-'#前缀
    if not isinstance(标识,str) or not 标识.startswith(前缀):#须此前缀
        return False#否
    后缀=标识[len(前缀):]#后缀
    if re.fullmatch(r'0|[1-9]\d*',后缀) is None:#须十进制
        return False#否
    数值=int(后缀)#转数
    return abs(数值)<=9007199254740991#十进制安全整数

def 断言来源(消息):#断言消息来源
    """断言消息来源种类与智能体中继字段。"""
    来源=记录(消息['source'],'message source')#来源对象
    if not isinstance(来源.get('kind'),str) or 来源['kind'] not in 来源种类:#未知种类
        raise 会话格式不支持迁移错误('cannot safely transform unclassified message source')#拒绝
    if 来源['kind']=='agent-message':#智能体中继
        精确键(来源,['kind','form','senderSessionId'],[],'agent-message source')#精确键
        if (来源['form']!='relay' or not isinstance(来源['senderSessionId'],str)
            or len(来源['senderSessionId'])==0):#须relay与发送方
            raise 会话格式错误('agent-message source requires relay form and senderSessionId')#错误

def 内容数组(值,标签):#内容数组
    """要求内容为数组。"""
    if not isinstance(值,list):#须数组
        raise 会话格式错误(标签+': content must be an array')#错误
    return 值#断言

def 断言自有内容(事件,数据):#断言自有内容
    """按事件类型审计自有内容块。"""
    标签='format v2 '+事件['type']+' at seq '+str(事件['seq'])+' data'#路径前缀
    类型=事件['type']#类型
    if 类型=='user/message' or 类型=='tool/code-dispatch':#用户消息或代码分发
        断言内容种类列表(数据.get('content'),标签+'.content')#审计content
    elif 类型=='assistant/message' or 类型=='tool/result' or 类型=='team/message/queued':#嵌套消息
        断言内容种类列表(记录(数据['message'],标签+'.message').get('content'),标签+'.message.content')#审计嵌套content
    elif 类型=='agent/inbox/spliced' or 类型=='session/title-llm-request':#多消息
        字段='inserted' if 类型=='agent/inbox/spliced' else 'messages'#字段名
        for 下标,值 in enumerate(内容数组(数据.get(字段),标签+'.'+字段)):#逐条
            路径=标签+'.'+字段+'['+str(下标)+']'#路径
            断言内容种类列表(记录(值,路径).get('content'),路径+'.content')#审计content
    elif 类型=='compaction/summary':#压缩摘要
        断言内容种类列表(数据.get('summary'),标签+'.summary')#审计summary
        if 'rawOutput' in 数据:#可选rawOutput
            断言内容种类列表(数据['rawOutput'],标签+'.rawOutput')#审计
    if 类型=='assistant/message' or 类型=='assistant/attempt':#内嵌流
        for 下标,值 in enumerate(内容数组(数据.get('stream'),标签+'.stream')):#流记录
            路径=标签+'.stream['+str(下标)+']'#路径
            条目=记录(值,路径)#条目
            #仅原始 chunk 携带块；打包增量及其他 chunk 载荷保持不透明。
            if 条目.get('type')!='chunk':#跳过非chunk
                continue#继续
            块=记录(条目['chunk'],路径+'.chunk')#chunk对象
            if 块.get('type')=='block-end':#结束块
                断言内容块(块.get('block'),路径+'.chunk.block')#断言
            if 块.get('type')=='block-start':#起始种类
                断言内容种类(块.get('blockType'),路径+'.chunk.blockType')#断言

def 断言内容种类(种类,标签):#断言内容种类
    """断言单个内容种类名。"""
    if not isinstance(种类,str) or 种类 not in 内容种类:#未知种类
        raise 会话格式不支持迁移错误(标签+': cannot safely transform unclassified message content kind '+_json串(种类))#拒绝

def 断言内容种类列表(内容,标签):#断言内容数组
    """断言内容数组中每一块。"""
    for 下标,值 in enumerate(内容数组(内容,标签)):#逐块
        断言内容块(值,标签+'['+str(下标)+']')#断言

def 断言内容块(值,标签):#断言内容块
    """断言单个内容块及其文件/工具结果特例。"""
    块=记录(值,标签)#块对象
    断言内容种类(块.get('type'),标签)#种类
    if 块.get('type')=='tool-result':#工具结果块
        if not isinstance(块.get('content'),list):#须数组
            raise 会话格式错误(标签+'.content: invalid message content kind "tool-result": content must be an array')#错误
        断言内容种类列表(块['content'],标签+'.content')#递归审计
    if 块.get('type')=='file':#文件块
        精确键(块,['type','attachment'],[],标签+' kind "file"')#精确键
        附件=记录(块['attachment'],标签+' kind "file" attachment')#附件
        精确键(附件,['attachmentId','name','bytes'],[],标签+' kind "file" attachment')#附件键
        if (not isinstance(附件.get('attachmentId'),str) or len(附件['attachmentId'])==0
            or not isinstance(附件.get('name'),str)):#须标识与名
            raise 会话格式错误(标签+' kind "file": file attachment requires attachmentId and name')#错误
        会话格式计数(附件['bytes'],标签+' kind "file" attachment bytes')#字节数
        return#返回
    #复用冻结字段规则，且不递归再访 tool-result 子节点或解释不透明 JSON。
    叶子={**块,'content':[]} if 块.get('type')=='tool-result' else 块#叶子探测块
    探测={'type':'user/message','seq':0,'time':0,'data':{#合成探测事件
        'id':'content-admission','role':'user','source':{'kind':'user'},'content':[叶子],#探测载荷
    }}#probe结束
    try:#尝试冻结语义
        断言已发布载荷语义(探测,2)#v2语义
    except BaseException as 错误:#捕获
        #冻结载荷失败需要原始事件与内容路径，而非合成消息。
        raise 会话格式错误(标签+': invalid message content kind '+_json串(块.get('type'))+': '+str(错误))#包装错误

def 断言v3结构行(值):#断言v3结构行
    """即使越过可恢复的物理行失败，也拒绝 V3 结构载荷违规。"""
    if not isinstance(值,dict):#非对象行跳过
        return#返回
    行=值#行对象
    if 行.get('type')=='request/header':#请求头
        数据=记录(行.get('data'),'request/header data')#载荷
        if 'system' in 记录(数据.get('header'),'request header'):#含退役system
            raise 会话格式不支持迁移错误('format v3 request/header rejects retired header.system')#拒绝
    elif 行.get('type')=='system/message':#系统消息
        数据=记录(行.get('data'),'system/message data')#载荷
        断言系统({'type':'system/message','seq':0,'time':0,'data':数据},数据)#断言系统载荷

def 断言系统(事件,数据):#断言系统载荷
    """断言系统消息载荷字段。"""
    精确键(数据,['turn','step','message'],[],'system/message data')#精确键
    for 坐标 in ('turn','step'):#坐标
        if 会话格式计数(数据[坐标],坐标)==0:#须为正
            raise 会话格式错误(坐标+' must be positive')#错误
    消息=记录(数据['message'],'system message')#消息
    精确键(消息,['id','role','source','content'],[],'system message')#消息键
    if (not isinstance(消息.get('id'),str) or len(消息['id'])==0
        or 消息.get('role')!='system'):#身份与角色
        raise 会话格式错误('system message requires an id and system role')#错误
    来源=记录(消息['source'],'system source')#来源
    if (来源.get('kind')!='plugin' or not isinstance(来源.get('plugin'),str)
        or len(来源['plugin'])==0):#须插件来源
        raise 会话格式错误('system message requires plugin source')#错误
    断言已发布载荷语义({**事件,'type':'user/message','data':{**消息,'role':'user'}},3)#按用户消息语义探测

def 断言反馈(类型,数据):#断言反馈载荷
    """断言反馈 put/delete 载荷。"""
    精确键(数据,['sessionId','item'] if 类型=='feedback/message-put' else ['sessionId','messageId'],[],类型)#精确键
    if not isinstance(数据.get('sessionId'),str):#sessionId须串
        raise 会话格式错误('feedback sessionId must be a string')#错误
    if 类型=='feedback/message-delete':#删除
        if not isinstance(数据.get('messageId'),str):#messageId须串
            raise 会话格式错误('feedback messageId must be a string')#错误
        return#返回
    条目=记录(数据['item'],'feedback item')#条目
    精确键(条目,['messageId','rating','version','createdAt','updatedAt'],['note'],'feedback item')#条目键
    for 键 in ('messageId','version'):#字符串字段
        if not isinstance(条目.get(键),str):#须串
            raise 会话格式错误('feedback '+键+' must be a string')#错误
    if 条目.get('rating')!='positive' and 条目.get('rating')!='negative':#评分
        raise 会话格式错误('invalid feedback rating')#错误
    if 'note' in 条目 and not isinstance(条目['note'],str):#备注
        raise 会话格式错误('feedback note must be a string')#错误
    会话格式计数(条目['createdAt'],'feedback createdAt')#创建时间
    会话格式计数(条目['updatedAt'],'feedback updatedAt')#更新时间

def 断言v3事件(事件,已知事件类型=None):#断言v3事件
    """校验一条规范 V3 事件，且不解释插件自有载荷或日志关系。"""
    值=记录(事件,'format v3 event')#事件对象
    主语=f"format v3 {事件['type']} at seq {事件['seq']}"#诊断主语
    过时=事件['type']=='tool/code-dispatch-start' or 事件['type']=='tool/code-dispatch'#前代PTC
    已知=(not 过时 and (事件['type'] in 表面类型
        or 事件['type'] in 已发布v2事件处置
        or 事件['type']=='tool/ptc-dispatch-start' or 事件['type']=='tool/ptc-dispatch'
        or 事件['type']=='feedback/message-put' or 事件['type']=='feedback/message-delete'
        or (已知事件类型 is not None and 事件['type'] in 已知事件类型)))#是否已知
    不透明=not 已知#是否不透明
    精确键(值,['type','seq','time','data'],
        ['ignorable','surfaceOp','sourceEventSeqs'] if (事件['type'] in 表面类型 or 不透明) else ['ignorable'],主语)#信封键
    if not isinstance(事件.get('type'),str):#类型须串
        raise 会话格式错误(f'{主语} type must be a string')#错误
    会话格式计数(事件['seq'],f'{主语} seq')#序号
    会话格式安全整数(事件['time'],f'{主语} time')#时间
    if 'ignorable' in 值 and 值['ignorable'] is not True:#ignorable非法
        raise 会话格式错误(f'{主语} ignorable must be true when present')#错误
    if 事件['type'] in 表面类型:#表面事件
        操作=值.get('surfaceOp')#表面操作
        if 操作 is None:#须标记
            raise 会话格式错误(f'{主语} requires a surfaceOp marker')#错误
        if 操作!='append':#替换
            替换=记录(操作,f'{主语} surfaceOp')#替换对象
            if (len(替换)!=3 or 替换.get('op')!='replace'
                or 'startSeq' not in 替换 or 'endSeq' not in 替换):#须精确字段
                raise 会话格式错误(f'{主语} requires exact replace fields op/startSeq/endSeq')#错误
            for 键 in ('startSeq','endSeq'):#端点
                if 会话格式计数(替换[键],f'{主语} surfaceOp {键}')>=事件['seq']:#须更早
                    raise 会话格式错误(f'{主语} replacement endpoints must reference earlier events')#错误
        溯源=值.get('sourceEventSeqs')#溯源
        if 事件['type']=='assistant/message' and 溯源 is not None:#助手禁止溯源
            raise 会话格式错误(f'{主语} embeds its stream and cannot carry sourceEventSeqs')#错误
        if 溯源 is not None:#有溯源
            if not isinstance(溯源,list) or len(溯源)==0:#须非空数组
                raise 会话格式错误(f'{主语} sourceEventSeqs must be a non-empty array')#错误
            已见=set()#已见
            for 源 in 溯源:#逐项
                序号=会话格式计数(源,f'{主语} sourceEventSeqs member')#成员序号
                if 序号>=事件['seq'] or 序号 in 已见:#唯一更早
                    raise 会话格式错误(f'{主语} sourceEventSeqs must be unique earlier seqs')#错误
                已见.add(序号)#记入
    断言v3结构行(事件)#结构行规则
    断言规范载荷(事件)#规范载荷

def 断言规范载荷(事件):#断言规范载荷
    """断言请求头空可选与工具错误结果一致性。"""
    主语=f"format v3 {事件['type']} at seq {事件['seq']}"#诊断主语
    if 事件['type']=='request/header':#请求头
        数据=记录(事件['data'],f'{主语} data')#载荷
        头=记录(数据['header'],f'{主语} header')#头对象
        if ((isinstance(头.get('tools'),list) and len(头['tools'])==0)
            or (是否会话格式json对象(头.get('adapterDefaults')) and len(头['adapterDefaults'])==0)):#空可选须省略
            raise 会话格式错误(f'{主语} empty optional header fields must be omitted')#错误
    if 事件['type']!='tool/result':#非工具结果
        return#返回
    数据=记录(事件['data'],f'{主语} data')#载荷
    if 'error' not in 数据:#无错误
        return#返回
    消息=记录(数据['message'],f'{主语} message')#消息
    内容=消息.get('content')#内容
    if (not isinstance(内容,list) or len(内容)!=1 or not 是否会话格式json对象(内容[0])
        or 内容[0].get('type')!='tool-result' or 内容[0].get('isError') is not True):#须单错误结果块
        raise 会话格式错误(f'{主语} carries error metadata for a non-error tool result')#错误

def 规范化已转换事件(事件):#规范化已转换事件
    """规范化结构已转换的事件，且不改变其目标坐标。"""
    目标=事件#目标
    操作=事件.get('surfaceOp')#表面操作
    if 操作 is not None and 操作!='append':#替换
        替换=记录(操作,f"format v2 {事件['type']} at seq {事件['seq']} surfaceOp")#替换对象
        if (len(替换)!=3 or 替换.get('op')!='replace'
            or 'start' not in 替换 or 'end' not in 替换):#须精确start/end
            raise 会话格式错误(f"format v2 {事件['type']} at seq {事件['seq']} requires exact replace fields op/start/end")#错误
        目标={**事件,'surfaceOp':{#重命名端点
            'op':'replace',#操作
            'startSeq':会话格式计数(替换['start'],f"format v2 {事件['type']} at seq {事件['seq']} replace start"),#起点
            'endSeq':会话格式计数(替换['end'],f"format v2 {事件['type']} at seq {事件['seq']} replace end"),#终点
        }}#surfaceOp结束
    if 事件['type']=='request/header':#请求头
        数据=记录(事件['data'],f"format v2 request/header at seq {事件['seq']} data")#载荷
        头=记录(数据['header'],f"format v2 request/header at seq {事件['seq']} header")#头
        空键=[]#空可选键
        for 键 in 头.keys():#找空可选
            if ((键=='tools' and isinstance(头[键],list) and len(头[键])==0)
                or (键=='adapterDefaults' and 是否会话格式json对象(头[键]) and len(头[键])==0)):#空
                空键.append(键)#记下
        if len(空键)>0:#有空可选
            规范={键:值 for 键,值 in 头.items() if 键 not in 空键}#省略空键
            目标={**目标,'data':{**数据,'header':规范}}#写回
    断言v3事件(目标)#目标须通过v3校验
    return 目标#返回

def _json串(值):#JSON诊断串
    """用 JSON 渲染诊断值。"""
    return json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False)#渲染
