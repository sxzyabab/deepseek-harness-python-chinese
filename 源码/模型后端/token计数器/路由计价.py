"""请求投影表面定价：用路由到模型的图片与文件表示替换附件块启发式。

公开面仅中文名。
"""
from .类型 import 计量错误#计量异常
from .计价 import 计价内容#内容计价

__all__=['计价表面']#仅中文公开名

def 计价表面(节点列表,计价=None,文件文本=None):#为表面定价
    """在其模型请求附件投影下为一有序表面定价。节点为 dict。"""
    图片列表=[] if 计价 is None else [图 for 节点 in 节点列表 for 图 in (节点.get('images') or [])]#全部图片出现
    有文件=文件文本 is not None and any(len(节点.get('files') or [])>0 for 节点 in 节点列表)#是否有文件
    if (计价 is None or len(图片列表)==0) and not 有文件:#无路由替换
        表面令牌=0#合计
        公开=[]#公开节点
        for 节点 in 节点列表:#逐节点
            启发式=节点['heuristicTokens'] if 'heuristicTokens' in 节点 else 节点['tokens']#启发式
            表面令牌+=启发式#累加
            公开.append({'seq':节点['seq'],'tokens':启发式,'heuristicTokens':启发式})#公开
        return {'nodes':公开,'surfaceTokens':表面令牌}#返回
    价格列表=[] if 计价 is None else 计价['priceImages'](图片列表)#问路由价
    if 计价 is not None and len(价格列表)!=len(图片列表):#错位
        raise 计量错误(
            'token meter: route image pricing answered '+str(len(价格列表))+' prices for '+str(len(图片列表))+' occurrences',
        )#响亮失败
    游标=0#图片游标
    表面令牌=0#合计
    公开=[]#公开节点
    for 节点 in 节点列表:#逐节点
        启发式=节点['heuristicTokens'] if 'heuristicTokens' in 节点 else 节点['tokens']#启发式
        令牌数=启发式#起点
        文件列表=节点.get('files') or []#文件
        if 文件文本 is not None and len(文件列表)>0:#替换文件结构价
            令牌数-=节点.get('fileStructuralTokens') or 0#减结构
            for 文件 in 文件列表:#逐文件
                令牌数+=计价内容([{'type':'text','text':文件文本(文件)}])#加句柄文本
        图片=节点.get('images') or []#图片
        if 计价 is not None and len(图片)>0:#替换图片结构价
            令牌数-=节点.get('imageStructuralTokens') or 0#减结构
            for _ in 图片:#逐出现
                价格=价格列表[游标]#取价
                游标+=1#推进
                令牌数+=价格['visualTokens']+计价内容([{'type':'text','text':价格['text']}])#加视觉与句柄
        表面令牌+=令牌数#累加
        公开.append({'seq':节点['seq'],'tokens':令牌数,'heuristicTokens':启发式})#公开
    return {'nodes':公开,'surfaceTokens':表面令牌}#返回
