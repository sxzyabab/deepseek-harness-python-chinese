from urllib.parse import unquote as 百分号解码,urlparse as 解析URL

__all__=['文本预览种类','文本预览标识','基名','文本定义']#仅中文公开名

文本预览种类='text'#本包拥有的 tab 种类（线路字面量）
文本预览标识='@deepseek-ai/dsh-client-ui-sidebar-documentpreview'#实现身份，亦为正文登记键


def _解析文件地址(地址):
    """读回 `dsh-resource://file/…`；非法则 None。语法归属 util/workspace-path，内嵌以免扩大移植面。"""
    try:
        网址=解析URL(地址)
        if 网址.scheme!='dsh-resource' or 网址.netloc!='file':#非本方案
            return None#拒绝
        段列表=网址.path.split('/')#['', scope, ...]
        if len(段列表)<2:#过短
            return None#拒绝
        if 段列表[1]!='session':#非会话
            return None#拒绝
        其余=段列表[2:]#rest
        if len(其余)==0 or 其余[0]=='' or len(其余)<2:#缺 id 或路径
            return None#拒绝
        return {'scope':'session','sessionId':百分号解码(其余[0]),'path':'/'.join(百分号解码(段) for 段 in 其余[1:])}
    except (ValueError,UnicodeError):
        return None


def 基名(地址):
    """一个 `file:` 地址的标签标题：解码后的 basename。"""
    名=地址[地址.rfind('/')+1:]#末段
    if 名=='':#无段
        return 地址#整址
    try:
        return 百分号解码(名)
    except (ValueError,UnicodeError):
        return 名


def 文本定义():
    """文本类型的注册表定义。"""
    return {#右侧侧栏 tab 定义
        'id':文本预览标识,#实现身份
        'kind':文本预览种类,#种类
        'patterns':['dsh-resource://file/**'],#地址模式
        'priority':'fallback',#兜底档
        'canOpen':lambda 地址:(_解析文件地址(地址) or {}).get('scope')=='session',#仅会话
        'title':基名,#芯片标题
    }#定义结束
