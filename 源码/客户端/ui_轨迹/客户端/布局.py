"""轨迹列表折叠：展开助手块、用量、自身时长、partial/runningCalls 与组描述。

对齐上游 `ui-trajectory/src/client/layout.ts`。公开面仅中文名。
"""
import json#源值字符串化
import math#有限数判定
from urllib.parse import urlparse as 解析URL#安全图片源协议校验
from .轨迹记录 import 格式化已用秒数,取字段#时长格式化

__all__=['派生轨迹布局','追加轨迹流式布局','追加轨迹部分布局']#仅中文公开名

安全整数最大=9007199254740991#Number.MAX_SAFE_INTEGER

def 有限时间(时间):#收窄为有限毫秒
    """可用作绝对时间的纪元毫秒，否则 None。"""
    return 时间 if isinstance(时间,(int,float)) and math.isfinite(时间) else None#非有限则 None

def 时长秒(较晚,较早):#自身时长秒
    """两个纪元毫秒之差得到自身秒数；任一不可用则为 None。"""
    if 较早 is None or not math.isfinite(较晚) or not math.isfinite(较早):#缺一端
        return None#缺一端
    return max(0,(较晚-较早)/1000)#毫秒差转秒，下限 0

def 条目排序键(条目):#条目排序键
    """初始系统提示排最前，其余按 seq。"""
    if 取字段(条目,'kind')=='system' and 取字段(取字段(条目,'change'),'kind')=='initial':#初始系统提示
        return float('-inf')#负无穷
    return 取字段(条目,'seq')#其余按 seq

def 源块(值):#未知值转源块
    """把内容块或任意值转成轨迹源块。"""
    if not isinstance(值,dict):#非对象
        return {'type':'unknown','content':stringify源值(值)}#未知类型
    类型=值.get('type') if isinstance(值.get('type'),str) else 'unknown'#类型字段
    if isinstance(值.get('text'),str):#有文本
        return {'type':'thinking' if 类型=='reasoning' else 类型,'content':值['text']}#推理改 thinking
    图片源=抽图片源(值)#尝试抽图片源
    替代=值.get('alt') if isinstance(值.get('alt'),str) else None#可选 alt
    结果={'type':类型,'content':'' if 图片源 is not None else stringify源值(值)}#通用源块
    if 图片源 is not None:#挂图片源
        结果['imageSrc']=图片源#图片
    if 替代 is not None:#挂 alt
        结果['imageAlt']=替代#alt
    return 结果#源块

def stringify源值(值):#源值转展示字符串
    """缩进 JSON；失败退回 str。"""
    try:#序列化
        文本=json.dumps(值,ensure_ascii=False,indent=2)#缩进 JSON
        return 文本 if 文本 else str(值)#JSON 空则退回 str
    except (TypeError,ValueError):#无法序列化
        return str(值)#退回

def 抽图片源(块):#从块里抽安全图片 URL
    """类型含 image 才尝试。"""
    类型=块.get('type')#类型
    if not isinstance(类型,str) or 'image' not in 类型.lower():#类型不含 image
        return None#无
    for 候选 in (块.get('url'),块.get('image_url')):#常见 URL 字段
        if isinstance(候选,str):#字符串
            return 安全图片源(候选)#校验
    数据=块.get('data')#内嵌 base64
    if isinstance(数据,str):#有 data
        MIME=None#MIME
        for 键 in ('mimeType','mediaType','media_type'):#MIME 候选
            if isinstance(块.get(键),str):#命中
                MIME=块[键]#用之
                break#找到
        if MIME is None:#默认
            MIME='image/png'#png
        地址=数据 if 数据.startswith('data:') else f'data:{MIME};base64,{数据}'#拼 data URL
        return 安全图片源(地址)#校验
    源=块.get('source')#嵌套 source
    if not isinstance(源,dict):#无嵌套
        return None#无
    if isinstance(源.get('url'),str):#source.url
        return 安全图片源(源['url'])#校验
    if not isinstance(源.get('data'),str):#无 data
        return None#无
    MIME=源['media_type'] if isinstance(源.get('media_type'),str) else 'image/png'#MIME
    return 安全图片源(f'data:{MIME};base64,{源["data"]}')#拼 data URL

def 安全图片源(值):#只放行安全图片源
    """data:image、blob、http(s) 直通。"""
    if 值.startswith('data:image/') or 值.startswith('blob:'):#直通
        return 值#放行
    try:#解析 URL 协议
        协议=解析URL(值).scheme#取协议
        return 值 if 协议 in ('http','https') else None#仅 http(s)
    except Exception:#无法解析
        return None#丢弃

def 助手源块(块):#助手块转源块
    """按块种类转换。"""
    种类=取字段(块,'kind')#块种类
    if 种类=='text':#文本
        return {'type':'text','content':取字段(块,'text') or ''}#文本
    if 种类=='reasoning':#推理
        return {'type':'thinking','content':取字段(块,'text') or ''}#thinking
    if 种类=='tool-call':#工具调用
        return {'type':'tool-call','content':取字段(块,'argsRaw') or '','callId':取字段(块,'callId'),'toolName':取字段(块,'name')}#调用
    if 种类=='image':#图片附件
        return {'type':'image','content':stringify源值(取字段(块,'attachment'))}#附件元数据
    return 源块(取字段(块,'block'))#其它块走通用转换

def 挂用量(单元格,用量):#挂用量字段
    """有提供方用量时拷到 Message 单元格。"""
    if 用量 is None:#无用量
        return#无
    if 取字段(用量,'inputTokens') is not None:#输入
        单元格['input']=取字段(用量,'inputTokens')#写入
    if 取字段(用量,'cacheReadTokens') is not None:#缓存读
        单元格['cacheRead']=取字段(用量,'cacheReadTokens')#写入
    if 取字段(用量,'cacheWriteTokens') is not None:#缓存写
        单元格['cacheWrite']=取字段(用量,'cacheWriteTokens')#写入
    if 取字段(用量,'outputTokens') is not None:#输出
        单元格['output']=取字段(用量,'outputTokens')#写入
    if 取字段(用量,'reasoningTokens') is not None:#推理
        单元格['think']=取字段(用量,'reasoningTokens')#写入

