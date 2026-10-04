'设置控制器远程错误与中止查询'
from .异常 import 远程错误#本包异常

__all__=['远程错误','远程错误消息','已中止','若已中止则抛出']#仅中文公开名

def 远程错误消息(错误):
    '把错误收成字符串'
    return str(错误)#消息

def 已中止(信号):
    '信号是否已中止。无信号视为未中止'
    if 信号 is None:#无
        return False#未中止
    return 信号.is_set()#Event 置位

def 若已中止则抛出(信号):
    '已中止则抛出取消'
    if 已中止(信号):#已中止
        raise 远程错误('gateway/cancelled','aborted',{})#取消
