__all__=['文件种类','文件标识','文件定义','文件夹页字形']

#常量
#线路字面量：tab 种类与正文登记键
文件种类='files'
文件标识='@deepseek-ai/dsh-client-ui-sidebar-files'

#工具
def 文件夹页字形(属性=None):
    """向导胶囊与芯片标题共用的文件夹页字形。"""
    属性=属性 if 属性 is not None else {}
    return {
        'type':'FileTypeIcon',
        'props':{
            'kind':'folder',
            'size':属性['size'] if 'size' in 属性 else None,
            'className':属性['className'] if 'className' in 属性 else None,
        },
    }


def 文件定义(翻译):
    """右侧侧栏的 files 类型。翻译每次取标签时重新读，不缓存文案。"""
    return {
        'id':文件标识,
        'kind':文件种类,
        'priority':'builtin',
        'title':lambda:翻译('type.label'),
        'guide':[{
            'order':10,
            'title':lambda:翻译('guide.title'),
            'description':lambda:翻译('guide.description'),
            'icon':文件夹页字形,
        }],
    }
