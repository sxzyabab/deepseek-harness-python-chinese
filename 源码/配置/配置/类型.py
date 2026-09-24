"""客户端安全的配置表单视图与变更通知。"""

def 设置命名空间品牌(原始):
    """把字符串打成设置命名空间品牌。一个配置档插件条目的名义 id。不做校验。"""
    return 原始

设置更新来源=('update','provider')

# 事件 settings/document-updated(ns, revision) @mode emit：一个配置档条目的表单值、可用性或页面策略已变。表单客户端再读其 schema、解析值与修订。参数 ns 为配置档条目 id，revision 为该条目新修订号。
