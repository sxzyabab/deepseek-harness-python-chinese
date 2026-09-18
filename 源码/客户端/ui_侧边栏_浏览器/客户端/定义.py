__all__=['浏览器种类','浏览器标识','浏览器定义']#仅中文公开名

浏览器种类='browser'#浏览器标签种类（线路字面量）
浏览器标识='@deepseek-ai/dsh-client-ui-sidebar-browser'#实现身份与带键席位键

def 浏览器定义(翻译):
    """构造带实时文案的浏览器类型定义。"""
    return {#右侧侧栏 tab 定义
        'id':浏览器标识,#实现身份
        'kind':浏览器种类,#种类
        'multiple':True,#可多开
        'priority':'builtin',#内置档
        'title':lambda:翻译('type.label'),#芯片标题
        'guide':[{#引导条目
            'id':'new',#引导 id
            'order':30,#行序
            'title':lambda:翻译('guide.title'),#引导标题
            'description':lambda:翻译('guide.description'),#引导说明
            'icon':'IconGlobeOutline14',#地球图标名
        }],
    }#定义结束
