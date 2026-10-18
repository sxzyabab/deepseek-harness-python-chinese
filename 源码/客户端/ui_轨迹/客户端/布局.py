import json
import math
from .复制代码 import 压缩中断错误#界面渲染前的稳定标记
from .轨迹记录 import 格式化已用秒数#组墙钟标签

__all__=['派生轨迹布局','追加轨迹流式布局']

def 布局条目序(条目):
    '初始系统提示排最前，其余按 seq'
    if 条目['kind']=='system' and 条目['change'].get('kind')=='initial':
        return float('-inf')
    return 条目['seq']

def 有限时间(时间):
    '可用作绝对时间的纪元毫秒，否则 None'
    if isinstance(时间,bool) or not isinstance(时间,(int,float)):
        return None
    if not math.isfinite(时间):
        return None
    return 时间

def 时长秒(较晚,较早):
    '两个纪元毫秒之差得到自身秒数；任一不可用则为 None'
    if 较早 is None or not isinstance(较晚,(int,float)) or isinstance(较晚,bool):
        return None
    if not math.isfinite(较晚) or not math.isfinite(较早):
        return None
    return max(0,(较晚-较早)/1000)

def 序列化源值(值):
    '缩进 JSON；空串退回 str'
    文本=json.dumps(值,indent=2,ensure_ascii=False)
    if 文本:
        return 文本
    return str(值)

def 源块(值):
    '把内容块或任意值转成轨迹源块'
    if not isinstance(值,dict):
        return {'type':'unknown','content':序列化源值(值)}
    类型=值['type'] if isinstance(值.get('type'),str) else 'unknown'
    if isinstance(值.get('text'),str):
        return {'type':'thinking' if 类型=='reasoning' else 类型,'content':值['text']}
    附件=值.get('attachment')
    if 类型 in ('image','file') and isinstance(附件,dict) and isinstance(附件.get('attachmentId'),str):
        块={'type':类型,'content':序列化源值(值)}
        if 类型=='image':
            块['attachment']=附件
        else:
            块['file']=附件
        return 块
    return {'type':类型,'content':序列化源值(值)}

def 图片块数(内容):
    '内容里的图片块个数'
    return sum(1 for 块 in 内容 if isinstance(块,dict) and 块.get('type')=='image')

def 详情内容(内容):
    '拼接 type=text 的 text'
    段=[]
    for 块 in 内容:
        if isinstance(块,dict) and 块.get('type')=='text' and isinstance(块.get('text'),str):
            段.append(块['text'])
    return '\n'.join(段)

def 预览内容(内容):
    '首段 text 或 None'
    for 块 in 内容:
        if isinstance(块,dict) and 块.get('type')=='text' and isinstance(块.get('text'),str):
            return 块['text']
    return None

def 挂用量(格,用量):
    '有提供方用量时拷到 Message 单元格'
    if not isinstance(用量,dict):
        return
    if 'inputTokens' in 用量 and 用量['inputTokens'] is not None:
        格['input']=用量['inputTokens']
    if 'cacheReadTokens' in 用量 and 用量['cacheReadTokens'] is not None:
        格['cacheRead']=用量['cacheReadTokens']
    if 'cacheWriteTokens' in 用量 and 用量['cacheWriteTokens'] is not None:
        格['cacheWrite']=用量['cacheWriteTokens']
    if 'outputTokens' in 用量 and 用量['outputTokens'] is not None:
        格['output']=用量['outputTokens']
    if 'reasoningTokens' in 用量 and 用量['reasoningTokens'] is not None:
        格['think']=用量['reasoningTokens']

def 摘要调用(名称,参数原文):
    '名作 text，非空参数作预览'
    结果={'toolName':名称,'text':名称}
    if 参数原文!='':
        结果['previewMarkdown']=参数原文
    return 结果

def 摘要结果(节点):
    '错误码或首段文本或无输出'
    if 节点.get('isError') is True:
        错误=节点.get('error')
        码=错误.get('code') if isinstance(错误,dict) else None
        return {'result':码 if 码 is not None else 'error'}
    for 块 in 节点.get('content') or []:
        if isinstance(块,dict) and 块.get('type')=='text' and isinstance(块.get('text'),str) and 块['text']!='':
            return {'result':'','resultPreviewMarkdown':块['text']}
    图片=图片块数(节点.get('content') or [])
    if 图片>0:
        return {'result':'图片 ×'+str(图片)}
    return {'result':'无输出'}

def 结果当文本(结果):
    'result → text，预览 Markdown 原样'
    文本={'text':'' if 结果 is None else 结果.get('result') or ''}
    if 结果 is not None and 结果.get('resultPreviewMarkdown') is not None:
        文本['previewMarkdown']=结果['resultPreviewMarkdown']
    return 文本

