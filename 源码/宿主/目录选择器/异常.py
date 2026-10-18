'浏览原语的带码失败。消费方按 code 分支，不必匹配说明文字'
from typing import Literal as 字面量#封闭业务码

__all__=['目录选择器错误码','目录选择器错误']#仅中文公开名

目录选择器错误码=字面量['directory-unreadable','directory-exists','directory-create-failed']#关闭失败词


class 目录选择器错误(OSError):#浏览原语抛出
    '关闭业务码 directory-unreadable、directory-exists、directory-create-failed，并带绝对路径'
    def __init__(自身,业务码,绝对路径,说明):#业务码、绝对路径、给人看的说明
        '记下业务码、绝对路径和说明'
        super().__init__(说明)#说明进异常消息
        自身.code=业务码#关闭业务码
        自身.path=绝对路径#失败所关于的绝对路径
        自身.name='DirectoryPickerError'#错误名
