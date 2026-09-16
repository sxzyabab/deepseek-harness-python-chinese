"""外层输出账本用的 JSON 字符串前缀计量。"""
__all__=['json字符串字节上限','json值字节上限','截断json字符串字节']#仅中文公开名

原生列表=list#模块捕获的 list
原生字典=dict#模块捕获的 dict
原生类型=type#模块捕获的 type
原生字符串=str#模块捕获的 str
原生长度=len#模块捕获的 len

def 字节长度(文本):#UTF-8 字节数
    """经 UTF-8 计算字节长度。"""
    return 原生长度(文本.encode('utf-8'))#UTF-8 字节

def 序列化字符字节(字符):#JSON 引号内一个码点的序列化字节
    """一个完整 Unicode 码点在 JSON 引号内贡献的序列化字节。"""
    码=ord(字符)#码点
    if 码>0xffff:#增补平面
        return 4#UTF-8 四字节
    if 字符=='"' or 字符=='\\':#需转义
        return 2#反斜杠加字符
    if 码>=0xd800 and 码<=0xdfff:#孤立代理
        return 6#\\uXXXX
    if 码<0x20:#控制字符
        if 码==0x08 or 码==0x09 or 码==0x0a or 码==0x0c or 码==0x0d:#短转义
            return 2#\\b \\t \\n \\f \\r
        return 6#\\uXXXX
    return 字节长度(字符)#其余按 UTF-8

def json字符串字节上限(文本,最大字节):#计量一个 JSON 字符串
    """计量一个 JSON 字符串而不物化完整转义形式。文本是候选字符串。最大字节是调用方可接纳的最大序列化大小。返回精确序列化字节；一越过上限就返回空。"""
    if 最大字节<2:#连引号都放不下
        return None#越界
    字节=2#左右引号
    for 字符 in 文本:#逐码点
        字节+=序列化字符字节(字符)#累加
        if 字节>最大字节:#越界
            return None#越界
    return 字节#精确字节

def json值字节上限(值,最大字节):#计量一个无损 JSON 值
    """计量一个无损 JSON 值而不分配序列化文本。值已校验为无损 JSON。最大字节是调用方可接纳的最大序列化大小。返回精确序列化字节；一越过上限就返回空。"""
    字节=0#已计入
    def 加上(代价):#累加并检查
        """累加代价，未越界为真。"""
        nonlocal 字节#写外层
        字节+=代价#累加
        return 字节<=最大字节#未越界
    任务=[{'kind':'value','value':值}]#根任务
    while 原生长度(任务)>0:#直到栈空
        当前=任务.pop()#弹出
        if 当前['kind']=='value':#一个值
            节点=当前['value']#当前值
            if 节点 is None:#null
                if not 加上(4):#null 四字节
                    return None#越界
            elif 原生类型(节点) is str:#字符串
                串字节=json字符串字节上限(节点,最大字节-字节)#字符串预算
                if 串字节 is None:#越界
                    return None#越界
                字节+=串字节#累加
            elif 原生类型(节点) is bool:#布尔须先于 int
                if not 加上(4 if 节点 else 5):#true/false
                    return None#越界
            elif 原生类型(节点) in (int,float):#数字
                if not 加上(字节长度(原生字符串(节点))):#数字文本
                    return None#越界
            elif 原生类型(节点) is 原生列表:#数组
                if not 加上(2):#[]
                    return None#越界
                if 原生长度(节点)>0:#非空
                    任务.append({'kind':'array','value':节点,'index':0})#数组帧
            else:#对象
                if not 加上(2):#{}
                    return None#越界
                键列表=原生列表(节点.keys())#自有键
                if 原生长度(键列表)>0:#非空
                    任务.append({'kind':'object','value':节点,'keys':键列表,'index':0})#对象帧
            continue#下一任务
        if 当前['index']>0 and not 加上(1):#分隔逗号
            return None#越界
        if 当前['kind']=='array':#数组项
            项=当前['value'][当前['index']]#取出项
            if 当前['index']+1<原生长度(当前['value']):#还有后续
                任务.append({'kind':'array','value':当前['value'],'index':当前['index']+1})#推进
            任务.append({'kind':'value','value':项})#访问项
            continue#下一任务
        键=当前['keys'][当前['index']]#对象键
        键字节=json字符串字节上限(键,最大字节-字节)#键字符串
        if 键字节 is None:#越界
            return None#越界
        if not 加上(键字节+1):#键加冒号
            return None#越界
        项=当前['value'][键]#属性值
        if 当前['index']+1<原生长度(当前['keys']):#还有后续
            任务.append({'kind':'object','value':当前['value'],'keys':当前['keys'],'index':当前['index']+1})#推进
        任务.append({'kind':'value','value':项})#访问属性
    return 字节#精确字节

def 截断json字符串字节(文本,最大字节):#最长可放入预算的码点对齐前缀
    """返回最长码点对齐前缀，其 JSON 字符串编码（含左右引号）放入最大字节。连有用内容都放不下时返回空串。"""
    if 最大字节<2:#连引号都放不下
        return ''#空前缀
    字节=2#左右引号
    结束=0#前缀码点数
    已见=0#已走过的码点数
    for 字符 in 文本:#逐码点
        代价=序列化字符字节(字符)#本字符代价
        if 字节+代价>最大字节:#放不下
            break#停
        字节+=代价#累加
        结束+=1#收下
        已见+=1#走过
    if 结束==原生长度(文本):#全部放下
        return 文本#原串
    return 文本[:结束]#前缀
