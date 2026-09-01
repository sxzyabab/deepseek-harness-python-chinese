"""标题文本归一化与 UTF-8 截断（对齐上游 normalize.ts）。"""
import re#正则清洗
_OSC=re.compile(r'(?:\x1b\]|\x9d)(?:(?!\x07|\x1b\\)[\s\S])*(?:\x07|\x1b\\|$)',re.U)#OSC 序列
_CSI=re.compile(r'(?:\x1b\[|\x9b)[0-?]*[ -/]*[@-~]',re.U)#CSI 序列
_ESC=re.compile(r'\x1b[@-_]',re.U)#两字节 ESC
_控制=re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]',re.U)#控制字符
_方向=re.compile(r'[\u200b\u200e\u200f\u202a-\u202e\u2060-\u2064\u2066-\u206f\ufeff]',re.U)#不可见方向控制

def _断言正整数(名称,值):#断言正整数
    """断言正整数配置。"""
    if not isinstance(值,int) or 值<=0:#非法
        raise Exception(名称+' must be a positive integer')#拒绝

def _清洗标题(输入):#清洗标题文本
    """去掉控制并压成一行。"""
    文本=输入#起点
    文本=_OSC.sub('',文本)#去 OSC
    文本=_CSI.sub('',文本)#去 CSI
    文本=_ESC.sub('',文本)#去 ESC
    文本=_控制.sub('',文本)#去控制
    文本=_方向.sub('',文本)#去方向控制
    文本=re.sub(r'\s+',' ',文本,flags=re.U).strip()#压空白
    return 文本#干净文本

def 截断标题utf8(输入,最大字节):#按 UTF-8 字节预算截断
    """按 UTF-8 字节预算截断，不劈开码点。"""
    _断言正整数('maxBytes',最大字节)#校验
    if len(输入.encode('utf-8'))<=最大字节:#未超
        return 输入#原样
    已用=0#已用字节
    输出=''#结果
    for 字符 in 输入:#逐码点
        字节=len(字符.encode('utf-8'))#本字符字节
        if 已用+字节>最大字节:#超预算
            break#停
        输出+=字符#追加
        已用+=字节#累计
    return 输出#截断结果

def 归一化会话标题(输入,最大字节):#归一化并接受标题
    """归一化一条标题并强制字节上限。"""
    return 截断标题utf8(_清洗标题(输入),最大字节).rstrip()#去尾空白

def 回退会话标题(输入,最大词数,最大字节):#确定性回退标题
    """从首条人类消息派生回退标题。"""
    _断言正整数('maxWords',最大词数)#校验
    词们=_清洗标题(输入).split(' ')#分词
    词们=[词 for 词 in 词们 if 词!=''][:最大词数]#取前 N 词
    return 截断标题utf8(' '.join(词们),最大字节).rstrip()#截断
