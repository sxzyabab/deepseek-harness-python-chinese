'一条活动或已落定助手流的块层级'

from ..格式 import 检查器预览上限#折叠推理头的长度上限

class 助手日志流:
    '原始增量留在各自的块下面，折叠的推理头只留有限前缀'
    def __init__(自身,父):
        '父是稳定的助手事件行或活动尝试行'
        自身.父=父#行身份
        自身.块={}#块下标到条目
        自身.计数=0#已收到的原始块数

    @property
    def 长度(自身):
        '全部已收块，包括折叠块里的子行'
        return 自身.计数#计数

    def 追加(自身,块):
        '加入一块原始增量，并更新对应块的展开状态。没有开始块的增量仍是助手的直接子行'
        下标=自身.计数#这一块的序号
        自身.计数=下标+1#推进
        键=自身.父+'/chunk:'+str(下标)#稳定行键
        位置=下标#默认插在已有块数的位置
        行={'key':键,'parent':自身.父,'depth':1}#先当作助手的直接子行
        头=None#需要替换的块头
        条目=None#这一块的账
        if 块.get('type')=='block-start':#块开始
            条目={'row':dict(行),'offset':下标,'children':0}#新块
            条目['row']['disclosure']='open'#开始时展开
            if 块.get('blockType')=='reasoning':#推理块记前缀
                条目['reasoningText']=''#空前缀
            行=条目['row']#行就是块头
            自身.块[块.get('index')]=条目#按下标记住
        else:#块内或没有块的增量
            if 'index' in 块:#有块下标
                条目=自身.块.get(块.get('index'))#已加载的块
            if 条目 is not None:#落进已有块
                位置=条目['offset']+1+条目['children']#插在块头之后
                条目['children']=条目['children']+1#子行加一
                行={'key':键,'parent':条目['row']['key'],'depth':2}#成为块的子行
                for 后续 in 自身.块.values():#后面的块整体后移
                    if 后续['offset']>条目['offset']:#在这个块之后开始
                        后续['offset']=后续['offset']+1#让出一个位置
                if 块.get('type')=='reasoning-delta' and 'reasoningText' in 条目:#推理文本
                    条目['reasoningText']=(条目['reasoningText']+str(块.get('text') or ''))[:检查器预览上限]#有界前缀
                if 块.get('type')=='block-end':#块结束
                    合上=dict(条目['row'])#新的头
                    合上['disclosure']='closed'#默认合上
                    条目['row']=合上#替换头
                    头={'position':条目['offset'],'row':合上}#告诉调用方替换这一行
        结果={'key':键,'index':下标,'position':位置,'row':行}#这一次插入
        if 头 is not None:#头要替换
            结果['header']=头#替换位置和行
        if 条目 is not None and 'reasoningText' in 条目:#推理块有折叠预览
            前缀=条目['reasoningText']#当前前缀
            摘要='blockType: reasoning' #折叠头的固定前缀
            if 前缀!='':#有文本
                摘要=摘要+' · '+前缀#接上前缀
            结果['collapsed']={'key':条目['row']['key'],'summary':摘要[:检查器预览上限]}#折叠时用的摘要
        return 结果#插入、可选的新头和折叠摘要