def 详情结果(节点):
    '错误名:码，或文本块，或 JSON'
    if 节点.get('isError') is True:
        错误=节点.get('error')
        if not isinstance(错误,dict):
            return 'error'
        return str(错误.get('name'))+': '+str(错误.get('code'))
    段=[]
    for 块 in 节点.get('content') or []:
        if isinstance(块,dict) and 块.get('type')=='text' and isinstance(块.get('text'),str):
            段.append(块['text'])
    文本='\n'.join(段)
    if 文本!='':
        return 文本
    图片=图片块数(节点.get('content') or [])
    if 图片>0:
        return '图片 ×'+str(图片)
    内容=节点.get('content') or []
    if len(内容)==0 or all(isinstance(块,dict) and 块.get('type')=='text' and (not isinstance(块.get('text'),str) or 块.get('text')=='') for 块 in 内容):
        return '无输出'
    return json.dumps(内容,indent=2,ensure_ascii=False)

def 包围用户轮次(后续助手,流式,最近助手轮):
    '下一助手轮，否则 partial，否则最后助手+1 或 1'
    if 后续助手 is not None:
        return 后续助手['turn']
    if 流式 is not None:
        return 流式['turn']
    if 最近助手轮 is not None:
        return 最近助手轮+1
    return 1

def 输入格详情(节点):
    '用户/转向/上下文共用字段；工具增减和附件另有摘要'
    内容=节点.get('content') or []
    if 节点.get('kind')=='context' and len(内容)>0 and all(isinstance(块,dict) and 块.get('type') in ('tool-addition','tool-removal') for 块 in 内容):
        新增=[块['toolName'] for 块 in 内容 if 块.get('type')=='tool-addition']
        移除=[块['toolName'] for 块 in 内容 if 块.get('type')=='tool-removal']
        单个=内容[0] if len(内容)==1 else None
        if len(新增)>0 and len(移除)>0:
            摘要='新增 '+str(len(新增))+' 个，移除 '+str(len(移除))+' 个'
        elif len(新增)>0:
            摘要='新增 '+str(len(新增))+' 个'
        else:
            摘要='移除 '+str(len(移除))+' 个'
        if 单个 is not None:
            if 单个.get('type')=='tool-addition':
                文本='已添加工具：'+str(单个.get('toolName') or '')
            else:
                文本='已移除工具：'+str(单个.get('toolName') or '')
        else:
            文本='工具已更新 · '+摘要
        结果={
            'text':文本,
            'sourceSeq':节点['seq'],
            'sourceBlocks':[{'type':块.get('type'),'content':块.get('toolName')} for 块 in 内容],
            'timeSeconds':0,
            'startedAt':有限时间(节点.get('time')),
        }
        if 单个 is None:
            行=[]
            if len(新增)>0:
                行.append('新增：'+', '.join(str(名) for 名 in 新增))
            if len(移除)>0:
                行.append('移除：'+', '.join(str(名) for 名 in 移除))
            结果['inputDetail']='\n'.join(行)
        return 结果
    预览=预览内容(内容)
    图片=图片块数(内容)
    文件=sum(1 for 块 in 内容 if isinstance(块,dict) and 块.get('type')=='file')
    附件=[]
    if 图片>0:
        附件.append('图片 ×'+str(图片))
    if 文件>0:
        附件.append('文件 ×'+str(文件))
    结果={
        'text':' · '.join(附件),
        'sourceSeq':节点['seq'],
        'messageSource':节点.get('source'),
        'inputDetail':详情内容(内容),
        'sourceBlocks':[源块(块) for 块 in 内容],
        'timeSeconds':0,
        'startedAt':有限时间(节点.get('time')),
    }
    if isinstance(预览,str) and 预览!='':
        结果['previewMarkdown']=预览#空串不当预览
    return 结果

