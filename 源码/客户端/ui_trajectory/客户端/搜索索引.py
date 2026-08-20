"""轨迹账本的增量全文索引。

对齐上游 `ui-trajectory/src/client/trajectory-search-index.ts`。公开面仅中文名。
"""
import json#任意值压成 JSON
from .轨迹记录 import 轨迹记录身份,取字段#稳定记录身份
from .轨迹预览 import 轨迹预览文本#Markdown 预览纯文本

__all__=['轨迹搜索索引']#仅中文公开名

def 可检索JSON(值):#任意值压成可检索 JSON 文本
    """缺省或无法序列化则空串。"""
    if 值 is None:#缺省
        return ''#空串
    try:#stringify 可能因循环引用失败
        return json.dumps(值,ensure_ascii=False)#序列化后纳入索引
    except (TypeError,ValueError):#无法序列化
        return ''#失败则空串

def 同源片段(左,右):#两边源片段是否逐项相同
    """等长且每项相等。"""
    return len(左)==len(右) and all(甲==乙 for 甲,乙 in zip(左,右))#等长且每项相等

def Markdown预览(单元格):#单元格 Markdown 预览拼进检索正文
    """摘要与预览用间隔点拼接。"""
    预览源=取字段(单元格,'previewMarkdown')#预览 Markdown
    if 预览源 is None:#没有预览源
        return ''#空
    预览=轨迹预览文本(预览源)#抽有界纯文本预览
    摘要=取字段(单元格,'text') or ''#摘要文本
    if 摘要=='':#摘要为空
        return 预览#只用预览
    return 摘要 if 预览=='' else f'{摘要} · {预览}'#有摘要则与预览拼接

def 结果预览(单元格):#工具结果侧纳入检索的文本
    """结果预览 Markdown 或结果摘要。"""
    结果Markdown=取字段(单元格,'resultPreviewMarkdown')#结果预览
    if 结果Markdown is None:#没有结果预览 Markdown
        return 取字段(单元格,'result') or ''#退回结果摘要或空串
    return 轨迹预览文本(结果Markdown)#抽有界纯文本

def 记录源片段(回合,组标题,单元格):#从单元格抽出参与比对的源片段
    """返回源片段列表。"""
    源块=list(取字段(单元格,'sourceBlocks') or [])#源消息块
    输出块=list(取字段(单元格,'outputBlocks') or [])#输出结果块
    块们=源块+输出块#拼在一起
    片段=[#所有参与比对的片段
        'between turns' if 回合 is None else f'turn {回合}',#回合标签
        组标题,#组标题
        取字段(单元格,'kind') or '',#记录种类
        'assistant' if 取字段(单元格,'kind')=='message' else '',#消息格额外挂 assistant
        取字段(单元格,'text') or '',#摘要文本
        取字段(单元格,'previewMarkdown') or '',#预览 Markdown
        取字段(单元格,'inputDetail') or '',#输入详情
        取字段(单元格,'outputDetail') or '',#输出详情
        取字段(单元格,'thinkingDetail') or '',#推理详情
        取字段(单元格,'schemaDetail') or '',#工具模式详情
        取字段(单元格,'result') or '',#工具结果摘要
        取字段(单元格,'resultPreviewMarkdown') or '',#结果预览 Markdown
        取字段(单元格,'callId') or '',#工具调用 id
    ]#片段主体
    for 块 in 块们:#每块再拆成可检索字段
        片段.extend([#块字段
            取字段(块,'type') or '',#块类型
            取字段(块,'content') or '',#块正文
            取字段(块,'callId') or '',#块上的调用 id
            取字段(块,'toolName') or '',#块上的工具名
            取字段(块,'imageAlt') or '',#图片替代文本
        ])#块字段结束
    片段.append(可检索JSON(取字段(单元格,'messageSource')))#消息来源 JSON
    片段.append(可检索JSON(取字段(单元格,'promptDetail')))#当前提示快照 JSON
    片段.append(可检索JSON(取字段(单元格,'previousPromptDetail')))#先前提示快照 JSON
    return 片段#源片段列表

class 轨迹搜索索引:#轨迹搜索索引
    """会话视图本地索引：仅当某条记录的源片段变化时才重解析 Markdown。"""
    def __init__(自身):#空索引
        """初始化条目表与布局引用。"""
        自身.条目={}#记录 id → 检索条目
        自身.布局们=None#上次同步的布局切片引用

    def 更新(自身,布局们):#同步布局到索引
        """增量同步一份或多份当前轨迹布局切片；布局引用变化时返回真。"""
        if 自身.布局们 is 布局们:#同一引用则无需重扫
            return False#无变化
        自身.布局们=布局们#记下当前布局引用
        仍在=set()#本轮仍存在的记录 id
        for 轮次们 in 布局们:#每份布局切片
            for 轮次 in 轮次们:#每个回合
                for 组 in 取字段(轮次,'groups') or []:#每个组
                    for 单元格 in 取字段(组,'cells') or []:#每个单元格
                        if 取字段(单元格,'requestOnly') is True:#纯请求锚点不入索引
                            continue#跳过
                        标识=轨迹记录身份(单元格)#稳定记录身份
                        源们=记录源片段(取字段(轮次,'turn'),取字段(组,'title') or '',单元格)#抽出源片段
                        先前=自身.条目.get(标识)#已有条目
                        if 先前 is not None and 同源片段(先前['sources'],源们):#源未变则复用
                            条目=先前#沿用旧条目
                        else:#源变了则重建
                            正文='\n'.join(list(源们)+[Markdown预览(单元格),结果预览(单元格)]).lower()#检索正文小写
                            条目={'sources':源们,'text':正文}#新条目
                        自身.条目[标识]=条目#写入/覆盖
                        仍在.add(标识)#标记仍存在
        for 标识 in list(自身.条目.keys()):#扫已有条目
            if 标识 not in 仍在:#本轮未见
                del 自身.条目[标识]#删除
        return True#布局引用已更新

    def 搜索(自身,查询):#按查询词匹配记录
        """空格分隔、大小写不敏感；无查询词时为 None。"""
        词们=[词 for 词 in 查询.strip().lower().split() if 词]#切词、去空白、小写
        if len(词们)==0:#没有有效词
            return None#不算检索
        命中=set()#命中的记录 id
        for 标识,条目 in 自身.条目.items():#逐条比对
            正文=条目['text']#检索正文
            if all(词 in 正文 for 词 in 词们):#所有词都出现才命中
                命中.add(标识)#命中
        return 命中#命中集合
