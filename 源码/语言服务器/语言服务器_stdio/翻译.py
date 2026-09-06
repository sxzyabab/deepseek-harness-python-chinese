"""本地宿主的纯协议翻译：服务器能力允许什么，以及如何把其 Location/LocationLink/Hover 载荷归一成 seam 的封闭结果联合。无 I/O、无进程状态——这里每个函数都是纯变换，假 stdio 测试会精确钉住。"""
from ..语言服务器 import 语言服务器错误#带稳定code的语言服务器错误
from ...模型后端.llm import 断言永不#封闭联合穷尽断言

def 请求方法(操作):
    """每种 LSP 操作对应的 textDocument/* 请求方法。"""
    if 操作=='goToDefinition':#定义查询
        return 'textDocument/definition'#方法名
    if 操作=='findReferences':#引用查询
        return 'textDocument/references'#方法名
    if 操作=='goToImplementation':#实现查询
        return 'textDocument/implementation'#方法名
    if 操作=='hover':#悬停查询
        return 'textDocument/hover'#方法名
    return 断言永不(操作,'requestMethod')#封闭联合穷尽

def 能力值(能力,操作):
    """每种操作背后的 ServerCapabilities 提供方字段。能力是 LSP 报文 dict。"""
    if 操作=='goToDefinition':#定义能力
        return 能力['definitionProvider'] if 'definitionProvider' in 能力 else None#槽
    if 操作=='findReferences':#引用能力
        return 能力['referencesProvider'] if 'referencesProvider' in 能力 else None#槽
    if 操作=='goToImplementation':#实现能力
        return 能力['implementationProvider'] if 'implementationProvider' in 能力 else None#槽
    if 操作=='hover':#悬停能力
        return 能力['hoverProvider'] if 'hoverProvider' in 能力 else None#槽
    return 断言永不(操作,'capabilityValue')#封闭联合穷尽

def 支持能力(值):
    """服务器送来 true 或选项对象（不是 false/缺席）时，提供方能力视为存在。"""
    if 值 is None:#缺席则不支持
        return False#不支持
    if isinstance(值,bool):#布尔则原样
        return 值#原样
    return True#选项对象视为支持

def 支持操作(能力,操作):
    """服务器是否宣称支持所请求的操作。能力是 LSP 报文 dict。"""
    return 支持能力(能力值(能力,操作))#查对应能力槽

def 是打开关闭种类(种类):
    """遗留枚举：Full(1) 或 Incremental(2) 隐含打开/关闭；None(0) 不支持。"""
    return 种类==1 or 种类==2#Full或Incremental

def 支持瞬时打开(同步):
    """textDocumentSync 值是否允许本宿主依赖的瞬时 didOpen/didClose。遗留枚举形态对 Full/Incremental 隐含打开/关闭；选项形态要求显式 openClose: true，因为协议把省略的 openClose 默认成 false。同步是 LSP 报文。"""
    if 同步 is None:#未宣称则不支持
        return False#不支持
    if isinstance(同步,bool):#布尔不是枚举
        return False#不支持
    if isinstance(同步,(int,float)):#枚举形态按种类判断
        return 是打开关闭种类(同步)#按种类
    if 'openClose' not in 同步:#选项形态省略则默认 false
        return False#不支持
    return 同步['openClose'] is True#必须显式 openClose: true

def 协商位置编码(编码):
    """归一协商出的位置编码。省略时默认 utf-16；任何非 utf-16 值都是本宿主不支持的协议错误。"""
    if 编码 is None or 编码=='utf-16':#缺省或utf-16则接受
        return 'utf-16'#锁定
    raise 语言服务器错误('server negotiated unsupported position encoding "'+str(编码)+'"; this host requires utf-16','LSP_PROTOCOL')#拒绝其他编码

def 转范围(范围):
    """把线协议范围转成 seam 范围（结构相同，但重塑为只读映射）。范围是 dict。"""
    起点=范围['start']#起点
    终点=范围['end']#终点
    return {#组装只读范围
        'start':{'line':起点['line'],'character':起点['character']},#起点
        'end':{'line':终点['line'],'character':终点['character']},#终点
    }#LspRange结束

def 是协议坐标(值):
    """线坐标是否为有效的非负整数。排除布尔。"""
    if isinstance(值,bool):#布尔不是整数
        return False#否
    return isinstance(值,int) and 值>=0#非负整数

def 是位置(值):
    """结构位置守卫。位置是 dict。"""
    if isinstance(值,dict) is False:#非映射
        return False#否
    if 'line' not in 值 or 'character' not in 值:#缺字段
        return False#否
    return 是协议坐标(值['line']) and 是协议坐标(值['character'])#行列都必须是协议坐标

def 是范围(值):
    """两种位置形态共用的结构范围守卫。范围是 dict。"""
    if isinstance(值,dict) is False:#非映射
        return False#否
    if 'start' not in 值 or 'end' not in 值:#缺字段
        return False#否
    return 是位置(值['start']) and 是位置(值['end'])#起止都必须是位置

def 是定位链接(记录):
    """记录是否为 LocationLink（有 targetUri + targetSelectionRange）。记录是 dict。"""
    if 'targetUri' not in 记录 or 'targetSelectionRange' not in 记录:#缺字段
        return False#否
    return isinstance(记录['targetUri'],str) and 是范围(记录['targetSelectionRange'])#目标uri加选择范围