def 摘要调用(名称,参数原文):#调用名 + 参数预览
    """名作 text，非空参数作预览。"""
    结果={'text':名称}#工具名
    if 参数原文!='':#有参数
        结果['previewMarkdown']=参数原文#预览
    return 结果#展示字段

def 摘要结果(节点):#结果预览字段
    """错误码或首段文本或 No output。"""
    if 取字段(节点,'isError'):#错误结果
        错误=取字段(节点,'error')#错误对象
        return {'result':取字段(错误,'code') if 错误 is not None else 'error'}#错误码
    for 块 in 取字段(节点,'content') or []:#找首段非空文本
        if 取字段(块,'type')=='text' and isinstance(取字段(块,'text'),str) and 取字段(块,'text')!='':#文本块
            return {'result':'','resultPreviewMarkdown':取字段(块,'text')}#正文留给预览
    return {'result':'No output'}#无输出

def 结果当文本(结果):#结果预览改写成 text/preview
    """result → text，预览 Markdown 原样。"""
    if 结果 is None:#无结果
        return {'text':''}#空
    字段={'text':取字段(结果,'result') or ''}#结果短文
    预览=取字段(结果,'resultPreviewMarkdown')#预览
    if 预览 is not None:#有预览
        字段['previewMarkdown']=预览#挂预览
    return 字段#文本展示

def 详情结果(节点):#结果详情全文
    """错误名:码，或文本块，或 JSON。"""
    if 取字段(节点,'isError'):#错误
        错误=取字段(节点,'error')#错误对象
        if 错误 is None:#无错误对象
            return 'error'#占位
        return f'{取字段(错误,"name")}: {取字段(错误,"code")}'#名:码
    内容=取字段(节点,'content') or []#内容块
    文本='\n'.join(取字段(块,'text') or '' for 块 in 内容 if 取字段(块,'type')=='text' and isinstance(取字段(块,'text'),str))#文本拼接
    if 文本!='':#有文本
        return 文本#用之
    if len(内容)==0 or all(取字段(块,'type')=='text' and (not isinstance(取字段(块,'text'),str) or 取字段(块,'text')=='') for 块 in 内容):#无有效文本
        return 'No output'#无输出
    return json.dumps(内容,ensure_ascii=False,indent=2)#整份内容 JSON

def 详情内容(内容):#文本块详情
    """拼接 type=text 的 text。"""
    return '\n'.join(取字段(块,'text') or '' for 块 in 内容 if 取字段(块,'type')=='text' and isinstance(取字段(块,'text'),str))#换行拼接

def 详情推理(内容):#推理块详情
    """拼接 type=reasoning 的 text。"""
    return '\n'.join(取字段(块,'text') or '' for 块 in 内容 if 取字段(块,'type')=='reasoning' and isinstance(取字段(块,'text'),str))#换行拼接

def 预览内容(内容):#首段文本预览
    """首段 text 或 None。"""
    for 块 in 内容:#找第一段文本
        if 取字段(块,'type')=='text' and isinstance(取字段(块,'text'),str):#命中
            return 取字段(块,'text')#返回
    return None#没有

def 预览内容属性(内容):#有预览则包成 previewMarkdown 字段
    """无则空字典。"""
    预览=预览内容(内容)#首段文本
    return {} if 预览 is None else {'previewMarkdown':预览}#无则空

def 输入单元格详情(节点):#输入单元格共用字段
    """用户/转向/上下文共用字段。"""
    内容=取字段(节点,'content') or []#内容块
    预览=预览内容(内容)#首段文本预览
    字段={#输入单元格字段
        'text':'',#正文留给预览
        'sourceSeq':取字段(节点,'seq'),#源序号
        'messageSource':取字段(节点,'source'),#消息来源
        'inputDetail':详情内容(内容),#输入详情文本
        'sourceBlocks':[源块(块) for 块 in 内容],#源块
        'timeSeconds':0,#输入无自身耗时
        'startedAt':有限时间(取字段(节点,'time')),#节点时间
    }#字段结束
    if 预览 is not None:#有预览才挂
        字段['previewMarkdown']=预览#预览
    return 字段#共用字段

def 索引结果(节点们):#callId → 结果节点
    """扫描 tool-result 节点。"""
    表={}#结果表
    for 节点 in 节点们:#扫描
        if 取字段(节点,'kind')=='tool-result':#结果
            表[取字段(节点,'callId')]=节点#写入
    return 表#结果表

def 索引助手调用标识(节点们):#助手已发出的 callId
    """扫描助手 tool-call 块。"""
    标识们=set()#id 集合
    for 节点 in 节点们:#扫描助手
        if 取字段(节点,'kind')!='assistant':#非助手
            continue#跳过
        for 块 in 取字段(节点,'blocks') or []:#块
            if 取字段(块,'kind')=='tool-call':#调用
                标识们.add(取字段(块,'callId'))#记下
    return 标识们#集合

def 索引后续助手(节点们):#每个下标 → 其后最近助手
    """与 nodes 等长。"""
    后续=[None]*len(节点们)#结果数组
    助手=None#自后向前记住的助手
    for 下标 in range(len(节点们)-1,-1,-1):#倒序
        后续[下标]=助手#当前位置之后的助手
        节点=节点们[下标]#当前节点
        if 取字段(节点,'kind')=='assistant':#遇到助手
            助手=节点#更新
    return 后续#等长映射

