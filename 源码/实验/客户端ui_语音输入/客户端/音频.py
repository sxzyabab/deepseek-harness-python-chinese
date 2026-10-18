'浏览器里的麦克风采集，以及重采样后的 PCM16 WAV'
from ....客户端.模块.客户端.通告 import 取握手窗口
import base64#无 data URL 前缀的 base64
import math#振幅的平方根
from ..异常 import 录制错误#采集失败种类

__all__=['逐项','编码波形','音频base64','录制']#采集与编码


def 逐项(序列):
    '页面数组和 Python 列表都能逐个取出'
    if 序列 is None:#没有
        return#空
    if isinstance(序列,(list,tuple)):#本地列表
        for 项 in 序列:#逐个
            yield 项#交出
        return#完
    长度=序列.length#页面数组的长度
    序号=0#下标
    while 序号<长度:#还没读完
        yield 序列[序号]#这一项
        序号=序号+1#下一项


def 采样长度(采样):
    'Float32Array 用 length，列表用 len'
    if isinstance(采样,(list,tuple)):#本地序列
        return len(采样)#个数
    return 采样.length#页面数组


def 读采样(采样,序号):
    '按下标读一个浮点样本'
    return 采样[序号]#这一格


def 写无符号(字节,位置,值,宽度):
    '按小端写入无符号整数'
    片段=int(值).to_bytes(宽度,'little',signed=False)#小端
    字节[位置:位置+宽度]=片段#放进缓冲


def 写文本(字节,位置,文本):
    '把 ASCII 写进指定偏移'
    序号=0#字符下标
    for 字符 in 文本:#逐个
        字节[位置+序号]=ord(字符)#字节值
        序号=序号+1#下一位


def 编码波形(采样):
    '把 16 kHz 单声道浮点采样编成 Host 接受的 PCM16 WAV'
    长度=采样长度(采样)#样本个数
    字节=bytearray(44+长度*2)#头加每个样本两字节
    写文本(字节,0,'RIFF')#组标识
    写无符号(字节,4,len(字节)-8,4)#文件长度减 8
    写文本(字节,8,'WAVE')#格式
    写文本(字节,12,'fmt ')#fmt 块
    写无符号(字节,16,16,4)#fmt 块长度
    写无符号(字节,20,1,2)#PCM
    写无符号(字节,22,1,2)#单声道
    写无符号(字节,24,16000,4)#采样率
    写无符号(字节,28,32000,4)#字节率
    写无符号(字节,32,2,2)#块对齐
    写无符号(字节,34,16,2)#位深
    写文本(字节,36,'data')#数据块
    写无符号(字节,40,长度*2,4)#数据长度
    序号=0#样本下标
    while 序号<长度:#逐个样本
        值=读采样(采样,序号)#原始浮点
        if 值>1:#钳到 1
            值=1#上限
        if 值<-1:#钳到 -1
            值=-1#下限
        幅度=32768 if 值<0 else 32767#负向多一位
        带半=值*幅度#要取整的数
        if 带半>=0:#非负，半数远离零
            整数=int(带半+0.5)#加半再截断
        else:#负数
            整数=int(带半-0.5)#减半再截断
        字节[44+序号*2:44+序号*2+2]=int(整数).to_bytes(2,'little',signed=True)#小端
        序号=序号+1#下一样本
    return bytes(字节)#完整 WAV


def 音频base64(字节):
    '规范 base64，无 data URL 前缀'
    return base64.b64encode(字节).decode('ascii')#与 btoa 的二进制结果相同


