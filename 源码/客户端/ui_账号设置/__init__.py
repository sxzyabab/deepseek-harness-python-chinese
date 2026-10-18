from . import 上手引导设置,客户端,异常,联系配置
from .上手引导设置 import 引导设置
from .联系配置 import 联系配置全局键,联系字段

__all__=['应用','配置','客户端','异常','联系配置','上手引导设置']

def 配置(原始=None):
    '合并问卷选项和设备本地的上手引导进度'
    if 原始 is None:
        原始={}
    if isinstance(原始,dict) is False:
        raise RuntimeError('account config must be an object')
    结果=联系字段(原始)
    结果.update(引导设置(原始))
    return 结果

def 应用(上下文,配置值):
    '浏览器插件激活前发布问卷选项，并关掉设置的自动呈现'
    def 接线(子上下文):
        '有 settings 时关掉自动呈现'
        def 挂():
            'auto:false 绑到本纤程'
            return 子上下文.settings.configure({'auto':False},上下文.纤程)
        子上下文.副作用(挂)
    上下文.依赖启动(['settings'],接线)
    def 注入页(表):
        '写入不含账号凭证的页面全局'
        表.append({
            'kind':'global',
            'name':联系配置全局键,
            'value':{
                'contactFormUrl':配置值['contactFormUrl'],
                'contactSource':配置值['contactSource'],
                'bonusAckRetryDelayMs':配置值['bonusAckRetryDelayMs'],
                'bonusAckRetryMaxDelayMs':配置值['bonusAckRetryMaxDelayMs'],
            },
        })
    上下文.监听('webserver/index-inject',注入页)

apply=应用
Config=配置
