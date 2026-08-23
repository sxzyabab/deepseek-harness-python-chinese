"""面向模型的只读 Cordis 能力查询的宿主注册表。

对齐上游 `拓展/cordis-host-runner/src/inspect-registry.ts`。公开面仅中文名。
"""
from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#Cordis 服务基类
是否thenable=cordis.工具.是否thenable#可等待判定

__all__=['巡检注册表服务','宿主巡检提供方登记']#仅中文公开名

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 视图(平面,清单):#拼目录行
    """拷方法数组。"""
    return {'platform':平面,**清单,'methods':list(清单.get('methods') or [])}#拷方法数组

def 校验清单(清单):#校验清单
    """冻结前校验 id / description / methods。"""
    if not str(清单.get('id') or '').strip():#id 不能空
        raise Exception('Cordis inspect provider id must not be empty')#id 不能空
    if not str(清单.get('description') or '').strip():#需要说明
        raise Exception(f'Cordis inspect provider "{清单.get("id")}" needs a description')#需要说明
    名们=set()#方法名集合
    方法们=[]#校验后方法
    for 方法 in 清单.get('methods') or []:#逐条方法
        名=方法.get('name') if isinstance(方法,dict) else getattr(方法,'name',None)#方法名
        if not str(名 or '').strip():#方法名空
            raise Exception(f'Cordis inspect provider "{清单.get("id")}" has an empty method name')#方法名空
        if 名 in 名们:#方法名重复
            raise Exception(f'Cordis inspect provider "{清单.get("id")}" repeats method "{名}"')#重复
        说明=方法.get('description') if isinstance(方法,dict) else getattr(方法,'description',None)#说明
        if not str(说明 or '').strip():#方法需要说明
            raise Exception(f'Cordis inspect method {清单.get("id")}.{名} needs a description')#方法需要说明
        名们.add(名)#收入集合
        方法们.append(dict(方法) if isinstance(方法,dict) else {'name':名,'description':说明,'inputSchema':getattr(方法,'inputSchema',None),'outputSchema':getattr(方法,'outputSchema',None)})#拷贝
    return {**清单,'methods':方法们}#校验后的清单

def 找方法(清单,名):#按名找方法
    """没有则抛。"""
    for 方法 in 清单.get('methods') or []:#查找
        if (方法.get('name') if isinstance(方法,dict) else 方法)==名 or (isinstance(方法,dict) and 方法.get('name')==名):#命中
            return 方法#命中
    raise Exception(f'Cordis inspect provider "{清单.get("id")}" has no method "{名}"')#没有