def 展开助手(节点,起始下标,上一绝对,结果表,开始表,调用表,流式=False,计时=None):
    '展开助手块并挂用量'
    if 流式 is True and len(节点.get('blocks') or [])==0:
        return []
    输出=[]
    下标=起始下标-1
    用量=节点.get('usage')
    实际计时=计时 if 计时 is not None else 节点.get('timing')
    记录起点=有限时间(None if not isinstance(实际计时,dict) else 实际计时.get('stepStartTime'))
    if 流式:
        消息时长=None
        节点绝对=None
    else:
        消息时长=时长秒(节点.get('time'),记录起点 if 记录起点 is not None else 上一绝对)
        节点绝对=有限时间(节点.get('time'))
    消息段=[]
    思考段=[]
    for 块 in 节点.get('blocks') or []:
        if not isinstance(块,dict):
            continue
        if 块.get('kind')=='text' and (not 流式 or 块.get('text')!=''):
            消息段.append(块.get('text') or '')
        if 块.get('kind')=='reasoning' and (not 流式 or 块.get('text')!=''):
            思考段.append(块.get('text') or '')
    消息文本='\n\n'.join(消息段)
    思考文本='\n\n'.join(思考段)
    if 消息文本!='' or 思考文本!='':
        摘要=''
    else:
        工具表={}
        for 块 in 节点.get('blocks') or []:
            if isinstance(块,dict) and 块.get('kind')=='tool-call':
                工具表[块.get('name')]=工具表.get(块.get('name'),0)+1
        if len(工具表)>0:
            摘要='仅工具调用'
        else:
            图片=sum(1 for 块 in 节点.get('blocks') or [] if isinstance(块,dict) and 块.get('kind')=='image')
            摘要='图片 ×'+str(图片) if 图片>0 else ''
    消息={
        'index':下标+1,
        'recordId':'assistant\u0000'+str(节点['turn'])+'\u0000'+str(节点['step']),
        'kind':'message',
        'sourceSeq':节点.get('seq'),
        'text':摘要,
        'sourceBlocks':[],
        'timeSeconds':消息时长,
        'startedAt':记录起点,
    }
    下标=消息['index']
    if 消息文本!='':
        消息['previewMarkdown']=消息文本
        消息['outputDetail']=消息文本
    elif 思考文本!='':
        消息['previewMarkdown']=思考文本
    if 思考文本!='':
        消息['thinkingDetail']=思考文本
    if 节点.get('interrupted') is True:
        消息['isError']=True
    for 块 in 节点.get('blocks') or []:
        if not isinstance(块,dict):
            消息['sourceBlocks'].append(源块(块))
            continue
        种类=块.get('kind')
        if 种类=='text':
            消息['sourceBlocks'].append({'type':'text','content':块.get('text') or ''})
        elif 种类=='reasoning':
            消息['sourceBlocks'].append({'type':'thinking','content':块.get('text') or ''})
        elif 种类=='tool-call':
            消息['sourceBlocks'].append({
                'type':'tool-call',
                'content':块.get('argsRaw') or '',
                'callId':块.get('callId'),
                'toolName':块.get('name'),
            })
        elif 种类=='image':
            消息['sourceBlocks'].append(源块({'type':'image','attachment':块.get('attachment')}))
        else:
            消息['sourceBlocks'].append(源块(块.get('block')))
    挂用量(消息,用量 if isinstance(用量,dict) else None)
    输出令牌=None
    if isinstance(用量,dict) and isinstance(用量.get('outputTokens'),(int,float)) and not isinstance(用量.get('outputTokens'),bool) and math.isfinite(用量['outputTokens']):
        输出令牌=用量['outputTokens']
    消息['assistantMetrics']={
        'timingRecorded':实际计时 is not None,
        'stepStartTime':None if not isinstance(实际计时,dict) else 实际计时.get('stepStartTime'),
        'firstTokenTime':None if not isinstance(实际计时,dict) else 实际计时.get('firstTokenTime'),
        'completedTime':None if 流式 else 有限时间(节点.get('time')),
        'usageProvided':用量 is not None,
        'outputTokens':输出令牌,
    }
    输出.append({'absTime':节点绝对,'cell':消息})
    for 块 in 节点.get('blocks') or []:
        if not isinstance(块,dict) or 块.get('kind')!='tool-call':
            continue
        结果=结果表.get(块.get('callId'))
        if 流式 or 结果 is None:
            工具时长=None
        else:
            工具时长=时长秒(结果.get('time'),结果.get('callTime'))
        调用绝对=有限时间(开始表.get(块.get('callId')))
        调用=调用表.get(块.get('callId'))
        预览=None if 结果 is None else 摘要结果(结果)
        格={
            'index':下标+1,
            'kind':'tool',
            'callId':块.get('callId'),
            'timeSeconds':工具时长,
            'startedAt':调用绝对,
        }
        下标=格['index']
        格.update(摘要调用(块.get('name') or '',块.get('argsRaw') or ''))
        格['inputDetail']=块.get('argsRaw')
        if 结果 is not None:
            格['outputDetail']=详情结果(结果)
            格['outputBlocks']=[源块(项) for 项 in 结果.get('content') or []]
            格.update(预览 or {})
            格['isError']=结果.get('isError')
        已铺={'absTime':调用绝对,'toolName':块.get('name'),'callId':块.get('callId'),'cell':格}
        if 调用 is not None:
            已铺['subCalls']=调用.get('subCalls')
        输出.append(已铺)
    return 输出