class 录制:
    '一次麦克风采集。权限框可能在取消之后才落下'
    def __init__(自身,拆除回调,设备标识=''):
        '记下拆除回调和要打开的设备。空标识跟随系统输入'
        自身.拆除回调=拆除回调#从在途表摘掉
        自身.设备标识=设备标识#exact 约束；空则不指定
        自身.窗口=取握手窗口()#当前页
        自身.流=None#MediaStream
        自身.记录器=None#MediaRecorder
        自身.音频上下文=None#AudioContext
        自身.分析器=None#AnalyserNode
        自身.采样=None#时域缓冲
        自身.块表=[]#录到的 Blob
        自身.已拆=False#拆除只做一次
        自身.寿命=自身.窗口.AbortController()#作废还没回来的授权

    def 已中止(自身):
        '寿命信号是否已经中止'
        信号=自身.寿命.signal#取消信号
        return 信号.aborted is True#已中止

    def 抛若已中止(自身):
        '已取消则抛出取消'
        if 自身.已中止():#授权或停止已被取消
            raise 录制错误('cancelled')#调用方按取消显示

    def 停全部轨(自身,流):
        '停掉这一路媒体的全部轨道'
        if 流 is None:#没有流
            return#不用停
        for 轨 in 逐项(流.getTracks()):#每条轨
            轨.stop()#释放设备

    def 预览(自身,出错=None):
        '只打开选定麦克风和分析器，不录音。已取消的授权立刻停轨'
        设备接口=自身.窗口.navigator.mediaDevices#麦克风
        if 设备接口 is None:#浏览器没有媒体设备
            raise 录制错误('unavailable')#不能录
        音频={'echoCancellation':True,'noiseSuppression':True}#回声和噪声
        if 自身.设备标识!='':#指定了设备
            音频['deviceId']={'exact':自身.设备标识}#必须是这一只
        try:#向浏览器要麦克风
            流=设备接口.getUserMedia({'audio':音频,'video':False})#只要音频
        except Exception as 错误:#授权或设备失败
            名=getattr(错误,'name',None)#DOMException 名
            if 名=='NotAllowedError':#用户拒绝
                raise 录制错误('permission')#权限
            if 名=='NotFoundError' or 名=='OverconstrainedError':#没有这只设备
                raise 录制错误('deviceMissing')#换一只
            raise#其余原样抛出
        if 自身.已中止():#权限框落下时已经取消
            自身.停全部轨(流)#立刻放掉
            raise 录制错误('cancelled')#取消
        自身.流=流#留下这一路
        try:#接上电平分析
            自身.音频上下文=自身.窗口.AudioContext()#音频图
            自身.采样=自身.窗口.Float32Array(256)#时域长度
            自身.分析器=自身.音频上下文.createAnalyser()#电平
            自身.分析器.fftSize=自身.采样.length#与缓冲一样长
            音源=自身.音频上下文.createMediaStreamSource(流)#媒体源
            音源.connect(自身.分析器)#只分析，不播放
            for 轨 in 逐项(流.getTracks()):#每条轨
                def 轨结束(事件,这一轨出错=出错):
                    '设备中途断开'
                    自身.中断(这一轨出错)#先拆再通知
                轨.addEventListener('ended',轨结束)#轨道结束
        except Exception:#分析器没接上
            自身.拆除()#放掉已经打开的设备
            raise#再把原因抛出去

    def 开始(自身,出错=None):
        '打开麦克风并开始录音。已取消的授权立刻停轨'
        记录器类=自身.窗口.MediaRecorder#录音器构造
        if 记录器类 is None:#浏览器不能录
            raise 录制错误('unavailable')#不能录
        自身.预览(出错)#先拿到流和分析器
        if 自身.已中止():#预览期间被取消
            raise 录制错误('cancelled')#取消
        try:#开始把音频写成块
            自身.记录器=记录器类(自身.流)#用当前流
            def 有数据(事件):
                '未取消且有内容才留下'
                if 自身.已中止():#已经取消
                    return#丢掉
                数据=事件.data#这一块
                if 数据 is not None and 数据.size>0:#有字节
                    自身.块表.append(数据)#留下
            def 录出错(事件):
                '录音器失败'
                自身.中断(出错)#通知调用方
            自身.记录器.addEventListener('dataavailable',有数据)#数据块
            自身.记录器.addEventListener('error',录出错)#失败
            自身.记录器.start()#开始
        except Exception:#没开始成功
            自身.拆除()#放掉设备
            raise#再抛

    def 中断(自身,出错):
        '设备或录音器中断。关闭失败不能挡住通知'
        if 自身.已中止():#已经在拆
            return#不用再通知
        try:#先放设备
            自身.拆除()#停轨并关闭上下文
        except Exception as 关闭错误:#关闭失败不掩盖中断
            关闭错误=None#丢掉关闭错误
        try:#再告诉界面
            if 出错 is not None:#调用方要听
                出错(录制错误('interrupted'))#中断
        except Exception as 处理错误:#界面回调自己失败
            自身.窗口.console.error('Speech recording error handler failed',处理错误)#留下日志

    def 振幅(自身):
        '当前 RMS。还没采集时是 0'
        if 自身.分析器 is None or 自身.采样 is None:#没在采集
            return 0#静音
        自身.分析器.getFloatTimeDomainData(自身.采样)#读时域
        合计=0#平方和
        长度=采样长度(自身.采样)#样本数
        序号=0#下标
        while 序号<长度:#逐个
            值=读采样(自身.采样,序号)#样本
            合计=合计+值*值#平方
            序号=序号+1#下一样本
        if 长度==0:#没有样本
            return 0#静音
        return math.sqrt(合计/长度)#均方根

    def 设备信息(自身):
        '实际打开的音轨名称和设备组。没在采集时没有'
        if 自身.流 is None:#没有流
            return None#还没打开
        轨列表=自身.流.getAudioTracks()#音轨
        轨=None#第一轨
        for 一项 in 逐项(轨列表):#取第一只
            轨=一项#这一只
            break#只要第一只
        if 轨 is None:#没有音轨
            return None#没有信息
        设置=轨.getSettings()#轨道设置
        if isinstance(设置,dict):#字典设置
            组=设置.get('groupId') or ''#组标识
        elif 设置 is None:#没有设置
            组=''#空
        else:#页面对象
            组=设置.groupId#设备组
            if 组 is None:#没有组
                组=''#空
        return {'label':轨.label,'groupId':组}#名称和组

    def 停止(自身,最长秒):
        '结束采集，重采样到 16 kHz，返回 WAV。无论成败都拆除'
        记录器=自身.记录器#当前录音器
        音频上下文=自身.音频上下文#用来解码
        if 记录器 is None or 音频上下文 is None or 记录器.state!='recording':#没在录
            自身.拆除()#放掉
            raise 录制错误('empty')#没有音频
        try:#停、解码、重采样
            完成={'停':False,'错':None}#停事件的结果
            def 已停(事件):
                '录音器已经停止'
                完成['停']=True#可以读最后一块
            def 停出错(事件):
                '停止时失败'
                完成['错']=录制错误('empty')#当成没有音频
            记录器.addEventListener('stop',已停)#停止
            记录器.addEventListener('error',停出错)#失败
            记录器.stop()#要求停止
            if 完成['错'] is not None:#停止失败
                raise 完成['错']#空录音
            自身.停全部轨(自身.流)#放掉麦克风
            自身.抛若已中止()#取消则不再解码
            类型=记录器.mimeType#录音器声明的类型
            块=自身.窗口.Blob(自身.块表,{'type':类型})#拼成一块
            if 块.size==0:#没有数据
                raise 录制错误('empty')#空
            缓冲=块.arrayBuffer()#原始字节
            解码=音频上下文.decodeAudioData(缓冲)#解成音频缓冲
            自身.抛若已中止()#解码期间被取消
            时长=解码.duration#秒
            if 时长>最长秒:#超出宿主上限
                时长=最长秒#截断
            帧数=int(时长*16000)#16 kHz 的帧数
            if 帧数<1:#至少一帧
                帧数=1#避免零长度
            离线=自身.窗口.OfflineAudioContext(1,帧数,16000)#单声道重采样
            源=离线.createBufferSource()#缓冲源
            源.buffer=解码#整段
            源.connect(离线.destination)#接到输出
            源.start()#排进离线渲染
            重采样=离线.startRendering()#渲染结果
            自身.抛若已中止()#渲染期间被取消
            return 编码波形(重采样.getChannelData(0))#第一声道编成 WAV
        finally:#无论成败都放设备
            自身.拆除()#停轨并关闭上下文

    def 拆除(自身):
        '释放这一次采集，并作废还没落下的授权'
        if 自身.已拆:#已经拆过
            return#共享同一次清理
        自身.已拆=True#只做一次
        try:#停寿命、轨和上下文
            自身.寿命.abort(录制错误('cancelled'))#后来的授权也算取消
            if 自身.记录器 is not None and 自身.记录器.state=='recording':#还在录
                自身.记录器.stop()#停掉
            自身.停全部轨(自身.流)#放麦克风
            自身.流=None#不再引用
            上下文=自身.音频上下文#待关闭
            自身.音频上下文=None#先摘掉
            自身.分析器=None#分析器随上下文走
            自身.块表=[]#丢掉块
            if 上下文 is not None and 上下文.state!='closed':#还开着
                上下文.close()#关闭
        finally:#关闭失败也要通知拥有者
            自身.拆除回调()#从在途表摘掉
