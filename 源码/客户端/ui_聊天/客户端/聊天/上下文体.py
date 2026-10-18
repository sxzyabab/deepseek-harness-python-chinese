import json
from ....ui_基础界面组件.markdown.json块 import json块
from ....ui_对话.异常 import 标样式模块
from .用披露 import 注入聊天样式

__all__=['不透明体','须知体','选择上下文体']

样式模块='context-body'
字数上限=20000
条目上限=200


def 是记录(值):
    '普通对象。数组不算'
    return isinstance(值,dict)


def 有界文本(文本,翻译):
    '超过展示上限就截断并写总数'
    if not isinstance(文本,str):
        文本='' if 文本 is None else str(文本)
    if len(文本)<=字数上限:
        return 文本
    return 文本[:字数上限]+'\n'+翻译('json.truncated',{'total':len(文本)})


def 字段值(值,翻译):
    '字符串原样。数字和布尔转字。其余压成 JSON'
    if isinstance(值,str):
        文本=值
    elif isinstance(值,(int,float,bool)) and not isinstance(值,bool) or isinstance(值,bool):
        文本=str(值)
    else:
        文本=json.dumps(值,ensure_ascii=False)
    return 有界文本(文本,翻译)


def 内容段(内容):
    '相邻文本并成一段。不认识的块单独留下'
    段=[]
    for 块 in 内容 if isinstance(内容,list) else []:
        if isinstance(块,dict) and 块.get('type')=='text':
            if len(段)>0 and 'text' in 段[-1]:
                段[-1]['text']+=块.get('text') or ''
            else:
                段.append({'text':块.get('text') or ''})
        else:
            段.append({'block':块})
    return 段


def 未知块(内容):
    '只留下这份界面不认识的块'
    return [段['block'] for 段 in 内容段(内容) if 'block' in 段]


def 画未知块(文档,窗口,块,翻译):
    '一个不认识的块画成 JSON'
    def 截断(总):
        '截断脚注'
        return 翻译('json.truncated',{'total':总})
    视图=json块({
        'window':窗口,
        'label':翻译('message.unknownBlock'),
        'payload':块,
        'truncatedLabel':截断,
    })
    return 视图.渲染()


def 画面对模型(文档,窗口,内容,翻译):
    '按模型收到的顺序画文本和未知块'
    盒=文档.createDocumentFragment()
    for 段 in 内容段(内容):
        if 'text' in 段:
            if 段['text']=='':
                continue
            预=文档.createElement('pre')
            预.className='text'
            标样式模块(预,样式模块)
            预.setAttribute('data-context-text','')
            预.textContent=有界文本(段['text'],翻译)
            盒.appendChild(预)
        else:
            画出=画未知块(文档,窗口,段['block'],翻译)
            if 画出 is not None:
                盒.appendChild(画出)
    return 盒


def 画来源字段(文档,来源,已渲染形态,翻译):
    'kind 不画。专用正文已经表达 form 时也不再画 form'
    if not 是记录(来源):
        return None
    隐藏=['kind','form'] if 已渲染形态 else ['kind']
    盒=文档.createElement('dl')
    盒.className='fields'
    标样式模块(盒,样式模块)
    盒.setAttribute('data-context-fields','')
    有=False
    for 键,值 in 来源.items():
        if 键 in 隐藏:
            continue
        有=True
        行=文档.createElement('div')
        行.className='field'
        标样式模块(行,样式模块)
        名=文档.createElement('dt')
        名.className='fieldKey'
        标样式模块(名,样式模块)
        名.textContent=str(键)
        价=文档.createElement('dd')
        价.className='fieldValue'
        标样式模块(价,样式模块)
        价.textContent=字段值(值,翻译)
        行.appendChild(名)
        行.appendChild(价)
        盒.appendChild(行)
    if not 有:
        return None
    return 盒


def 不透明体(文档,窗口,内容,来源,翻译):
    '不认识的形态：模型文本加上来源字段'
    注入聊天样式(文档,样式模块,'上下文体.module.css')
    盒=文档.createDocumentFragment()
    盒.appendChild(画面对模型(文档,窗口,内容,翻译))
    字段=画来源字段(文档,来源,False,翻译)
    if 字段 is not None:
        盒.appendChild(字段)
    return 盒


def 须知体(文档,窗口,内容,翻译):
    '须知正文就是模型看到的文本'
    注入聊天样式(文档,样式模块,'上下文体.module.css')
    return 画面对模型(文档,窗口,内容,翻译)


def 指令变更(来源):
    '整份都可读才返回。认不出的动作整份作废'
    if not 是记录(来源) or not isinstance(来源.get('changes'),list):
        return None
    变更=[]
    见过=set()
    for 项 in 来源['changes']:
        if not 是记录(项):
            return None
        路径=项.get('path')
        动作=项.get('action')
        if not isinstance(路径,str) or 路径=='':
            return None
        if 动作 not in ('set','replace','remove'):
            return None
        if 路径 in 见过:
            continue
        见过.add(路径)
        条={'action':动作,'path':路径}
        if isinstance(项.get('digest'),str):
            条['digest']=项['digest']
        变更.append(条)
    if len(变更)==0:
        return None
    return 变更


