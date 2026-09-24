"""面向模型的只读 Cordis 能力查询的宿主注册表。"""
import threading
from ...依赖.cordis import 服务
from ...工具.超时 import 已中止,若已中止则抛出
from ...内核.会话 import 快照json值
from ...内核.工具 import 断言受支持json模式,校验json模式值
from .类型 import 动态cordis错误

__all__=['巡检注册表服务','宿主巡检查询上下文','宿主巡检提供方登记']

#工具
def 视图(平面,清单):
    """拼一条带平面的目录行，方法数组另拷一份。"""
    行=dict(清单)
    行['platform']=平面
    行['methods']=[dict(方法) for 方法 in 清单['methods']]
    return 行

def 校验清单(清单):
    """校验提供方清单并拷出不可变方法表。"""
    if 清单['id'].strip()=='':
        raise 动态cordis错误('Cordis 巡检提供方 id 不能为空')
    if 清单['description'].strip()=='':
        raise 动态cordis错误(f'Cordis 巡检提供方 "{清单["id"]}" 需要说明')
    名集=set()
    方法表=[]
    for 方法 in 清单['methods']:
        if 方法['name'].strip()=='':
            raise 动态cordis错误(f'Cordis 巡检提供方 "{清单["id"]}" 有空方法名')
        if 方法['name'] in 名集:
            raise 动态cordis错误(f'Cordis 巡检提供方 "{清单["id"]}" 重复方法 "{方法["name"]}"')
        if 方法['description'].strip()=='':
            raise 动态cordis错误(f'Cordis 巡检方法 {清单["id"]}.{方法["name"]} 需要说明')
        断言受支持json模式(方法['inputSchema'])
        断言受支持json模式(方法['outputSchema'])
        名集.add(方法['name'])
        方法表.append(dict(方法))
    出=dict(清单)
    出['methods']=tuple(方法表)
    return 出

def 查找方法(清单,名):
    """按名找方法；没有则抛。"""
    for 候选 in 清单['methods']:
        if 候选['name']==名:
            return 候选
    raise 动态cordis错误(f'Cordis 巡检提供方 "{清单["id"]}" 没有方法 "{名}"')

def 校验输入(平面,提供方,方法,输入):
    """对照输入模式校验；不合则抛。"""
    候选=输入 if 输入 is not None else {}
    违规=校验json模式值(方法['inputSchema'],候选,'input')
    if len(违规)>0:
        raise 动态cordis错误(
            f'{平面} Cordis 巡检 {提供方}.{方法["name"]} 拒绝了输入: '+'; '.join(违规)
        )

def 校验输出(平面,提供方,方法,数据):
    """快照并对照输出模式校验，返回脱离后的 JSON。"""
    快照=快照json值(数据)
    if 快照 is None:
        raise 动态cordis错误(f'{平面} Cordis 巡检 {提供方}.{方法["name"]} 返回了非 JSON 值')
    违规=校验json模式值(方法['outputSchema'],快照,'output')
    if len(违规)>0:
        raise 动态cordis错误(
            f'{平面} Cordis 巡检 {提供方}.{方法["name"]} 返回了非法输出: '+'; '.join(违规)
        )
    return 快照

#
class 宿主巡检查询上下文:
    """交给宿主巡检查询的上下文。"""
    def __init__(自身,信号,智能体):
        """信号为 threading.Event 或中止信号。"""
        自身.信号=信号
        自身.智能体=智能体

class 宿主巡检提供方登记:
    """与可序列化清单配对的本地登记。"""
    def __init__(自身,清单,查询):
        """清单为巡检提供方线协议字典；查询(方法名,输入,上下文)返回 JSON。"""
        自身.清单=清单
        自身.查询=查询

