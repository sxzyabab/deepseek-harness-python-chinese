"""把 gen-cordis-api 产出的 TS 对象字面量数组解析成 Python 列表。

只覆盖 api-catalog 使用的子集：单引号字符串、标识符键、嵌套对象/数组、行注释。
"""

__all__=['解析数组字面量','提取导出常量数组']#公开面

class 字面量游标:#扫描器
    def __init__(自身,文本):#绑定源文本
        """保存源与当前位置。"""
        自身.文本=文本#源
        自身.位置=0#下标

    def 结束(自身):#是否读完
        """布尔。"""
        return 自身.位置>=len(自身.文本)#越界即结束

    def 跳过空白与注释(自身):#吃空白与 // 注释
        """前进到下一有效字符。"""
        while not 自身.结束():#还有字符
            字=自身.文本[自身.位置]#当前
            if 字 in ' \t\r\n':#空白
                自身.位置+=1#前进
                continue#继续
            if 字=='/' and 自身.位置+1<len(自身.文本) and 自身.文本[自身.位置+1]=='/':#行注释
                自身.位置+=2#跳过 //
                while not 自身.结束() and 自身.文本[自身.位置] not in '\r\n':#直到换行
                    自身.位置+=1#前进
                continue#继续
            break#有效字符

    def 窥视(自身):#看下一有效字符
        """返回字符或空串。"""
        自身.跳过空白与注释()#对齐
        if 自身.结束():#完
            return ''#空
        return 自身.文本[自身.位置]#字符

    def 吃掉(自身,期望):#断言并前进
        """匹配期望字符。"""
        自身.跳过空白与注释()#对齐
        if 自身.结束() or 自身.文本[自身.位置]!=期望:#不匹配
            raise Exception('expected '+repr(期望)+' at '+str(自身.位置))#失败
        自身.位置+=1#前进

    def 解析字符串(自身):#单引号字符串
        """解码为 Python str。"""
        自身.跳过空白与注释()#对齐
        if 自身.结束() or 自身.文本[自身.位置]!="'":#必须单引号
            raise Exception('expected string at '+str(自身.位置))#失败
        自身.位置+=1#跳过开引号
        块=[]#字符缓冲
        while not 自身.结束():#读到闭引号
            字=自身.文本[自身.位置]#当前
            自身.位置+=1#前进
            if 字=="'":#结束
                return ''.join(块)#拼成
            if 字=='\\':#转义
                if 自身.结束():#残缺
                    raise Exception('unterminated escape at '+str(自身.位置))#失败
                转义=自身.文本[自身.位置]#下一字符
                自身.位置+=1#前进
                if 转义=='n':#换行
                    块.append('\n')#收入
                elif 转义=='r':#回车
                    块.append('\r')#收入
                elif 转义=='t':#制表
                    块.append('\t')#收入
                elif 转义=='\\':#反斜杠
                    块.append('\\')#收入
                elif 转义=="'":#单引号
                    块.append("'")#收入
                elif 转义=='"':#双引号
                    块.append('"')#收入
                else:#其它原样
                    块.append(转义)#收入
                continue#继续
            块.append(字)#普通字符
        raise Exception('unterminated string at '+str(自身.位置))#未闭合

    def 解析标识符(自身):#键名
        """读出标识符。"""
        自身.跳过空白与注释()#对齐
        if 自身.结束():#完
            raise Exception('expected identifier at '+str(自身.位置))#失败
        字=自身.文本[自身.位置]#首字
        if not (字.isalpha() or 字 in '_$'):#非法起首
            raise Exception('expected identifier at '+str(自身.位置))#失败
        起=自身.位置#起点
        自身.位置+=1#前进
        while not 自身.结束():#后续
            字=自身.文本[自身.位置]#当前
            if 字.isalnum() or 字 in '_$':#合法
                自身.位置+=1#前进
                continue#继续
            break#结束
        return 自身.文本[起:自身.位置]#切片

    def 解析值(自身):#任意值
        """对象/数组/字符串。"""
        字=自身.窥视()#下一字符
        if 字=="'":#字符串
            return 自身.解析字符串()#解码
        if 字=='{':#对象
            return 自身.解析对象()#字典
        if 字=='[':#数组
            return 自身.解析数组()#列表
        raise Exception('unexpected value start '+repr(字)+' at '+str(自身.位置))#未知

    def 解析对象(自身):#花括号对象
        """返回 dict。"""
        自身.吃掉('{')#开
        结果={}#条目
        while True:#字段循环
            字=自身.窥视()#下一
            if 字=='}':#结束
                自身.吃掉('}')#闭
                return 结果#字典
            键=自身.解析标识符()#字段名
            自身.吃掉(':')#冒号
            结果[键]=自身.解析值()#赋值
            字=自身.窥视()#分隔
            if 字==',':#还有
                自身.吃掉(',')#吃逗号
                if 自身.窥视()=='}':#尾逗号
                    自身.吃掉('}')#闭
                    return 结果#字典
                continue#下一字段
            if 字=='}':#结束
                自身.吃掉('}')#闭
                return 结果#字典
            raise Exception('expected , or } at '+str(自身.位置))#失败

    def 解析数组(自身):#方括号数组
        """返回 list。"""
        自身.吃掉('[')#开
        结果=[]#元素
        while True:#元素循环
            字=自身.窥视()#下一
            if 字==']':#结束
                自身.吃掉(']')#闭
                return 结果#列表
            结果.append(自身.解析值())#收入
            字=自身.窥视()#分隔
            if 字==',':#还有
                自身.吃掉(',')#吃逗号
                if 自身.窥视()==']':#尾逗号
                    自身.吃掉(']')#闭
                    return 结果#列表
                continue#下一元素
            if 字==']':#结束
                自身.吃掉(']')#闭
                return 结果#列表
            raise Exception('expected , or ] at '+str(自身.位置))#失败

