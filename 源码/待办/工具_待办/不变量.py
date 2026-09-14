import json#JSON 片段
包名='@deepseek-ai/dsh-tool-todo'#本包的不变量所有权名
名称='tool-todo-invariant'#配套不变量插件名（字面量）
注入=['invariants']#依赖 invariants 服务
待办状态集合=set(('pending','in_progress','completed'))#耐久允许的三态

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 编码内容(值):#对齐 JSON.stringify 的报错片段
    """把值编成 JSON 片段，对齐 TypeScript JSON.stringify。"""
    return json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False)#JSON 片段

def 校验待办列表(值,失败):#校验一整表快照
    """校验一条整表待办快照。故意不限制 in_progress 条数：那是工具的部署政策，不是耐久形状规则。"""
    if not isinstance(值,list):#必须是数组
        失败('todo/write 的 todos 必须是数组')#不是数组
        return#已失败
    已见=set()#已见内容
    for 条目 in 值:#逐条
        if not isinstance(条目,dict):#必须是对象
            失败('todo/write 条目必须是对象')#不是对象
            continue#下一条仍扫完
        内容=条目['content'] if 'content' in 条目 else None#任务文案
        状态=条目['status'] if 'status' in 条目 else None#生命周期
        if (not isinstance(内容,str)) or len(内容)==0 or 内容.strip()!=内容:#必须非空且已修剪
            失败('todo/write 的 content 必须非空且已修剪')#内容非法
        if 内容 in 已见:#内容重复
            失败('todo/write 重复了 content '+编码内容(内容))#重复内容
        已见.add(内容)#记下
        if (not isinstance(状态,str)) or 状态 not in 待办状态集合:#未知状态
            失败('todo/write 携带未知 status '+编码内容(状态))#未知状态

def 校验事件(事件,失败):#只认本包事件
    """校验本包拥有的事件字段，无关事件放过。"""
    if 事件['type']=='todo/write':#整表写入
        校验待办列表(事件['data']['todos'],失败)#校验载荷

def 安装(上下文对象,失败):#安装已加载与新追加校验
    """为已加载和新追加的整表待办快照安装校验。"""
    for 会话 in 上下文对象.sessions.list():#已有会话
        for 事件 in 会话.events:#日志
            校验事件(事件,失败)#先校验
    def 内部派发(_模式,事件名,参数,*其余):#提交前检查
        """提交前检查 session/event。"""
        if 事件名!='session/event':#非会话事件
            return#放过
        事件=参数[1]#第二实参是事件
        校验事件(事件,失败)#校验
    上下文对象.监听('internal/dispatch',内部派发,{'全局':True})#全局监听

安装.inject=['sessions']#安装时还要 sessions

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文对象.invariants.register(包名,安装)#登记贡献

name=名称#Cordis插件名
inject=注入#Cordis依赖声明
apply=应用#Cordis插件入口
