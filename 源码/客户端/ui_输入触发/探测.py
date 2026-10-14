import re#正则
from ...上下文.文件引用.词法 import 光标处活动令牌#@ 含未闭合引号，可跨空白

__all__=['检测触发','词边界可']#仅中文公开名

词字符=re.compile(r'[\w]',re.UNICODE)#带 /u：UNICODE 下 \w 即字母+数字+_，与 JS \d 要加 re.ASCII 方向相反
空白=re.compile(r'\s',re.UNICODE)#带 /u：按 Unicode 空白而不是 ASCII
非空白=re.compile(r'\S',re.ASCII)#无 u 旗，仅匹配 ASCII

def 词边界可(草稿,下标,字符):#该位置的触发字符是否满足词边界
    '触发字符只在草稿开头、空白之后、或标点之后才打开'
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

def _命中(草稿,位置,光标,字符,查询,引号):
    '只编排 / 与 @。候选不在这里生成。'
    非空白命中=非空白.search(草稿)#去空白后首个非空白
    前导=非空白命中 is not None and 非空白命中.start()==位置#是否位于草稿前导
    return {#命中
        'trigger':字符,#触发字符
        'query':查询,#触发到光标的切片
        'quoted':引号 is True,#引号路径
        'position':'leading' if 前导 else 'inline',#位置
        'span':{'start':位置,'end':光标,'draftRev':0},#跨度；draftRev 由外壳盖章
    }

def 检测触发(草稿,光标,守卫):#检测光标处的触发令牌
    '光标处无活触发时返回 None。只认 / 与 @；span.draftRev 由外壳盖章'
    档=守卫['tier'] if isinstance(守卫,dict) and 'tier' in 守卫 else None#可用性档
    if 档=='frozen':#冻结档：无触发存活
        return None#无
    艾特=光标处活动令牌(草稿,光标)#先认 @，引号路径可以跨过空白
    if 艾特 is not None:#活着的 @
        前缀=艾特['prefix'] if 'prefix' in 艾特 else ''#含 @ 的前缀
        起点=光标-len(前缀)#触发字符下标
        查询=艾特['query'] if 'query' in 艾特 else ''#@ 后的查询
        引号=艾特['quoted'] is True if 'quoted' in 艾特 else False#是否引号
        return _命中(草稿,起点,光标,'@',查询,引号)#@ 命中
    for 位置 in range(光标-1,-1,-1):#斜杠不跨空白，从光标向左扫
        字=草稿[位置]#当前位置字符
        if 空白.search(字):#令牌不跨空白
            return None#无
        if 字!='/':#只编排斜杠；@ 已在上面处理
            continue#继续
        if 档=='claimed':#claimed 档斜杠全抑
            continue#当普通字符
        if not 词边界可(草稿,位置,'/'):#URL 里的斜杠不当触发
            continue#继续
        return _命中(草稿,位置,光标,'/',草稿[位置+1:光标],False)#斜杠命中
    return None#扫到头仍无活触发
