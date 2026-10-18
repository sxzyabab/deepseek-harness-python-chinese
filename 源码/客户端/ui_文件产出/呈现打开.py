'提供改动摘要与对比，并打开经会话文件系统校验的已声明或已改动工作区文件'
import re
import threading
from urllib.parse import urlparse, parse_qs
from ...基础设施.通用工具 import 是否非负安全整数,紧凑json编码
from ...api.会话控制器.远程错误与并发 import 已中止,若已中止则抛出
from ...类型化远程调用.协议 import 取远程错误
from .已呈现 import 呈现打开路径,呈现宿主路径,是否已呈现数据,是否已呈现文件
from .改动 import 已改文件路径,改动对比路径,改动打开路径

__all__=['登记呈现打开']

数字形态=re.compile(r'^\d+$')


def 查询(请求):
    '取查询串里的第一个值'
    解析=urlparse(请求.get('url') or '')
    参数=parse_qs(解析.query)

    def 取(名):
        '缺席为 None'
        列=参数.get(名)
        if 列 is None or len(列)==0:
            return None
        return 列[0]

    return 取


def 文本应答(状态,正文):
    '纯文本应答，不缓存'
    return {
        'status':状态,
        'headers':{'content-type':'text/plain;charset=UTF-8','cache-control':'no-store'},
        'body':正文.encode('utf-8'),
    }


def 应答json(载荷):
    'JSON 应答，不缓存'
    return {
        'status':200,
        'headers':{'content-type':'application/json; charset=utf-8','cache-control':'no-store'},
        'body':紧凑json编码(载荷).encode('utf-8'),
    }


def 空应答(状态):
    '无正文'
    return {'status':状态,'headers':{'cache-control':'no-store'},'body':None}


def 坐标数(值):
    '纯数字且在安全整数内'
    if not isinstance(值,str) or 数字形态.match(值) is None:
        return None
    数=int(值)
    if not 是否非负安全整数(数):
        return None
    return 数


def 失败状态(错误):
    '找不到是 404，其余 500'
    远程=取远程错误(错误)
    码=None
    if 远程 is not None:
        码=远程.code
    elif isinstance(错误,BaseException):
        码=getattr(错误,'code',None)
    缺失=码 in (
        'session/not-found','workspace-file/not-found','workspace-file/not-regular-file',
        'SESSION_QUERY_SESSION_NOT_FOUND','SESSION_QUERY_EVENT_NOT_FOUND','ENOENT','ENOTDIR',
    )
    if 缺失:
        return 404
    return 500


def 停则抛(寿命,信号):
    '中止则抛出，让外层不再回失败正文'
    if 寿命.is_set():
        若已中止则抛出(寿命)
    若已中止则抛出(信号)


def 打开已校验(上下文,请求,路径,动作,寿命):
    '文件经会话文件系统往返校验。目录只做宿主映射'
    信号=请求.get('signal')
    停则抛(寿命,信号)
    映射=上下文.fs.宿主路径转进程路径(路径)
    解析=None
    if 映射 is not None:
        解析=上下文.fs.解析(映射,{'signal':信号})
    if 映射 is None or 上下文.fs.进程路径(解析)!=路径:
        return 文本应答(422,'Path has no verified Host path.')
    停则抛(寿命,信号)
    if 请求.get('method')=='GET':
        return 应答json(上下文.sessionController.workspacePathApplications({'path':路径},信号))
    应用=查询(请求)('application')
    参数={'path':路径}
    if 动作=='reveal':
        参数['action']='reveal'
    elif 应用 is not None:
        参数['application']=应用
    上下文.sessionController.openWorkspacePath(参数,信号)
    return 空应答(204)


def 处理呈现打开(上下文,请求,寿命):
    '打开一条已声明文件，或在 GET 时返回能打开它的应用'
    取=查询(请求)
    动作=取('action')
    if 动作 is None:
        动作='open'
    if 动作!='open' and 动作!='reveal':
        return 文本应答(400,'Invalid file action.')
    标识=取('sessionId')
    序号=坐标数(取('seq'))
    下标=坐标数(取('index'))
    if not 标识 or 序号 is None or 下标 is None:
        return 文本应答(400,'Invalid Presented file coordinates.')
    信号=请求.get('signal')
    try:
        停则抛(寿命,信号)
        if not 上下文.sessionController.workspaceDesktop()['available']:
            return 文本应答(409,'Host desktop unavailable.')
        读得=上下文.sessionQuery.读取事件({
            'sessionId':标识,
            'seq':序号,
            'before':0,
            'after':0,
        },信号)
        目标=读得['target']
        会话=读得['session']
        文件=None
        if isinstance(目标,dict) and 目标.get('type')=='deliverables/presented' and 是否已呈现数据(目标.get('data')):
            文件表=目标['data']['files']
            if isinstance(文件表,list) and 下标<len(文件表):
                文件=文件表[下标]
        if not 是否已呈现文件(文件):
            return 文本应答(404,'Presented file not found in this Session result.')
        停则抛(寿命,信号)
        工作目录=会话.get('cwd') if isinstance(会话,dict) else getattr(会话,'cwd',None)
        if 工作目录 is None:
            工作目录=上下文.sandboxPolicy.workspaceRoot
        状态=上下文.workspaceFiles.stat({
            'sessionId':标识,
            'workspaceRoot':工作目录,
        },文件['path'],信号)
        return 打开已校验(上下文,请求,状态['absolutePath'],动作,寿命)
    except Exception as 错误:
        停则抛(寿命,信号)
        return 文本应答(失败状态(错误),'Presented file unavailable.')


