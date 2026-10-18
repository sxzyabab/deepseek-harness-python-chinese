'把采集或识别失败换成中文表里的句子'
from ..异常 import 录制错误#采集失败种类

__all__=['失败文本']#多处使用，留成函数


def 失败文本(失败):
    '录制错误用对应中文句，其余套进失败模板'
    if isinstance(失败,录制错误):#种类对应中文表
        if 失败.kind=='unavailable':#浏览器不能录
            return '当前浏览器不支持录音，请使用支持麦克风的浏览器。'
        if 失败.kind=='permission':#没给权限
            return '麦克风权限未开启，请在浏览器和系统设置中允许访问。'
        if 失败.kind=='empty':#没有声音
            return '未识别到语音'
        if 失败.kind=='cancelled':#用户取消
            return '已取消语音输入。'
        if 失败.kind=='interrupted':#采集中断
            return '录音中断，请重试。'
        if 失败.kind=='deviceMissing':#设备不在
            return '麦克风不可用，请选择其他输入设备'
        return str(失败.kind)#未知种类保留 kind
    if isinstance(失败,BaseException):#普通错误取消息
        消息=str(失败)#Python 异常的消息
    else:#不是异常
        消息=str(失败)#原样转成文字
    return '语音识别失败：{message}'.replace('{message}',消息)#中文表 failed
