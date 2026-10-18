import re
from ...ui_基础界面组件.markdown.纯文本 import 抽取Markdown纯文本#去掉标记

__all__=['轨迹预览文本']

预览源字符上限=2048#先截源再抽纯文本
预览输出字符上限=512#纯文本再截一刀
空白折叠=re.compile(r'\s+')#连续空白收成一格

def 轨迹预览文本(文本):
    '在不解析完整 Markdown 文档的前提下，生成有界单行预览'
    源=文本[:预览源字符上限]#有界源
    紧凑=空白折叠.sub(' ',抽取Markdown纯文本(源)).strip()#单行纯文本
    预览=紧凑[:预览输出字符上限].rstrip()#输出上限
    if len(源)<len(文本) or len(预览)<len(紧凑):
        return 预览+'…'#被截断
    return 预览#完整