def 指令动作键(动作,基线):
    '删除、基线载入、新增、更新各用一条文案'
    if 动作=='remove':
        return 'message.context.instructions.removed'
    if 基线:
        return 'message.context.instructions.loaded'
    if 动作=='set':
        return 'message.context.instructions.added'
    return 'message.context.instructions.updated'


def 画指令(文档,窗口,内容,来源,翻译):
    '文件清单，然后是模型文本'
    变更=指令变更(来源)
    if 变更 is None:
        return 不透明体(文档,窗口,内容,来源,翻译)
    基线=是记录(来源) and 来源.get('baseline') is True
    盒=文档.createDocumentFragment()
    表=文档.createElement('ul')
    表.className='files'
    标样式模块(表,样式模块)
    表.setAttribute('data-context-files','')
    for 条 in 变更:
        项=文档.createElement('li')
        项.className='file'
        标样式模块(项,样式模块)
        if isinstance(条.get('digest'),str):
            项.setAttribute('title',条['digest'])
        路=文档.createElement('span')
        路.className='filePath'
        标样式模块(路,样式模块)
        路.textContent=条['path']
        动=文档.createElement('span')
        动.className='fileAction'
        标样式模块(动,样式模块)
        动.textContent=翻译(指令动作键(条['action'],基线))
        项.appendChild(路)
        项.appendChild(动)
        表.appendChild(项)
    盒.appendChild(表)
    盒.appendChild(画面对模型(文档,窗口,内容,翻译))
    return 盒


def 目录条目(来源):
    '空列表是一份真目录。读不出形状才作废'
    if not 是记录(来源) or not isinstance(来源.get('entries'),list):
        return None
    条目=[]
    for 项 in 来源['entries']:
        if not 是记录(项):
            return None
        名=项.get('name')
        描述=项.get('description')
        if not isinstance(名,str) or 名=='' or not isinstance(描述,str):
            return None
        条目.append({'name':名,'description':描述})
    return 条目


def 画目录(文档,窗口,内容,来源,翻译):
    '目录替换模型原文。未知块仍留下'
    条目=目录条目(来源)
    if 条目 is None:
        return 不透明体(文档,窗口,内容,来源,翻译)
    盒=文档.createDocumentFragment()
    if 是记录(来源) and 来源.get('update') is True:
        注=文档.createElement('p')
        注.className='catalogNotice'
        标样式模块(注,样式模块)
        注.setAttribute('data-context-catalog-update','')
        注.textContent=翻译('message.context.catalog.replaced')
        盒.appendChild(注)
    所示=条目[:条目上限]
    表=文档.createElement('ul')
    表.className='entries'
    标样式模块(表,样式模块)
    表.setAttribute('data-context-entries','')
    for 条 in 所示:
        项=文档.createElement('li')
        项.className='entry'
        标样式模块(项,样式模块)
        名=文档.createElement('code')
        名.className='entryName'
        标样式模块(名,样式模块)
        名.textContent=条['name']
        述=文档.createElement('span')
        述.className='entryDescription'
        标样式模块(述,样式模块)
        述.textContent=条['description']
        项.appendChild(名)
        项.appendChild(述)
        表.appendChild(项)
    盒.appendChild(表)
    if len(所示)<len(条目):
        注=文档.createElement('p')
        注.className='catalogNotice'
        标样式模块(注,样式模块)
        注.setAttribute('data-context-entries-truncated','')
        注.textContent=翻译('message.context.catalog.more',{'count':len(条目)-len(所示)})
        盒.appendChild(注)
    for 块 in 未知块(内容):
        画出=画未知块(文档,窗口,块,翻译)
        if 画出 is not None:
            盒.appendChild(画出)
    return 盒


def 快照节(来源):
    '每一节都要有名字和文本'
    if not 是记录(来源) or not isinstance(来源.get('sections'),list):
        return None
    节=[]
    for 项 in 来源['sections']:
        if not 是记录(项):
            return None
        名=项.get('name')
        文=项.get('text')
        if not isinstance(名,str) or 名=='' or not isinstance(文,str):
            return None
        节.append({'name':名,'text':文})
    if len(节)==0:
        return None
    return 节


def 画快照(文档,窗口,来源,翻译):
    '按生产者切开的节，不再把拼接后的原文再贴一遍'
    节=快照节(来源)
    if 节 is None:
        return None
    盒=文档.createDocumentFragment()
    注=文档.createElement('p')
    注.className='catalogNotice'
    标样式模块(注,样式模块)
    注.setAttribute('data-context-snapshot-supersedes','')
    注.textContent=翻译('message.context.snapshot.supersedes')
    盒.appendChild(注)
    表=文档.createElement('dl')
    表.className='sections'
    标样式模块(表,样式模块)
    表.setAttribute('data-context-sections','')
    for 条 in 节:
        行=文档.createElement('div')
        行.className='section'
        标样式模块(行,样式模块)
        名=文档.createElement('dt')
        名.className='sectionName'
        标样式模块(名,样式模块)
        名.textContent=条['name']
        文=文档.createElement('dd')
        文.className='sectionText'
        标样式模块(文,样式模块)
        文.textContent=有界文本(条['text'],翻译)
        行.appendChild(名)
        行.appendChild(文)
        表.appendChild(行)
    盒.appendChild(表)
    return 盒


