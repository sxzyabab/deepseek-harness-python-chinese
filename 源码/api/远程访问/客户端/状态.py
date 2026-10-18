'浏览器侧访问快照。答案是稳定身份的布尔源'
import json#不可达帧的诊断

关闭快照={'kind':'closed'}#没有基线，或非所有者流失败
所有者快照={'kind':'owner'}#所有者，答案不依赖流
全局键='\u0000global'#全局资源在缓存键里的种类

def 是记录(值):
    '非空、非列表的 dict'
    return isinstance(值,dict)#对象

def 是资源(值):
    'global 无标识，其它种类必须有字符串标识'
    if not 是记录(值) or not isinstance(值.get('kind'),str):#缺种类
        return False#不是
    return 值['kind']=='global' or isinstance(值.get('id'),str)#合法

def 是授予(值):
    '资源加字符串动作列表'
    if not 是记录(值) or not 是资源(值.get('resource')):#资源非法
        return False#不是
    动作=值.get('actions')#动作
    return isinstance(动作,list) and all(isinstance(项,str) for 项 in 动作)#全是字符串

def 解析注入基线(值):
    '页面注入值。没有注入则空。不是基线则抛类型错误'
    if 值 is None:#没有注入
        return None#空
    if not 是记录(值) or 值.get('type')!='baseline':#不是基线帧
        raise TypeError('remote access: the injected access snapshot is not a baseline frame')#拒绝
    if 值.get('owner') is True:#所有者
        return {'type':'baseline','owner':True}#基线
    授予=值.get('grants')#授予
    if 值.get('owner') is not False or not isinstance(授予,list) or not all(是授予(项) for 项 in 授予):#授予坏了
        raise TypeError('remote access: the injected access snapshot carries malformed grants')#拒绝
    return {'type':'baseline','owner':False,'grants':授予}#非所有者基线

def 回答(快照,种类,标识,动作):
    '当前快照对这一问的布尔答案'
    种类名=快照['kind']#快照种类
    if 种类名=='closed':#没有快照
        return False#不允许
    if 种类名=='owner':#所有者
        return True#允许
    if 种类名=='granted':#按授予
        if 种类==全局键:#全局
            允许=快照['global']#全局动作
        else:#具体资源
            按种类=快照['resources'].get(种类)#这一类
            允许=None if 按种类 is None else 按种类.get(标识)#这一项
        return False if 允许 is None else 动作 in 允许#有没有这个动作
    raise RuntimeError('unreachable access frame: '+json.dumps(快照))#封闭种类

def 带授予(快照,授予,移除=False):
    '在已授予快照上更新或去掉一项，返回新快照'
    资源=授予['resource']#资源
    if 资源['kind']=='global':#全局
        副本=dict(快照)#拷贝
        副本['global']=set(授予['actions'])#换成新动作
        return 副本#新快照
    资源表=dict(快照['resources'])#拷贝种类表
    原表=资源表.get(资源['kind'])#这一类
    授予表={} if 原表 is None else dict(原表)#拷贝
    if 移除:#去掉
        授予表.pop(资源['id'],None)#删
    else:#更新
        授予表[资源['id']]=set(授予['actions'])#新动作
    资源表[资源['kind']]=授予表#写回
    副本=dict(快照)#拷贝
    副本['resources']=资源表#新表
    return 副本#新快照

class 客户端访问状态:
    '一代快照的所有者。同一种类、标识、动作共用一个布尔源'
    def __init__(自身,初始=None):
        '没有初始基线时，基线到达前全部答案为不允许'
        自身.快照=关闭快照#默认关闭
        自身.监听者=set()#订阅
        自身.来源表={}#缓存的布尔源
        if 初始 is not None:#有注入基线
            自身.替换基线(初始)#先用它

    def 全局许可(自身,动作):
        '全局资源上一个动作是否允许'
        return 自身._缓存(全局键,'',动作)#稳定源

    def 资源许可(自身,种类,标识,动作):
        '一个资源上的动作是否允许'
        return 自身._缓存(种类,标识,动作)#稳定源

    def 替换基线(自身,帧):
        '用一代的开口帧替换快照'
        if 帧['owner']:#所有者
            自身._发布(所有者快照)#所有者
            return#完
        全局=set()#全局动作
        资源表={}#种类到标识
        for 项 in 帧['grants']:#逐条授予
            资源=项['resource']#资源
            动作=项['actions']#动作
            if 资源['kind']=='global':#全局
                全局=set(动作)#替换
                continue#下一条
            授予表=资源表.get(资源['kind'])#这一类
            if 授予表 is None:#还没有
                授予表={}#新建
                资源表[资源['kind']]=授予表#记下
            授予表[资源['id']]=set(动作)#这一项
        自身._发布({'kind':'granted','global':全局,'resources':资源表})#发布

    def 更新帧(自身,帧):
        '应用更新或移除。还不是已授予快照则忽略'
        当前=自身.快照#当前
        if 当前['kind']!='granted':#还不能增量
            return#忽略
        if 帧['type']=='upsert':#更新
            自身._发布(带授予(当前,帧['grant']))#写入
            return#完
        if 帧['type']=='remove':#移除
            自身._发布(带授予(当前,{'resource':帧['resource'],'actions':[]},True))#删掉
            return#完

    @property
    def 是所有者(自身):
        '当前快照是不是所有者'
        return 自身.快照['kind']=='owner'#所有者

    def 标记不可用(自身):
        '流终态失败。所有者答案不变，非所有者改为不允许'
        if 自身.快照['kind']!='owner':#非所有者
            自身._发布(关闭快照)#关闭

    def _缓存(自身,种类,标识,动作):
        '同一三元组返回同一个源'
        键=种类+'\u0000'+标识+'\u0000'+动作#缓存键
        来源=自身.来源表.get(键)#已有
        if 来源 is None:#新建
            def 取快照():
                '读当前答案'
                return 回答(自身.快照,种类,标识,动作)#布尔
            def 订阅(监听):
                '登记监听，返回卸下函数'
                自身.监听者.add(监听)#登记
                def 卸下():
                    '卸下这一份'
                    自身.监听者.discard(监听)#卸
                return 卸下#拆除
            来源={'getSnapshot':取快照,'subscribe':订阅}#稳定源
            自身.来源表[键]=来源#缓存
        return 来源#源

    def _发布(自身,下一份):
        '换上快照并通知监听者'
        自身.快照=下一份#换
        for 监听 in list(自身.监听者):#拷贝，避免回调里改集合
            监听()#通知
