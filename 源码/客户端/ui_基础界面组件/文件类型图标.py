from .代码文件类型 import 分类代码文件类型,是否代码文件类型#代码分类

__all__=[#仅中文公开名
    '文件扩展名',
    '分类文件类型',
    '文件类型图标',
    '传统文件类型表',
]#公开面结束

传统文件类型表=('code','excel','folder','html','image','markdown','other','pdf','ppt','video','word')#传统类别

_扩展名类型={#扩展名 → 分类（代码扩展由代码分类器先接管）
    'scss':'code','sass':'code','less':'code','vue':'code','svelte':'code','astro':'code',
    'bat':'code','cmd':'code','csv':'code','tsv':'code',
    'html':'html','htm':'html',
    'png':'image','jpg':'image','jpeg':'image','gif':'image','svg':'image','webp':'image',
    'avif':'image','bmp':'image','ico':'image','tif':'image','tiff':'image','heic':'image','heif':'image',
    'md':'markdown','mdx':'markdown','markdown':'markdown',
    'pdf':'pdf','ppt':'ppt','pptx':'ppt','key':'ppt',
    'mp4':'video','mov':'video','m4v':'video','webm':'video','mkv':'video','avi':'video','mpg':'video','mpeg':'video',
    'doc':'word','docx':'word','rtf':'word','odt':'word','pages':'word',
    'xls':'excel','xlsx':'excel','xlsm':'excel','numbers':'excel',
}#扩展结束

_整名类型={#整名 → 分类
    'changelog':'markdown','contributing':'markdown','readme':'markdown',
}#整名结束

def _路径末段(路径):#取末段
    """正斜杠或反斜杠分隔的末段。"""
    return 路径[max(路径.rfind('/'),路径.rfind('\\'))+1:]#末段

def 文件扩展名(路径):#取后缀
    """对齐 fileExtension：末段最后一点之后；无或尾点则空串。"""
    名=_路径末段(路径)#末段
    点=名.rfind('.')#末点
    return '' if 点<0 else 名[点+1:]#后缀

def 分类文件类型(路径,上下文=None):#分类呈现类别
    """对齐 classifyFileType：代码规则优先，未知回落 other。不含 folder。"""
    名=_路径末段(路径).lower()#小写末段
    扩展=文件扩展名(名).lower()#小写扩展
    代码=分类代码文件类型(名,扩展,上下文)#代码分类
    if 代码 is not None:#命中代码
        return 代码#代码类型
    if 名 in _整名类型:#整名
        return _整名类型[名]#整名类型
    if 扩展 in _扩展名类型:#扩展
        return _扩展名类型[扩展]#扩展类型
    return 'other'#回落

class 文件类型图标:#装饰文件类型字形
    """按 path 或 kind 解析类别；宿主按 kind 画 SVG。"""
    def __init__(自身,属性=None):#构造
        """记下 props。"""
        自身.属性=属性 if 属性 is not None else {}#合成

    def 更新(自身,属性):#刷新
        """记下最新。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 视图(自身):#读视图模型
        """解析类别与尺寸。"""
        属性=自身.属性#props
        尺寸=属性['size'] if 'size' in 属性 and 属性['size'] is not None else 28#默认 28
        类名=属性['className'] if 'className' in 属性 else None#类
        if 'kind' in 属性 and 属性['kind'] is not None:#已解析
            类型=属性['kind']#种类
        else:#按路径
            路径=属性['path'] if 'path' in 属性 else ''#路径
            上下文=属性['context'] if 'context' in 属性 else None#上下文
            类型=分类文件类型(路径,上下文)#分类
        return {#视图
            'type':'file-type-icon',#类型
            'kind':类型,#类别
            'isCode':是否代码文件类型(类型),#是否全彩代码集
            'size':尺寸,#尺寸
            'className':类名,#类
            'cssModule':'FileTypeIcon.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.视图()#渲