def 中继发送者(来源):
    '发送方会话标识'
    if not 是记录(来源):
        return None
    发送=来源.get('senderSessionId')
    if isinstance(发送,str) and 发送!='':
        return 发送
    return None


def 画中继(文档,窗口,内容,来源,翻译):
    '先写发送方，再写它说的话'
    发送=中继发送者(来源)
    if 发送 is None:
        return 不透明体(文档,窗口,内容,来源,翻译)
    盒=文档.createDocumentFragment()
    段=文档.createElement('p')
    段.className='relaySender'
    标样式模块(段,样式模块)
    段.setAttribute('data-context-relay-sender','')
    段.textContent=翻译('message.context.relay.from',{'session':发送})
    盒.appendChild(段)
    盒.appendChild(画面对模型(文档,窗口,内容,翻译))
    return 盒


def 召回会话(来源):
    '缺保留数、省略数或是否截断，整份作废'
    if not 是记录(来源) or not isinstance(来源.get('references'),list):
        return None
    会话=[]
    for 项 in 来源['references']:
        if not 是记录(项):
            return None
        标签=项.get('label')
        保留=项.get('retainedMessages')
        省略=项.get('omittedMessages')
        截断=项.get('truncated')
        if not isinstance(标签,str) or 标签=='':
            return None
        if isinstance(保留,bool) or not isinstance(保留,int):
            return None
        if isinstance(省略,bool) or not isinstance(省略,int):
            return None
        if not isinstance(截断,bool):
            return None
        会话.append({'label':标签,'retained':保留,'omitted':省略,'truncated':截断})
    if len(会话)==0:
        return None
    return 会话


def 画召回(文档,窗口,内容,来源,翻译):
    '先写每段召回留下了多少，再写材料本身'
    会话=召回会话(来源)
    if 会话 is None:
        return 不透明体(文档,窗口,内容,来源,翻译)
    盒=文档.createDocumentFragment()
    表=文档.createElement('ul')
    表.className='recalls'
    标样式模块(表,样式模块)
    表.setAttribute('data-context-recalls','')
    for 条 in 会话:
        项=文档.createElement('li')
        项.className='recall'
        标样式模块(项,样式模块)
        标=文档.createElement('span')
        标.className='recallLabel'
        标样式模块(标,样式模块)
        标.textContent=条['label']
        数=文档.createElement('span')
        数.className='recallCounts'
        标样式模块(数,样式模块)
        数.textContent=翻译('message.context.recall.counts',{'retained':条['retained'],'omitted':条['omitted']})
        项.appendChild(标)
        项.appendChild(数)
        if 条['truncated']:
            截=文档.createElement('span')
            截.className='recallCounts'
            标样式模块(截,样式模块)
            截.textContent=翻译('message.context.recall.truncated')
            项.appendChild(截)
        表.appendChild(项)
    盒.appendChild(表)
    盒.appendChild(画面对模型(文档,窗口,内容,翻译))
    return 盒


def 须知摘要(来源):
    '折叠行上的一行说明'
    if not 是记录(来源):
        return None
    摘要=来源.get('summary')
    if isinstance(摘要,str) and 摘要!='':
        return 摘要
    return None


def 选择上下文体(形态,文档,窗口,内容,来源,翻译):
    '实际画出来的形态。读不出字段就退回不透明'
    注入聊天样式(文档,样式模块,'上下文体.module.css')
    不透明={'rendered':None,'summary':None,'body':不透明体(文档,窗口,内容,来源,翻译)}
    if 形态=='instructions':
        if 指令变更(来源) is None:
            return 不透明
        return {'rendered':'instructions','summary':None,'body':画指令(文档,窗口,内容,来源,翻译)}
    if 形态=='catalog':
        if 目录条目(来源) is None:
            return 不透明
        return {'rendered':'catalog','summary':None,'body':画目录(文档,窗口,内容,来源,翻译)}
    if 形态=='snapshot':
        体=画快照(文档,窗口,来源,翻译)
        if 体 is None:
            return 不透明
        return {'rendered':'snapshot','summary':None,'body':体}
    if 形态=='notice':
        摘要=须知摘要(来源)
        if 摘要 is None:
            return 不透明
        return {'rendered':'notice','summary':摘要,'body':须知体(文档,窗口,内容,翻译)}
    if 形态=='relay':
        if 中继发送者(来源) is None:
            return 不透明
        return {'rendered':'relay','summary':None,'body':画中继(文档,窗口,内容,来源,翻译)}
    if 形态=='recall':
        if 召回会话(来源) is None:
            return 不透明
        return {'rendered':'recall','summary':None,'body':画召回(文档,窗口,内容,来源,翻译)}
    if 形态 is None:
        return 不透明
    raise ValueError('unreachable context form: '+str(形态))
