import re

__all__=['联系配置全局键','联系字段','配置','Config']

联系配置全局键='__DSH_CONTACT_CONFIG__'
默认问卷地址='https://trtgsjkv6r.feishu.cn/share/base/form/shrcnlCoGElW7MQznGy9r3YYXcg?hide_uid=1&hide_device_info=1&hide_harness_version=1'
问卷地址格式=re.compile(r'^https://[^/\s]+/')

def 取文本(原始,键,默认):
    '缺席用默认。给出了就必须是字符串'
    if 键 not in 原始 or 原始[键] is None:
        return 默认
    值=原始[键]
    if isinstance(值,str) is False:
        raise RuntimeError(键+' must be a string')
    return 值

def 取正数(原始,键,默认):
    '缺席用默认。给出了就必须是不小于 1 的数'
    if 键 not in 原始 or 原始[键] is None:
        return 默认
    值=原始[键]
    if isinstance(值,bool) or isinstance(值,(int,float)) is False or 值<1:
        raise RuntimeError(键+' must be a number >= 1')
    return 值

def 联系字段(原始=None):
    '校验问卷地址、来源和赠金确认重试间隔'
    if 原始 is None:
        原始={}
    if isinstance(原始,dict) is False:
        raise RuntimeError('contact config must be an object')
    地址=取文本(原始,'contactFormUrl',默认问卷地址)
    if 问卷地址格式.search(地址) is None:
        raise RuntimeError('contactFormUrl must be an https URL')
    return {
        'contactFormUrl':地址,
        'contactSource':取文本(原始,'contactSource',''),
        'bonusAckRetryDelayMs':取正数(原始,'bonusAckRetryDelayMs',1000),
        'bonusAckRetryMaxDelayMs':取正数(原始,'bonusAckRetryMaxDelayMs',60000),
    }

def 配置(原始=None):
    '校验宿主和浏览器共用的问卷选项'
    return 联系字段(原始)

Config=配置
