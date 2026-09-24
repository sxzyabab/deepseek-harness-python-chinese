from .....客户端.存储 import 通知订阅者

__all__=['客户端作业模型']

渲染尾上限=128*1024

def 按字节裁尾(文本,上限):
    """保留末尾上限字节，切点落在 UTF-8 字符边界。"""
    字节=文本.encode('utf-8')
    if len(字节)<=上限:
        return 文本,False
    切=len(字节)-上限
    while 切<len(字节) and (字节[切]&0xC0)==0x80:
        切+=1
    return 字节[切:].decode('utf-8'),True

class 客户端作业模型:
    """无 UI 的作业名册与观察态。"""
    def __init__(自身):
        """空快照。"""
        自身._会话表行={}
        自身._观察态={}
        自身._监听者=set()
        自身._快照缓存={'rows':{},'observed':{}}
        自身._快照脏=False

    def 获取快照(自身):
        """身份稳定的当前快照。"""
        if 自身._快照脏:
            表行={}
            for 标识,作业列表 in 自身._会话表行.items():
                表行[标识]=作业列表
            观察={}
            for 标识,状态 in 自身._观察态.items():
                观察[标识]=状态['view']
            自身._快照缓存={'rows':表行,'observed':观察}
            自身._快照脏=False
        return 自身._快照缓存

    def 订阅(自身,监听者):
        """登记失效回调。"""
        自身._监听者.add(监听者)
        def 退订():
            """去掉监听者。"""
            自身._监听者.discard(监听者)
        return 退订

    def 替换表行(自身,会话标识,作业列表):
        """用整表替换一名册；空表去掉键。"""
        键=str(会话标识)
        if len(作业列表)==0:
            if 键 not in 自身._会话表行:
                return
            del 自身._会话表行[键]
        else:
            自身._会话表行[键]=作业列表
        自身._已变()

    def 丢弃表行(自身,会话标识):
        """最后一名监视者离开或流出失败。"""
        if 自身._会话表行.pop(str(会话标识),None) is None:
            return
        自身._已变()

    def 游标(自身,标识):
        """下一代观察的 from；新观察为 None。"""
        状态=自身._观察态.get(str(标识))
        if 状态 is None:
            return None
        return 状态['cursor']

    def 观察已打开(自身,标识,帧):
        """开口锚到达时安装或重置观察态。"""
        已有=自身._观察态.get(str(标识))
        已有文本='' if 已有 is None else 已有['view']['text']
        已有缺口=False if 已有 is None else 已有['view']['gapBefore']
        新过零=(已有 is None or 已有文本=='') and 帧['from']>0
        缺口=已有缺口 or 帧['from']<帧['job']['output']['earliest'] or 新过零
        视图={'jobId':标识,'text':已有文本,'gapBefore':缺口,'streaming':True}
        自身._观察态[str(标识)]={'view':视图,'cursor':帧['from']}
        自身._已变()

    def 观察输出(自身,标识,帧):
        """把一帧输出追加到有界渲染尾。"""
        状态=自身._观察态.get(str(标识))
        if 状态 is None:
            return
        文本=状态['view']['text']+''.join(块['text'] for 块 in 帧['chunks'])
        缺口=状态['view']['gapBefore'] or 帧.get('lossy') is True
        for 块 in 帧['chunks']:
            if 块.get('gapBefore') is True:
                缺口=True
        文本,裁过=按字节裁尾(文本,渲染尾上限)
        if 裁过:
            缺口=True
        状态['view']={**状态['view'],'text':文本,'gapBefore':缺口}
        状态['cursor']=帧['next']
        自身._已变()

    def 观察已结算(自身,标识):
        """终态帧到达后关闭直播。"""
        状态=自身._观察态.get(str(标识))
        if 状态 is None:
            return
        状态['view']={**状态['view'],'streaming':False}
        自身._已变()

    def 观察失败(自身,标识,错误):
        """记下观察流异常结束。"""
        状态=自身._观察态.get(str(标识))
        if 状态 is None:
            自身._观察态[str(标识)]={
                'view':{'jobId':标识,'text':'','gapBefore':False,'streaming':False,'error':str(错误)},
                'cursor':None,
            }
            自身._已变()
            return
        状态['view']={**状态['view'],'streaming':False,'error':str(错误)}
        自身._已变()

    def 观察已停止(自身,标识):
        """最后一名观察者离开。"""
        if str(标识) not in 自身._观察态:
            return
        del 自身._观察态[str(标识)]
        自身._已变()

    def _已变(自身):
        """标脏并通知。"""
        自身._快照脏=True
        通知订阅者(自身._监听者,'jobs')
