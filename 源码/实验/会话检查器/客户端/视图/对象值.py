'只看一层的运行时对象。不转 JSON，也不去调用取值器'

import datetime#日期标签
import json#字符串预览的引号
import re#正则标签

class 集合属性:
    '数组或类型化数组上、下标以外的自有属性'
    def __init__(自身,值,长度):
        '记下原集合和当时的长度，展开时再枚举'
        自身.值=值#原集合
        自身.长度=长度#下标范围

def 字段(值,键,下标):
    '一个自有字段。没有描述符时算空槽，只有取值器时不执行'
    if isinstance(值,dict):#字典没有空槽和取值器
        return {'key':str(键),'name':str(键),'value':值.get(键)}#直接的值
    if isinstance(值,(list,tuple)):#按下标
        文本=str(键)#下标文本
        if 文本.isdigit() and int(文本)<len(值):#有这个下标
            return {'key':文本,'name':文本,'value':值[int(文本)]}#值
        return {'key':文本,'name':文本,'value':None,'absent':True}#空槽
    名=str(键)#属性名
    字典=getattr(值,'__dict__',None)#实例字典，不触发特性
    if isinstance(字典,dict) and 名 in 字典:#实例自己的值
        return {'key':名,'name':名,'value':字典[名]}#不调用取值器
    return {'key':名,'name':名,'value':None,'accessor':True}#类上的取值器不执行

class 检查器对象值:
    '一层的类型或标量预览。子项的取值器留到它自己展开时'
    def __init__(自身,值):
        '记下原值，并生成不访问子项的标签'
        自身.值=值#原值
        自身.可展开=值 is not None and not isinstance(值,(str,int,float,bool,datetime.datetime,datetime.date,re.Pattern))#容器才能展开
        if isinstance(值,datetime.datetime):#日期
            try:#非法日期
                文本=值.isoformat()#ISO 文本
            except ValueError:#无法表示
                文本='Invalid'#无效
            自身.标签='Date('+文本+')'#日期标签
            自身.可展开=False#日期不展开
        elif isinstance(值,re.Pattern):#正则
            自身.标签=str(值)#正则文本
            自身.可展开=False#不展开
        elif isinstance(值,set):#集合
            自身.标签='Set('+str(len(值))+')'#大小
        elif isinstance(值,(list,tuple)):#数组
            自身.标签='Array('+str(len(值))+')'#长度
        elif isinstance(值,(bytes,bytearray)):#字节
            自身.标签='Uint8Array('+str(len(值))+')'#按类型化数组显示
        elif isinstance(值,集合属性):#下标以外的属性
            自身.标签='Object'#对象
        elif isinstance(值,dict):#普通对象
            自身.标签='Object'#对象
        elif 值 is not None and not isinstance(值,(str,int,float,bool)):#类实例
            自身.标签=type(值).__name__ or 'Object'#构造名
        elif isinstance(值,str):#字符串
            自身.标签=json.dumps(值,ensure_ascii=False)#带引号
        elif callable(值):#函数
            自身.标签='[Function '+getattr(值,'__name__','')+']'#函数名
            自身.可展开=False#函数不展开
        else:#其余标量
            自身.标签=str(值)#文本
            自身.可展开=False#不展开

    def 条目(自身):
        '只枚举一层。不执行取值器，也不进入子值'
        值=自身.值#原值
        if isinstance(值,set):#集合按序号
            下标=0#序号
            for 项 in 值:#逐项
                yield {'key':str(下标),'name':str(下标),'value':项}#值本身
                下标=下标+1#下一个
            return#集合没有别的字段
        if isinstance(值,(bytes,bytearray)):#字节视图
            yield {'key':'bytes','name':'bytes','value':值}#整段字节
            return#不再拆下标
        if isinstance(值,(list,tuple)):#数组先给出其他属性，再给下标
            yield {'key':'properties','name':'','properties':True,'value':集合属性(值,len(值))}#非下标属性
            下标=0#下标
            while 下标<len(值):#每个下标
                yield 字段(值,str(下标),下标)#这一格
                下标=下标+1#下一个
            return#数组结束
        if isinstance(值,集合属性):#非下标属性
            目标=值.值#原集合
            if isinstance(目标,(list,tuple)):#数组没有额外自有字段
                return#下标和 length 都不重复列出
            字典=getattr(目标,'__dict__',None)#实例字段
            if isinstance(字典,dict):#有实例字典
                下标=0#序号
                for 键,内容 in 字典.items():#自有字段
                    yield {'key':str(键),'name':str(键),'value':内容}#不执行取值器
                    下标=下标+1#下一个
            return#结束
        if isinstance(值,dict):#普通对象
            for 键,内容 in 值.items():#自有键
                yield {'key':str(键),'name':str(键),'value':内容}#值
            return#结束
        if 值 is not None and not isinstance(值,(str,int,float,bool)):#类实例
            字典=getattr(值,'__dict__',None)#只要实例字典
            if isinstance(字典,dict):#有自有字段
                for 键,内容 in 字典.items():#不走类上的取值器
                    yield {'key':str(键),'name':str(键),'value':内容}#原值
