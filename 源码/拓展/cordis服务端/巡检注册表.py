from ...依赖 import cordis#外部依赖胶水
from .类型 import 动态插件错误#本包异常
服务=cordis.服务#Cordis 服务基类

__all__=['巡检注册表服务','宿主巡检提供方登记']#仅中文公开名

def 视图(平面,清单):
    """拷方法数组。清单为 dict。"""
    if 'methods' in 清单 and 清单['methods'] is not None:#有方法表
        方法表=list(清单['methods'])#拷方法数组
    else:#缺席当空
        方法表=[]#空
    return {'platform':平面,**清单,'methods':方法表}#拷方法数组

def 校验清单(清单):
    """冻结前校验 id / description / methods。清单与方法均为 dict。"""
    标识=清单['id'] if 'id' in 清单 else None#id
    if 标识 is None or len(str(标识).strip())==0:#id 不能空
        raise 动态插件错误('Cordis inspect provider id must not be empty')#id 不能空
    说明=清单['description'] if 'description' in 清单 else None#说明
    if 说明 is None or len(str(说明).strip())==0:#需要说明
        raise 动态插件错误('Cordis inspect provider "'+str(标识)+'" needs a description')#需要说明
    名集合=set()#方法名集合
    方法表=[]#校验后方法
    if 'methods' in 清单 and 清单['methods'] is not None:#有方法表
        原始方法=清单['methods']#方法数组
    else:#缺席当空
        原始方法=[]#空
    for 方法 in 原始方法:#逐条方法 dict
        名=方法['name'] if 'name' in 方法 else None#方法名
        if 名 is None or len(str(名).strip())==0:#方法名空
            raise 动态插件错误('Cordis inspect provider "'+str(标识)+'" has an empty method name')#方法名空
        if 名 in 名集合:#方法名重复
            raise 动态插件错误('Cordis inspect provider "'+str(标识)+'" repeats method "'+str(名)+'"')#重复
        方法说明=方法['description'] if 'description' in 方法 else None#说明
        if 方法说明 is None or len(str(方法说明).strip())==0:#方法需要说明
            raise 动态插件错误('Cordis inspect method '+str(标识)+'.'+str(名)+' needs a description')#方法需要说明
        名集合.add(名)#收入集合
        方法表.append(dict(方法))#拷贝
    return {**清单,'methods':方法表}#校验后的清单

def 找方法(清单,名):
    """没有则抛。清单为 dict，方法为 dict。"""
    if 'methods' in 清单 and 清单['methods'] is not None:#有方法表
        方法表=清单['methods']#方法数组
    else:#缺席
        方法表=[]#空
    for 方法 in 方法表:#查找
        if 'name' in 方法 and 方法['name']==名:#命中
            return 方法#命中
    标识=清单['id'] if 'id' in 清单 else ''#诊断 id
    raise 动态插件错误('Cordis inspect provider "'+str(标识)+'" has no method "'+名+'"')#没有

def 已中止(信号):
    """调用方是否已中止。信号是 threading.Event 或 None。"""
    if 信号 is None:#无信号
        return False#未中止
    return 信号.is_set()#Event 置位

