"""已发布 v0/v1 校验共用的记录与精确键辅助。"""
import json#意外键诊断
from ..会话格式 import 会话格式错误,是否会话格式json对象#导入格式错误与对象判定

def 已发布v0记录(值,标签):#已发布v0记录
    """要求一个普通 JSON 对象。"""
    if not 是否会话格式json对象(值):#非对象
        raise 会话格式错误(f'{标签} must be a JSON object')#非对象
    return 值#断言返回

def 断言已发布v0键(记录,必填,可选=None,标签=''):#断言已发布v0键
    """要求每个命名成员存在，且无可选列表外的成员。"""
    if 可选 is None:#默认无可选
        可选=[]#空可选
    允许=set([*必填,*可选])#允许集
    意外=None#意外键
    for 键 in 记录.keys():#遍历自有键
        if 键 not in 允许:#意外
            意外=键#记下
            break#找到
    if 意外 is not None:#有意外
        raise 会话格式错误(f'{标签} has unexpected member {json.dumps(意外,ensure_ascii=False)}')#意外
    缺失=None#缺失键
    for 键 in 必填:#遍历必填
        if 键 not in 记录:#缺失
            缺失=键#记下
            break#找到
    if 缺失 is not None:#有缺失
        raise 会话格式错误(f'{标签} lacks required member {json.dumps(缺失,ensure_ascii=False)}')#缺失