def 收集调用标识(轮次桶):#布局里出现过的 callId
    """各轮各组各格。"""
    标识们=set()#收集器
    for 桶 in 轮次桶.values():#各轮
        for 组 in 桶['groups']:#各组
            for 已铺 in 组['laid']:#各格
                if 已铺.get('callId') is not None:#有 id
                    标识们.add(已铺['callId'])#收下
    return 标识们#集合

def 挂工具模式(已铺,调用模式表):#按 callId 把 schema 挂到单元格
    """就地写入 schemaDetail。"""
    if 已铺.get('callId') is None or 调用模式表 is None:#无 id 或无表
        return#无
    模式=调用模式表.get(已铺['callId']) if isinstance(调用模式表,dict) else None#该调用 schema
    if 模式 is None and hasattr(调用模式表,'get'):#Map 形
        模式=调用模式表.get(已铺['callId'])#再取
    if 模式 is None:#表中没有
        return#无
    已铺['cell']['schemaDetail']=json.dumps(模式,ensure_ascii=False,indent=2)#缩进 JSON

def 组描述(已铺们):#组描述文案
    """墙钟跨度 + 工具直方图。"""
    片段=[]#时长与工具片段
    时间点=[]#墙钟采样点
    for 项 in 已铺们:#每格贡献时间点
        绝对=项.get('absTime')#绝对时间
        if 绝对 is None or not math.isfinite(绝对):#不可用
            continue#跳过
        时间点.append(绝对)#起点
        单元格=项['cell']#单元格
        秒=取字段(单元格,'timeSeconds')#自身秒数
        if 取字段(单元格,'kind')=='tool' and 秒 is not None and math.isfinite(秒):#工具且有时长
            时间点.append(绝对+秒*1000)#终点
    if len(时间点)>=2:#至少两点
        跨度文案=格式化已用秒数((max(时间点)-min(时间点))/1000)#最大减最小再转秒
        if 跨度文案 is not None and 跨度文案!='—':#有格式化结果
            片段.append(跨度文案)#加入
    elif len(时间点)==1:#单点则退回该格自身时长
        自身=None#自身秒数
        for 项 in 已铺们:#找对应格
            if 项.get('absTime')==时间点[0]:#命中
                自身=取字段(项['cell'],'timeSeconds')#记下
                break#找到
        if 自身 is not None:#有
            跨度文案=格式化已用秒数(自身)#格式化
            if 跨度文案 is not None and 跨度文案!='—':#有效
                片段.append(跨度文案)#加入
    工具计数={}#工具名 → 次数
    for 项 in 已铺们:#统计工具格
        if 项.get('toolName') is None or 取字段(项['cell'],'kind')!='tool':#非工具或无名
            continue#跳过
        名=项['toolName']#工具名
        工具计数[名]=工具计数.get(名,0)+1#累加
    for 名,次数 in 工具计数.items():#输出直方图
        片段.append(f'{名}×{次数}' if 次数>1 else 名)#多次带 ×N
    return None if len(片段)==0 else ' '.join(片段)#空则无描述

def 转轮次模型(回合号,桶):#桶转成对外轮次模型
    """组转模型并挂描述。"""
    组们=[]#组列表
    for 组 in 桶['groups']:#各组
        描述=组描述(组['laid'])#墙钟+工具直方图
        一项={'title':组['title'],'cells':[项['cell'] for 项 in 组['laid']]}#一组
        if 描述 is not None:#有描述才挂
            一项['description']=描述#描述
        组们.append(一项)#收下
    return {'turn':回合号,'groups':组们}#轮次模型

def 首格下标(轮次):#该轮最小单元格下标
    """用折叠时单调分配的单元格下标。"""
    下标们=[取字段(单元格,'index') for 组 in 取字段(轮次,'groups') or [] for 单元格 in 取字段(组,'cells') or []]#所有格下标
    return min(下标们) if 下标们 else float('inf')#空轮时正无穷

def 提示变更标签(变更):#提示变更标签
    """initial / system / tools / both。"""
    种类=取字段(变更,'kind')#变更种类
    if 种类=='initial':#初始
        return 'Initial System Prompt'#初始系统提示
    if 种类=='system':#系统
        return 'System Prompt Updated'#系统提示已更新
    if 种类=='tools':#工具
        return 'Tools Updated'#工具已更新
    return 'System Prompt and Tools Updated'#系统提示与工具都更新

def 助手活动摘要(块们):#无正文时的活动摘要
    """有工具调用则 Tool call only。"""
    for 块 in 块们:#只统计调用块
        if 取字段(块,'kind')=='tool-call':#有调用
            return 'Tool call only'#仅工具调用
    return ''#无活动文案

def 包围用户轮次(后续助手,流式,最近助手轮):#用户消息归入哪一轮
    """下一助手轮，否则 partial，否则最后助手+1 或 1。"""
    if 后续助手 is not None:#有后续助手
        return 取字段(后续助手,'turn')#用其轮
    if 流式 is not None:#否则用进行中轮
        return 取字段(流式,'turn')#partial
    if 最近助手轮 is not None:#否则开新轮
        return 最近助手轮+1#下一轮
    return 1#默认第 1 轮

def 转向安放(后续助手,流式,最近助手轮,位置):#转向消息安放位置
    """轮次与可选 Step。"""
    if 取字段(位置,'kind')=='step':#位置钉在某 Step
        return {'turn':取字段(取字段(位置,'turn'),'turn'),'step':取字段(取字段(位置,'step'),'step')}#用位置
    钉轮=取字段(取字段(位置,'turn'),'turn') if 取字段(位置,'kind')=='turn' else None#仅轮位置
    if 后续助手 is not None and (钉轮 is None or 取字段(后续助手,'turn')==钉轮):#有后续助手且位置兼容
        结果={'turn':取字段(后续助手,'turn')}#跟后续助手
        if 取字段(后续助手,'step')>0:#Step>0 才挂步
            结果['step']=取字段(后续助手,'step')#步
        return 结果#跟助手
    if 流式 is not None and (钉轮 is None or 取字段(流式,'turn')==钉轮):#进行中且位置兼容
        结果={'turn':取字段(流式,'turn')}#跟 partial
        if 取字段(流式,'step')>0:#Step>0
            结果['step']=取字段(流式,'step')#步
        return 结果#跟 partial
    if 钉轮 is not None:#只信位置上的轮
        return {'turn':钉轮}#位置轮
    return {'turn':最近助手轮 if 最近助手轮 is not None else 1}#否则最近助手轮或 1