class 巡检注册表服务(服务):
    """两套面向模型的巡检工具背后的注册表与跨页路由器。"""

    def __init__(自身,上下文):
        """以 cordisInspect 键提供。"""
        super().__init__(上下文,'cordisInspect')#登记服务
        自身.提供方={}#宿主提供方，按 id 索引；值按对象引用相等识别
        自身.挂起={}#待客户端回答
        自身.客户端清单=None#客户端清单镜像
        自身.下一请求=1#查询序号

    def 登记(自身,登记项):
        """登记一个宿主提供方；返回幂等拆除器。登记项为 dict。"""
        清单=校验清单(登记项['manifest'])#校验清单
        if 清单['id'] in 自身.提供方:#重复 id
            raise 动态插件错误('Host Cordis inspect provider "'+清单['id']+'" is already registered')#重复
        存档={**登记项,'manifest':清单}#带校验后清单
        自身.提供方[清单['id']]=存档#写入

        def 拆除():
            """仍是本条才拿掉；按对象引用相等，不是值相等。"""
            if 清单['id'] in 自身.提供方 and 自身.提供方[清单['id']] is 存档:#仍是本条
                del 自身.提供方[清单['id']]#拿掉

        return 拆除#拆除器

    def 同步客户端清单(自身,提供方列表):
        """替换镜像的客户端提供方目录。"""
        标识集合=set()#去重
        已校验=[]#校验后
        for 提供方 in 提供方列表:#逐条校验
            清单=校验清单(提供方)#校验
            if 清单['id'] in 标识集合:#重复 id
                raise 动态插件错误('Client Cordis inspect manifest repeats provider "'+清单['id']+'"')#重复
            标识集合.add(清单['id'])#收入
            已校验.append(清单)#收下
        自身.客户端清单=tuple(已校验)#冻结镜像近似

    def 列表(自身):
        """宿主提供方在前，客户端提供方在后。"""
        宿主=[]#宿主视图
        for 项 in 自身.提供方.values():#宿主登记
            宿主.append(视图('host',项['manifest']))#宿主
        if 自身.客户端清单 is None:#尚未同步
            客户端=[]#空
        else:#已同步
            客户端=[]#客户端视图
            for 项 in 自身.客户端清单:#镜像项
                客户端.append(视图('client',项))#客户端
        return 宿主+客户端#拼接

    def 查询(自身,平面,提供方标识,方法名,输入,智能体,信号):
        """在所属平面上执行一条提供方查询。"""
        if 平面=='host':#宿主平面
            if 提供方标识 not in 自身.提供方:#未登记
                raise 动态插件错误('Host Cordis inspect provider "'+提供方标识+'" is not registered')#未登记
            登记项=自身.提供方[提供方标识]#取登记
            找方法(登记项['manifest'],方法名)#找方法；没有则抛
            if 已中止(信号):#已取消
                raise 动态插件错误('aborted')#取消
            查询函数=登记项['query']#查询回调
            return 查询函数(方法名,输入,{'agent':智能体,'signal':信号})#本地查询；同步
        return 自身.查询客户端(提供方标识,方法名,输入,智能体,信号)#客户端平面

    def 结算客户端查询(自身,智能体,请求标识,决议):
        """本响应是否落定了仍在等待的查询。决议为 dict。"""
        if 请求标识 not in 自身.挂起:#未知
            return {'accepted':False}#不受理
        挂起=自身.挂起[请求标识]#待处理项
        请求=挂起['request']#原请求
        if 'agentId' not in 请求 or 请求['agentId']!=智能体.id:#会话不对
            return {'accepted':False}#不受理
        if 'ok' not in 决议 or not 决议['ok']:#失败回答不认领
            return {'accepted':False}#拒绝
        del 自身.挂起[请求标识]#从表拿掉
        挂起['settle'](决议)#唤醒等待方
        自身.ctx.广播('cordis/inspect-query-resolved',{'requestId':请求标识})#广播已落定
        return {'accepted':True}#认领成功

    def 查询客户端(自身,提供方标识,方法名,输入,智能体,信号):
        """等第一条合法回答。"""
        提供方=None#在镜像里找
        if 自身.客户端清单 is not None:#已同步
            for 项 in 自身.客户端清单:#逐条
                if 'id' in 项 and 项['id']==提供方标识:#命中
                    提供方=项#找到
                    break#停
        if 提供方 is None:#未同步
            raise 动态插件错误('Client Cordis inspect provider "'+提供方标识+'" is not registered')#未同步
        方法=找方法(提供方,方法名)#找方法
        if 已中止(信号):#已取消
            raise 动态插件错误('aborted')#取消
        请求标识='inspect-'+str(自身.下一请求)#铸造查询 id
        自身.下一请求+=1#推进
        请求={'requestId':请求标识,'agentId':智能体.id,'provider':提供方标识,'method':方法名}#广播请求
        if 输入 is not None:#有输入才带上
            请求['input']=输入#输入
        结果盒={'resolution':None}#落定盒

        def 落定(决议):
            """写入结果盒。"""
            结果盒['resolution']=决议#写入

        自身.挂起[请求标识]={'request':请求,'method':方法,'settle':落定}#挂起

        def 取消():
            """取消决议。"""
            if 请求标识 not in 自身.挂起:#已落定
                return#返回
            挂起=自身.挂起[请求标识]#仍在等
            del 自身.挂起[请求标识]#拿掉
            挂起['settle']({'ok':False,'reason':'cancelled','message':'Client inspect query '+提供方标识+'.'+方法名+' was cancelled'})#取消决议
            自身.ctx.广播('cordis/inspect-query-resolved',{'requestId':请求标识})#广播已落定

        if 已中止(信号):#已经取消
            取消()#立刻走
        else:#向页面广播
            自身.ctx.广播('cordis/inspect-query',请求)#广播
        决议=结果盒['resolution']#第一条合法回答（同步路径可能仍空）
        if 决议 is None:#仍在等——同步宿主侧无法阻塞页面；返回挂起说明
            raise 动态插件错误('Client inspect query '+提供方标识+'.'+方法名+' is pending page response')#等待页面
        if 'ok' not in 决议 or not 决议['ok']:#失败则抛
            消息=决议['message'] if 'message' in 决议 else ''#失败消息
            raise 动态插件错误(提供方标识+'.'+方法名+': '+str(消息))#失败
        return 决议['data']#数据

宿主巡检提供方登记=dict#登记项形态：manifest + query
