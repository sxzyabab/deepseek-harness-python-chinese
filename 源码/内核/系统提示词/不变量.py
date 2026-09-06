"""系统提示词组装的包内不变量。对齐上游 `@deepseek-ai/dsh-system-prompt/invariant`。"""
import json,re#json 与正则

包名='@deepseek-ai/dsh-system-prompt'#本包名
变量名规则=re.compile(r'^[a-z][a-z0-9_]*$',re.ASCII)#与根模块相同的合法变量名
名称='system-prompt-invariant'#配套插件名
注入=['invariants']#依赖 invariants 服务

def 是否合法变量名(名):
    """对齐 /^[a-z][a-z0-9_]*$/.test：必须是字符串且整串匹配。"""
    if not isinstance(名,str):
        return False#非字符串非法
    return 变量名规则.fullmatch(名) is not None#整串合法

def 校验组装(组装,失败):
    """校验瀑布链返回的权威组装结果。"""
    已见段落=set()#已见段落名
    for 段 in 组装['sections']:
        if len(段['name'])==0:
            失败('assembled section names must be non-empty')#段落名不得为空
        if 段['name'] in 已见段落:
            失败('assembled section name '+json.dumps(段['name'],ensure_ascii=False,separators=(',',':'),allow_nan=False)+' is duplicated')#段落名不得重复
        已见段落.add(段['name'])#记下段落名
        if not isinstance(段['text'],str):
            失败('assembled section '+json.dumps(段['name'],ensure_ascii=False,separators=(',',':'),allow_nan=False)+' text must be a string')#段落文本必须是字符串
    已见上下文=set()#已见上下文名
    for 上下文块 in 组装['contexts']:
        if len(上下文块['name'])==0:
            失败('assembled context names must be non-empty')#上下文名不得为空
        if 上下文块['name'] in 已见上下文:
            失败('assembled context name '+json.dumps(上下文块['name'],ensure_ascii=False,separators=(',',':'),allow_nan=False)+' is duplicated')#上下文名不得重复
        已见上下文.add(上下文块['name'])#记下上下文名
        if not isinstance(上下文块['text'],str):
            失败('assembled context '+json.dumps(上下文块['name'],ensure_ascii=False,separators=(',',':'),allow_nan=False)+' text must be a string')#上下文文本必须是字符串
    for 工具 in 组装['tools']:
        if len(工具['name'])==0:
            失败('assembled tool names must be non-empty')#工具名不得为空
    for 名,值 in 组装['variables'].items():
        if not 是否合法变量名(名):
            失败('assembled variable name '+json.dumps(名,ensure_ascii=False,separators=(',',':'),allow_nan=False)+' is invalid')#变量名须合法
        if 值 is not None and not isinstance(值,str):
            失败('assembled variable '+json.dumps(名,ensure_ascii=False,separators=(',',':'),allow_nan=False)+' must be a string or undefined')#变量值须为字符串或缺省

def 安装(上下文对象,失败):
    """在权威组装瀑布结果外包一层校验。"""
    def 监听(_载体,_组装,_上下文,下一步):
        """先得到组装结果再校验。"""
        已组装=下一步()#组装已是同步
        校验组装(已组装,失败)#校验结果
        return 已组装#原样交回
    上下文对象.监听('system-prompt/assemble',监听,{'全局':True,'前置':True})#全局且前置

def 应用(上下文对象):
    """注册系统提示词不变量配套。"""
    return 上下文对象.invariants.register(包名,安装)#登记贡献并返回拆除器

应用.name=名称#Cordis name 槽
应用.inject=注入#Cordis inject 槽
default=应用#Cordis 默认导出槽
