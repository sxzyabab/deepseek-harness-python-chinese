"""触发检测纯核心：从光标向后扫描，按守卫档位找存活的触发字符。

对齐上游 `ui-input-trigger/src/core/detect.ts`。公开面仅中文名。零 React / DOM / cordis。
"""
import re#正则

__all__=['检测触发','词边界可']#仅中文公开名

词字符=re.compile(r'[\w]',re.UNICODE)#词字符：字母、数字、下划线（含 Unicode）
空白=re.compile(r'\s',re.UNICODE)#空白（含换行）

def 词边界可(草稿,下标,字符):#该位置的触发字符是否满足词边界
    """触发字符只在草稿开头、空白之后、或标点之后才打开。"""
    if 下标==0:#草稿开头一律打开
        return True#开
    前=草稿[下标-1]#触发字符前一个字符
    if 空白.search(前):#空白（含换行）之后打开
        return True#开
    if 词字符.search(前):#词字符之后不打开
        return False#关
    if 字符=='/':#斜杠有两处 URL 例外
        if 前=='/':#第二个 '/' 不打开
            return False#关
        if 前==':' and 下标>=2 and not 空白.search(草稿[下标-2]):#协议分隔符后的 '/' 不打开
            return False#关
    return True#其余标点之后打开

def 检测触发(草稿,光标,守卫):#检测光标处的触发令牌
    """光标处无活触发时返回 None；span.draftRev 占位 0，由外壳盖章。"""
    档=守卫.get('tier') if isinstance(守卫,dict) else getattr(守卫,'tier',None)#可用性档
    if 档=='frozen':#冻结档：无触发存活
        return None#无
    for 位置 in range(光标-1,-1,-1):#从光标左侧向草稿开头扫
        字=草稿[位置]#当前位置字符
        if 空白.search(字):#令牌不跨空白，遇空白即无命中
            return None#无
        if 字 not in ('/','@'):#非触发字符，继续向左
            continue#继续
        if 档=='claimed' and 字=='/':#'/' 在 claimed 档全抑，当普通字符
            continue#继续
        if not 词边界可(草稿,位置,字):#未过词边界，当普通字符继续扫
            continue#继续
        非空白=re.search(r'\S',草稿)#去空白后首个非空白
        前导=非空白 is not None and 非空白.start()==位置#去空白后是否以该令牌开头
        return {#命中
            'trigger':字,#触发字符
            'query':草稿[位置+1:光标],#触发到光标的切片
            'position':'leading' if 前导 else 'inline',#位置
            'span':{'start':位置,'end':光标,'draftRev':0},#跨度；draftRev 由外壳盖章
        }#结束 return
    return None#扫到头仍无活触发
