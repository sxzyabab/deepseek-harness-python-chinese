"""提供改动摘要与对比，并打开经会话文件系统校验的已声明或已改动工作区文件。"""
import re#坐标数字
import threading#寿命中止
from concurrent.futures import Future as _原生Future,wait as _等待全部#在飞任务
from .已呈现 import (#已呈现校验与路径
    呈现打开路径,呈现宿主路径,是否已呈现数据,是否已呈现文件,
)
from .改动 import 已改文件路径,改动对比路径,改动打开路径#改动路由

__all__=['登记呈现打开','呈现打开错误']#仅中文公开名

_序号形态=re.compile(r'^\d+\Z')#仅数字

class 呈现打开错误(Exception):
    """呈现打开失败。"""
    def __init__(自身,消息):
        """记下消息。"""
        super().__init__(消息)#英文

def 登记呈现打开(上下文):#登记交付物路由
    """桌面元数据、改动摘要与对比、已声明与已改文件打开。"""
    def 宿主应答():#桌面元数据
        """GET present.host。"""
        桌面=上下文.sessionController.workspaceDesktop()#桌面
        return {'status':200,'headers':{'cache-control':'no-store'},'json':桌面}#JSON 应答
    上下文.connection.fetch.register({#登记宿主 GET
        'path':呈现宿主路径,'methods':['GET'],'requestBody':'buffered','fetch':宿主应答,
    })#HOST 结束
    def 摘要应答(请求):#改动摘要
        """GET changes.summary。"""
        return _处理改动摘要(上下文,请求)#处理
    上下文.connection.fetch.register({#登记摘要 GET
        'path':已改文件路径,'methods':['GET'],'requestBody':'buffered','fetch':摘要应答,
    })#摘要结束
    寿命=threading.Event()#寿命中止旗
    在飞=set()#在飞 Future

    def 拆除():#拆除路由
        """取消未完并等结算。"""
        寿命.set()#中止
        if len(在飞)>0:#有在飞
            _等待全部(list(在飞))#等全部

    def 拆除工厂():#副作用拆除器
        """返回拆除。"""
        return 拆除#拆除
    上下文.副作用(拆除工厂,'ui-deliverables: present-open lifetime')#寿命副作用

    def 包一层(处理):#在飞包装
        """记下 Future。"""
        def 应答(请求):#处理
            """带寿命。"""
            if 寿命.is_set():#已拆除
                return {'status':499,'body':'呈现打开已拆除。'}#拆除
            未来=_原生Future()#拆除时等待
            在飞.add(未来)#记下
            try:#直接处理
                结果=处理(上下文,请求,寿命)#同步
                未来.set_result(结果)#兑现
                return 结果#应答
            except BaseException as 错误:#失败
                未来.set_exception(错误)#拒绝
                raise#上抛
            finally:#结算后
                在飞.discard(未来)#移出
        return 应答#包装
    上下文.connection.fetch.register({#已呈现打开
        'path':呈现打开路径,'methods':['POST'],'requestBody':'buffered','fetch':包一层(_处理呈现打开),
    })#OPEN 结束
    上下文.connection.fetch.register({#改动打开
        'path':改动打开路径,'methods':['POST'],'requestBody':'buffered','fetch':包一层(_处理改动打开),
    })#改动打开结束
    上下文.connection.fetch.register({#改动对比
        'path':改动对比路径,'methods':['GET'],'requestBody':'buffered','fetch':包一层(_处理改动对比),
    })#对比结束

def _坐标数(值):#安全整数坐标
    """非纯数字则 None。"""
    if 值 is None or not _序号形态.match(str(值)):#形态
        return None#否
    数=int(值)#转
    return 数 if abs(数)<2**53 else None#安全

