import json as _json#解析工具参数
from .已呈现 import 是否已呈现数据,是否已呈现文件,路径末段 as _已呈现路径末段#已呈现校验
from .改动 import 是否改动事件#改动事件

__all__=[#仅中文公开名
    '收口产出',
    '收口已呈现',
    '收口改动',
    '选出产出文件',
    '交付物定义',
    '交付物错误',
    '路径末段',
    '产出文件提及',
    '唯一末段路径',
    '是否追加面事件',
]#公开面结束

表面事件类型=frozenset({'user/message','assistant/message','tool/result'})#可进表面的事件类型

class 交付物错误(Exception):
    """本包异常基类。"""

def 是否追加面事件(事件):#表面且操作为追加
    """对齐 session/surface 的 isAppendSurfaceEvent。"""
    if 事件['type'] not in 表面事件类型:#类型不对
        return False#否
    return 事件['surfaceOp']=='append' if 'surfaceOp' in 事件 else False#追加

def _是否记录(值):#对象且非列表
    """窄化为 dict。"""
    return isinstance(值,dict)#是

def _路径值(值):#非空白路径
    """保留工具收到的精确拼写。"""
    return 值 if isinstance(值,str) and len(值.strip())>0 else None#有效

def _合法编辑参数(参数):#edit 字段
    """old/new 字符串且不同。"""
    if not isinstance(参数.get('old_string'),str) or len(参数['old_string'])==0:#旧串
        return False#否
    if not isinstance(参数.get('new_string'),str):#新串
        return False#否
    if 参数['old_string']==参数['new_string']:#相同
        return False#否
    全替=参数['replace_all'] if 'replace_all' in 参数 else None#全替
    return 全替 is None or isinstance(全替,bool)#合法

def _编辑器变更路径(参数):#str_replace_editor
    """仅完整变更命令。"""
    路径=_路径值(参数['path'] if 'path' in 参数 else None)#路径
    if 路径 is None:#空
        return None#否
    命令=参数['command'] if 'command' in 参数 else None#命令
    if 命令=='create':#创建
        return 路径 if isinstance(参数.get('file_text'),str) else None#有正文
    if 命令=='str_replace':#替换
        旧=参数['old_str'] if 'old_str' in 参数 else None#旧
        新=参数['new_str'] if 'new_str' in 参数 else None#新
        if not isinstance(旧,str) or len(旧)==0:#旧串
            return None#否
        if 新 is not None and not isinstance(新,str):#新串类型
            return None#否
        return 路径#路径
    if 命令=='insert':#插入
        行=参数['insert_line'] if 'insert_line' in 参数 else None#行
        新=参数['new_str'] if 'new_str' in 参数 else None#新
        if not isinstance(行,int) or 行<0 or not isinstance(新,str):#形态
            return None#否
        return 路径#路径
    return None#其它

def _变更路径(名,参数原文):#从工具参数取路径
    """受支持第一方变更才返回路径。"""
    try:#解析
        参数=_json.loads(参数原文)#JSON
    except Exception:#非法
        return None#空
    if not _是否记录(参数):#非对象
        return None#空
    if 名=='write':#写
        return _路径值(参数['file_path'] if 'file_path' in 参数 else None) if isinstance(参数.get('content'),str) else None#有内容
    if 名=='edit':#改
        return _路径值(参数['file_path'] if 'file_path' in 参数 else None) if _合法编辑参数(参数) else None#合法
    if 名=='str_replace_editor':#编辑器
        return _编辑器变更路径(参数)#命令
    return None#其它

def 收口产出(数据,序号=None):#读一个回合收口时应列出的产出路径
    """按首次出现顺序；没写过则为空。序号为 None 不过滤更晚结算。"""
    if 数据 is None:#尚未发布
        return []#无产出
    产出列表=数据['produced'] if 'produced' in 数据 and 数据['produced'] is not None else []#产出项
    路径表=[]#按首次出现累积
    已见=set()#已见过的路径
    for 产出 in 产出列表:#扫产出项
        路径=产出['path']#路径
        if 序号 is not None and 产出['seq']>序号:#晚于收口
            continue#跳过
        if 路径 in 已见:#已见
            continue#跳过
        已见.add(路径)#记下
        路径表.append(路径)#追加
    return 路径表#路径

