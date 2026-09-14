import re#坐标数字
import threading#寿命中止
from concurrent.futures import Future as _原生Future,wait as _等待全部#在飞任务
from .已呈现 import (#已呈现校验与路径
    呈现打开路径,呈现宿主路径,是否已呈现数据,是否已呈现文件,
)

__all__=['登记呈现打开','呈现打开错误']#仅中文公开名

_序号形态=re.compile(r'^\d+\Z')#仅数字

class 呈现打开错误(Exception):
    """呈现打开失败。"""
    def __init__(自身,消息):
        """记下消息。"""
        super().__init__(消息)#英文

def 登记呈现打开(上下文):#登记呈现打开
    """在连接的认证围栏内登记原生打开。"""
    def 宿主应答():#桌面元数据
        """GET present.host。"""
        桌面=上下文.sessionController.workspaceDesktop()#桌面
        return {'status':200,'headers':{'cache-control':'no-store'},'json':桌面}#JSON 应答
    上下文.connection.fetch.register({#登记宿主 GET
        'path':呈现宿主路径,'methods':['GET'],'requestBody':'buffered','fetch':宿主应答,
    })#HOST 结束
    寿命=threading.Event()#寿命中止旗
    在飞=set()#在飞 Future

    def 拆除():#拆除路由
        """取消未完并等结算。"""
        寿命.set()#中止
        if len(在飞)>0:#有在飞
            _等待全部(list(在飞))#等全部

    上下文.副作用(lambda:拆除,'ui-deliverables: present-open lifetime')#寿命副作用

    def 打开应答(请求):#处理打开
        """POST present.open。请求为 dict。"""
        if 寿命.is_set():#已拆除
            return {'status':499,'body':'呈现打开已拆除。'}#拆除
        未来=_原生Future()#拆除时等待
        在飞.add(未来)#记下
        try:#直接处理
            结果=_处理呈现打开(上下文,请求,寿命)#同步打开
            未来.set_result(结果)#兑现
            return 结果#应答
        except BaseException as 错误:#失败
            未来.set_exception(错误)#拒绝
            raise#上抛
        finally:#结算后
            在飞.discard(未来)#移出

    上下文.connection.fetch.register({#登记打开 POST
        'path':呈现打开路径,'methods':['POST'],'requestBody':'buffered','fetch':打开应答,
    })#OPEN 结束

def _处理呈现打开(上下文,请求,寿命):#处理呈现打开
    """校验坐标、读事件、校验宿主路径并打开。请求为 dict。"""
    查询=请求['query'] if 'query' in 请求 else {}#查询
    动作=查询['action'] if 'action' in 查询 else 'open'#默认打开
    if 动作 not in ('open','reveal'):#非法动作
        return {'status':400,'body':'非法文件动作。'}#400
    标识=查询['sessionId'] if 'sessionId' in 查询 else None#会话
    序号文=查询['seq'] if 'seq' in 查询 else None#序号串
    下标文=查询['index'] if 'index' in 查询 else None#下标串
    if (标识 is None or 序号文 is None or 下标文 is None
        or not _序号形态.match(str(序号文)) or not _序号形态.match(str(下标文))):#坐标形态
        return {'status':400,'body':'已呈现文件坐标非法。'}#400
    序号=int(序号文)#序号
    下标=int(下标文)#下标
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
        if 寿命.is_set():#再次中止
            raise 呈现打开错误('已中止')#中止
        工作区根=会话['cwd'] if 会话 is not None and 'cwd' in 会话 else 上下文.sandboxPolicy.workspaceRoot#根
        统计=上下文.workspaceFiles.stat({#解析绝对路径
            'sessionId':标识,'workspaceRoot':工作区根,
        },文件['path'])#相对路径
        路径=统计['absolutePath']#绝对路径
        映射=上下文.fs.processPathFromHostPath(路径)#宿主→进程
        if 映射 is None or 上下文.fs.processPath(上下文.fs.resolve(映射))!=路径:#往返校验
            return {'status':422,'body':'已呈现文件没有经过校验的宿主路径。'}#422
        if 寿命.is_set():#再次中止
            raise 呈现打开错误('已中止')#中止
        打开参={'path':路径}#打开参数
        if 动作=='reveal':#揭示
            打开参['action']=动作#带动作
        上下文.sessionController.openWorkspacePath(打开参)#打开
        return {'status':204,'headers':{'cache-control':'no-store'},'body':None}#成功
    except 呈现打开错误:#中止
        raise#上抛
    except Exception as 错误:#其余
        if 寿命.is_set():#中止优先
            raise 呈现打开错误('已中止') from 错误#中止
        码=None#错误码
        if hasattr(错误,'code'):#带码
            码=错误.code#码
        elif isinstance(错误,dict) and 'code' in 错误:#dict 码
            码=错误['code']#码
        缺失=码 in (#缺失类
            'session/not-found','workspace-file/not-found','workspace-file/not-regular-file',
            'SESSION_QUERY_SESSION_NOT_FOUND','SESSION_QUERY_EVENT_NOT_FOUND','ENOENT','ENOTDIR',
        )#缺失结束
        return {'status':404 if 缺失 else 500,'body':'已呈现文件不可用。'}#按类
