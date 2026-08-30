"""按回合折叠的产出文件定义与读取器。



对齐上游 `ui-deliverables/src/client/turn-deliverables.ts`。公开面仅中文名。

仅客户端、不看模型正文：词表来自变更工具随附的 locations。

"""



__all__=[#仅中文公开名

    '产出路径于视图',

    '收口产出',

    '选出产出文件',

    '交付物定义',

    '路径末段',

    '产出文件提及',

    '唯一末段路径',

    '是否追加面事件',

]#公开面结束



表面事件类型=frozenset({'user/message','assistant/message','tool/result'})#可进表面的事件类型



def 取字段(对象,键,缺省=None):#从映射或对象读字段

    """从映射或对象读字段，缺席为缺省。"""

    if 对象 is None:#空

        return 缺省#缺席

    if isinstance(对象,dict):#映射

        if 键 in 对象:#自有键

            return 对象[键]#值

        return 缺席#缺席

    return getattr(对象,键,缺省)#属性



def 是否追加面事件(事件):#表面且操作为追加

    """对齐 session/surface 的 isAppendSurfaceEvent。"""

    if 取字段(事件,'type') not in 表面事件类型:#类型不对

        return False#否

    return 取字段(事件,'surfaceOp')=='append'#追加



def 产出路径于视图(视图):#从调用视图取出产出路径

    """按渲染意图：diff 或 generic+edit。"""

    if 视图 is None:#无视图

        return []#无产出

    if 取字段(视图,'card')=='diff':#diff 卡片

        return [取字段(位置,'path') for 位置 in (取字段(视图,'locations') or [])]#locations 路径

    if 取字段(视图,'card')=='generic' and 取字段(视图,'kind')=='edit':#generic edit

        return [取字段(位置,'path') for 位置 in (取字段(视图,'locations') or [])]#locations 路径

    return []#其余不产出



def 收口产出(数据,序号=None):#读一个回合收口时应列出的产出路径

    """按首次出现顺序；没写过则为空。"""

    if 数据 is None:#尚未发布

        return []#无产出

    if 序号 is None:#不过滤更晚结算

        序号=float('inf')#无穷大

    路径表=[]#按首次出现累积

    已见=set()#已见过的路径

    for 产出 in (取字段(数据,'produced') or []):#扫产出项

        路径=取字段(产出,'path')#路径

        if 取字段(产出,'seq')>序号 or 路径 in 已见:#晚于收口或已见

            continue#跳过

        已见.add(路径)#记下

        路径表.append(路径)#追加

    return 路径表#路径



def 选出产出文件(所有者):#有产出才认领回合尾链

    """没有产出则 null（此处 None）。"""

    回合=取字段(所有者,'turn')#回合

    数据面=取字段(回合,'data') if 回合 is not None else None#数据面

    if 数据面 is not None and hasattr(数据面,'get'):#有 get

        数据=数据面.get('deliverables')#产出数据

    else:#映射或无

        数据=取字段(数据面,'deliverables') if isinstance(数据面,dict) else None#读

    路径表=收口产出(数据,取字段(所有者,'seq'))#过滤

    return None if len(路径表)==0 else 路径表#无则拒绝



def 匹配(事件):#判定事件是否属于本节点

    """turn/start 开节点；tool/call 与追加面 tool/result 为 update。"""

    类型=取字段(事件,'type')#类型

    数据=取字段(事件,'data') or {}#数据

    if 类型=='turn/start':#回合开始

        return {'id':str(取字段(数据,'turn')),'role':'start'}#开节点

    if 类型=='tool/call':#工具调用

        return {'id':str(取字段(数据,'turn')),'role':'update'}#update

    if 类型=='tool/result' and 是否追加面事件(事件):#追加面结果

        return {'id':str(取字段(数据,'turn')),'role':'update'}#update

    return None#忽略



