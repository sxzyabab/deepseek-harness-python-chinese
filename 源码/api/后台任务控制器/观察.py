from ...工具.超时 import 若已中止则抛出,已中止
from .唤醒 import 输出等待者,休眠

__all__=['观察作业输出']

def 是否终态(状态):
    """非 running/stopping 即为终态。"""
    return 状态!='running' and 状态!='stopping'

def 观察作业输出(注册表,请求,选项,信号):
    """从绝对偏移观察保留输出：开口锚、合并输出帧、终态后关闭。"""
    if 'from' in 请求:
        起点=请求['from']
        if isinstance(起点,bool) or not isinstance(起点,int) or 起点<0:
            raise ValueError('invalid observe offset: expected a non-negative safe integer, got '+repr(起点))
    若已中止则抛出(信号)
    标识=str(请求['jobId'])
    等待者=输出等待者()
    已移除=[None]
    def 监听(事件):
        """只响应本作业。"""
        变更=事件['id'] if 事件['type']=='output' else 事件['job']['id']
        if 变更!=标识:
            return
        if 事件['type']=='removed':
            已移除[0]=事件['job']
        等待者.唤醒()
    退订=注册表.events.subscribe({'owners':'all'},监听)
    try:
        会话=请求['sessionId'] if 'sessionId' in 请求 else None
        作业=注册表.get(标识,会话)
        游标=请求['from'] if 'from' in 请求 else 作业['output']['earliest']
        yield {'type':'opened','job':作业,'from':游标}
        while not 已中止(信号):
            if 已移除[0] is not None:
                yield {'type':'status','job':已移除[0]}
                return
            读=注册表.readAt(标识,游标,会话)
            if len(读['chunks'])>0 or 读.get('lossy'):
                yield from 输出帧(读['chunks'],读['next'],bool(读.get('lossy')),选项['maxFrameBytes'])
            游标=读['next']
            作业=注册表.get(标识,会话)
            if 是否终态(作业['status']) and 游标>=作业['output']['total']:
                yield {'type':'status','job':作业}
                return
            等待者.等待(信号)
            休眠(选项['flushMs'],信号)
    finally:
        退订()

def 输出帧(块列表,下一偏移,有损,最大帧字节):
    """按软字节预算切分一次读取。"""
    批次=[]
    批次字节=0
    标有损=有损
    for 块 in 块列表:
        批次.append(块)
        批次字节+=len(块['text'].encode('utf-8'))
        if 批次字节>=最大帧字节:
            末=批次[len(批次)-1]
            结束=末['at']+len(末['text'].encode('utf-8'))
            帧={'type':'output','chunks':批次,'next':结束}
            if 标有损:
                帧['lossy']=True
            yield 帧
            标有损=False
            批次=[]
            批次字节=0
    if len(批次)>0 or 标有损:
        帧={'type':'output','chunks':批次,'next':下一偏移}
        if 标有损:
            帧['lossy']=True
        yield 帧