def 展开子调用(子调用列表,起始下标):
    '一次父调用的子分派格。运行中没有时长'
    if not 子调用列表:
        return []
    输出=[]
    下标=起始下标
    for 子 in 子调用列表:
        if not isinstance(子,dict):
            continue
        if 'kind' not in 子 and 子.get('phase')=='preparing':
            continue
        已结算='kind' in 子
        预览=摘要结果(子) if 已结算 else None
        if 已结算:
            绝对=有限时间(子.get('callTime') if 子.get('callTime') is not None else 子.get('time'))
            工具名=None if not isinstance(子.get('call'),dict) else 子['call'].get('name')
            if 工具名 is None:
                工具名=子.get('callId')
        else:
            绝对=有限时间(子.get('time'))
            工具名=子.get('name')
        格={'index':下标+1,'kind':'subtool','callId':子.get('callId')}
        下标=格['index']
        if 已结算:
            调用=子.get('call')
            if isinstance(调用,dict):
                格.update(摘要调用(调用.get('name') or '',调用.get('argsRaw') or ''))
                格['inputDetail']=调用.get('argsRaw')
            else:
                格.update(结果当文本(预览))
            格['outputDetail']=详情结果(子)
            格['outputBlocks']=[源块(项) for 项 in 子.get('content') or []]
            if 预览 is not None:
                格.update(预览)
            格['isError']=子.get('isError')
            格['timeSeconds']=时长秒(子.get('time'),子.get('callTime'))
            格['startedAt']=有限时间(子.get('callTime'))
        else:
            格.update(摘要调用(子.get('name') or '',子.get('argsRaw') or ''))
            格['inputDetail']=子.get('argsRaw')
            格['timeSeconds']=None
            格['startedAt']=有限时间(子.get('time'))
        已铺={'absTime':绝对,'toolName':工具名,'callId':子.get('callId'),'cell':格}
        输出.append(已铺)
        for 孩子 in 展开子调用(子.get('subCalls'),下标):
            输出.append(孩子)
            下标=孩子['cell']['index']
    return 输出

def 带子调用(已铺列表):
    '把每个工具格的嵌套子调用插到它后面并重排下标'
    if not any(isinstance(项.get('subCalls'),list) and len(项['subCalls'])>0 for 项 in 已铺列表):
        return 已铺列表
    输出=[]
    下标=已铺列表[0]['cell']['index']-1 if len(已铺列表)>0 else 0
    for 已铺 in 已铺列表:
        格=dict(已铺['cell'])
        下标+=1
        格['index']=下标
        拷贝=dict(已铺)
        拷贝['cell']=格
        输出.append(拷贝)
        for 子 in 展开子调用(已铺.get('subCalls'),下标):
            输出.append(子)
            下标=子['cell']['index']
    return 输出

def 格式化组时长(秒):
    '组墙钟。非有限则不写'
    if not isinstance(秒,(int,float)) or isinstance(秒,bool) or not math.isfinite(秒):
        return None
    return 格式化已用秒数(秒)

def 转轮次模型(回合号,桶):
    '组转模型并挂墙钟与工具直方图'
    组列表=[]
    for 组 in 桶['groups']:
        部分=[]
        时刻=[]
        for 已铺 in 组['laid']:
            if 已铺.get('absTime') is None or not isinstance(已铺['absTime'],(int,float)) or not math.isfinite(已铺['absTime']):
                continue
            时刻.append(已铺['absTime'])
            格=已铺['cell']
            if 格.get('kind')=='tool' and 格.get('timeSeconds') is not None and isinstance(格['timeSeconds'],(int,float)) and math.isfinite(格['timeSeconds']):
                时刻.append(已铺['absTime']+格['timeSeconds']*1000)
        if len(时刻)>=2:
            跨度=格式化组时长((max(时刻)-min(时刻))/1000)
            if 跨度 is not None:
                部分.append(跨度)
        elif len(时刻)==1:
            自身秒=None
            for 已铺 in 组['laid']:
                if 已铺.get('absTime')==时刻[0]:
                    自身秒=已铺['cell'].get('timeSeconds')
                    break
            if 自身秒 is not None:
                跨度=格式化组时长(自身秒)
                if 跨度 is not None:
                    部分.append(跨度)
        工具表={}
        for 已铺 in 组['laid']:
            if 已铺.get('toolName') is None or 已铺['cell'].get('kind')!='tool':
                continue
            工具表[已铺['toolName']]=工具表.get(已铺['toolName'],0)+1
        for 名称,次数 in 工具表.items():
            部分.append(名称+'×'+str(次数) if 次数>1 else 名称)
        模型={'title':组['title'],'cells':[项['cell'] for 项 in 组['laid']]}
        if len(部分)>0:
            模型['description']=' '.join(部分)
        组列表.append(模型)
    return {'turn':回合号,'groups':组列表}

def 首格下标(轮次):
    '用折叠时单调分配的单元格下标'
    下标=[]
    for 组 in 轮次['groups']:
        for 格 in 组['cells']:
            下标.append(格['index'])
    if len(下标)==0:
        return float('inf')
    return min(下标)

