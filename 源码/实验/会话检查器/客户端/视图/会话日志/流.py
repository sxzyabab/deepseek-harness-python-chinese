'一条直播或持久 Assistant 流的、按 block 索引的层级'

from ..格式 import 预览上限

__all__=['助手日志流']

class 助手日志流:
    '原始 delta 行留在各自 block 下，折叠表头保留有界推理前缀'
    def __init__(自身,父):
        '父级是稳定的 Assistant 事件或直播 attempt 行身份'
        自身._父=父
        自身._块={}
        自身._数量=0

    @property
    def 长度(自身):
        '本流收到的原始分片数，包括已折叠 block 的子行'
        return 自身._数量

    def 追加(自身,分片):
        '加入一个原始分片，并更新对应 block 的展开状态'
        序号=自身._数量
        自身._数量+=1
        键=f'{自身._父}/chunk:{序号}'
        位置=序号
        行={'key':键,'parent':自身._父,'depth':1}
        头=None
        块=None
        类型=分片['type']
        if 类型=='block-start':
            块={'row':{**行,'disclosure':'open'},'offset':序号,'children':0}
            if 分片.get('blockType')=='reasoning':
                块['reasoningText']=''
            行=块['row']
            自身._块[分片['index']]=块
        else:
            if 'index' in 分片:
                块=自身._块.get(分片['index'])
            if 块 is not None:
                位置=块['offset']+1+块['children']
                块['children']+=1
                行={'key':键,'parent':块['row']['key'],'depth':2}
                for 后续 in 自身._块.values():
                    if 后续['offset']>块['offset']:
                        后续['offset']+=1
                if 类型=='reasoning-delta' and 'reasoningText' in 块:
                    块['reasoningText']=(块['reasoningText']+分片['text'])[:预览上限]
                if 类型=='block-end':
                    块['row']={**块['row'],'disclosure':'closed'}
                    头={'position':块['offset'],'row':块['row']}
        结果={'key':键,'index':序号,'position':位置,'row':行}
        if 头 is not None:
            结果['header']=头
        if 块 is not None and 'reasoningText' in 块:
            文本=块['reasoningText']
            摘要=f'blockType: reasoning{"" if 文本=="" else " · "+文本}'
            结果['collapsed']={'key':块['row']['key'],'summary':摘要[:预览上限]}
        return 结果