def _失败状态(错误):#失败→状态码
    """缺失类 404，其余 500。"""
    码=None#错误码
    if hasattr(错误,'code'):#带码
        码=错误.code#码
    elif isinstance(错误,dict) and 'code' in 错误:#dict 码
        码=错误['code']#码
    缺失=码 in (#缺失类
        'session/not-found','workspace-file/not-found','workspace-file/not-regular-file',
        'SESSION_QUERY_SESSION_NOT_FOUND','SESSION_QUERY_EVENT_NOT_FOUND','ENOENT','ENOTDIR',
    )#缺失结束
    return 404 if 缺失 else 500#映射

def _打开已校验(上下文,路径,动作,寿命):#打开已校验路径
    """文件经会话文件系统校验；目录仅映射。"""
    if 寿命.is_set():#中止
        raise 呈现打开错误('已中止')#中止
    映射=上下文.fs.processPathFromHostPath(路径)#宿主→进程
    if 映射 is None or 上下文.fs.processPath(上下文.fs.resolve(映射))!=路径:#往返校验
        return {'status':422,'body':'路径没有经过校验的宿主路径。'}#422
    打开参={'path':路径}#打开参数
    if 动作=='reveal':#揭示
        打开参['action']=动作#带动作
    上下文.sessionController.openWorkspacePath(打开参)#打开
    return {'status':204,'headers':{'cache-control':'no-store'},'body':None}#成功

def _处理呈现打开(上下文,请求,寿命):#处理呈现打开
    """校验坐标、读事件、校验宿主路径并打开。请求为 dict。"""
    查询=请求['query'] if 'query' in 请求 else {}#查询
    动作=查询['action'] if 'action' in 查询 else 'open'#默认打开
    if 动作 not in ('open','reveal'):#非法动作
        return {'status':400,'body':'非法文件动作。'}#400
    标识=查询['sessionId'] if 'sessionId' in 查询 else None#会话
    序号=_坐标数(查询['seq'] if 'seq' in 查询 else None)#序号
    下标=_坐标数(查询['index'] if 'index' in 查询 else None)#下标
    if 标识 is None or 序号 is None or 下标 is None:#坐标
        return {'status':400,'body':'已呈现文件坐标非法。'}#400
    try:#尝试打开
        if 寿命.is_set():#已中止
            raise 呈现打开错误('已中止')#中止
        if not 上下文.sessionController.workspaceDesktop()['available']:#桌面不可用
            return {'status':409,'body':'宿主桌面不可用。'}#409
        读得=上下文.sessionQuery.readEvent({#读事件
            'sessionId':标识,'seq':序号,'before':0,'after':0,
        })#查询
        目标=读得['target'] if 'target' in 读得 else None#目标事件
        会话=读得['session'] if 'session' in 读得 else None#会话
        数据=目标['data'] if 目标 is not None and 'data' in 目标 else None#数据
        文件=None#候选
        if (目标 is not None and 'type' in 目标 and 目标['type']=='deliverables/presented'
            and 是否已呈现数据(数据)):#已呈现事件
            文件表=数据['files']#文件表
            if 0<=下标<len(文件表):#下标合法
                文件=文件表[下标]#取文件
        if not 是否已呈现文件(文件):#未找到
            return {'status':404,'body':'本会话结果中找不到已呈现文件。'}#404
        工作区根=会话['cwd'] if 会话 is not None and 'cwd' in 会话 else 上下文.sandboxPolicy.workspaceRoot#根
        统计=上下文.workspaceFiles.stat({#解析绝对路径
            'sessionId':标识,'workspaceRoot':工作区根,
        },文件['path'])#相对路径
        return _打开已校验(上下文,统计['absolutePath'],动作,寿命)#打开
    except 呈现打开错误:#中止
        raise#上抛
    except Exception as 错误:#其余
        if 寿命.is_set():#中止优先
            raise 呈现打开错误('已中止') from 错误#中止
        return {'status':_失败状态(错误),'body':'已呈现文件不可用。'}#按类

