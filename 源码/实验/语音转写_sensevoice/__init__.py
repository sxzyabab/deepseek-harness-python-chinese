import os
from urllib.parse import urlparse
from .配置 import 配置,应用配置
from .识别器 import sensevoice工作者
from .输入 import 语言表

__all__=['名称','依赖','配置','应用']

名称='experimental-speech-to-text-sensevoice'
依赖=['speechToText','subprocess']

def 应用(上下文,配置值=None):
    """登记本地识别器；启用时只检查磁盘缓存。"""
    配置对象=应用配置(配置值)
    for 路径 in (配置对象['dataRoot'],配置对象['modelDirectory'],配置对象['vadModelPath']):
        if 路径 is not None and not os.path.isabs(路径):
            raise RuntimeError('SenseVoice paths must be absolute: '+路径)
    源表=配置对象['modelOrigins'] if 配置对象['modelOrigin'] is None else [配置对象['modelOrigin']]
    for 源 in 源表:
        urlparse(源)
    工作者=sensevoice工作者(上下文,配置对象)
    估算字节=1000000000 if 配置对象['precision']=='int8' else 2000000000
    def 挂():
        """登记提供方。"""
        def 转写(输入,信号):
            """交给工作者。"""
            return 工作者.transcribe(输入,信号)
        卸=上下文.speechToText.登记({
            'info':{
                'id':配置对象['providerId'],
                'name':'SenseVoiceSmall ('+配置对象['precision'].upper()+')',
                'location':'host-local',
                'languages':语言表,
                'downloadSources':工作者.downloadSources,
                'setupEstimate':{
                    'recommendedDiskBytes':估算字节,
                    'expectedMemoryBytes':估算字节,
                    'minimumMinutes':1,
                    'maximumMinutes':10,
                },
            },
            'preparation':{
                'snapshot':工作者.snapshot,
                'subscribe':工作者.subscribe,
                'prepare':工作者.prepare,
                'cancel':工作者.cancel,
            },
            'transcribe':转写,
        })
        工作者.inspect()
        def 拆():
            """先卸注册再停工作者。"""
            卸()
            工作者.dispose()
        return 拆
    上下文.副作用(挂)

name=名称
inject=依赖
apply=应用
Config=配置
