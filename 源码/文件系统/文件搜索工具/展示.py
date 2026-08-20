"""`grep` 与 `glob` 在结果时刻的搜索卡片展示。两种工具都落到同一种 `card: 'search'` 渲染意图，再用 `shape` 判别两种变体：`grep` 按文件分组投影命中，`glob` 投影扁平路径列表。本模块拥有各工具声明的值→`presentationMeta` 投影，以及各工具 `presentResult` 在回放时读回的防御性 `meta`→视图收窄。

规范值从不跨线传输——只有面向模型的渲染文本与这份 JSON `meta` 会传输——因此 UI 渲染的结构化形态必须骑在 `meta` 上。每次投影消费的保留命中/路径与面向模型的渲染相同，所以文本与卡片对哪些结果活过内联上限意见一致，并报告 `total` 与 `truncated`。

第二道独立上限约束 JSON `meta` 本身：宽搜索的保留命中仍可能序列化到数百 KB，而 `meta` 会随会话日志持久化并在每次请求重发。`限制元字节` 丢掉尾部文件组/路径直到序列化后的 `meta` 适合 `maxMetaBytes`，并标记 `truncated`；部署的最终输出预算只缩小 `content`、从不缩小 `meta`，因此由本投影负责把 `meta` 限制在预算内。
"""
import json#meta序列化字节计量

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 字节长(文本):#UTF-8字节长度
    """对齐 Buffer.byteLength(text, 'utf8')。"""
    return len(文本.encode('utf-8'))#按utf8计字节

def 按文件分组命中(命中们):#按文件首次出现顺序分组命中
    """按文件分组扁平命中（首次出现顺序），做成 UI 可展开的按文件结构。分组与面向模型的文本分组一致，因此卡片与文本对文件顺序与成员意见一致。"""
    按文件={}#路径到该文件命中列表（有序）
    顺序=[]#首次出现的路径顺序
    for 命中 in 命中们:#按输出顺序遍历命中
        条目={'lineNumber':取字段(命中,'lineNumber'),'line':取字段(命中,'line')}#本行的可序列化命中
        路径=取字段(命中,'path')#文件路径
        if 路径 in 按文件:#已有该文件的分组
            按文件[路径].append(条目)#已有则追加
        else:#没有则新建分组
            按文件[路径]=[条目]#新建
            顺序.append(路径)#记下首次出现顺序
    return [{'path':路径,'matches':按文件[路径]} for 路径 in 顺序]#按首次出现顺序的数组

def 元字节(元):#计算meta序列化后的UTF-8字节数
    """一份 meta 载荷序列化后的 UTF-8 字节大小（持久化并重发的大小）。"""
    return 字节长(json.dumps(元,ensure_ascii=False,separators=(',',':')))#按utf8计序列化字节

def 限制元字节(元,最大元字节):#把序列化meta压进字节预算
    """丢掉尾部顶层项（文件组或路径），直到序列化后的 meta 适合 maxMetaBytes；丢掉任何项时标记 truncated。total 保留。单独一项大到塞不进预算时仍保留：不变量是在可丢处有界，绝不是一张空卡片把真实结果藏起来。"""
    if 元字节(元)<=最大元字节:#已适合则原样返回
        return 元#原样
    if 取字段(元,'shape')=='matches':#按文件分组形态
        文件们=list(取字段(元,'files') or [])#复制分组以便弹出尾部
        while len(文件们)>1 and 元字节({**元,'files':文件们,'truncated':True})>最大元字节:#至少留一组，超预算则弹尾
            文件们.pop()#弹尾
        return {**元,'files':文件们,'truncated':True}#返回截断后的matches meta
    路径们=list(取字段(元,'paths') or [])#复制路径以便弹出尾部
    while len(路径们)>1 and 元字节({**元,'paths':路径们,'truncated':True})>最大元字节:#至少留一条，超预算则弹尾
        路径们.pop()#弹尾
    return {**元,'paths':路径们,'truncated':True}#返回截断后的paths meta