def 解析数组字面量(文本):#顶层数组
    """把 `[...]` 文本解析成 list。"""
    游标=字面量游标(文本)#扫描器
    结果=游标.解析数组()#数组
    游标.跳过空白与注释()#尾部
    if not 游标.结束():#还有垃圾
        raise Exception('trailing junk at '+str(游标.位置))#失败
    return 结果#列表

def 提取导出常量数组(源,常量名):#从整文件切出数组字面量
    """定位 `export const 名 ... = [` 到匹配的 `]`，返回含方括号的切片。"""
    标记='export const '+常量名#导出标记
    起=源.find(标记)#查找
    if 起<0:#没有
        raise Exception('missing export const '+常量名)#失败
    方括号=源.find('[',起)#数组起点
    if 方括号<0:#没有
        raise Exception('missing array for '+常量名)#失败
    深度=0#括号深度
    在字符串=False#是否在单引号串内
    转义=False#上一字符是反斜杠
    位置=方括号#扫描
    while 位置<len(源):#前进
        字=源[位置]#当前
        if 在字符串:#串内
            if 转义:#转义下一
                转义=False#清除
            elif 字=='\\':#开始转义
                转义=True#标记
            elif 字=="'":#闭串
                在字符串=False#出串
            位置+=1#前进
            continue#继续
        if 字=="'":#开串
            在字符串=True#进串
            位置+=1#前进
            continue#继续
        if 字=='/' and 位置+1<len(源) and 源[位置+1]=='/':#行注释
            位置+=2#跳过
            while 位置<len(源) and 源[位置] not in '\r\n':#到行尾
                位置+=1#前进
            continue#继续
        if 字=='/' and 位置+1<len(源) and 源[位置+1]=='*':#块注释
            位置+=2#跳过
            while 位置+1<len(源) and not (源[位置]=='*' and 源[位置+1]=='/'):#到结束
                位置+=1#前进
            位置+=2#跳过 */
            continue#继续
        if 字=='[':#开
            深度+=1#加深
        elif 字==']':#闭
            深度-=1#变浅
            if 深度==0:#顶层闭合
                return 源[方括号:位置+1]#含闭括号
        位置+=1#前进
    raise Exception('unclosed array for '+常量名)#未闭合
