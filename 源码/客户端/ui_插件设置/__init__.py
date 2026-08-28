"""插件设置面的节点半边。

对齐上游 `@deepseek-ai/dsh-client-ui-settings-plugins`。公开面仅中文名。空 apply 存在是为了让插件出现在宿主 cordis.yml / Loader 中；浏览器半边通过 exports["./client"] 拥有分区及其可配置页签。本页编辑的每个分区都由登记它的宿主插件拥有，因此本包不登记自己的命名空间。
"""

__all__=['应用']#仅中文公开名

def 应用():#宿主插件体
    """本表面插件无宿主侧行为。"""
    return#空 apply，仅占 Loader 行
