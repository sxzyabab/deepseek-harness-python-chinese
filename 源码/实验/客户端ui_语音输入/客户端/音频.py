from functools import partial as 偏函数
import base64,math
from ....基础设施.js特性 import PromiseEX as 期约#停录、拆除与启动的异步结果
__all__=['录制错误','编码波形','音频base64','录制']

from ..异常 import 录制错误#采集失败

def 编码波形(采样):
    '把 16 kHz 单声道浮点采样编成 Host 接受的 PCM16 WAV'
    数量=len(采样)
    总长=44+数量*2
    缓冲=bytearray(总长)
    def 写文本(位置,值):
        '按 ASCII 写入四字符块'
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
    '规范 base64，无 data URL 前缀'
    return base64.b64encode(字节).decode('ascii')

class 录制:
    '一次麦克风采集；权限对话框可能在取消之后才落下'
    def __init__(自身,拆除回调):
        '记下拆除回调'
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
        '取得麦克风；已取消的授权立刻停轨。返回期约，采集开始后兑现；开始阶段失败时先拆除再拒绝'
        导航=globals().get('navigator')
        记录器类=globals().get('MediaRecorder')
        音频上下文类=globals().get('AudioContext')
        设备=None if 导航 is None else getattr(导航,'mediaDevices',None)
        if 设备 is None or 记录器类 is None or 音频上下文类 is None:
            raise 录制错误('unavailable')
        def 抛出原失败(失败,拆除值=None):#拆除完成
            '抛出原失败'
            raise 失败
        def 拆除后抛出(失败):#开始记录失败
            '先拆除，拆除完成后抛出原失败'
            return 自身.拆除().然后(偏函数(抛出原失败,失败))
        def 收到数据(事件):
            '累积未中止且非空的数据块'
            if not 自身.寿命.信号.已中止() and 事件.data.size>0:
                自身.块表.append(事件.data)
        def 忽略拆除失败(拆除错误):#拆除失败
            '中断回调不依赖拆除结果，拆除失败可忽略'
            return None#失败已消化
        def 记录失败(*位置参数):
            '采集中断则拆除并回调'
            if 自身.寿命.信号.已中止():
                return
            自身.拆除().捕获(忽略拆除失败)#拆除失败不影响中断回调
            try:
                if 出错 is not None:
                    出错(录制错误('interrupted'))
            except Exception as 回调错误:
                print('Speech recording error handler failed',回调错误)
        def 开始采集(启动值):#取得麦克风
            '取得麦克风并开始记录；开始记录阶段失败则拆除后抛出'
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
                自身.记录器.ondataavailable=收到数据
                自身.记录器.onerror=记录失败
                自身.记录器.start()
            except Exception as 错误:
                return 拆除后抛出(错误)
        起点=期约()#取得麦克风在返回之后才开始
        结果=起点.然后(开始采集)
        起点.解决(None)
        return 结果

    def 振幅(自身):
        '当前 RMS；未采集时为 0'
        if 自身.分析器 is None:
            return 0
        自身.分析器.getFloatTimeDomainData(自身.采样)
        平方和=0.0
        for 样本 in 自身.采样:
            平方和+=样本*样本
        return math.sqrt(平方和/len(自身.采样))

    def stop(自身,最长秒):
        '结束采集并重采样到 16 kHz 单声道 WAV。返回期约，兑现值是 WAV 字节；无论成败都拆除'
        记录器=自身.记录器
        上下文=自身.上下文
        if 记录器 is None or 上下文 is None or 记录器.state!='recording':
            def 拆除后抛出空录音(拆除值):#拆除完成
                '拆除后抛出空录音'
                raise 录制错误('empty')
            return 自身.拆除().然后(拆除后抛出空录音)
        完成=期约()#最后一块到达时兑现，停录出错时拒绝
        def 已停(*位置参数):
            '最后一块到达'
            完成.解决(None)
        def 停失败(*位置参数):
            '停录失败'
            完成.拒绝(录制错误('empty'))
        记录器.onstop=已停
        记录器.onerror=停失败
        try:
            记录器.stop()
        except Exception as 错误:
            完成.拒绝(错误)
        def 重采样并编码(停止值):#最后一块已到达
            '停轨后合成二进制块、解码并重采样编码'
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
        return 完成.然后(重采样并编码).最终(自身.拆除)#无论成败都拆除

    def 拆除(自身):
        '释放本采集并作废未决授权。返回共享期约；释放失败（含 AudioContext 关闭失败）时拒绝'
        if 自身.拆除完成 is None:
            起点=期约()#释放在共享期约登记之后才开始
            def 执行释放(启动值):#开始释放
                '执行释放；失败使共享期约拒绝'
                自身.释放()
            自身.拆除完成=起点.然后(执行释放)
            起点.解决(None)
        return 自身.拆除完成

    def 释放(自身):
        '停轨并关闭 AudioContext'
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