def 派生轨迹布局(输入):
    '把快照折成 turn → Message/Step 组，并展开单元格'
    节点列表=输入.get('nodes') or []
    位置表=输入.get('eventLocations')
    流式=输入.get('partial')
    运行中=输入.get('runningCalls') or []
    请求列表=输入.get('requests') or []
    模式表=输入.get('callSchemas')
    结果表={}
    for 节点 in 节点列表:
        if isinstance(节点,dict) and 节点.get('kind')=='tool-result':
            结果表[节点.get('callId')]=节点
    调用表=dict(结果表)
    for 调用 in 运行中:
        if isinstance(调用,dict):
            调用表[调用.get('callId')]=调用
    已发出=set()
    for 节点 in 节点列表:
        if isinstance(节点,dict) and 节点.get('kind')=='assistant':
            for 块 in 节点.get('blocks') or []:
                if isinstance(块,dict) and 块.get('kind')=='tool-call':
                    已发出.add(块.get('callId'))
    后续=[]
    助手=None
    for 节点 in reversed(节点列表):
        后续.append(助手)
        if isinstance(节点,dict) and 节点.get('kind')=='assistant':
            助手=节点
    后续.reverse()
    开始表={}
    for 结果 in 结果表.values():
        起点=有限时间(结果.get('callTime'))
        if 起点 is not None:
            开始表[结果.get('callId')]=起点
    for 调用 in 运行中:
        if not isinstance(调用,dict) or 调用.get('phase')=='preparing':
            continue
        起点=有限时间(调用.get('time'))
        if 起点 is not None:
            开始表[调用.get('callId')]=起点
    轮次表={}
    独立压缩=[]
    下标=0
    上一绝对=None
    最近助手轮=None

    def 桶(回合):
        '按回合取组桶，没有就建'
        已有=轮次表.get(回合)
        if 已有 is None:
            已有={'groups':[]}
            轮次表[回合]=已有
        return 已有

    def 推消息(回合,已铺):
        '并进 Message 组，没有则新开'
        组列表=桶(回合)['groups']
        最后=组列表[-1] if len(组列表)>0 else None
        if 最后 is not None and 最后['title']=='消息':
            最后['laid'].append(已铺)
            return
        组列表.append({'title':'消息','laid':[已铺]})

    def 推步骤(回合,步号,已铺列表):
        '并进 Step 组'
        if len(已铺列表)==0:
            return
        组列表=桶(回合)['groups']
        标题='第 '+str(步号)+' 步'
        for 组 in 组列表:
            if 组['title']==标题:
                组['laid'].extend(已铺列表)
                return
        组列表.append({'title':标题,'laid':list(已铺列表)})

    已代表=set()
    for 节点 in 节点列表:
        if isinstance(节点,dict) and 节点.get('kind')=='assistant' and 节点.get('step',0)>0:
            已代表.add(str(节点['turn'])+'\u0000'+str(节点['step']))
    if isinstance(流式,dict) and 流式.get('step',0)>0:
        已代表.add(str(流式['turn'])+'\u0000'+str(流式['step']))
    for 调用 in 运行中:
        if isinstance(调用,dict) and 调用.get('step',0)>0:
            已代表.add(str(调用['turn'])+'\u0000'+str(调用['step']))
    条目=[]
    for 提示 in 输入.get('systemPrompts') or []:
        if not isinstance(提示,dict):
            continue
        条目.append({
            'kind':'system',
            'seq':提示.get('seq'),
            'systemPrompt':提示.get('text'),
            'change':{
                'seq':提示.get('seq'),
                'time':提示.get('time'),
                'kind':'system' if 提示.get('update') else 'initial',
            },
        })
    for 节点下标,节点 in enumerate(节点列表):
        条目.append({'kind':'node','seq':节点.get('seq') if isinstance(节点,dict) else 0,'node':节点,'nodeIndex':节点下标})
    for 请求 in 请求列表:
        if isinstance(请求,dict) and 请求.get('purpose')=='compaction':
            条目.append({'kind':'compaction','seq':请求.get('startSeq'),'request':请求})
    for 请求 in 请求列表:
        if not isinstance(请求,dict) or 请求.get('purpose')!='assistant':
            continue
        if 请求.get('promptChange') is None or 请求.get('prompt') is None:
            continue
        条目.append({
            'kind':'system',
            'seq':请求['promptChange'].get('seq'),
            'request':请求,
            'change':请求['promptChange'],
        })
    for 请求 in 请求列表:
        if not isinstance(请求,dict) or 请求.get('purpose')!='assistant':
            continue
        if str(请求.get('turn'))+'\u0000'+str(请求.get('step')) in 已代表:
            continue
        条目.append({'kind':'request','seq':请求.get('startSeq'),'request':请求})
    条目.sort(key=布局条目序)
    for 条目项 in 条目:
        if 条目项['kind']=='request':
            请求=条目项['request']
            下标+=1
            格={
                'index':下标,
                'kind':'message',
                'text':'',
                'sourceSeq':请求.get('startSeq'),
                'requestOnly':True,
                'timeSeconds':None if 请求.get('completedAt') is None else 时长秒(请求.get('completedAt'),请求.get('startedAt')),
                'startedAt':有限时间(请求.get('startedAt')),
            }
            if 请求.get('status')=='error':
                格['isError']=True
            推步骤(请求.get('turn'),请求.get('step'),[{'absTime':有限时间(请求.get('startedAt')),'cell':格}])
            完成=有限时间(请求.get('completedAt'))
            开始=有限时间(请求.get('startedAt'))
            上一绝对=完成 if 完成 is not None else 开始 if 开始 is not None else 上一绝对
            continue
        if 条目项['kind']=='system':
            变更=条目项['change']
            if 变更.get('kind')=='initial':
                回合号列表=[]
                for 节点 in 节点列表:
                    if isinstance(节点,dict) and 节点.get('kind')=='assistant' and 节点.get('turn',0)>0:
                        回合号列表.append(节点['turn'])
                if isinstance(流式,dict) and 流式.get('turn',0)>0:
                    回合号列表.append(流式['turn'])
                回合=1 if len(回合号列表)==0 else min(回合号列表)
            else:
                下一=None
                for 节点 in 节点列表:
                    if isinstance(节点,dict) and 节点.get('seq',0)>变更.get('seq',0) and 节点.get('kind')=='assistant' and 节点.get('step',0)>0:
                        下一=节点
                        break
                if isinstance(下一,dict):
                    回合=下一['turn']
                else:
                    回合=流式['turn'] if isinstance(流式,dict) else 1
            下标+=1
            格={
                'index':下标,
                'kind':'system',
                'text':{
                    'initial':'初始系统提示词',
                    'system':'系统提示词已更新',
                    'tools':'工具已更新',
                }.get(变更.get('kind'),'系统提示词和工具已更新'),
                'sourceSeq':变更.get('seq'),
                'timeSeconds':0,
                'startedAt':有限时间(变更.get('time')),
            }
            请求=条目项.get('request')
            if isinstance(请求,dict) and 请求.get('prompt') is not None:
                格['promptDetail']=请求['prompt']
            if 条目项.get('systemPrompt') is not None:
                格['systemPromptDetail']=条目项['systemPrompt']
            if 变更.get('previous') is not None:
                格['previousPromptDetail']=变更['previous']
            推消息(回合,{'absTime':有限时间(变更.get('time')),'cell':格})
            时刻=有限时间(变更.get('time'))
            上一绝对=时刻 if 时刻 is not None else 上一绝对
            continue
        if 条目项['kind']=='compaction':
            请求=条目项['request']
            原始=请求.get('rawOutput') if 请求.get('rawOutput') is not None else 请求.get('summary')
            思考=''
            if isinstance(原始,list):
                思考段=[]
                for 块 in 原始:
                    if isinstance(块,dict) and 块.get('type')=='reasoning' and isinstance(块.get('text'),str):
                        思考段.append(块['text'])
                思考='\n'.join(思考段)
            下标+=1
            if 请求.get('status')=='running':
                文本='正在压缩上下文…'
            elif 请求.get('status')=='error':
                if 请求.get('error')==压缩中断错误:
                    文本='上下文压缩在完成前被中断。'
                elif 请求.get('error') is not None:
                    文本=请求['error']
                else:
                    文本='上下文压缩失败'
            elif 请求.get('summary') is None:
                文本='上下文已压缩'
            else:
                文本=''
            格={
                'index':下标,
                'kind':'compacted',
                'text':文本,
                'sourceSeq':请求.get('startSeq'),
                'timeSeconds':None if 请求.get('completedAt') is None else 时长秒(请求.get('completedAt'),请求.get('startedAt')),
                'startedAt':有限时间(请求.get('startedAt')),
            }
            if 请求.get('status')=='complete' and 请求.get('summary') is not None:
                预览=预览内容(请求['summary'])
                if 预览 is not None:
                    格['previewMarkdown']=预览
            if 请求.get('summary') is not None:
                格['outputDetail']=详情内容(请求['summary'])
                格['outputBlocks']=[源块(块) for 块 in 请求['summary']]
            if 思考!='':
                格['thinkingDetail']=思考
            if isinstance(原始,list):
                格['sourceBlocks']=[源块(块) for 块 in 原始]
            if 请求.get('status')=='error':
                格['isError']=True
            挂用量(格,请求.get('usage') if isinstance(请求.get('usage'),dict) else None)
            压缩桶={'groups':[{'title':'压缩 '+str(请求.get('startSeq')),'laid':[{'absTime':有限时间(请求.get('startedAt')),'cell':格}]}]}
            if 请求.get('turn') is None:
                独立压缩.append(压缩桶)
            else:
                桶(请求['turn'])['groups'].extend(压缩桶['groups'])
            完成=有限时间(请求.get('completedAt'))
            开始=有限时间(请求.get('startedAt'))
            上一绝对=完成 if 完成 is not None else 开始 if 开始 is not None else 上一绝对
            continue
        节点=条目项['node']
        节点下标=条目项['nodeIndex']
        if not isinstance(节点,dict):
            continue
        if 节点.get('kind')=='user':
            回合=包围用户轮次(后续[节点下标] if 节点下标<len(后续) else None,流式,最近助手轮)
            下标+=1
            格={'index':下标,'kind':'user','opensTurn':True}
            格.update(输入格详情(节点))
            推消息(回合,{'absTime':有限时间(节点.get('time')),'cell':格})
            时刻=有限时间(节点.get('time'))
            上一绝对=时刻 if 时刻 is not None else 上一绝对
            continue
        if 节点.get('kind')=='steering':
            后续助手=后续[节点下标] if 节点下标<len(后续) else None
            位置=None if 位置表 is None else 位置表.get(节点.get('seq'))
            if isinstance(位置,dict) and 位置.get('kind')=='step':
                回合=位置.get('turn',{}).get('turn') if isinstance(位置.get('turn'),dict) else None
                步号=位置.get('step',{}).get('step') if isinstance(位置.get('step'),dict) else None
                安放={'turn':回合,'step':步号}
            else:
                定位回合=位置['turn']['turn'] if isinstance(位置,dict) and 位置.get('kind')=='turn' and isinstance(位置.get('turn'),dict) else None
                if 后续助手 is not None and (定位回合 is None or 后续助手.get('turn')==定位回合):
                    安放={'turn':后续助手['turn']}
                    if 后续助手.get('step',0)>0:
                        安放['step']=后续助手['step']
                elif isinstance(流式,dict) and (定位回合 is None or 流式.get('turn')==定位回合):
                    安放={'turn':流式['turn']}
                    if 流式.get('step',0)>0:
                        安放['step']=流式['step']
                elif 定位回合 is not None:
                    安放={'turn':定位回合}
                else:
                    安放={'turn':1 if 最近助手轮 is None else 最近助手轮}
            下标+=1
            格={'index':下标,'kind':'user'}
            格.update(输入格详情(节点))
            已铺={'absTime':有限时间(节点.get('time')),'cell':格}
            if 'step' not in 安放:
                推消息(安放['turn'],已铺)
            else:
                组列表=桶(安放['turn'])['groups']
                标题='第 '+str(安放['step'])+' 步'
                已有=None
                for 组 in 组列表:
                    if 组['title']==标题:
                        已有=组
                        break
                if 已有 is None:
                    组列表.append({'title':标题,'laid':[已铺]})
                else:
                    请求位=-1
                    for 位,项 in enumerate(已有['laid']):
                        if 项['cell'].get('requestOnly') is True:
                            请求位=位
                            break
                    if 请求位==-1:
                        已有['laid'].append(已铺)
                    else:
                        已有['laid'][请求位:请求位]=[已铺]
            时刻=有限时间(节点.get('time'))
            上一绝对=时刻 if 时刻 is not None else 上一绝对
            continue
        if 节点.get('kind')=='assistant':
            已铺列表=带子调用(展开助手(节点,下标+1,上一绝对,结果表,开始表,调用表,False,None))
            if 节点.get('step',0)>0:
                推步骤(节点.get('turn'),节点.get('step'),已铺列表)
            else:
                for 已铺 in 已铺列表:
                    推消息(节点.get('turn'),已铺)
            if len(已铺列表)>0:
                下标=已铺列表[-1]['cell']['index']
            时刻=有限时间(节点.get('time'))
            上一绝对=时刻 if 时刻 is not None else 上一绝对
            最近助手轮=节点.get('turn')
            continue
        if 节点.get('kind')=='context':
            回合=包围用户轮次(后续[节点下标] if 节点下标<len(后续) else None,流式,最近助手轮)
            下标+=1
            格={'index':下标,'kind':'context'}
            格.update(输入格详情(节点))
            推消息(回合,{'absTime':有限时间(节点.get('time')),'cell':格})
            时刻=有限时间(节点.get('time'))
            上一绝对=时刻 if 时刻 is not None else 上一绝对
            continue
        if 节点.get('kind')=='compaction':
            时刻=有限时间(节点.get('time'))
            上一绝对=时刻 if 时刻 is not None else 上一绝对
            continue
        if 节点.get('kind')=='tool-result' and 节点.get('callId') not in 已发出:
            调用=节点.get('call')
            工具名=调用.get('name') if isinstance(调用,dict) else None
            预览=摘要结果(节点)
            下标+=1
            格={
                'index':下标,
                'kind':'tool',
                'sourceSeq':节点.get('seq'),
                'outputDetail':详情结果(节点),
                'outputBlocks':[源块(块) for 块 in 节点.get('content') or []],
                'callId':节点.get('callId'),
                'isError':节点.get('isError'),
                'timeSeconds':时长秒(节点.get('time'),节点.get('callTime')),
                'startedAt':有限时间(节点.get('callTime')),
            }
            if isinstance(调用,dict):
                格.update(摘要调用(调用.get('name') or '',调用.get('argsRaw') or ''))
                格['inputDetail']=调用.get('argsRaw')
            else:
                格.update(结果当文本(预览))
            格.update(预览)
            已铺列表=[{
                'absTime':有限时间(节点.get('callTime') if 节点.get('callTime') is not None else 节点.get('time')),
                'callId':节点.get('callId'),
                'subCalls':节点.get('subCalls'),
                'cell':格,
            }]
            if 工具名 is not None:
                已铺列表[0]['toolName']=工具名
            for 已铺 in 展开子调用(节点.get('subCalls'),下标):
                已铺列表.append(已铺)
                下标=已铺['cell']['index']
            推步骤(0,1,已铺列表)
            时刻=有限时间(节点.get('time'))
            上一绝对=时刻 if 时刻 is not None else 上一绝对
    if isinstance(流式,dict):
        假={'kind':'assistant','seq':9007199254740991,'time':0,'turn':流式.get('turn'),'step':流式.get('step'),'blocks':流式.get('blocks') or []}
        已铺列表=带子调用(展开助手(假,下标+1,上一绝对,结果表,开始表,调用表,True,流式.get('timing')))
        if 流式.get('step',0)>0:
            推步骤(流式.get('turn'),流式.get('step'),已铺列表)
        else:
            for 已铺 in 已铺列表:
                推消息(流式.get('turn'),已铺)
        if len(已铺列表)>0:
            下标=已铺列表[-1]['cell']['index']
    见过=set()
    for 桶项 in 轮次表.values():
        for 组 in 桶项['groups']:
            for 已铺 in 组['laid']:
                if 已铺.get('callId') is not None:
                    见过.add(已铺['callId'])
    for 调用 in 运行中:
        if not isinstance(调用,dict) or 调用.get('phase')=='preparing' or 调用.get('callId') in 见过:
            continue
        下标+=1
        格={'index':下标,'kind':'tool','callId':调用.get('callId'),'timeSeconds':None,'startedAt':有限时间(调用.get('time'))}
        格.update(摘要调用(调用.get('name') or '',调用.get('argsRaw') or ''))
        格['inputDetail']=调用.get('argsRaw')
        已铺列表=[{'absTime':None,'toolName':调用.get('name'),'callId':调用.get('callId'),'subCalls':调用.get('subCalls'),'cell':格}]
        for 已铺 in 展开子调用(调用.get('subCalls'),下标):
            已铺列表.append(已铺)
            下标=已铺['cell']['index']
        if 调用.get('step',0)>0:
            推步骤(调用.get('turn'),调用.get('step'),已铺列表)
        else:
            for 已铺 in 已铺列表:
                推消息(调用.get('turn'),已铺)
    序幕=轮次表.get(0)
    if 序幕 is not None:
        del 轮次表[0]
        第一=轮次表.get(1)
        if 第一 is None:
            第一={'groups':[]}
        第一['groups']=序幕['groups']+第一['groups']
        轮次表[1]=第一
    if isinstance(模式表,dict):
        for 桶项 in list(轮次表.values())+独立压缩:
            for 组 in 桶项['groups']:
                for 已铺 in 组['laid']:
                    if 已铺.get('callId') is None:
                        continue
                    模式=模式表.get(已铺['callId'])
                    if 模式 is not None:
                        已铺['cell']['schemaDetail']=json.dumps(模式,indent=2,ensure_ascii=False)
    结果=[]
    for 回合,桶项 in 轮次表.items():
        结果.append(转轮次模型(回合,桶项))
    for 桶项 in 独立压缩:
        结果.append(转轮次模型(None,桶项))
    结果.sort(key=首格下标)
    return 结果