def grep搜索元(保留页,最大元字节):#投影grep保留页为搜索卡片meta
    """把已保留的 grep 命中投影为搜索卡片用的 SearchMeta。消费与面向模型渲染相同的保留结果，按文件分组，报告 total 与 truncated，再把序列化 meta 限制到 maxMetaBytes。"""
    元={#按文件分组的meta
        'shape':'matches',#命中形态
        'files':按文件分组命中(取字段(保留页,'items') or []),#保留命中按文件分组
        'truncated':bool(取字段(保留页,'truncated')),#内联是否已截断
        'total':取字段(保留页,'seen'),#截断前命中总数
    }#grep meta组装结束
    return 限制元字节(元,最大元字节)#再按字节预算截尾

def glob搜索元(保留页,最大元字节):#投影glob保留页为搜索卡片meta
    """把已保留的 glob 路径投影为搜索卡片用的 SearchMeta。消费与面向模型渲染相同的保留结果，报告 total 与 truncated，再把序列化 meta 限制到 maxMetaBytes。"""
    元={#扁平路径的meta
        'shape':'paths',#路径形态
        'paths':list(取字段(保留页,'items') or []),#保留的路径页
        'truncated':bool(取字段(保留页,'truncated')),#内联是否已截断
        'total':取字段(保留页,'seen'),#截断前路径总数
    }#glob meta组装结束
    return 限制元字节(元,最大元字节)#再按字节预算截尾

def 是否搜索行命中(值):#收窄单行命中
    """value 是否为合法的 SearchLineMatch（从不透明 meta 做防御性收窄）。"""
    if not isinstance(值,dict) or 值 is None:#必须是非数组对象
        return False#非法
    行号=取字段(值,'lineNumber')#行号
    行=取字段(值,'line')#行文本
    return isinstance(行号,(int,float)) and not isinstance(行号,bool) and isinstance(行,str)#行号为数且行为字符串

def 是否搜索文件命中(值):#收窄按文件分组
    """value 是否为合法的 SearchFileMatches（从不透明 meta 做防御性收窄）。"""
    if not isinstance(值,dict) or 值 is None:#必须是非数组对象
        return False#非法
    路径=取字段(值,'path')#路径
    命中们=取字段(值,'matches')#命中列表
    if not isinstance(路径,str) or not isinstance(命中们,list):#路径为字符串且命中为列表
        return False#非法
    for 命中 in 命中们:#逐条校验
        if not 是否搜索行命中(命中):#命中不合法
            return False#非法
    return True#合法

def 搜索视图自元(元):#把不透明meta收窄为搜索卡片视图
    """把不透明的实时或回放结果元数据收窄为 SearchResultView。畸形元数据返回 None，以便 presentResult 回退到通用卡片，而不是在回放更旧或手改日志时抛错。视图不携带结果文本。

    零结果 meta（files: [] / paths: []）收窄为一张合法空卡片——零命中 grep 是合法结果，UI 显示为“无匹配”，而不是缺失投影。
    """
    if not isinstance(元,dict) or 元 is None:#非对象则无法收窄
        return None#放弃
    已截断=取字段(元,'truncated')#截断标志
    总数=取字段(元,'total')#总数
    if not isinstance(已截断,bool) or not isinstance(总数,(int,float)) or isinstance(总数,bool):#缺少合法truncated或total则放弃
        return None#放弃
    if 取字段(元,'shape')=='matches':#按文件分组的命中形态
        文件们=取字段(元,'files')#取出文件分组
        if not isinstance(文件们,list):#必须是列表
            return None#放弃
        for 文件 in 文件们:#逐组校验
            if not 是否搜索文件命中(文件):#分组不合法
                return None#放弃
        return {'card':'search','shape':'matches','files':文件们,'truncated':已截断,'total':总数}#组装命中卡片
    if 取字段(元,'shape')=='paths':#扁平路径列表形态
        路径们=取字段(元,'paths')#取出路径列表
        if not isinstance(路径们,list):#必须是列表
            return None#放弃
        for 路径 in 路径们:#路径项必须全是字符串
            if not isinstance(路径,str):#非字符串
                return None#放弃
        return {'card':'search','shape':'paths','paths':路径们,'truncated':已截断,'total':总数}#组装路径卡片
    return None#未知shape则回退
