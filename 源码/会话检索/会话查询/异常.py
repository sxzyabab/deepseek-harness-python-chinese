'带类型的会话检索失败'
from ...模型后端.llm.异常 import harness错误#Harness错误基类

__all__=['会话查询错误']#仅中文公开名

def 去掉绝对路径(文本):
    '失败说明里去掉盘符路径、根路径和家目录路径'
    留下=[]#留下的词
    for 词 in str(文本).split():#逐词
        统一=词.strip('\'"').replace('\\','/')#统一分隔
        if 统一.startswith('/') or 统一.startswith('~/'):#根或家目录
            continue#丢掉
        if len(统一)>2 and 统一[0].isalpha() and 统一[1]==':' and 统一[2]=='/':#盘符
            continue#丢掉
        留下.append(词)#保留
    return ' '.join(留下).strip()#拼回

class 会话查询错误(harness错误):#会话检索错误
    '带类型的会话检索失败，其 code 是封闭分类中的一员'
    def __init__(自身,消息,码,选项=None):#构造检索错误
        '说明去掉绝对路径'
        干净=去掉绝对路径(消息)#去路径
        if 干净=='':#掏空
            干净=str(码)#用分类码
        harness错误.__init__(自身,干净,码,选项)#交给Harness错误基类
