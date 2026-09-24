from ...依赖.schemastery import (
    字符串字段,
    自然数字段,
    数字字段,
    枚举字段,
    列表字段,
    字典字段,
)
from ...工具.超时 import 定时器延迟上限毫秒

__all__=['配置','应用配置']

源模式=r'^https?://[^/\s?#@]+/?$'

配置=字典字段(字典结构={
    'providerId':字符串字段(最小长度=1,默认值='sensevoice-local'),
    'dataRoot':字符串字段(最小长度=1),
    'modelDirectory':字符串字段(最小长度=1,可空=True),
    'vadModelPath':字符串字段(最小长度=1,可空=True),
    'precision':枚举字段('int8','fp32',默认值='int8'),
    'modelOrigin':字符串字段(格式=源模式,可空=True),
    'modelOrigins':列表字段(字符串字段(格式=源模式),最小数量=1,默认值=['https://huggingface.co','https://hf-mirror.com']),
    'modelProbeTimeoutMs':自然数字段(最小=1,最大=定时器延迟上限毫秒,默认值=3000),
    'threads':自然数字段(最小=1,默认值=2),
    'segmentSeconds':数字字段(最小=1,最大=120,默认值=30),
    'vadThreshold':数字字段(最小=0,最大=1,默认值=0.5),
    'minSpeechSeconds':数字字段(最小=0,默认值=0.25),
    'minSilenceSeconds':数字字段(最小=0.01,默认值=0.5),
    'maxAudioBytes':自然数字段(最小=46,默认值=4*1024*1024),
    'prepareTimeoutMs':自然数字段(最小=1,最大=定时器延迟上限毫秒,默认值=3600000),
    'inferenceTimeoutMs':自然数字段(最小=1,最大=定时器延迟上限毫秒,默认值=120000),
    'idleTimeoutMs':自然数字段(最大=定时器延迟上限毫秒,默认值=300000),
    'maxPending':自然数字段(最小=1,默认值=4),
    'graceMs':自然数字段(最小=1,最大=定时器延迟上限毫秒,默认值=1000),
    'maxLogBytes':自然数字段(最小=1,默认值=64*1024),
    'maxResponseBytes':自然数字段(最小=1,默认值=128*1024),
    'progressIntervalMs':自然数字段(最小=1,最大=定时器延迟上限毫秒,默认值=100),
})

缺省源=['https://huggingface.co','https://hf-mirror.com']

def 取(配置值,键,缺省):
    """配置映射缺席用缺省。"""
    if 配置值 is None or 键 not in 配置值 or 配置值[键] is None:
        return 缺省
    return 配置值[键]

def 应用配置(配置值):
    """部署期运行时选择。"""
    return {
        'providerId':取(配置值,'providerId','sensevoice-local'),
        'dataRoot':配置值['dataRoot'],
        'modelDirectory':取(配置值,'modelDirectory',None),
        'vadModelPath':取(配置值,'vadModelPath',None),
        'precision':取(配置值,'precision','int8'),
        'modelOrigin':取(配置值,'modelOrigin',None),
        'modelOrigins':取(配置值,'modelOrigins',缺省源),
        'modelProbeTimeoutMs':取(配置值,'modelProbeTimeoutMs',3000),
        'threads':取(配置值,'threads',2),
        'segmentSeconds':取(配置值,'segmentSeconds',30),
        'vadThreshold':取(配置值,'vadThreshold',0.5),
        'minSpeechSeconds':取(配置值,'minSpeechSeconds',0.25),
        'minSilenceSeconds':取(配置值,'minSilenceSeconds',0.5),
        'maxAudioBytes':取(配置值,'maxAudioBytes',4*1024*1024),
        'prepareTimeoutMs':取(配置值,'prepareTimeoutMs',3600000),
        'inferenceTimeoutMs':取(配置值,'inferenceTimeoutMs',120000),
        'idleTimeoutMs':取(配置值,'idleTimeoutMs',300000),
        'maxPending':取(配置值,'maxPending',4),
        'graceMs':取(配置值,'graceMs',1000),
        'maxLogBytes':取(配置值,'maxLogBytes',64*1024),
        'maxResponseBytes':取(配置值,'maxResponseBytes',128*1024),
        'progressIntervalMs':取(配置值,'progressIntervalMs',100),
    }

Config=配置
