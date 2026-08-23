"""系统提示词组装的包内不变量。对齐上游 `@deepseek-ai/dsh-system-prompt/invariant`。公开面仅中文名；Cordis 加载槽 `name` / `inject` / `apply` 为协议兼容别名。"""
import json,re#json 与正则
from ...依赖 import cordis#外部依赖胶水
是否thenable=cordis.工具.是否thenable#可等待判定
已兑现=cordis.工具.已兑现#立刻兑现

包名='@deepseek-ai/dsh-system-prompt'#本包名（登记到 invariants 的所有权键）
变量名规则=re.compile(r'^[a-z][a-z0-9_]*$')#与根模块相同的合法变量名
名称='system-prompt-invariant'#配套插件名（字面量）
注入=['invariants']#预占包所有权前必须具备的服务
name=名称#Cordis 插件名（协议槽）
inject=注入#Cordis 依赖声明（协议槽）

def 取字段(对象,键):
    """读取映射或对象上的必填字段；缺键按原语义抛错。"""
    if isinstance(对象,dict):#普通映射
        return 对象[键]#映射键
    return getattr(对象,键)#对象属性

def 是否合法变量名(名):
    """对齐 /^[a-z][a-z0-9_]*$/.test：必须是字符串且整串匹配。"""
    if not isinstance(名,str):#必须是字符串
        return False#非字符串非法
    return 变量名规则.fullmatch(名) is not None#整串合法

def 校验组装(组装,失败):
    """校验瀑布链返回的权威组装结果：段落/上下文名非空且唯一、文本为字符串、工具名非空、变量名合法且值为字符串或缺省。"""
    已见段落=set()#已见段落名
    for 段 in 取字段(组装,'sections'):#遍历段落
        if len(取字段(段,'name'))==0:#空名
            失败('assembled section names must be non-empty')#段落名不得为空
        if 取字段(段,'name') in 已见段落:#重复
            失败('assembled section name '+json.dumps(取字段(段,'name'))+' is duplicated')#段落名不得重复
        已见段落.add(取字段(段,'name'))#记下段落名
        if not isinstance(取字段(段,'text'),str):#非字符串
            失败('assembled section '+json.dumps(取字段(段,'name'))+' text must be a string')#段落文本必须是字符串
    已见上下文=set()#已见上下文名
    for 上下文块 in 取字段(组装,'contexts'):#遍历上下文块
        if len(取字段(上下文块,'name'))==0:#空名
            失败('assembled context names must be non-empty')#上下文名不得为空
        if 取字段(上下文块,'name') in 已见上下文:#重复
            失败('assembled context name '+json.dumps(取字段(上下文块,'name'))+' is duplicated')#上下文名不得重复
        已见上下文.add(取字段(上下文块,'name'))#记下上下文名
        if not isinstance(取字段(上下文块,'text'),str):#非字符串
            失败('assembled context '+json.dumps(取字段(上下文块,'name'))+' text must be a string')#上下文文本必须是字符串
    for 工具 in 取字段(组装,'tools'):#遍历工具
        if len(取字段(工具,'name'))==0:#空名
            失败('assembled tool names must be non-empty')#工具名不得为空
    for 名,值 in 取字段(组装,'variables').items():#遍历变量
        if not 是否合法变量名(名):#名不合法
            失败('assembled variable name '+json.dumps(名)+' is invalid')#变量名须合法
        if 值 is not None and not isinstance(值,str):#值既不是缺省也不是字符串
            失败('assembled variable '+json.dumps(名)+' must be a string or undefined')#变量值须为字符串或缺省

def 安装(上下文对象,失败):
    """在权威组装瀑布结果外包一层校验：全局且前置，先得到 next() 结果再校验，原样交回。"""
    def 监听(_载体,_组装,_上下文,下一步):#先得到组装结果再校验
        """先得到组装结果再校验。派发 this 由 Cordis 绑成首参。"""
        已组装=下一步()#先得到组装结果
        if 是否thenable(已组装):#可等待
            已组装=已组装.等待()#对齐 await
        校验组装(已组装,失败)#校验结果
        return 已组装#原样交回
    上下文对象.on('system-prompt/assemble',监听,{'global':True,'prepend':True})#全局且前置

def 应用(上下文对象):
    """注册系统提示词不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记贡献并返回已兑现拆除器

apply=应用#Cordis 插件入口（协议槽）
