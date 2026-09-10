"""权威的瞬时队列投影与持久 steering 交接。

对齐上游 `session-controller/src/client/sessions/queue-mirror.ts`。公开面仅中文名。
"""
__all__=['会话队列镜像']#仅中文公开名

_队列预览字符=200#预览字符上限

def _预览(内容):
    """生成预览：排除附件块。"""
    片段=[]#片段
    for 块 in 内容:#逐块
        if not isinstance(块,dict):#非对象
            continue#跳过
        种类=块['type'] if 'type' in 块 else None#类型
        if 种类 in ('image','file'):#附件
            continue#跳过
        if 种类=='text':#文本
            片段.append(块['text'] if 'text' in 块 else '')#文本
        else:#其它
            片段.append('['+str(种类)+']')#类型标
    扁平=' '.join(片段)#拼接
    扁平=' '.join(扁平.split())#压平空白
    码点=list(扁平)#按码点
    if len(码点)>_队列预览字符:#截断
        return ''.join(码点[:_队列预览字符])+'…'#截断
    return 扁平#原样

def _纯文本(内容):
    """纯文本或 None。"""
    if not all(isinstance(块,dict) and 块.get('type')=='text' for 块 in 内容):#非纯文本
        return None#无
    return ''.join(块['text'] if 'text' in 块 else '' for 块 in 内容)#拼接

class 会话队列镜像:
    """权威的瞬时队列投影与持久 steering 交接。"""

    def __init__(自身):
        """空投影。"""
        自身._当前=()#当前投影

    def 快照(自身):
        """返回当前不可变队列投影。"""
        return 自身._当前#当前

    def 替换(自身,项列表):
        """用一条权威流队列帧整体替换。"""
        行列表=[]#行
        for 项 in 项列表:#映射
            内容=list(项['message']['content']) if isinstance(项.get('message'),dict) and 'content' in 项['message'] else []#内容
            行={
                'id':项['id'],
                'messageId':项['message']['id'] if isinstance(项.get('message'),dict) and 'id' in 项['message'] else 项['id'],
                'placement':项['placement'],
                'content':内容,
                'preview':_预览(内容),
                'text':_纯文本(内容),
            }#行
            if 'rpcId' in 项 and 项['rpcId'] is not None:#可选 rpc
                行['rpcId']=项['rpcId']#写入
            行列表.append(行)#收下
        自身._当前=tuple(行列表)#冻结

    def 接受耐久(自身,事件):
        """当其持久消息进入日志后，退役一条瞬时 steering 行。返回是否变化。"""
        if 事件.get('type')!='user/message':#仅用户消息
            return False#无
        消息标识=事件['data']['id'] if isinstance(事件.get('data'),dict) and 'id' in 事件['data'] else None#消息 id
        if 消息标识 is None:#无
            return False#无
        下标=-1#定位
        for 候选下标,项 in enumerate(自身._当前):#扫描
            if 项.get('placement')=='steering' and 项.get('messageId')==消息标识:#命中
                下标=候选下标#记下
                break#停
        if 下标<0:#未找到
            return False#无
        自身._当前=tuple(项 for 候选下标,项 in enumerate(自身._当前) if 候选下标!=下标)#移除
        return True#已变化
