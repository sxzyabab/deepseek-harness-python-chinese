import time
import sherpa_onnx
from .输入 import 校验输入

__all__=['创建转写器']

def 创建转写器(配置):
    """加载一对本地模型；每条录音重置 VAD 并更新语言提示。"""
    识别器=sherpa_onnx.OfflineRecognizer.from_sense_voice(
        model=配置['model'],
        tokens=配置['tokens'],
        num_threads=配置['threads'],
        language='auto',
        use_itn=True,
        provider='cpu',
    )
    vad配置=sherpa_onnx.VadModelConfig()
    vad配置.silero_vad.model=配置['vad']
    vad配置.silero_vad.threshold=配置['vadThreshold']
    vad配置.silero_vad.min_silence_duration=配置['minSilenceSeconds']
    vad配置.silero_vad.min_speech_duration=配置['minSpeechSeconds']
    vad配置.silero_vad.max_speech_duration=配置['segmentSeconds']
    vad配置.sample_rate=16000
    vad配置.num_threads=配置['threads']
    vad配置.provider='cpu'
    检测器=sherpa_onnx.VoiceActivityDetector(vad配置,配置['segmentSeconds']+配置['minSilenceSeconds']+1)
    def 转写(音频,语言):
        """同步推理，不出进程。"""
        音频秒=校验输入(音频,语言,配置['maxAudioBytes'])
        pcm=memoryview(音频)[44:]
        样本=[]
        下标=0
        while 下标+2<=len(pcm):
            值=int.from_bytes(pcm[下标:下标+2],'little',signed=True)
            样本.append(值/32768)
            下标+=2
        开始=time.perf_counter()
        文本=[]
        def 排空():
            """取出全部 VAD 段。"""
            while not 检测器.empty():
                段=检测器.front
                流=识别器.create_stream()
                流.accept_waveform(16000,段.samples)
                识别器.decode_stream(流)
                文本.append(识别器.get_result(流).text.strip())
                检测器.pop()
        偏移=0
        while 偏移<len(样本):
            检测器.accept_waveform(样本[偏移:偏移+512])
            排空()
            偏移+=512
        检测器.flush()
        排空()
        检测器.reset()
        return {
            'text':' '.join(项 for 项 in 文本 if 项).strip(),
            'audioSeconds':音频秒,
            'inferenceSeconds':(time.perf_counter()-开始),
        }
    return 转写
