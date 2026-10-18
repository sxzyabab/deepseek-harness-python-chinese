'窗口级键盘序列时序。宿主注入前校验，浏览器服务在读到页面全局时再校验一次'
from .异常 import 抛出非法快捷键配置#非法时序

__all__=['配置']

def 配置(原始=None):
    '校验 stopSequenceMs。缺键时用 500。只接受 1 到 2147483646 的整数，其余键不保留'
    if not isinstance(原始,dict):#不是对象
        抛出非法快捷键配置()#拒绝
    if 'stopSequenceMs' not in 原始:#缺省
        毫秒=500#连续 Escape 的默认间隔
    else:#显式
        毫秒=原始['stopSequenceMs']#原值
        if type(毫秒) is not int or 毫秒<1 or 毫秒>2147483646:#不是范围内的整数
            抛出非法快捷键配置()#拒绝
    return {'stopSequenceMs':毫秒}#已校验配置
