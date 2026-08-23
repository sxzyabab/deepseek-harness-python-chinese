"""从 `./client` 导出的浏览器实现的宿主加载器入口。

对齐上游 `@deepseek-ai/dsh-client-ui-settings-general`。公开面仅中文名。在存在设置提供方时登记持久化 GUI 引导分区。
"""
from ...依赖 import schemastery#外部依赖胶水
模式=schemastery.模式#配置模式

__all__=['应用','引导设置命名空间','引导设置模式']#仅中文公开名

引导设置命名空间='ui-onboarding'#产品级 GUI 引导事实的持久化设置命名空间
引导设置模式=模式.对象({#持久化引导分区模式
    'welcomeNoticeVersion':模式.字符串(),#欢迎声明版本字符串
})#模式结束

def 应用(上下文):#安装宿主引导设置
    """在存在设置提供方时登记持久化 GUI 引导分区。"""
    def 登记(设置上下文):#等 settings 出现再登记
        """登记引导设置分区。"""
        设置上下文.settings.register(引导设置命名空间,引导设置模式)#登记分区
    上下文.inject(['settings'],登记)#等 settings 出现再登记