def 追加轨迹流式布局(轮次列表,流式,最后下标):
    '把变化中的 in-flight 助手单元格接到已定稿布局上'
    if 流式 is None:
        return 轮次列表
    部分=派生轨迹布局({'nodes':[],'partial':流式,'runningCalls':[]})
    if len(部分)==0:
        return 轮次列表
    流式轮=部分[0]
    流过={
        'turn':流式轮['turn'],
        'groups':[{
            'title':组['title'],
            **({'description':组['description']} if 'description' in 组 else {}),
            'cells':[{**格,'index':格['index']+最后下标} for 格 in 组['cells']],
        } for 组 in 流式轮['groups']],
    }
    回合下标=-1
    for 位,轮次 in enumerate(轮次列表):
        if 轮次['turn']==流过['turn']:
            回合下标=位
            break
    if 回合下标==-1:
        return list(轮次列表)+[流过]
    当前=轮次列表[回合下标]
    组列表=list(当前['groups'])
    for 流组 in 流过['groups']:
        组下标=-1
        for 位,组 in enumerate(组列表):
            if 组['title']==流组['title']:
                组下标=位
                break
        if 组下标==-1:
            组列表.append(流组)
            continue
        组=组列表[组下标]
        流式调用=set(格['callId'] for 格 in 流组['cells'] if 格.get('callId') is not None)
        组列表[组下标]={
            'title':流组['title'],
            **({'description':流组['description']} if 'description' in 流组 else {}),
            'cells':[格 for 格 in 组['cells'] if 格.get('requestOnly') is not True and (格.get('callId') is None or 格['callId'] not in 流式调用)]+流组['cells'],
        }
    更新=list(轮次列表)
    更新[回合下标]={'turn':当前['turn'],'groups':组列表}
    return 更新
