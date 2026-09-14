import json,re#JSON片段与正则

克劳德字面=re.compile(r'^[A-Za-z0-9_|]+\Z')#Claude字面模式正则；行尾用\\Z对齐 JS $

def 是否全匹配(匹配器):
    """缺席/空/`'*'`模式——全匹配哨兵。"""
    return 匹配器 is None or 匹配器=='' or 匹配器=='*'#缺席、空或星号都算全匹配

def 编译正则(模式):
    """编译未锚定匹配正则；非法模式返回 None。加 re.ASCII 对齐 JS \\d\\w\\s。"""
    try:
        return re.compile(模式,re.ASCII)#按模式构造正则
    except re.error:
        #正则构造是 try 里唯一操作，因此只预期畸形模式语法失败
        return None#非法模式不当正则

def 匹配诊断(匹配器,模式):
    """桥接层接受配置组之前校验一条匹配器。有效则 None，否则返回稳定诊断。"""
    if 是否全匹配(匹配器):#全匹配哨兵有效
        return None#无诊断
    图案=匹配器#越过哨兵后必为非空字符串
    if 模式=='claude-code' and 克劳德字面.match(图案) is not None:#Claude字面模式有效
        return None#无诊断
    if 编译正则(图案) is None:#正则编译失败则给出诊断
        return '非法 '+模式+' 正则匹配器 '+json.dumps(图案,ensure_ascii=False,separators=(',',':'),allow_nan=False)#稳定诊断文案
    return None#正则有效则无诊断

def 匹配命中(匹配器,查询,模式):
    """在给定方言下匹配器是否选中查询。Claude字面模式对竖线分隔的备选项做精确匹配；其余模式都是未锚定正则。非法正则返回假而不抛。"""
    if 是否全匹配(匹配器):#全匹配哨兵一律选中
        return True#选中
    图案=匹配器#断言为具体模式
    if 模式=='claude-code' and 克劳德字面.match(图案) is not None:#Claude字面模式走精确备选
        return 查询 in 图案.split('|')#竖线切开后看是否含查询
    正则=编译正则(图案)#编译正则
    if 正则 is None:#非法正则
        return False#不匹配
    return 正则.search(查询) is not None#未锚定正则测试；未匹配则为假
