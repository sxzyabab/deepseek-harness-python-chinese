from ...依赖.schemastery import 字符串字段,字典字段

__all__=['配置','联系配置全局键']

联系配置全局键='__DSH_CONTACT_CONFIG__'

默认问卷地址='https://trtgsjkv6r.feishu.cn/share/base/form/shrcnlCoGElW7MQznGy9r3YYXcg'

配置=字典字段(字典结构={
    'contactFormUrl':字符串字段(格式=r'https://[^/\s]+/',默认值=默认问卷地址),
    'contactSource':字符串字段(默认值=''),
})

def 解析联系配置(原始):
    """把页面注入的问卷选项收成带默认值的配置。"""
    表={} if 原始 is None else dict(原始)
    地址=表['contactFormUrl'] if 'contactFormUrl' in 表 and 表['contactFormUrl'] else 默认问卷地址
    来源=表['contactSource'] if 'contactSource' in 表 and 表['contactSource'] is not None else ''
    return {'contactFormUrl':地址,'contactSource':来源}

Config=配置