def 选出产出文件(所有者):#有产出才认领回合尾链
    """没有产出则 null（此处 None）。属主为 dict。"""
    回合=所有者['turn'] if 'turn' in 所有者 else None#回合
    数据面=回合['data'] if 回合 is not None and 'data' in 回合 else None#数据面 dict
    if 数据面 is None:#无
        数据=None#空
    elif hasattr(数据面,'get'):#Map 或 dict
        数据=数据面.get('deliverables') if callable(getattr(数据面,'get',None)) else (数据面['deliverables'] if 'deliverables' in 数据面 else None)#取
    else:#无
        数据=None#空
    序号=所有者['seq'] if 'seq' in 所有者 else None#收口序号
    路径表=收口产出(数据,序号)#过滤
    if len(路径表)==0:#无产出
        return None#拒绝
    return 路径表#路径

def _交付数据(所有者):#读 deliverables 回合数据
    """属主 turn.data。"""
    回合=所有者['turn'] if 'turn' in 所有者 else None#回合
    数据面=回合['data'] if 回合 is not None and 'data' in 回合 else None#数据面
    if 数据面 is None:#无
        return None#空
    if hasattr(数据面,'get') and callable(数据面.get):#Map
        return 数据面.get('deliverables')#取
    return 数据面['deliverables'] if 'deliverables' in 数据面 else None#dict

def 收口已呈现(所有者):#收口前每条路径的最新声明
    """按首次出现路径顺序的可回放交付。属主为 dict。"""
    数据=_交付数据(所有者)#产出数据
    序号=所有者['seq'] if 'seq' in 所有者 else None#收口序号
    已呈现列表=数据['presented'] if 数据 is not None and 'presented' in 数据 and 数据['presented'] is not None else []#已呈现
    文件表={}#路径 → 最新声明（保序）
    for 项 in 已呈现列表:#扫
        if 序号 is not None and 项['seq']>=序号:#收口及之后排除
            continue#跳过
        文件表[项['path']]=项#后写覆盖
    return list(文件表.values())#保序值

def 收口改动(所有者):#回合最新改动公告
    """宿主未记录则为 None。"""
    数据=_交付数据(所有者)#数据
    if 数据 is None or 'changes' not in 数据 or 数据['changes'] is None:#无
        return None#空
    return 数据['changes']#改动

def 匹配(事件):#判定事件是否属于本节点
    """turn/start 开节点；tool/call、presented、workspace/changes 与追加面 tool/result 为 update。"""
    类型=事件['type']#类型
    数据=事件['data'] if 'data' in 事件 and 事件['data'] is not None else {}#数据
    if 类型=='turn/start':#回合开始
        return {'id':str(数据['turn'] if 'turn' in 数据 else None),'role':'start'}#开节点
    if 类型=='tool/call':#工具调用
        return {'id':str(数据['turn'] if 'turn' in 数据 else None),'role':'update'}#update
    if 类型=='deliverables/presented':#已呈现交付
        if not 是否已呈现数据(数据):#非法
            return None#忽略
        return {'id':str(数据['turn'] if 'turn' in 数据 else None),'role':'update'}#update
    if 类型=='workspace/changes':#改动公告
        if not 是否改动事件(数据):#非法
            return None#忽略
        return {'id':str(数据['turn'] if 'turn' in 数据 else None),'role':'update'}#update
    if 类型=='tool/result' and 是否追加面事件(事件):#追加面结果
        return {'id':str(数据['turn'] if 'turn' in 数据 else None),'role':'update'}#update
    return None#忽略

def 起始(上下文,匹配结果):#用 turn/start 建折叠状态
    """开节点必须是 turn/start。"""
    事件=匹配结果['event']#事件
    if 事件['type']!='turn/start':#必须
        raise 交付物错误('deliverables start requires turn/start')#开节点必须是 turn/start
    数据=事件['data'] if 'data' in 事件 and 事件['data'] is not None else {}#数据
    return {'turn':数据['turn'] if 'turn' in 数据 else None,'calls':{},'produced':[]}#空表