def _处理改动摘要(上下文,请求):#改动摘要
    """不含宿主工作目录；不再服务时 404。"""
    查询=请求['query'] if 'query' in 请求 else {}#查询
    标识=查询['sessionId'] if 'sessionId' in 查询 else None#会话
    序号=_坐标数(查询['seq'] if 'seq' in 查询 else None)#序号
    if 标识 is None or 序号 is None:#非法
        return {'status':400,'body':'改动摘要坐标非法。'}#400
    摘要=上下文.workspaceChanges.summary(标识,序号)#摘要
    if 摘要 is None:#不可用
        return {'status':404,'body':'改动摘要不可用。'}#404
    return {'status':200,'headers':{'cache-control':'no-store'},'json':{#字段
        'turn':摘要['turn'],'files':摘要['files'],'total':摘要['total'],
        'added':摘要['added'],'deleted':摘要['deleted'],
    }}#JSON

def _改动坐标(请求):#改动文件坐标
    """合法则 dict，否则 400 应答。"""
    查询=请求['query'] if 'query' in 请求 else {}#查询
    标识=查询['sessionId'] if 'sessionId' in 查询 else None#会话
    序号=_坐标数(查询['seq'] if 'seq' in 查询 else None)#序号
    下标=_坐标数(查询['index'] if 'index' in 查询 else None)#下标
    if 标识 is None or 序号 is None or 下标 is None:#非法
        return {'status':400,'body':'已改文件坐标非法。'}#400
    return {'id':标识,'seq':序号,'index':下标}#坐标

def _处理改动对比(上下文,请求,寿命):#改动对比
    """列表中某一文件的对比。"""
    坐标=_改动坐标(请求)#坐标
    if 'status' in 坐标:#400
        return 坐标#应答
    try:#取对比
        if 寿命.is_set():#中止
            raise 呈现打开错误('已中止')#中止
        对比=上下文.workspaceChanges.diff(坐标['id'],坐标['seq'],坐标['index'])#对比
        if 对比 is None:#不可用
            return {'status':404,'body':'改动对比不可用。'}#404
        return {'status':200,'headers':{'cache-control':'no-store'},'json':对比}#JSON
    except 呈现打开错误:#中止
        raise#上抛
    except Exception as 错误:#失败
        if 寿命.is_set():#中止
            raise 呈现打开错误('已中止') from 错误#中止
        return {'status':_失败状态(错误),'body':'改动对比不可用。'}#按类

def _处理改动打开(上下文,请求,寿命):#打开改动
    """按摘要下标打开已改文件。"""
    坐标=_改动坐标(请求)#坐标
    if 'status' in 坐标:#400
        return 坐标#应答
    try:#打开
        if 寿命.is_set():#中止
            raise 呈现打开错误('已中止')#中止
        if not 上下文.sessionController.workspaceDesktop()['available']:#桌面不可用
            return {'status':409,'body':'宿主桌面不可用。'}#409
        摘要=上下文.workspaceChanges.summary(坐标['id'],坐标['seq'])#摘要
        if 摘要 is None:#不可用
            return {'status':404,'body':'改动摘要不可用。'}#404
        文件表=摘要['files'] if 'files' in 摘要 else []#文件
        if 坐标['index']>=len(文件表):#无名
            return {'status':404,'body':'本摘要中找不到已改文件。'}#404
        文件=文件表[坐标['index']]#文件
        统计=上下文.workspaceFiles.stat({#stat
            'sessionId':坐标['id'],'workspaceRoot':摘要['cwd'],
        },文件['path'])#路径
        return _打开已校验(上下文,统计['absolutePath'],'open',寿命)#打开
    except 呈现打开错误:#中止
        raise#上抛
    except Exception as 错误:#失败
        if 寿命.is_set():#中止
            raise 呈现打开错误('已中止') from 错误#中止
        return {'status':_失败状态(错误),'body':'已改文件不可用。'}#按类
