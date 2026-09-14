from ...约定.种子 import 向导种类#向导种类

__all__=['向导标识','向导定义']#仅中文公开名

向导标识='@deepseek-ai/dsh-client-ui-sidebar-right/guide'#实现身份，亦为正文键


def 向导定义(翻译):
    """向导类型注册表定义。翻译每次取标题时新鲜读取。"""
    return {#右侧 tab 定义
        'id':向导标识,
        'kind':向导种类,
        'priority':'builtin',
        'title':lambda 地址:翻译('tab.guide.title'),
    }#定义结束
