import base64,math,threading
from ....工具.超时 import 中止控制器,若已中止则抛出

__all__=['录制错误','编码波形','音频base64','录制']

class 录制错误(Exception):
    """采集失败，文案键由调用方按 kind 翻译。"""
    def __init__(自身,kind):
        """kind 为 unavailable / permission / empty / cancelled / interrupted。"""
        super().__init__(kind)
        自身.kind=kind
        自身.name='RecordingError'

def 编码波形(采样):
    """把 16 kHz 单声道浮点采样编成 Host 接受的 PCM16 WAV。"""
    数量=len(采样)
    总长=44+数量*2
    缓冲=bytearray(总长)
    def 写文本(位置,值):
        """按 ASCII 写入四字符块。"""
        for 下标,字符 in enumerate(值):
            缓冲[位置+下标]=ord(字符)
    写文本(0,'RIFF')
    缓冲[4:8]=(总长-8).to_bytes(4,'little')
    写文本(8,'WAVE')
    写文本(12,'fmt ')
    缓冲[16:20]=(16).to_bytes(4,'little')
    缓冲[20:22]=(1).to_bytes(2,'little')
    缓冲[22:24]=(1).to_bytes(2,'little')
    缓冲[24:28]=(16000).to_bytes(4,'little')
    缓冲[28:32]=(32000).to_bytes(4,'little')
    缓冲[32:34]=(2).to_bytes(2,'little')
    缓冲[34:36]=(16).to_bytes(2,'little')
    写文本(36,'data')
    缓冲[40:44]=(数量*2).to_bytes(4,'little')
    for 下标 in range(数量):
        样本=采样[下标]
        夹取=max(-1,min(1,样本))
        量化=int(round(夹取*(32768 if 夹取<0 else 32767)))
        缓冲[44+下标*2:46+下标*2]=量化.to_bytes(2,'little',signed=True)
    return bytes(缓冲)

def 音频base64(字节):
    """规范 base64，无 data URL 前缀。"""
    return base64.b64encode(字节).decode('ascii')

class 录制:
    """一次麦克风采集；权限对话框可能在取消之后才落下。"""
    def __init__(自身,拆除回调):
        """记下拆除回调。"""
        自身.流=None
        自身.记录器=None
        自身.上下文=None
        自身.分析器=None
        自身.采样=[0.0]*256
        自身.块表=[]
        自身.寿命=中止控制器()
        自身.拆除完成=None
        自身.拆除回调=拆除回调

    def start(自身,出错=None):
        """取得麦克风；已取消的授权立刻停轨。"""
        导航=globals().get('navigator')
        记录器类=globals().get('MediaRecorder')
        音频上下文类=globals().get('AudioContext')
        设备=None if 导航 is None else getattr(导航,'mediaDevices',None)
        if 设备 is None or 记录器类 is None or 音频上下文类 is None:
            raise 录制错误('unavailable')
        try:
            流=设备.getUserMedia({'audio':{'echoCancellation':True,'noiseSuppression':True},'video':False})
        except Exception as 错误:
            名称=getattr(错误,'name',None)
            if 名称=='NotAllowedError':
                raise 录制错误('permission')
            raise
        if 自身.寿命.信号.已中止():
            for 轨 in 流.getTracks():
                轨.stop()
            raise 录制错误('cancelled')
        自身.流=流
        try:
            自身.上下文=音频上下文类()
            自身.分析器=自身.上下文.createAnalyser()
            自身.分析器.fftSize=len(自身.采样)
            自身.上下文.createMediaStreamSource(流).connect(自身.分析器)
            自身.记录器=记录器类(流)
            def 收到数据(事件):
                """累积未中止且非空的数据块。"""
                if not 自身.寿命.信号.已中止() and 事件.data.size>0:
                    自身.块表.append(事件.data)
            def 记录失败(*位置参数):
                """采集中断则拆除并回调。"""
                if 自身.寿命.信号.已中止():
                    return
                try:
                    自身.拆除()
                except Exception:
                    pass
                try:
                    if 出错 is not None:
                        出错(录制错误('interrupted'))
                except Exception as 回调错误:
                    print('Speech recording error handler failed',回调错误)
            自身.记录器.ondataavailable=收到数据
            自身.记录器.onerror=记录失败
            自身.记录器.start()
        except Exception:
            自身.拆除()
            raise

    def 振幅(自身):
        """当前 RMS；未采集时为 0。"""
        if 自身.分析器 is None:
            return 0
        自身.分析器.getFloatTimeDomainData(自身.采样)
        平方和=0.0
        for 样本 in 自身.采样:
            平方和+=样本*样本
        return math.sqrt(平方和/len(自身.采样))

    def stop(自身,最长秒):
        """结束采集并重采样到 16 kHz 单声道 WAV。"""
        记录器=自身.记录器
        上下文=自身.上下文
        if 记录器 is None or 上下文 is None or 记录器.state!='recording':
            自身.拆除()
            raise 录制错误('empty')
        try:
            完成=threading.Event()
            失败=[None]
            def 已停(*位置参数):
                """最后一块到达。"""
                完成.set()
            def 停失败(*位置参数):
                """停录失败。"""
                失败[0]=录制错误('empty')
                完成.set()
            记录器.onstop=已停
            记录器.onerror=停失败
            记录器.stop()
            完成.wait()
            if 失败[0] is not None:
                raise 失败[0]
            if 自身.流 is not None:
                for 轨 in 自身.流.getTracks():
                    轨.stop()
            若已中止则抛出(自身.寿命.信号)
            二进制块类=globals()['Blob']
            二进制块=二进制块类(自身.块表,{'type':记录器.mimeType})
            if 二进制块.size==0:
                raise 录制错误('empty')
            解码=上下文.decodeAudioData(二进制块.arrayBuffer())
            若已中止则抛出(自身.寿命.信号)
            帧数=max(1,int(min(解码.duration,最长秒)*16000))
            离线类=globals()['OfflineAudioContext']
            离线=离线类(1,帧数,16000)
            源=离线.createBufferSource()
            源.buffer=解码
            源.connect(离线.destination)
            源.start()
            重采样=离线.startRendering()
            若已中止则抛出(自身.寿命.信号)
            return 编码波形(重采样.getChannelData(0))
        finally:
            自身.拆除()

    def 拆除(自身):
        """释放本采集并作废未决授权。"""
        if 自身.拆除完成 is None:
            自身.拆除完成=threading.Event()
            try:
                自身.释放()
            finally:
                自身.拆除完成.set()
        自身.拆除完成.wait()

    def 释放(自身):
        """停轨并关闭 AudioContext。"""
        自身.寿命.中止(录制错误('cancelled'))
        if 自身.记录器 is not None and 自身.记录器.state=='recording':
            自身.记录器.stop()
        if 自身.流 is not None:
            for 轨 in 自身.流.getTracks():
                轨.stop()
        自身.流=None
        上下文=自身.上下文
        自身.上下文=None
        自身.分析器=None
        自身.块表=[]
        try:
            if 上下文 is not None and 上下文.state!='closed':
                上下文.close()
        finally:
            自身.拆除回调()
