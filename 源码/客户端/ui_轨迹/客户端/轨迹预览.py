"""轨迹消费方共用的有界 Markdown→纯文本投影。

对齐上游 `ui-trajectory/src/client/trajectory-preview.ts`。公开面仅中文名。
运行时 primitives 未迁完时本地实现有界纯文本抽取。
"""
import re#空白折叠与简单标记剥离

__all__=['轨迹预览文本']#仅中文公开名

预览源字节上限=2048#截取源文本的 UTF-8 字节上限
预览输出字节上限=512#输出预览的 UTF-8 字节上限
围栏代码=re.compile(r'```.*?```',re.DOTALL)#围栏代码块
行内代码=re.compile(r'`([^`]*)`')#行内代码
图片标记=re.compile(r'!\[([^\]]*)\]\([^)]*\)')#图片 alt
链接标记=re.compile(r'\[([^\]]*)\]\([^)]*\)')#链接文案
强调标记=re.compile(r'[*_~#>]+')#强调/标题标记
空白折叠=re.compile(r'[ \t\n\r\f\v]+')#ASCII 空白

def 按字节截(文本,上限):#按 UTF-8 字节截断
    """切点落在字符边界。"""
    编码=文本.encode('utf-8')#字节
    if len(编码)<=上限:#未超
        return 文本#原样
    截=编码[:上限]#硬切
    while len(截)>0 and (截[-1]&0xC0)==0x80:#续字节
        截=截[:-1]#退一字节
    if len(截)>0 and (截[-1]&0x80)!=0:#不完整首字节
        截=截[:-1]#再退
    return 截.decode('utf-8')#解码

def 抽取Markdown纯文本(文本):#Markdown 抽纯文本的最小实现
    """去掉常见 Markdown 标记，保留可读正文。"""
    结果=围栏代码.sub(' ',文本,count=0)#去掉围栏代码块
    结果=行内代码.sub(r'\1',结果,count=0)#行内代码
    结果=图片标记.sub(r'\1',结果,count=0)#图片 alt
    结果=链接标记.sub(r'\1',结果,count=0)#链接文案
    结果=强调标记.sub(' ',结果,count=0)#常见强调/标题标记
    return 结果#纯文本近似

def 轨迹预览文本(文本):#有界单行预览
    """在不解析完整 Markdown 文档的前提下，生成有界单行预览。"""
    源=按字节截(文本,预览源字节上限)#只取源文本前缀
    紧凑=空白折叠.sub(' ',抽取Markdown纯文本(源),count=0).strip()#抽纯文本并压成单行
    预览=按字节截(紧凑,预览输出字节上限).rstrip()#再截输出上限并去尾空白
    if len(源.encode('utf-8'))<len(文本.encode('utf-8')) or len(预览.encode('utf-8'))<len(紧凑.encode('utf-8')):#源或压实文本被截断
        return 预览+'…'#截断预览加省略号
    return 预览#完整预览