def 包围提示轮次(节点们,序号,流式):#提示变更包进哪一轮
    """其后第一个 Step 助手，否则 partial 或 1。"""
    for 节点 in 节点们:#找后续 Step 助手
        if 取字段(节点,'seq')>序号 and 取字段(节点,'kind')=='assistant' and 取字段(节点,'step')>0:#命中
            return 取字段(节点,'turn')#用其轮
    return 取字段(流式,'turn') if 流式 is not None else 1#否则进行中轮或 1

def 最早可见轮次(节点们,流式):#最早可见轮次
    """所选轨迹分支里最早出现的原始轮次。"""
    轮次们=[取字段(节点,'turn') for 节点 in 节点们 if 取字段(节点,'kind')=='assistant' and 取字段(节点,'turn')>0]#助手正数轮
    if 流式 is not None and 取字段(流式,'turn')>0:#进行中正数轮
        轮次们.append(取字段(流式,'turn'))#收下
    return 1 if len(轮次们)==0 else min(轮次们)#空则 1，否则最小轮

def 展开子调用(子们,起始下标):#展开一层子调用（递归）
    """一次 run_code 父调用的子分派格。"""
    if not 子们:#无子调用
        return []#空
    输出=[]#子格列表
    下标=起始下标#从父格下标接着编
    for 子 in 子们:#每个子调用
        已结算='kind' in 子 if isinstance(子,dict) else hasattr(子,'kind')#已结算还是进行中
        结果预览=摘要结果(子) if 已结算 else None#已结算才有结果预览
        下标+=1#下一个下标
        if 已结算:#已结算
            调用=取字段(子,'call')#调用元数据
            展示=摘要调用(取字段(调用,'name'),取字段(调用,'argsRaw')) if 调用 is not None else 结果当文本(结果预览)#名+参数或结果
            单元格={#子工具单元格
                'index':下标,'kind':'subtool','callId':取字段(子,'callId'),#下标种类 id
                **展示,#展示字段
                'timeSeconds':时长秒(取字段(子,'time'),取字段(子,'callTime')),#时长
                'startedAt':有限时间(取字段(子,'callTime')),#开始
                'outputDetail':详情结果(子),#输出详情
                'outputBlocks':[源块(块) for 块 in 取字段(子,'content') or []],#输出源块
                'isError':取字段(子,'isError'),#是否错误
            }#单元格结束
            if 调用 is not None:#有调用
                单元格['inputDetail']=取字段(调用,'argsRaw')#输入
            if 结果预览 is not None:#有预览
                单元格.update(结果预览)#并入
            绝对=有限时间(取字段(子,'callTime') if 取字段(子,'callTime') is not None else 取字段(子,'time'))#绝对时间
            工具名=取字段(调用,'name') if 调用 is not None else 取字段(子,'callId')#工具名
        else:#进行中
            展示=摘要调用(取字段(子,'name'),取字段(子,'argsRaw'))#名+参数
            单元格={#进行中子格
                'index':下标,'kind':'subtool','callId':取字段(子,'callId'),#下标
                **展示,#展示
                'inputDetail':取字段(子,'argsRaw'),#输入
                'timeSeconds':None,#进行中无时长
                'startedAt':有限时间(取字段(子,'time')),#开始
            }#单元格结束
            绝对=有限时间(取字段(子,'time'))#绝对时间
            工具名=取字段(子,'name')#工具名
        已铺={'absTime':绝对,'toolName':工具名,'callId':取字段(子,'callId'),'cell':单元格}#已铺
        输出.append(已铺)#推入
        for 孙 in 展开子调用(取字段(子,'subCalls'),下标):#再展开孙调用
            输出.append(孙)#插入
            下标=取字段(孙['cell'],'index')#同步下标
    return 输出#全部子格

def 插入子调用(已铺列表):#插入子调用并重编号
    """把每个工具格的嵌套子调用插到它后面。"""
    if not any(取字段(项,'subCalls') for 项 in 已铺列表):#无子调用
        return 已铺列表#原样
    输出=[]#输出
    下标=取字段(已铺列表[0]['cell'],'index')-1 if 已铺列表 else 0#自增基数
    for 项 in 已铺列表:#父格
        下标+=1#重编号
        新格=dict(项['cell'])#拷贝单元格
        新格['index']=下标#新下标
        输出.append({**项,'cell':新格})#重编号后推入
        for 子 in 展开子调用(取字段(项,'subCalls'),下标):#其子调用
            输出.append(子)#插入子格
            下标=取字段(子['cell'],'index')#同步
    return 输出#重编号列表

