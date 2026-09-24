import base64,math
from ...typert.协议 import 远程服务,远程
from ...依赖.schemastery import 自然数字段,数字字段,字典字段
from ...工具.超时 import 若已中止则抛出
from ..语音转写.波形 import 校验波形
from .类型 import 远程错误

__all__=['依赖','配置','应用','语音转写控制器','远程贡献']

依赖=['speechToText','typert']

配置=字典字段(字典结构={
    'maxAudioBytes':自然数字段(最小=46,默认值=4*1024*1024),
    'maxDurationSeconds':数字字段(最小=1,默认值=120),
})

def 取配置(配置值,键,缺省):
    """配置映射缺席用缺省。"""
    if 配置值 is None or 键 not in 配置值:
        return 缺省
    return 配置值[键]

def 远程流(方法):
    """标为流式 Remote。"""
    方法._typert_remote_marker={'invocation':{'kind':'direct','mode':'stream'}}
    return 方法

class 语音转写控制器(远程服务):
    """带认证、可取消的语音能力 Client 入口。"""
    def __init__(自身,上下文,配置值=None):
        """登记 speech Remote。"""
        super().__init__(上下文,'speechController',{'namespace':'speech'})
        自身.上下文=上下文
        自身.maxAudioBytes=取配置(配置值,'maxAudioBytes',4*1024*1024)
        自身.maxDurationSeconds=取配置(配置值,'maxDurationSeconds',120)

    def 限制(自身):
        """录音接收上限。"""
        return {'maxAudioBytes':自身.maxAudioBytes,'maxDurationSeconds':自身.maxDurationSeconds}

    @远程
    def catalog(自身):
        """读提供方选择，不准备识别器。"""
        return {**自身.上下文.speechToText.快照(),**自身.限制()}

    @远程流
    def follow(自身,signal):
        """独立于 Session 与准备寿命的就绪流。"""
        for 快照 in 自身.上下文.speechToText.跟随(signal):
            yield {**快照,**自身.限制()}

    @远程
    def configure(自身,patch):
        """持久化识别偏好。"""
        return 自身.上下文.speechToText.配置选择(patch)

    @远程
    def prepare(自身,providerId,options=None):
        """启动或加入 Host 准备任务。"""
        自身.上下文.speechToText.准备(providerId,options)

    @远程
    def cancelPreparation(自身,providerId):
        """显式取消准备。"""
        return 自身.上下文.speechToText.取消准备(providerId)

    @远程
    def transcribe(自身,request,signal):
        """校验规范 base64 WAV 后走指定提供方。"""
        若已中止则抛出(signal)
        编码=request['audioBase64']
        上限=math.ceil(自身.maxAudioBytes/3)*4
        if len(编码)>上限:
            raise 远程错误('speech/invalid-audio','Audio is invalid or exceeds the configured byte limit',{'reason':'encoding-or-size'})
        try:
            音频=base64.b64decode(编码,validate=True)
            if base64.b64encode(音频).decode('ascii')!=编码:
                raise RuntimeError('Audio must use canonical base64 encoding')
            if len(音频)>自身.maxAudioBytes:
                raise RuntimeError('Audio exceeds the configured byte limit')
            校验波形(音频,自身.maxDurationSeconds)
            请求={'audio':音频}
            if 'providerId' in request and request['providerId'] is not None:
                请求['providerId']=request['providerId']
            if 'language' in request and request['language'] is not None:
                请求['language']=request['language']
            规格=自身.上下文.speechToText.解析(请求)
            return 自身.上下文.speechToText.转写(规格,signal)
        except Exception as 错误:
            若已中止则抛出(signal)
            if isinstance(错误,远程错误):
                raise 错误
            原因=str(错误)
            raise 远程错误('speech/transcription-failed',原因,{'reason':原因})

远程贡献={
    'package':'@deepseek-ai/dsh-experimental-api-speech-to-text',
    'namespace':'speech',
}

def 应用(上下文,配置值=None):
    """挂上 speech Remote 控制器。"""
    return 语音转写控制器(上下文,配置值)

inject=依赖
apply=应用
Config=配置
default=语音转写控制器
name='speechController'
