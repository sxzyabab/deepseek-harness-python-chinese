"""本包登记的第一阶段：`text` tab 类型是什么。

对齐上游 `ui-sidebar-documentpreview/src/client/definition.ts`。公开面仅中文名。
该类型以 `fallback` 档认领每个 `dsh-resource://file/session/<sessionId>/<path>` 地址。
"""
from urllib.parse import unquote,urlparse#段解码与 URI

__all__=['文本预览种类','文本预览标识','基名','文本定义']#仅中文公开名

文本预览种类='text'#本包拥有的 tab 种类（线路字面量）
文本预览标识='@deepseek-ai/dsh-client-ui-sidebar-documentpreview'#实现身份，亦为正文登记键


def _解析文件地址(地址):
    """读回 `dsh-resource://file/…`；非法则 None。语法归属 util/workspace-path，内嵌以免扩大移植面。"""
    try:
        网址=urlparse(地址)#解析
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
        return {'scope':'session','sessionId':unquote(其余[0]),'path':'/'.join(unquote(段) for 段 in 其余[1:])}#会话
    except Exception:#畸形
        return None#拒绝


def 基名(地址):
    """一个 `file:` 地址的标签标题：解码后的 basename。"""
    名=地址[地址.rfind('/')+1:]#末段
    if 名=='':#无段
        return 地址#整址
    try:
        return unquote(名)#解码
    except Exception:#畸形百分号
        return 名#原样


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