def 更新(上下文,匹配结果):#按调用与结果累积产出路径
    """调用记下变更路径；成功结果追加；已呈现与改动事件写入。"""
    状态=上下文['state'] if 'state' in 上下文 and 上下文['state'] is not None else {}#状态
    事件=匹配结果['event']#事件
    类型=事件['type']#类型
    if 类型=='workspace/changes':#改动公告
        新状态=dict(状态)#拷贝
        新状态['changes']={'seq':事件['seq']}#记下序号
        return 新状态#返回
    if 类型=='deliverables/presented':#已呈现交付
        数据=事件['data'] if 'data' in 事件 and 事件['data'] is not None else {}#数据
        文件表=数据['files'] if 'files' in 数据 and 数据['files'] is not None else []#文件
        序号=事件['seq']#事件序号
        本批=[]#本批已呈现
        for 下标,文件 in enumerate(文件表):#按下标
            if 是否已呈现文件(文件):#合法
                项=dict(文件)#浅拷贝
                项['seq']=序号#序号
                项['index']=下标#下标
                本批.append(项)#收下
        if len(本批)==0:#无合法
            return 状态#不变
        新状态=dict(状态)#拷贝
        已有=状态['presented'] if 'presented' in 状态 and 状态['presented'] is not None else []#已有
        新状态['presented']=list(已有)+本批#接到末尾
        return 新状态#返回
    if 类型=='tool/call':#调用发出
        调用表=dict(状态['calls'] if 'calls' in 状态 and 状态['calls'] is not None else {})#拷贝
        数据=事件['data'] if 'data' in 事件 and 事件['data'] is not None else {}#数据
        名=数据['name'] if 'name' in 数据 else ''#名
        参数=数据['arguments'] if 'arguments' in 数据 else ''#参数
        调用表[str(数据['callId'] if 'callId' in 数据 else None)]=_变更路径(名,参数)#记下路径
        新状态=dict(状态)#拷贝
        新状态['calls']=调用表#写回
        return 新状态#返回
    if 类型!='tool/result':#不是结果
        return 状态#不变
    数据=事件['data'] if 'data' in 事件 and 事件['data'] is not None else {}#数据
    消息=数据['message'] if 'message' in 数据 and 数据['message'] is not None else {}#消息
    内容=消息['content'] if 'content' in 消息 and 消息['content'] is not None else []#内容
    结果块=内容[0] if len(内容)>0 else {}#首块
    if 'isError' in 结果块 and 结果块['isError'] is True:#失败
        return 状态#不贡献
    来源=消息['source'] if 'source' in 消息 else None#来源
    调用来源=来源['callId'] if 来源 is not None and 'callId' in 来源 else None#callId
    调用标识=str(调用来源)#字符串
    调用表=状态['calls'] if 'calls' in 状态 and 状态['calls'] is not None else {}#调用表
    路径=调用表[调用标识] if 调用标识 in 调用表 else None#该次路径
    if 路径 is None:#无路径
        return 状态#不变
    新状态=dict(状态)#拷贝
    已有=状态['produced'] if 'produced' in 状态 and 状态['produced'] is not None else []#已累积
    新状态['produced']=list(已有)+[{'seq':事件['seq'],'path':路径}]#接到末尾
    return 新状态#返回

def 建位置数据(上下文,范围,先前=None):#写回合位置数据
    """非回合范围或尚无状态则 null；未变则复用先前。"""
    状态=上下文['state'] if 'state' in 上下文 else None#状态
    if 范围!='turn' or 状态 is None:#不写
        return None#null
    值={'produced':状态['produced'] if 'produced' in 状态 else None}#已累积产出
    if 'presented' in 状态 and 状态['presented'] is not None:#有已呈现
        值['presented']=状态['presented']#已呈现
    if 'changes' in 状态 and 状态['changes'] is not None:#有改动
        值['changes']=状态['changes']#改动
    if (先前 is not None and 'kind' in 先前 and 先前['kind']=='turn'
        and 先前.get('turn')==状态.get('turn') and 先前.get('key')=='deliverables'
        and 先前.get('value')==值):#未变——浅比不够，按字段
        旧值=先前['value'] if 'value' in 先前 else None#旧
        if (旧值 is not None and 旧值.get('produced') is 状态.get('produced')
            and 旧值.get('presented') is 状态.get('presented')
            and 旧值.get('changes') is 状态.get('changes')):#引用同
            return 先前#复用
    return {#回合位置
        'kind':'turn',#回合
        'turn':状态['turn'] if 'turn' in 状态 else None,#回合号
        'key':'deliverables',#本贡献键
        'value':值,#已累积
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
    return _已呈现路径末段(路径)#与已呈现模块同算法

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
        def 打开():#打开该路径
            """转调打开文件。"""
            打开文件(路径)#打开
            return None#无返回
        return {'open':打开,'label':标签(路径),'title':路径}#打开面
    return {'resolve':解析}#解析器