class 巡检注册表服务(服务):#巡检注册表服务
    """两套面向模型的巡检工具背后的注册表与跨页路由器。"""
    def __init__(自身,上下文):#构造
        """以 cordisInspect 键提供。"""
        super().__init__(上下文,'cordisInspect')#登记服务
        自身.提供方={}#宿主提供方
        自身.挂起={}#待客户端回答
        自身.客户端清单=None#客户端清单镜像
        自身.下一请求=1#查询序号

    def 登记(自身,登记项):#登记
        """登记一个宿主提供方；返回幂等拆除器。"""
        清单=校验清单(登记项['manifest'] if isinstance(登记项,dict) else 登记项.manifest)#校验清单
        if 清单['id'] in 自身.提供方:#重复 id
            raise Exception(f'Host Cordis inspect provider "{清单["id"]}" is already registered')#重复
        存档={**登记项,'manifest':清单} if isinstance(登记项,dict) else {'manifest':清单,'query':登记项.query}#带校验后清单
        自身.提供方[清单['id']]=存档#写入
        def 拆除():#拆除器
            """仍是本条才拿掉。"""
            if 自身.提供方.get(清单['id']) is 存档:#仍是本条
                自身.提供方.pop(清单['id'],None)#拿掉
        return 拆除#拆除器

    def 同步客户端清单(自身,提供方们):#同步客户端清单
        """替换镜像的客户端提供方目录。"""
        标识们=set()#去重
        已校验=[]#校验后
        for 提供方 in 提供方们:#逐条校验
            清单=校验清单(提供方)#校验
            if 清单['id'] in 标识们:#重复 id
                raise Exception(f'Client Cordis inspect manifest repeats provider "{清单["id"]}"')#重复
            标识们.add(清单['id'])#收入
            已校验.append(清单)#收下
        自身.客户端清单=tuple(已校验)#冻结镜像近似

    def 列表(自身):#列目录
        """宿主提供方在前，客户端提供方在后。"""
        宿主=[视图('host',项['manifest']) for 项 in 自身.提供方.values()]#宿主
        客户端=[视图('client',项) for 项 in (自身.客户端清单 or [])]#客户端
        return 宿主+客户端#拼接

    def 查询(自身,平面,提供方标识,方法名,输入,智能体,信号):#分发查询
        """在所属平面上执行一条提供方查询。"""
        if 平面=='host':#宿主平面
            登记项=自身.提供方.get(提供方标识)#取登记
            if 登记项 is None:#未登记
                raise Exception(f'Host Cordis inspect provider "{提供方标识}" is not registered')#未登记
            方法=找方法(登记项['manifest'],方法名)#找方法
            if 信号 is not None and getattr(信号,'aborted',False):#已取消
                raise Exception('aborted')#取消
            查询函数=登记项['query'] if isinstance(登记项,dict) else 登记项.query#查询
            数据=解开(查询函数(方法名,输入,{'agent':智能体,'signal':信号}))#本地查询
            return 数据#数据
        return 自身.查询客户端(提供方标识,方法名,输入,智能体,信号)#客户端平面

    def 结算客户端查询(自身,智能体,请求标识,决议):#认领客户端回答
        """本响应是否落定了仍在等待的查询。"""
        挂起=自身.挂起.get(请求标识)#待处理项
        if 挂起 is None or 挂起['request'].get('agentId')!=智能体.id:#未知或会话不对
            return {'accepted':False}#不受理
        if not 决议.get('ok'):#失败回答不认领
            return {'accepted':False}#拒绝
        自身.挂起.pop(请求标识,None)#从表拿掉
        挂起['settle'](决议)#唤醒等待方
        自身.ctx.emit('cordis/inspect-query-resolved',{'requestId':请求标识})#广播已落定
        return {'accepted':True}#认领成功

    def 查询客户端(自身,提供方标识,方法名,输入,智能体,信号):#向客户端广播查询
        """等第一条合法回答。"""
        提供方=next((项 for 项 in (自身.客户端清单 or []) if 项.get('id')==提供方标识),None)#在镜像里找
        if 提供方 is None:#未同步
            raise Exception(f'Client Cordis inspect provider "{提供方标识}" is not registered')#未同步
        方法=找方法(提供方,方法名)#找方法
        if 信号 is not None and getattr(信号,'aborted',False):#已取消
            raise Exception('aborted')#取消
        请求标识=f'inspect-{自身.下一请求}'#铸造查询 id
        自身.下一请求+=1#推进
        请求={'requestId':请求标识,'agentId':智能体.id,'provider':提供方标识,'method':方法名}#广播请求
        if 输入 is not None:#有输入才带上
            请求['input']=输入#输入
        结果盒={'resolution':None}#落定盒
        def 落定(决议):#落定回调
            """写入结果盒。"""
            结果盒['resolution']=决议#写入
        自身.挂起[请求标识]={'request':请求,'method':方法,'settle':落定}#挂起
        def 取消():#工具取消
            """取消决议。"""
            挂起=自身.挂起.pop(请求标识,None)#仍在等？
            if 挂起 is None:#已落定
                return#返回
            挂起['settle']({'ok':False,'reason':'cancelled','message':f'Client inspect query {提供方标识}.{方法名} was cancelled'})#取消决议
            自身.ctx.emit('cordis/inspect-query-resolved',{'requestId':请求标识})#广播已落定
        if 信号 is not None:#听取消
            添加=getattr(信号,'addEventListener',None) or getattr(信号,'add_event_listener',None)#监听
            if 添加 is not None:#有监听 API
                添加('abort',取消)#听取消
            if getattr(信号,'aborted',False):#已经取消
                取消()#立刻走
            else:#向页面广播
                自身.ctx.emit('cordis/inspect-query',请求)#广播
        else:#无信号则直接广播
            自身.ctx.emit('cordis/inspect-query',请求)#广播
        决议=结果盒['resolution']#第一条合法回答（同步路径可能仍空）
        if 决议 is None:#仍在等——同步宿主侧无法阻塞页面；返回挂起说明
            raise Exception(f'Client inspect query {提供方标识}.{方法名} is pending page response')#等待页面
        if not 决议.get('ok'):#失败则抛
            raise Exception(f'{提供方标识}.{方法名}: {决议.get("message")}')#失败
        return 决议['data']#数据

#工具面上游方法名对照
巡检注册表服务.register=巡检注册表服务.登记#register
巡检注册表服务.list=巡检注册表服务.列表#list
巡检注册表服务.query=巡检注册表服务.查询#query
CordisInspectRegistryService=巡检注册表服务#英文别名
宿主巡检提供方登记=dict#登记项形态：manifest + query
