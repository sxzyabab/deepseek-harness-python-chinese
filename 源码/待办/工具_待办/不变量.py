"""`@deepseek-ai/dsh-tool-todo` 的本包拥有不变量配套：校验耐久待办整表快照。

对齐上游 `tool-todo/src/invariant.ts`。公开面仅中文名。

故意不约束有多少条是 `in_progress`。那是工具的按部署政策（`allowParallelInProgress`），不是耐久形状规则：在允许并行工作时写出的日志，在部署收紧策略后仍必须能回放。
"""
import json#JSON 片段
from ...依赖 import cordis#外部依赖胶水
包名='@deepseek-ai/dsh-tool-todo'#本包的不变量所有权名
名称='tool-todo-invariant'#配套不变量插件名（字面量）
注入=['invariants']#依赖 invariants 服务
待办状态集合=set(('pending','in_progress','completed'))#耐久允许的三态

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 编码内容(值):#对齐 JSON.stringify 的报错片段
    """把值编成 JSON 片段，对齐 TypeScript JSON.stringify。"""
    return json.dumps(值,ensure_ascii=False)#JSON 片段

def 校验待办们(值,失败):#校验一整表快照
    """校验一条整表待办快照。故意不限制 in_progress 条数：那是工具的部署政策，不是耐久形状规则。"""
    if not isinstance(值,list):#必须是数组
        失败('todo/write todos must be an array')#不是数组
        return#已失败
    已见=set()#已见内容
    for 条目 in 值:#逐条
        if not isinstance(条目,dict) or 条目 is None:#必须是对象
            失败('todo/write entries must be objects')#不是对象
            continue#下一条仍扫完
        内容=取字段(条目,'content')#任务文案
        状态=取字段(条目,'status')#生命周期
        if (not isinstance(内容,str)) or len(内容)==0 or 内容.strip()!=内容:#必须非空且已修剪
            失败('todo/write content must be non-empty and already trimmed')#内容非法
        if 内容 in 已见:#内容重复
            失败('todo/write repeats content '+编码内容(内容))#重复内容
        已见.add(内容)#记下
        if (not isinstance(状态,str)) or 状态 not in 待办状态集合:#未知状态
            失败('todo/write carries unknown status '+编码内容(状态))#未知状态

def 校验事件(事件,失败):#只认本包事件
    """校验本包拥有的事件字段，无关事件放过。"""
    if 取字段(事件,'type')=='todo/write':#整表写入
        校验待办们(取字段(取字段(事件,'data'),'todos'),失败)#校验载荷

def 安装(上下文对象,失败):#安装已加载与新追加校验
    """为已加载和新追加的整表待办快照安装校验。"""
    for 会话对象 in 上下文对象.sessions.list():#已有会话
        for 事件 in 会话对象.events:#日志
            校验事件(事件,失败)#先校验
    def 内部派发(_模式,事件名,参数,*其余):#提交前检查
        """提交前检查 session/event。"""
        if 事件名!='session/event':#非会话事件
            return#放过
        事件=参数[1]#第二实参是事件
        校验事件(事件,失败)#校验
    上下文对象.on('internal/dispatch',内部派发,{'global':True})#全局监听

安装.inject=['sessions']#安装时还要 sessions

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记并包成立即兑现的承诺
