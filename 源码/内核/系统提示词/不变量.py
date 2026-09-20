import json,re#json 与正则

包名='@deepseek-ai/dsh-system-prompt'#本包名
变量名规则=re.compile(r'^[a-z][a-z0-9_]*\Z',re.ASCII)#与根模块相同的合法变量名
名称='system-prompt-invariant'#配套插件名
依赖=['invariants']

def 是否合法变量名(名):
    """必须是字符串且整串匹配小写变量名规则。"""
    if not isinstance(名,str):
        return False#非字符串非法
    return 变量名规则.fullmatch(名) is not None#整串合法

def 校验组装(组装,失败):
    """校验瀑布链返回的权威组装结果。"""
    已见段落=set()#已见段落名
    for 段 in 组装['sections']:
        if len(段['name'])==0:
            失败('组装后的段落名不得为空')#段落名不得为空
        if 段['name'] in 已见段落:
            失败('组装后的段落名 '+json.dumps(段['name'],ensure_ascii=False,separators=(',',':'),allow_nan=False)+' 重复')#段落名不得重复
        已见段落.add(段['name'])#记下段落名
        if not isinstance(段['text'],str):
            失败('组装后的段落 '+json.dumps(段['name'],ensure_ascii=False,separators=(',',':'),allow_nan=False)+' 的 text 必须是字符串')#段落文本必须是字符串
    已见上下文=set()#已见上下文名
    for 上下文块 in 组装['contexts']:
        if len(上下文块['name'])==0:
            失败('组装后的上下文名不得为空')#上下文名不得为空
        if 上下文块['name'] in 已见上下文:
            失败('组装后的上下文名 '+json.dumps(上下文块['name'],ensure_ascii=False,separators=(',',':'),allow_nan=False)+' 重复')#上下文名不得重复
        已见上下文.add(上下文块['name'])#记下上下文名
        if not isinstance(上下文块['text'],str):
            失败('组装后的上下文 '+json.dumps(上下文块['name'],ensure_ascii=False,separators=(',',':'),allow_nan=False)+' 的 text 必须是字符串')#上下文文本必须是字符串
    for 工具 in 组装['tools']:
        if len(工具['name'])==0:
            失败('组装后的工具名不得为空')#工具名不得为空
    for 名,值 in 组装['variables'].items():
        if not 是否合法变量名(名):
            失败('组装后的变量名 '+json.dumps(名,ensure_ascii=False,separators=(',',':'),allow_nan=False)+' 非法')#变量名须合法
        if 值 is not None and not isinstance(值,str):
            失败('组装后的变量 '+json.dumps(名,ensure_ascii=False,separators=(',',':'),allow_nan=False)+' 必须是字符串或未定义')#变量值须为字符串或缺省

def 安装(上下文,失败):
    """在权威组装瀑布结果外包一层校验。"""
    def 监听(_载体,_组装,_上下文,下一步):
        """先得到组装结果再校验。"""
        已组装=下一步()#组装已是同步
        校验组装(已组装,失败)#校验结果
        return 已组装#原样交回
    上下文.监听('system-prompt/assemble',监听,{'全局':True,'前置':True})#全局且前置

def 应用(上下文):
    """注册系统提示词不变量配套。"""
    return 上下文.invariants.register(包名,安装)#登记贡献并返回拆除器

应用.name=名称#Cordis name 槽
应用.inject=依赖
default=应用#Cordis 默认导出槽