def 展开助手(节点,起始下标,上一绝对,结果表,开始表,调用表,流式=False):#把助手节点展开成 Message + Tool 格
    """展开助手块并挂用量。"""
    块们=取字段(节点,'blocks') or []#块列表
    if 流式 and len(块们)==0:#流式空块
        return []#不产出
    输出=[]#输出列表
    下标=起始下标-1#自增前基数
    用量=取字段(节点,'usage')#用量
    计时=取字段(节点,'timing')#计时
    记录开始=有限时间(取字段(计时,'stepStartTime'))#步骤开始
    消息时长=None if 流式 else 时长秒(取字段(节点,'time'),记录开始 if 记录开始 is not None else 上一绝对)#自身秒数
    节点绝对=None if 流式 else 有限时间(取字段(节点,'time'))#绝对完成时间
    正文='\n\n'.join(取字段(块,'text') or '' for 块 in 块们 if 取字段(块,'kind')=='text' and ((not 流式) or 取字段(块,'text')!=''))#文本拼接
    推理='\n\n'.join(取字段(块,'text') or '' for 块 in 块们 if 取字段(块,'kind')=='reasoning' and ((not 流式) or 取字段(块,'text')!=''))#推理拼接
    下标+=1#Message 下标
    消息={#助手 Message 格
        'index':下标,#下标
        'recordId':f"assistant\u0000{取字段(节点,'turn')}\u0000{取字段(节点,'step')}",#助手记录 id
        'kind':'message',#消息格
        'sourceSeq':取字段(节点,'seq'),#源序号
        'text':'' if 正文!='' or 推理!='' else 助手活动摘要(块们),#活动摘要或留给预览
        'sourceBlocks':[助手源块(块) for 块 in 块们],#助手源块
        'timeSeconds':消息时长,#自身秒数
        'startedAt':记录开始,#步骤开始
    }#消息结束
    if 正文!='':#有正文
        消息['previewMarkdown']=正文#正文作预览
        消息['outputDetail']=正文#正文作输出详情
    elif 推理!='':#无正文有推理
        消息['previewMarkdown']=推理#推理作预览
    if 推理!='':#有推理
        消息['thinkingDetail']=推理#推理详情
    挂用量(消息,用量)#挂用量
    消息['assistantMetrics']={#助手计时与用量指标
        'timingRecorded':计时 is not None,#是否有计时
        'stepStartTime':取字段(计时,'stepStartTime') if 计时 is not None else None,#步骤开始
        'firstTokenTime':取字段(计时,'firstTokenTime') if 计时 is not None else None,#首 token
        'completedTime':None if 流式 else 有限时间(取字段(节点,'time')),#完成时间
        'usageProvided':用量 is not None,#是否带用量
        'outputTokens':取字段(用量,'outputTokens') if 用量 is not None and 有限时间(取字段(用量,'outputTokens')) is not None else None,#输出 token
    }#指标结束
    输出.append({'absTime':节点绝对,'cell':消息})#先推 Message
    for 块 in 块们:#再为每个工具调用出格
        if 取字段(块,'kind')!='tool-call':#非调用块
            continue#跳过
        调用标识=取字段(块,'callId')#调用 id
        结果=结果表.get(调用标识)#对应结果
        工具时长=None if 流式 or 结果 is None else 时长秒(取字段(结果,'time'),取字段(结果,'callTime'))#时长
        调用绝对=有限时间(开始表.get(调用标识))#调用开始
        调用=调用表.get(调用标识)#调用块
        结果预览=摘要结果(结果) if 结果 is not None else None#结果预览
        下标+=1#工具下标
        单元格={#工具单元格
            'index':下标,'kind':'tool','callId':调用标识,#下标
            **摘要调用(取字段(块,'name'),取字段(块,'argsRaw')),#名+参数
            'inputDetail':取字段(块,'argsRaw'),#输入
            'timeSeconds':工具时长,#时长
            'startedAt':调用绝对,#开始
        }#单元格结束
        if 结果 is not None:#已有结果
            单元格['outputDetail']=详情结果(结果)#输出详情
            单元格['outputBlocks']=[源块(块) for 块 in 取字段(结果,'content') or []]#输出源块
            单元格['isError']=取字段(结果,'isError')#是否错误
            if 结果预览 is not None:#有预览
                单元格.update(结果预览)#并入
        已铺={'absTime':调用绝对,'toolName':取字段(块,'name'),'callId':调用标识,'cell':单元格}#已铺
        if 调用 is not None:#有调用块
            已铺['subCalls']=取字段(调用,'subCalls')#挂子调用
        输出.append(已铺)#推入工具格
    return 输出#Message + Tool

