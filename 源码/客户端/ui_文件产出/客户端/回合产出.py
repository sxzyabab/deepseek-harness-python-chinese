'一轮里产出的文件、已呈现文件和改动宣告'
import json
from ....内核.会话.表面 import 是否追加表面事件
from ....工具.工作区路径 import 是否绝对工作区路径
from ..改动 import 是否改动事件
from ..已呈现 import 是否已呈现数据,是否已呈现文件,路径末段

__all__=[
    '收口产出','选出产出文件','交付物定义','收口改动','收口已呈现','路径末段','产出文件提及',
]


def 是否记录(值):
    '解析后的参数对象'
    return isinstance(值,dict)


def 路径值(值):
    '非空白路径保留工具收到的拼写'
    if isinstance(值,str) and len(值.strip())>0:
        return 值
    return None


def 收口产出(数据,序号=None):
    '按首次出现顺序。没写过则为空。序号缺省不过滤更晚结算'
    if 数据 is None:
        return []
    if 序号 is None:
        序号=float('inf')
    路径表=[]
    见过=set()
    for 产出 in 数据['produced']:
        if 产出['seq']>序号 or 产出['path'] in 见过:
            continue
        见过.add(产出['path'])
        路径表.append(产出['path'])
    return 路径表


def 选出产出文件(所有者):
    '没有产出则 None'
    路径表=收口产出(所有者['turn']['data'].get('deliverables'),所有者['seq'])
    if len(路径表)==0:
        return None
    return 路径表


def 匹配(事件):
    'turn/start 开节点。调用、已呈现、改动和追加的工具结果是更新'
    if 事件['type']=='turn/start':
        return {'id':str(事件['data']['turn']),'role':'start'}
    if 事件['type']=='tool/call':
        return {'id':str(事件['data']['turn']),'role':'update'}
    if 事件['type']=='deliverables/presented':
        if 是否已呈现数据(事件['data']):
            return {'id':str(事件['data']['turn']),'role':'update'}
        return None
    if 事件['type']=='workspace/changes':
        if 是否改动事件(事件['data']):
            return {'id':str(事件['data']['turn']),'role':'update'}
        return None
    if 事件['type']=='tool/result' and 是否追加表面事件(事件):
        return {'id':str(事件['data']['turn']),'role':'update'}
    return None


def 起始(上下文,匹配结果):
    '开节点必须是 turn/start'
    if 匹配结果['event']['type']!='turn/start':
        raise Exception('deliverables start requires turn/start')
    return {'turn':匹配结果['event']['data']['turn'],'calls':{},'produced':[]}