class 巡检注册表服务(服务):
    """两套面向模型的巡检工具背后的注册表与跨页路由器。"""
    def __init__(自身,上下文):
        """以 cordisInspect 键提供进程全局宿主注册表。"""
        super().__init__(上下文,'cordisInspect')
        自身._提供方={}
        自身._待处理={}
        自身._客户端清单=None
        自身._下一请求=1
        自身._锁=threading.Lock()

    def 登记(自身,提供方登记):
        """登记一个宿主提供方，返回幂等拆除器。"""
        清单=校验清单(提供方登记.清单)
        if 清单['id'] in 自身._提供方:
            raise 动态cordis错误(f'宿主 Cordis 巡检提供方 "{清单["id"]}" 已登记')
        已存=宿主巡检提供方登记(清单,提供方登记.查询)
        自身._提供方[清单['id']]=已存
        def 拆除():
            """仍是本条才拿掉。"""
            if 清单['id'] in 自身._提供方 and 自身._提供方[清单['id']] is 已存:
                del 自身._提供方[清单['id']]
        return 拆除

    def 同步客户端清单(自身,提供方列表):
        """替换镜像的客户端提供方目录。"""
        已见=set()
        已校验=[]
        for 提供方 in 提供方列表:
            清单=校验清单(提供方)
            if 清单['id'] in 已见:
                raise 动态cordis错误(f'客户端 Cordis 巡检清单重复提供方 "{清单["id"]}"')
            已见.add(清单['id'])
            已校验.append(清单)
        自身._客户端清单=tuple(已校验)

    def 列出(自身):
        """已知的完整宿主与客户端提供方目录，宿主在前。"""
        结果=[视图('host',登记.清单) for 登记 in 自身._提供方.values()]
        if 自身._客户端清单 is not None:
            for 清单 in 自身._客户端清单:
                结果.append(视图('client',清单))
        return 结果

    def 查询(自身,平面,提供方标识,方法名,输入,智能体,信号):
        """在所属平面上执行一条提供方查询。"""
        if 平面=='host':
            if 提供方标识 not in 自身._提供方:
                raise 动态cordis错误(f'宿主 Cordis 巡检提供方 "{提供方标识}" 未登记')
            登记=自身._提供方[提供方标识]
            方法=查找方法(登记.清单,方法名)
            校验输入('宿主',提供方标识,方法,输入)
            若已中止则抛出(信号)
            数据=登记.查询(方法名,输入,宿主巡检查询上下文(信号,智能体))
            若已中止则抛出(信号)
            return 校验输出('宿主',提供方标识,方法,数据)
        return 自身.查询客户端(提供方标识,方法名,输入,智能体,信号)

    def 结算客户端查询(自身,智能体,请求标识,决议):
        """接受待处理查询的第一条合法客户端响应。"""
        with 自身._锁:
            if 请求标识 not in 自身._待处理:
                return {'accepted':False}
            待处理=自身._待处理[请求标识]
            if 待处理['request']['agentId']!=智能体.id:
                return {'accepted':False}
            if 'ok' not in 决议 or 决议['ok'] is not True:
                return {'accepted':False}
            try:
                数据=校验输出('客户端',待处理['request']['provider'],待处理['method'],决议['data'])
            except 动态cordis错误:
                return {'accepted':False}
            del 自身._待处理[请求标识]
            落定=待处理['落定']
            已校验={'ok':True,'data':数据}
        落定(已校验)
        自身.所属上下文.广播('cordis/inspect-query-resolved',{'requestId':请求标识})
        return {'accepted':True}

    def 查询客户端(自身,提供方标识,方法名,输入,智能体,信号):
        """向客户端广播查询并阻塞等到第一条合法回答。"""
        提供方=None
        if 自身._客户端清单 is not None:
            for 候选 in 自身._客户端清单:
                if 候选['id']==提供方标识:
                    提供方=候选
                    break
        if 提供方 is None:
            raise 动态cordis错误(f'客户端 Cordis 巡检提供方 "{提供方标识}" 未登记')
        方法=查找方法(提供方,方法名)
        校验输入('客户端',提供方标识,方法,输入)
        若已中止则抛出(信号)
        请求标识=f'inspect-{自身._下一请求}'
        自身._下一请求+=1
        请求={
            'requestId':请求标识,
            'agentId':智能体.id,
            'provider':提供方标识,
            'method':方法名,
        }
        if 输入 is not None:
            请求['input']=输入
        完成=threading.Event()
        盒子={'决议':None}
        def 落定(决议):
            """唤醒等待方。"""
            盒子['决议']=决议
            完成.set()
        with 自身._锁:
            自身._待处理[请求标识]={'request':请求,'method':方法,'落定':落定}
        停止=threading.Event()
        def 取消():
            """工具取消则落定失败并广播。"""
            with 自身._锁:
                if 请求标识 not in 自身._待处理:
                    return
                待处理=自身._待处理[请求标识]
                del 自身._待处理[请求标识]
            待处理['落定']({
                'ok':False,
                'reason':'cancelled',
                'message':f'客户端巡检查询 {提供方标识}.{方法名} 已取消',
            })
            自身.所属上下文.广播('cordis/inspect-query-resolved',{'requestId':请求标识})
        def 看中止():
            """信号置位则取消仍在等待的查询。"""
            while not 停止.is_set():
                if 已中止(信号):
                    取消()
                    return
                停止.wait(0.05)
        监视=threading.Thread(target=看中止,daemon=True)
        监视.start()
        try:
            if 已中止(信号):
                取消()
            else:
                自身.所属上下文.广播('cordis/inspect-query',请求)
            完成.wait()
            决议=盒子['决议']
            if 'ok' not in 决议 or 决议['ok'] is not True:
                raise 动态cordis错误(f'{提供方标识}.{方法名}: {决议["message"]}')
            return 决议['data']
        finally:
            停止.set()
