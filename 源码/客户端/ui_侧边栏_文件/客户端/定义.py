"""本包登记的第一阶段：`files` tab 类型是什么。

对齐上游 `ui-sidebar-files/src/client/definition.tsx`。公开面仅中文名。
该类型是页面而非查看器：不宣称地址。向导页把它作为入口；树经 `tabActions.openResource`
打开文件，由 `dsh-resource://file` 查看器认领。
"""

__all__=['文件种类','文件标识','文件定义','文件夹页字形']#仅中文公开名

文件种类='files'#本包拥有的 tab 种类（线路字面量）
文件标识='@deepseek-ai/dsh-client-ui-sidebar-files'#实现身份，亦为正文登记键


def 文件夹页字形(属性=None):
    """向导胶囊字形尺寸下的彩色文件夹页，与芯片标题所绘一致。"""
    属性=属性 if 属性 is not None else {}#props
    return {#文件类型图标
        'type':'FileTypeIcon',
        'props':{
            'kind':'folder',#文件夹
            'size':属性['size'] if 'size' in 属性 else None,
            'className':属性['className'] if 'className' in 属性 else None,
        },
    }#图标结束


def 文件定义(翻译):
    """文件类型的注册表定义。翻译为命名空间绑定的可调用，每次取标签时新鲜读取。"""
    return {#右侧侧栏 tab 定义
        'id':文件标识,#实现身份
        'kind':文件种类,#种类
        'priority':'builtin',#内建优先级
        'title':lambda:翻译('type.label'),#类型标题
        'guide':[{#向导入口
            'order':10,#排序
            'title':lambda:翻译('guide.title'),#标题
            'description':lambda:翻译('guide.description'),#描述
            'icon':文件夹页字形,#文件夹字形
        }],#向导结束
    }#定义结束
