from ...依赖.schemastery import 字符串字段

__all__=['应用','引导设置命名空间','引导设置模式']

引导设置命名空间='ui-onboarding'
引导设置模式={
    'welcomeNoticeVersion':字符串字段(),
}

def 应用(上下文):
    """在存在设置提供方时登记持久化 GUI 引导分区。"""
    def 登记(设置上下文):
        """登记引导设置分区。"""
        设置上下文.settings.register(引导设置命名空间,引导设置模式)
    上下文.依赖启动(['settings'],登记)

apply=应用