def 派生轨迹布局(输入):#折叠整份轨迹
    """把快照折成 turn → Message/Step 组，并展开单元格。"""
    节点们=取字段(输入,'nodes') or []#会话节点
    事件位置=取字段(输入,'eventLocations')#事件序号→位置
    流式=取字段(输入,'partial')#进行中助手
    运行中=取字段(输入,'runningCalls') or []#进行中工具
    请求们=取字段(输入,'requests') or []#请求视图
    调用模式=取字段(输入,'callSchemas')#schema 表
    结果表=索引结果(节点们)#callId → 结果
    调用表=dict(结果表)#先填结果侧
    for 调用 in 运行中:#进行中覆盖
        调用表[取字段(调用,'callId')]=调用#写入
    已发调用=索引助手调用标识(节点们)#助手已发出
    后续助手=索引后续助手(节点们)#下标→后续助手
    开始表={}#callId → 开始毫秒
    for 结果 in 结果表.values():#已完成结果
        起点=有限时间(取字段(结果,'callTime'))#调用时刻
        if 起点 is not None:#可用
            开始表[取字段(结果,'callId')]=起点#写入
    for 调用 in 运行中:#进行中
        起点=有限时间(取字段(调用,'time'))#时刻
        if 起点 is not None:#可用
            开始表[取字段(调用,'callId')]=起点#写入
    轮次桶={}#轮次号 → 桶
    独立压缩=[]#无轮次的独立压缩
    下标=0#单元格单调下标
    上一绝对=None#上一绝对时间
    最近助手轮=None#最近一次助手轮次

    def 取桶(回合):#取或建该轮桶
        """取或建该轮桶。"""
        if 回合 not in 轮次桶:#尚未建
            轮次桶[回合]={'groups':[]}#空组
        return 轮次桶[回合]#该轮桶

    def 推进消息(回合,已铺):#把单元格推进 Message 组
        """追加到末 Message 组或新开。"""
        组们=取桶(回合)['groups']#该轮组
        if 组们 and 组们[-1]['title']=='Message':#已有 Message
            组们[-1]['laid'].append(已铺)#并入
            return#已追加
        组们.append({'title':'Message','laid':[已铺]})#新开

    def 推进步骤(回合,步,已铺们):#把单元格推进 Step 组
        """追加到同名 Step 或新开。"""
        if not 已铺们:#空
            return#不入组
        组们=取桶(回合)['groups']#该轮组
        标题=f'Step {步}'#Step N
        for 组 in 组们:#找同名
            if 组['title']==标题:#已有
                组['laid'].extend(已铺们)#并入
                return#已追加
        组们.append({'title':标题,'laid':list(已铺们)})#新开

    def 推进步骤输入(回合,步,已铺们):#把输入插到 Step 组请求单元格前
        """插到 requestOnly 前或追加。"""
        if not 已铺们:#空
            return#不入组
        组们=取桶(回合)['groups']#该轮组
        标题=f'Step {步}'#标题
        for 组 in 组们:#找同名
            if 组['title']==标题:#已有
                请求下标=next((号 for 号,项 in enumerate(组['laid']) if 取字段(项['cell'],'requestOnly') is True),-1)#仅请求占位
                if 请求下标==-1:#无占位
                    组['laid'].extend(已铺们)#追加
                else:#有占位
                    组['laid'][请求下标:请求下标]=list(已铺们)#插入
                return#已处理
        组们.append({'title':标题,'laid':list(已铺们)})#新开

    已代表=set()#已有节点代表的 turn\0step
    for 节点 in 节点们:#扫描助手
        if 取字段(节点,'kind')=='assistant' and 取字段(节点,'step')>0:#Step 助手
            已代表.add(f"{取字段(节点,'turn')}\u0000{取字段(节点,'step')}")#记为已代表
    if 流式 is not None and 取字段(流式,'step')>0:#进行中 Step
        已代表.add(f"{取字段(流式,'turn')}\u0000{取字段(流式,'step')}")#记为已代表
    for 调用 in 运行中:#进行中调用
        if 取字段(调用,'step')>0:#有步
            已代表.add(f"{取字段(调用,'turn')}\u0000{取字段(调用,'step')}")#记为已代表

    条目们=[]#合并四类条目
    for 号,节点 in enumerate(节点们):#每个会话节点
        条目们.append({'kind':'node','seq':取字段(节点,'seq'),'node':节点,'nodeIndex':号})#节点条目
    for 请求 in 请求们:#压缩请求
        if 取字段(请求,'purpose')=='compaction':#压缩用途
            条目们.append({'kind':'compaction','seq':取字段(请求,'startSeq'),'request':请求})#压缩条目
    for 请求 in 请求们:#系统提示变更
        if 取字段(请求,'purpose')=='assistant' and 取字段(请求,'promptChange') is not None and 取字段(请求,'prompt') is not None:#有变更
            变更=取字段(请求,'promptChange')#变更载荷
            条目们.append({'kind':'system','seq':取字段(变更,'seq'),'request':请求,'change':变更})#系统条目
    for 请求 in 请求们:#尚无节点的助手请求
        if 取字段(请求,'purpose')=='assistant' and f"{取字段(请求,'turn')}\u0000{取字段(请求,'step')}" not in 已代表:#未代表
            条目们.append({'kind':'request','seq':取字段(请求,'startSeq'),'request':请求})#仅请求
    条目们.sort(key=条目排序键)#按排序键排

    for 条目 in 条目们:#按序折叠
        种类=条目['kind']#条目种类
        if 种类=='request':#尚无节点的助手请求
            请求=条目['request']#该请求
            下标+=1#下一个下标
            已铺={'absTime':有限时间(取字段(请求,'startedAt')),'cell':{#仅请求占位
                'index':下标,'kind':'message','text':'','sourceSeq':取字段(请求,'startSeq'),#基本字段
                'requestOnly':True,#仅请求
                'timeSeconds':None if 取字段(请求,'completedAt') is None else 时长秒(取字段(请求,'completedAt'),取字段(请求,'startedAt')),#时长
                'startedAt':有限时间(取字段(请求,'startedAt')),#开始
            }}#已铺结束
            if 取字段(请求,'status')=='error':#出错
                已铺['cell']['isError']=True#标错
            推进步骤(取字段(请求,'turn'),取字段(请求,'step'),[已铺])#推进 Step
            上一绝对=有限时间(取字段(请求,'completedAt')) or 有限时间(取字段(请求,'startedAt')) or 上一绝对#推进游标
            continue#下一条
        if 种类=='system':#系统提示变更
            变更=条目['change']#变更
            请求=条目['request']#所属请求
            回合=最早可见轮次(节点们,流式) if 取字段(变更,'kind')=='initial' else 包围提示轮次(节点们,取字段(变更,'seq'),流式)#归入轮
            下标+=1#下一个下标
            单元格={'index':下标,'kind':'system','text':提示变更标签(变更),'sourceSeq':取字段(变更,'seq'),'timeSeconds':0,'startedAt':有限时间(取字段(变更,'time'))}#系统格
            if 取字段(请求,'prompt') is not None:#有现提示
                单元格['promptDetail']=取字段(请求,'prompt')#现提示
            if 取字段(变更,'previous') is not None:#有旧提示
                单元格['previousPromptDetail']=取字段(变更,'previous')#旧提示
            推进消息(回合,{'absTime':有限时间(取字段(变更,'time')),'cell':单元格})#推进 Message
            上一绝对=有限时间(取字段(变更,'time')) or 上一绝对#推进游标
            continue#下一条
        if 种类=='compaction':#压缩请求
            请求=条目['request']#该压缩
            原始输出=取字段(请求,'rawOutput') if 取字段(请求,'rawOutput') is not None else 取字段(请求,'summary')#原始或摘要
            推理详情=详情推理(原始输出) if 原始输出 is not None else ''#推理文本
            下标+=1#下一个下标
            状态=取字段(请求,'status')#状态
            if 状态=='running':#进行中
                文本='Compacting context…'#进行中文案
            elif 状态=='error':#失败
                文本=取字段(请求,'error') or 'Compaction failed'#错误文案
            elif 取字段(请求,'summary') is None:#完成但无摘要
                文本='Context compacted'#完成占位
            else:#有摘要
                文本=''#留给预览
            单元格={'index':下标,'kind':'compacted','text':文本,'sourceSeq':取字段(请求,'startSeq'),'timeSeconds':None if 取字段(请求,'completedAt') is None else 时长秒(取字段(请求,'completedAt'),取字段(请求,'startedAt')),'startedAt':有限时间(取字段(请求,'startedAt'))}#压缩格
            if 状态=='complete' and 取字段(请求,'summary') is not None:#完成且有摘要
                单元格.update(预览内容属性(取字段(请求,'summary')))#挂预览
                单元格['outputDetail']=详情内容(取字段(请求,'summary'))#摘要文本
                单元格['outputBlocks']=[源块(块) for 块 in 取字段(请求,'summary')]#摘要源块
            if 推理详情!='':#有推理
                单元格['thinkingDetail']=推理详情#挂推理
            if 原始输出 is not None:#有原始输出
                单元格['sourceBlocks']=[源块(块) for 块 in 原始输出]#原始源块
            if 状态=='error':#出错
                单元格['isError']=True#标错
            挂用量(单元格,取字段(请求,'usage'))#挂用量
            压缩桶={'groups':[{'title':f"Compaction {取字段(请求,'startSeq')}",'laid':[{'absTime':有限时间(取字段(请求,'startedAt')),'cell':单元格}]}]}#压缩桶
            if 取字段(请求,'turn') is None:#无轮次
                独立压缩.append(压缩桶)#独立段
            else:#有轮次
                取桶(取字段(请求,'turn'))['groups'].extend(压缩桶['groups'])#并入该轮
            上一绝对=有限时间(取字段(请求,'completedAt')) or 有限时间(取字段(请求,'startedAt')) or 上一绝对#推进游标
            continue#下一条
        节点=条目['node']#节点
        号=条目['nodeIndex']#原下标
        节点种=取字段(节点,'kind')#节点种类
        if 节点种=='user':#用户消息
            回合=包围用户轮次(后续助手[号],流式,最近助手轮)#包围轮次
            下标+=1#下一个下标
            单元格={'index':下标,'kind':'user',**输入单元格详情(节点),'opensTurn':True}#用户格
            推进消息(回合,{'absTime':有限时间(取字段(节点,'time')),'cell':单元格})#推进
            上一绝对=有限时间(取字段(节点,'time')) or 上一绝对#推进游标
            continue#下一条
        if 节点种=='steering':#转向消息
            位置=事件位置.get(取字段(节点,'seq')) if 事件位置 is not None else None#事件位置
            安放=转向安放(后续助手[号],流式,最近助手轮,位置)#安放
            下标+=1#下一个下标
            已铺={'absTime':有限时间(取字段(节点,'time')),'cell':{'index':下标,'kind':'user',**输入单元格详情(节点)}}#转向格
            if 取字段(安放,'step') is None:#无 Step
                推进消息(安放['turn'],已铺)#进 Message
            else:#有 Step
                推进步骤输入(安放['turn'],安放['step'],[已铺])#插到 Step
            上一绝对=有限时间(取字段(节点,'time')) or 上一绝对#推进游标
            continue#下一条
        if 节点种=='assistant':#助手消息
            已铺列表=插入子调用(展开助手(节点,下标+1,上一绝对,结果表,开始表,调用表))#展开并插子调用
            if 取字段(节点,'step')>0:#Step
                推进步骤(取字段(节点,'turn'),取字段(节点,'step'),已铺列表)#进 Step
            else:#Message
                for 项 in 已铺列表:#逐格
                    推进消息(取字段(节点,'turn'),项)#进 Message
            if 已铺列表:#有格
                下标=取字段(已铺列表[-1]['cell'],'index')#同步下标
            上一绝对=有限时间(取字段(节点,'time')) or 上一绝对#推进游标
            最近助手轮=取字段(节点,'turn')#记下助手轮
            continue#下一条
        if 节点种=='context':#上下文
            回合=包围用户轮次(后续助手[号],流式,最近助手轮)#包围轮次
            下标+=1#下一个下标
            推进消息(回合,{'absTime':有限时间(取字段(节点,'time')),'cell':{'index':下标,'kind':'context',**输入单元格详情(节点)}})#推进
            上一绝对=有限时间(取字段(节点,'time')) or 上一绝对#推进游标
            continue#下一条
        if 节点种=='compaction':#聊天侧压缩标记
            上一绝对=有限时间(取字段(节点,'time')) or 上一绝对#只推进游标
            continue#下一条
        if 节点种=='tool-result':#工具结果
            if 取字段(节点,'callId') not in 已发调用:#助手未发出
                工具名=取字段(取字段(节点,'call'),'name')#工具名
                结果预览=摘要结果(节点)#结果预览
                下标+=1#下一个下标
                调用=取字段(节点,'call')#调用元数据
                展示=摘要调用(取字段(调用,'name'),取字段(调用,'argsRaw')) if 调用 is not None else 结果当文本(结果预览)#展示
                单元格={'index':下标,'kind':'tool','sourceSeq':取字段(节点,'seq'),**展示,'outputDetail':详情结果(节点),'outputBlocks':[源块(块) for 块 in 取字段(节点,'content') or []],'callId':取字段(节点,'callId'),'isError':取字段(节点,'isError'),'timeSeconds':时长秒(取字段(节点,'time'),取字段(节点,'callTime')),'startedAt':有限时间(取字段(节点,'callTime'))}#工具格
                if 调用 is not None:#有调用
                    单元格['inputDetail']=取字段(调用,'argsRaw')#输入
                if 结果预览 is not None:#有预览
                    单元格.update(结果预览)#并入
                已铺列表=[{'absTime':有限时间(取字段(节点,'callTime') if 取字段(节点,'callTime') is not None else 取字段(节点,'time')),'toolName':工具名,'callId':取字段(节点,'callId'),'subCalls':取字段(节点,'subCalls'),'cell':单元格}]#首格
                for 子 in 展开子调用(取字段(节点,'subCalls'),下标):#展开子调用
                    已铺列表.append(子)#追加
                    下标=取字段(子['cell'],'index')#同步
                推进步骤(0,1,已铺列表)#孤儿先放 turn 0 Step 1
            上一绝对=有限时间(取字段(节点,'time')) or 上一绝对#推进游标

    if 流式 is not None:#有进行中助手
        假={'kind':'assistant','seq':安全整数最大,'time':0,'turn':取字段(流式,'turn'),'step':取字段(流式,'step'),'blocks':取字段(流式,'blocks')}#假助手
        已铺列表=插入子调用(展开助手(假,下标+1,上一绝对,结果表,开始表,调用表,True))#流式展开
        if 取字段(流式,'step')>0:#Step
            推进步骤(取字段(流式,'turn'),取字段(流式,'step'),已铺列表)#进 Step
        else:#Message
            for 项 in 已铺列表:#逐格
                推进消息(取字段(流式,'turn'),项)#进 Message
        if 已铺列表:#有格
            下标=取字段(已铺列表[-1]['cell'],'index')#同步

    已见=收集调用标识(轮次桶)#布局里已出现的 callId
    for 调用 in 运行中:#尚未入布局的进行中调用
        if 取字段(调用,'callId') in 已见:#已出现
            continue#跳过
        下标+=1#下一个下标
        单元格={'index':下标,'kind':'tool',**摘要调用(取字段(调用,'name'),取字段(调用,'argsRaw')),'inputDetail':取字段(调用,'argsRaw'),'callId':取字段(调用,'callId'),'timeSeconds':None,'startedAt':有限时间(取字段(调用,'time'))}#进行中工具格
        已铺列表=[{'absTime':None,'toolName':取字段(调用,'name'),'callId':取字段(调用,'callId'),'subCalls':取字段(调用,'subCalls'),'cell':单元格}]#首格
        for 子 in 展开子调用(取字段(调用,'subCalls'),下标):#展开子调用
            已铺列表.append(子)#追加
            下标=取字段(子['cell'],'index')#同步
        if 取字段(调用,'step')>0:#Step
            推进步骤(取字段(调用,'turn'),取字段(调用,'step'),已铺列表)#进 Step
        else:#Message
            for 项 in 已铺列表:#逐格
                推进消息(取字段(调用,'turn'),项)#进 Message

    if 0 in 轮次桶:#孤儿 turn-0
        前奏=轮次桶.pop(0)#去掉 0
        第一=轮次桶.get(1,{'groups':[]})#第 1 轮或空桶
        第一['groups']=前奏['groups']+第一['groups']#前奏组接在第 1 轮前
        轮次桶[1]=第一#写回

    for 桶 in list(轮次桶.values())+独立压缩:#所有桶
        for 组 in 桶['groups']:#各组
            for 项 in 组['laid']:#各格
                挂工具模式(项,调用模式)#挂 schema

    结果=[转轮次模型(回合,桶) for 回合,桶 in 轮次桶.items()]+[转轮次模型(None,桶) for 桶 in 独立压缩]#轮次模型
    结果.sort(key=首格下标)#按首格下标排
    return 结果#按首次出现顺序