def 起始(上下文,匹配结果):#用 turn/start 建折叠状态

    """开节点必须是 turn/start。"""

    事件=取字段(匹配结果,'event')#事件

    if 取字段(事件,'type')!='turn/start':#必须

        raise Exception('deliverables start requires turn/start')#开节点必须是 turn/start

    return {'turn':取字段(取字段(事件,'data'),'turn'),'calls':{},'produced':[]}#空表



def 更新(上下文,匹配结果):#按调用与结果累积产出路径

    """调用记下 callView；成功结果追加路径。"""

    状态=取字段(上下文,'state') or {}#状态

    事件=取字段(匹配结果,'event')#事件

    类型=取字段(事件,'type')#类型

    if 类型=='tool/call':#调用发出

        调用表=dict(取字段(状态,'calls') or {})#拷贝

        视图=取字段(匹配结果,'view')#视图

        调用视图=取字段(视图,'view') if 取字段(视图,'for')=='call' else None#call 视图

        调用表[str(取字段(取字段(事件,'data'),'callId'))]=调用视图#记下

        新状态=dict(状态)#拷贝

        新状态['calls']=调用表#写回

        return 新状态#返回

    if 类型!='tool/result':#不是结果

        return 状态#不变

    消息=取字段(取字段(事件,'data'),'message') or {}#消息

    内容=取字段(消息,'content') or []#内容

    结果块=内容[0] if len(内容)>0 else {}#首块

    if 取字段(结果块,'isError') is True:#失败

        return 状态#不贡献

    调用来源=取字段(取字段(消息,'source'),'callId')#callId

    调用标识=str(调用来源)#字符串

    调用表=取字段(状态,'calls') or {}#调用表

    追加=[{'seq':取字段(事件,'seq'),'path':路径} for 路径 in 产出路径于视图(调用表.get(调用标识))]#路径带序号

    if len(追加)==0:#无路径

        return 状态#不变

    新状态=dict(状态)#拷贝

    新状态['produced']=list(取字段(状态,'produced') or [])+追加#接到末尾

    return 新状态#返回



def 建位置数据(上下文,范围):#写回合位置数据

    """非回合范围或尚无状态则 null。"""

    状态=取字段(上下文,'state')#状态

    if 范围!='turn' or 状态 is None:#不写

        return None#null

    return {#回合位置

        'kind':'turn',#回合

        'turn':取字段(状态,'turn'),#回合号

        'key':'deliverables',#本贡献键

        'value':{'produced':取字段(状态,'produced')},#已累积

    }#位置结束



交付物定义={#产出文件会话节点定义

    'kind':'deliverables',#本贡献 kind

    'match':匹配,#匹配

    'start':起始,#起始

    'update':更新,#更新

    'buildLocationData':建位置数据,#位置数据

}#定义结束



def 路径末段(路径):#取路径末段

    """最后一段；没有分隔符则整串。"""

    斜=路径.rfind('/')#正斜杠

    反=路径.rfind('\\')#反斜杠

    位=斜 if 斜>反 else 反#最后分隔

    return 路径 if 位==-1 else 路径[位+1:]#末段



def 唯一末段路径(路径表,值):#末段恰好等于 value 的那一条

    """对不上或多于一条则为 None。"""

    命中=[路径 for 路径 in 路径表 if 路径末段(路径)==值]#末段匹配

    return 命中[0] if len(命中)==1 else None#恰好一条



def 产出文件提及(路径表,打开文件,标签):#给收口正文一套产出路径提及词表

    """MarkdownText 消费的解析器。"""

    def 解析(值):#把行内记号解析成可打开路径

        """先精确路径，否则唯一末段。"""

        路径=值 if 值 in 路径表 else 唯一末段路径(路径表,值)#解析

        if 路径 is None:#对不上

            return None#惰性

        return {'open':lambda:打开文件(路径),'label':标签(路径),'title':路径}#打开面

    return {'resolve':解析}#解析器


