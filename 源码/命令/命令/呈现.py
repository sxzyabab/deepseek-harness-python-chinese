"""shell 工具共用的渲染辅助。对齐上游 `shell/src/render.ts`。公开面仅中文名。

工具渲染器发出、展示层再解析回来的退出状态标记约定：
`[exit code: N]` / `[killed by signal: X]`。
"""
import re#正则
from typing import NotRequired,TypedDict#可选字段与结构类型

__all__=['解析退出状态字段','解析退出状态结果','解析退出状态']#仅中文公开名

搜索=re.search#正则搜索

解析退出状态字段=('body','exitCode','signal')#去掉标记后的正文，外加退出码或信号（载荷键字面量）

class 解析退出状态结果(TypedDict):#从已渲染结果恢复的退出状态
    body:str#去掉标记后的输出正文
    exitCode:NotRequired[int]#非零或干净退出时的退出码
    signal:NotRequired[str]#被信号杀死时的信号名

def 解析退出状态(文本):#从渲染文本恢复退出状态
    """把已渲染的 shell 工具结果字符串拆成输出正文与结构化退出状态。

    被杀死的标记得到 signal；否则非零标记得到 exitCode；两者都没有表示干净的退出 0。
    消费掉的标记从 body 去掉，因为终端展示把退出状态显示为自己的药丸。
    要求前导换行且位于字符串末尾，使普通输出不会误匹配。
    """
    信号匹配=搜索(r'\n\[killed by signal: ([^\]\n]+)\]\Z',文本)#末尾的被信号杀死标记
    if 信号匹配 is not None:#命中被信号杀死标记
        return {'body':文本[:信号匹配.start()],'signal':信号匹配.group(1)}#拆出信号
    退出匹配=搜索(r'\n\[exit code: ([0-9]+)\]\Z',文本)#末尾的退出码标记
    if 退出匹配 is not None:#命中退出码标记
        return {'body':文本[:退出匹配.start()],'exitCode':int(退出匹配.group(1))}#拆出退出码
    return {'body':文本,'exitCode':0}#无标记则当作干净退出 0