def 追加轨迹流式布局(轮次们,流式,最后下标):#把流式助手接到定稿布局
    """把变化中的 in-flight 助手单元格接到已定稿布局上。"""
    if 流式 is None:#无进行中
        return 轮次们#原样
    部分轮=派生轨迹布局({'nodes':[],'partial':流式,'runningCalls':[]})#只折 partial
    if not 部分轮:#折不出
        return 轮次们#原样
    流式轮=部分轮[0]#第一轮
    平移={'turn':取字段(流式轮,'turn'),'groups':[{**组,'cells':[{**单元格,'index':取字段(单元格,'index')+最后下标} for 单元格 in 取字段(组,'cells') or []]} for 组 in 取字段(流式轮,'groups') or []]}#下标平移
    回合下标=next((号 for 号,轮 in enumerate(轮次们) if 取字段(轮,'turn')==取字段(平移,'turn')),-1)#同号轮
    if 回合下标==-1:#无同号
        return list(轮次们)+[平移]#追加
    当前=轮次们[回合下标]#该轮现态
    组们=list(取字段(当前,'groups') or [])#可替换的组
    for 流式组 in 取字段(平移,'groups') or []:#流式各组
        组下标=next((号 for 号,组 in enumerate(组们) if 取字段(组,'title')==取字段(流式组,'title')),-1)#同标题
        if 组下标==-1:#尚无
            组们.append(流式组)#追加
            continue#下一组
        现组=组们[组下标]#现组
        流式调用=set(取字段(单元格,'callId') for 单元格 in 取字段(流式组,'cells') or [] if 取字段(单元格,'callId') is not None)#流式 callId
        保留=[单元格 for 单元格 in 取字段(现组,'cells') or [] if 取字段(单元格,'requestOnly') is not True and (取字段(单元格,'callId') is None or 取字段(单元格,'callId') not in 流式调用)]#过滤
        组们[组下标]={**流式组,'cells':保留+list(取字段(流式组,'cells') or [])}#用流式组替换
    更新=list(轮次们)#浅拷贝
    更新[回合下标]={**当前,'groups':组们}#写回该轮
    return 更新#共享未改轮次

追加轨迹部分布局=追加轨迹流式布局#别名，供视图半导入