def 处理改动摘要(上下文,请求):
    '一条 workspace/changes 宣告的摘要，不含工作目录'
    取=查询(请求)
    标识=取('sessionId')
    序号=坐标数(取('seq'))
    if not 标识 or 序号 is None:
        return 文本应答(400,'Invalid change summary coordinates.')
    摘要=上下文.workspaceChanges.摘要(标识,序号)
    if 摘要 is None:
        return 文本应答(404,'Change summary unavailable.')
    return 应答json({
        'turn':摘要['turn'],
        'files':摘要['files'],
        'total':摘要['total'],
        'added':摘要['added'],
        'deleted':摘要['deleted'],
    })


def 改动文件坐标(请求):
    '查询里的会话、序号和下标。缺了就是 400 应答'
    取=查询(请求)
    标识=取('sessionId')
    序号=坐标数(取('seq'))
    下标=坐标数(取('index'))
    if not 标识 or 序号 is None or 下标 is None:
        return 文本应答(400,'Invalid changed file coordinates.')
    return {'id':标识,'seq':序号,'index':下标}


def 处理改动对比(上下文,请求,寿命):
    '所列文件的对比。宿主不再提供时 404'
    坐标=改动文件坐标(请求)
    if 'status' in 坐标:
        return 坐标
    信号=请求.get('signal')
    try:
        停则抛(寿命,信号)
        对比=上下文.workspaceChanges.差异(坐标['id'],坐标['seq'],坐标['index'],信号)
        if 对比 is None:
            return 文本应答(404,'Change comparison unavailable.')
        return 应答json(对比)
    except Exception as 错误:
        停则抛(寿命,信号)
        return 文本应答(失败状态(错误),'Change comparison unavailable.')


def 处理改动打开(上下文,请求,寿命):
    '打开摘要里的一个已改文件'
    取=查询(请求)
    动作=取('action')
    if 动作 is None:
        动作='open'
    if 动作!='open' and 动作!='reveal':
        return 文本应答(400,'Invalid file action.')
    坐标=改动文件坐标(请求)
    if 'status' in 坐标:
        return 坐标
    信号=请求.get('signal')
    try:
        停则抛(寿命,信号)
        if not 上下文.sessionController.workspaceDesktop()['available']:
            return 文本应答(409,'Host desktop unavailable.')
        改动=上下文.workspaceChanges.摘要(坐标['id'],坐标['seq'])
        if 改动 is None:
            return 文本应答(404,'Change summary unavailable.')
        文件表=改动['files']
        if 坐标['index']>=len(文件表):
            return 文本应答(404,'Changed file not found in this summary.')
        文件=文件表[坐标['index']]
        状态=上下文.workspaceFiles.stat({
            'sessionId':坐标['id'],
            'workspaceRoot':改动['cwd'],
        },文件['path'],信号)
        return 打开已校验(上下文,请求,状态['absolutePath'],动作,寿命)
    except Exception as 错误:
        停则抛(寿命,信号)
        return 文本应答(失败状态(错误),'Changed file unavailable.')


def 登记呈现打开(上下文):
    '桌面元数据、改动摘要与对比、已声明与已改文件打开'
    def 宿主应答(请求):
        'GET present.host'
        return 应答json(上下文.sessionController.workspaceDesktop())

    上下文.connection.fetch.register({
        'path':呈现宿主路径,
        'methods':['GET'],
        'requestBody':'buffered',
        'fetch':宿主应答,
    })

    def 摘要应答(请求):
        'GET changes.summary'
        return 处理改动摘要(上下文,请求)

    上下文.connection.fetch.register({
        'path':已改文件路径,
        'methods':['GET'],
        'requestBody':'buffered',
        'fetch':摘要应答,
    })
    寿命=threading.Event()
    在飞=set()

    def 拆除():
        '中止未完的打开和对比，并等到它们不再写应答'
        寿命.set()
        for 完成 in list(在飞):
            完成.wait()

    def 登记寿命():
        '纤程卸下时拆除'
        return 拆除

    上下文.副作用(登记寿命)

    def 包一层(处理):
        '记下在飞，拆除时能等到'
        def 应答(请求):
            '带寿命调用处理'
            完成=threading.Event()
            在飞.add(完成)
            try:
                return 处理(上下文,请求,寿命)
            finally:
                完成.set()
                在飞.discard(完成)
        return 应答

    路由=(
        (呈现打开路径,['GET','POST'],处理呈现打开),
        (改动打开路径,['GET','POST'],处理改动打开),
        (改动对比路径,['GET'],处理改动对比),
    )
    for 路径,方法,处理 in 路由:
        上下文.connection.fetch.register({
            'path':路径,
            'methods':list(方法),
            'requestBody':'buffered',
            'fetch':包一层(处理),
        })
