from ..浏览器.导航 import 浏览器导航#导航

__all__=['浏览器标题']#仅中文公开名

def 浏览器标题(属性):
    """产出芯片标题：地球图标与当前主机名。"""
    标签=属性['useTabInfo']()['tab']#标签
    def 选当前(状态):
        """取当前历史条目。"""
        桶=状态['byTab'][标签['id']] if 标签['id'] in 状态['byTab'] else None#桶
        return 浏览器导航.当前(桶)#当前
    条目=属性['useStore'](选当前)#当前
    return {#结构
        'kind':'browser-title',#种类
        'title':条目['title'] if 条目 is not None else 标签['title'],#标题
        'icon':'IconGlobeOutline14',#图标
        'cssModule':'浏览器.module.css',#样式
    }#结束