def 更新(上下文,匹配结果):
    '调用记下变更路径。成功结果追加。已呈现和改动写入'
    状态=上下文['state']
    事件=匹配结果['event']
    if 事件['type']=='workspace/changes':
        return {**状态,'changes':{'seq':事件['seq']}}
    if 事件['type']=='deliverables/presented':
        文件表=事件['data']['files']
        序号=事件['seq']
        已呈现=[]
        下标=0
        while 下标<len(文件表):
            文件=文件表[下标]
            if 是否已呈现文件(文件):
                记下=dict(文件)
                记下['seq']=序号
                记下['index']=下标
                已呈现.append(记下)
            下标+=1
        if len(已呈现)==0:
            return 状态
        原有=状态['presented'] if 'presented' in 状态 and 状态['presented'] is not None else []
        return {**状态,'presented':[*原有,*已呈现]}
    if 事件['type']=='tool/call':
        调用=dict(状态['calls'])
        名=事件['data']['name']
        参数原文=事件['data']['arguments']
        变更=None
        try:
            参数=json.loads(参数原文)
        except Exception:
            参数=None
        if 是否记录(参数):
            if 名=='write':
                if isinstance(参数.get('content'),str):
                    变更=路径值(参数.get('file_path'))
            elif 名=='edit':
                旧文=参数.get('old_string')
                新文=参数.get('new_string')
                全部=参数.get('replace_all')
                合法=isinstance(旧文,str) and len(旧文)>0 and isinstance(新文,str) and 旧文!=新文 and ('replace_all' not in 参数 or isinstance(全部,bool))
                if 合法:
                    变更=路径值(参数.get('file_path'))
            elif 名=='str_replace_editor':
                编辑路径=路径值(参数.get('path'))
                if 编辑路径 is not None:
                    命令=参数.get('command')
                    if 命令=='create':
                        if isinstance(参数.get('file_text'),str):
                            变更=编辑路径
                    elif 命令=='str_replace':
                        旧串=参数.get('old_str')
                        新串=参数.get('new_str')
                        if isinstance(旧串,str) and len(旧串)>0 and ('new_str' not in 参数 or isinstance(新串,str)):
                            变更=编辑路径
                    elif 命令=='insert':
                        行号=参数.get('insert_line')
                        if isinstance(行号,int) and not isinstance(行号,bool) and 行号>=0 and isinstance(参数.get('new_str'),str):
                            变更=编辑路径
        调用[str(事件['data']['callId'])]=变更
        return {**状态,'calls':调用}
    if 事件['type']!='tool/result':
        return 状态
    if 事件['data']['message'].get('isError') is True:
        return 状态
    调用标识=str(事件['data']['message']['source']['callId'])
    if 调用标识 not in 状态['calls']:
        return 状态
    参数路径=状态['calls'][调用标识]
    if 参数路径 is None:
        return 状态
    元数据=事件['data'].get('meta')
    if not 是否记录(元数据) or 'path' not in 元数据:
        结果路径=参数路径
    elif isinstance(元数据.get('path'),str) and 是否绝对工作区路径(元数据['path']):
        结果路径=元数据['path']
    elif 是否绝对工作区路径(参数路径):
        结果路径=参数路径
    else:
        结果路径=None
    if 结果路径 is None:
        return 状态
    记下={'seq':事件['seq'],'path':结果路径}
    if 结果路径!=参数路径:
        记下['argumentPath']=参数路径
    return {**状态,'produced':[*状态['produced'],记下]}


def 建位置数据(上下文,范围,先前=None):
    '非回合范围或尚无状态则 None。未变则复用先前'
    状态=上下文.get('state')
    if 范围!='turn' or 状态 is None:
        return None
    if isinstance(先前,dict) and 先前.get('kind')=='turn' and 先前.get('turn')==状态['turn'] and 先前.get('key')=='deliverables':
        原值=先前.get('value')
        if isinstance(原值,dict) and 原值.get('produced') is 状态.get('produced') and 原值.get('presented') is 状态.get('presented') and 原值.get('changes') is 状态.get('changes'):
            return 先前
    值={'produced':状态['produced']}
    if 'presented' in 状态 and 状态['presented'] is not None:
        值['presented']=状态['presented']
    if 'changes' in 状态 and 状态['changes'] is not None:
        值['changes']=状态['changes']
    return {'kind':'turn','turn':状态['turn'],'key':'deliverables','value':值}


交付物定义={
    'kind':'deliverables',
    'match':匹配,
    'start':起始,
    'update':更新,
    'buildLocationData':建位置数据,
}


def 收口改动(所有者):
    '宿主没记录则为 None'
    数据=所有者['turn']['data'].get('deliverables')
    if not isinstance(数据,dict):
        return None
    return 数据.get('changes')


def 收口已呈现(所有者):
    '收口回复之前，每个路径留最后一次声明'
    数据=所有者['turn']['data'].get('deliverables')
    已呈现=[]
    if isinstance(数据,dict) and isinstance(数据.get('presented'),list):
        已呈现=数据['presented']
    按路径={}
    for 文件 in 已呈现:
        if 文件['seq']<所有者['seq']:
            按路径[文件['path']]=文件
    return list(按路径.values())


def 产出文件提及(路径表,打开文件,标签,操作=None):
    '行内代码对上唯一路径才可打开'
    if 操作 is None:
        操作=[]

    def 解析(值):
        '精确路径或末段只能对上一个目标'
        命中=set()
        for 路径 in 路径表:
            if 路径==值 or 路径末段(路径)==值:
                命中.add(路径)
        for 一项 in 操作:
            if 一项.get('argumentPath')==值:
                命中.add(一项['path'])
        if len(命中)!=1:
            return None
        路径=next(iter(命中))

        def 打开():
            '交给聊天视图打开这个路径'
            打开文件(路径)

        return {'open':打开,'label':标签(路径),'title':路径}

    return {'resolve':解析}