def 是定位(记录):
    """记录是否为 Location（有字符串 uri + 一段范围）。记录是 dict。"""
    if 'uri' not in 记录 or 'range' not in 记录:#缺字段
        return False#否
    return isinstance(记录['uri'],str) and 是范围(记录['range'])#uri加range

def 畸形响应(消息):
    """为畸形服务器结果载荷创建稳定的结构化错误。"""
    return 语言服务器错误(消息,'LSP_MALFORMED_RESPONSE')#带稳定code

def 归一位置列表(载荷):
    """把导航结果（Location、Location[]、LocationLink[] 或 null）归一成 seam 的位置列表。Location 直接映射；LocationLink 映射 targetUri + targetSelectionRange。"""
    if 载荷 is None:#null视为无结果
        return []#空列表
    元素列表=载荷 if isinstance(载荷,list) else [载荷]#单值包成数组
    位置列表=[]#收集归一化位置
    for 元素 in 元素列表:#逐条翻译
        if isinstance(元素,dict) is False:#非对象条目
            raise 畸形响应('LSP navigation result contained a non-object entry')#拒绝非对象
        if 是定位链接(元素):#LocationLink形态
            位置列表.append({'uri':元素['targetUri'],'range':转范围(元素['targetSelectionRange'])})#用选择范围
        elif 是定位(元素):#Location形态
            位置列表.append({'uri':元素['uri'],'range':转范围(元素['range'])})#用uri加range
        else:#两种都不是
            raise 畸形响应('LSP navigation result contained neither a Location nor a LocationLink')#拒绝未知形态
    return 位置列表#返回全部位置

def 渲染带标记字符串(值):
    """渲染一个 MarkedString（字符串形态原样；对象形态为带语言标签的围栏代码块）。值是 str 或 dict。"""
    if isinstance(值,str):#字符串形态原样
        return 值#原样
    return '```'+str(值['language'])+'\n'+str(值['value'])+'\n```'#对象形态围成代码块

def 是带标记字符串(值):
    """不受信任的值是否为 MarkedString 的任一种形态。"""
    if isinstance(值,str):#字符串形态
        return True#是
    if isinstance(值,dict) is False:#非映射
        return False#否
    if 'language' not in 值 or 'value' not in 值:#缺字段
        return False#否
    return isinstance(值['language'],str) and isinstance(值['value'],str)#语言加正文

def 渲染悬停内容(内容):
    """把三种 Hover.contents 编码渲染成一个字符串（输入是不受信任的线数据）。"""
    if 内容 is None:#缺少contents
        raise 畸形响应('LSP hover result had no contents')#拒绝空contents
    if isinstance(内容,str):#字符串MarkedString原样
        return 内容#原样
    if isinstance(内容,list):#MarkedString数组
        片段=[]#渲染片段
        for 项 in 内容:#逐项渲染再空行拼接
            if 是带标记字符串(项):#合法则渲染
                片段.append(渲染带标记字符串(项))#渲染
            else:#非法项
                raise 畸形响应('LSP hover contents contained a malformed MarkedString')#拒绝
        return '\n\n'.join(片段)#用空行拼接
    if isinstance(内容,dict) is False:#既非字符串也非对象
        raise 畸形响应('LSP hover contents were not MarkupContent, MarkedString, or an array')#拒绝未知类型
    种类=内容['kind'] if 'kind' in 内容 else None#标记种类
    if 种类=='markdown' or 种类=='plaintext':#MarkupContent形态
        if 'value' not in 内容 or isinstance(内容['value'],str) is False:#value不是字符串
            raise 畸形响应('LSP hover MarkupContent value was not a string')#拒绝非字符串value
        return 内容['value']#交出标记正文
    if 'language' in 内容 and 'value' in 内容 and isinstance(内容['language'],str) and isinstance(内容['value'],str):#带语言的MarkedString对象
        return 渲染带标记字符串({'language':内容['language'],'value':内容['value']})#按代码块渲染
    raise 畸形响应('LSP hover contents were not MarkupContent, MarkedString, or an array')#三种编码都不匹配

def 归一悬停(载荷):
    """把 Hover（或 null）归一成 seam 悬停。MarkupContent 用其 value；字符串 MarkedString 原样；带语言标签的 MarkedString 变成围栏代码块；数组用一个空行拼接各渲染片段。面向模型的工具拥有完整结果上限。载荷是 dict。"""
    if 载荷 is None:#null表示无悬停
        return None#无悬停
    if isinstance(载荷,dict) is False:#非对象则畸形（字符串不是Hover信封）
        raise 畸形响应('LSP hover result was not an object')#非对象则畸形
    if 'contents' not in 载荷:#缺少contents
        raise 畸形响应('LSP hover result had no contents')#拒绝
    内容=渲染悬停内容(载荷['contents'])#渲染三种contents编码
    if 内容=='':#空正文视为无悬停
        return None#无悬停
    if 'range' not in 载荷:#无范围键则只交正文
        return {'contents':内容}#无范围
    范围=载荷['range']#取出可选范围
    if 范围 is None:#显式null范围按协议视为畸形范围
        raise 畸形响应('LSP hover result contained a malformed range')#拒绝
    if 是范围(范围) is False:#范围结构无效
        raise 畸形响应('LSP hover result contained a malformed range')#拒绝
    return {'contents':内容,'range':转范围(范围)}#带范围的悬停
