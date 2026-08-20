"""外层输出账本的 JSON 字符串前缀计量。"""
import math#有限数判定

def 数据描述符(值):#空原型数据描述符
    """构造不能继承模型定义访问器字段的数据描述符。"""
    return {'value':值,'enumerable':False,'configurable':False,'writable':False}#仅数据值

def 定义可枚举数据属性(目标,键,值):#定义可枚举数据属性
    """定义普通可枚举数据槽。"""
    if isinstance(目标,dict):#映射
        目标[键]=值#写入
        return#结束
    setattr(目标,键,值)#对象属性

def 字节长度(文本):#UTF-8字节数
    """经内建计算UTF-8字节长度。"""
    return len(文本.encode('utf-8'))#按utf8计量

def 追加(目标,值):#安全追加
    """追加元素。"""
    目标.append(值)#追加

def 弹出末项(目标):#安全弹出末项
    """弹出末项。"""
    if len(目标)==0:#空
        return None#无末项
    return 目标.pop()#弹出

def 字符于(文本,下标):#按码点取字符
    """从字符串取出一个按码点对齐的字符。"""
    return 文本[下标]#Python str按码点索引

def 序列化字符字节(字符):#JSON转义后字节
    """一个完整Unicode码点在JSON引号内贡献的序列化字节。"""
    if len(字符.encode('utf-16-le'))==4 and len(字符)==1 and ord(字符)>0xffff:#代理对按UTF-8四字节
        return 4#四字节
    if 字符=='"' or 字符=='\\':#引号与反斜杠
        return 2#转义两字节
    码=ord(字符)#码点
    if 0xd800<=码<=0xdfff:#孤立代理
        return 6#\\uXXXX
    if 码<0x20:#控制字符
        return 2 if 码 in (0x08,0x09,0x0a,0x0c,0x0d) else 6#短转义或\\uXXXX
    return 字节长度(字符)#其余按UTF-8原文

def json字符串字节上限(文本,最大字节):#字符串JSON字节上限计量
    """计量一条JSON字符串，不物化完整转义形式；越过上限则None。"""
    if 最大字节<2:#连引号都装不下
        return None#越界
    字节=2#先计入两侧引号
    for 字符 in 文本:#按码点前进
        字节+=序列化字符字节(字符)#累加转义后字节
        if 字节>最大字节:#已越上限
            return None#越界
    return 字节#精确字节

def json值字节上限(值,最大字节):#值JSON字节上限计量
    """计量一个无损JSON值，不分配其序列化形式；越过上限则None。"""
    字节=0#已计入字节
    def 加(成本):#尝试加上成本
        nonlocal 字节#闭合字节
        字节+=成本#累加
        return 字节<=最大字节#是否仍在上限内
    任务们=[{'kind':'value','value':值}]#从根值开始
    while len(任务们)>0:#栈式迭代
        任务=弹出末项(任务们)#弹出
        if 任务['kind']=='value':#处理一个值
            当前=任务['value']#当前值
            if 当前 is None:#null固定4字节
                if not 加(4):#装不下
                    return None#越界
            elif isinstance(当前,str):#字符串
                串字节=json字符串字节上限(当前,最大字节-字节)#剩余预算内计量
                if 串字节 is None:#越界
                    return None#越界
                字节+=串字节#计入
            elif isinstance(当前,bool):#布尔须先于int（bool是int子类）
                if not 加(4 if 当前 else 5):#true=4/false=5
                    return None#越界
            elif isinstance(当前,(int,float)):#数字
                if isinstance(当前,float) and (math.isnan(当前) or math.isinf(当前)):#非法数
                    return None#越界语义上不应出现
                if not 加(字节长度(str(当前))):#十进制文本
                    return None#越界
            elif isinstance(当前,list):#数组
                if not 加(2):#先计入[]
                    return None#越界
                if len(当前)>0:#有元素
                    追加(任务们,{'kind':'array','value':当前,'index':0})#入栈数组帧
            elif isinstance(当前,dict):#对象
                if not 加(2):#先计入{}
                    return None#越界
                键们=list(当前.keys())#可枚举键
                if len(键们)>0:#有键
                    追加(任务们,{'kind':'object','value':当前,'keys':键们,'index':0})#入栈对象帧
            else:#未知
                return None#非法
            continue#下一任务
        if 任务['index']>0 and not 加(1):#相邻项逗号
            return None#越界
        if 任务['kind']=='array':#数组元素
            项=任务['value'][任务['index']]#当前元素
            if 任务['index']+1<len(任务['value']):#还有后续
                追加(任务们,{**任务,'index':任务['index']+1})#推进
            追加(任务们,{'kind':'value','value':项})#计量本元素
            continue#下一任务
        键=任务['keys'][任务['index']]#对象当前键
        键字节=json字符串字节上限(键,最大字节-字节)#计量键
        if 键字节 is None:#键越界
            return None#越界
        if not 加(键字节+1):#键加冒号
            return None#越界
        项=任务['value'][键]#属性值
        if 任务['index']+1<len(任务['keys']):#还有后续键
            追加(任务们,{**任务,'index':任务['index']+1})#推进
        追加(任务们,{'kind':'value','value':项})#计量本属性值
    return 字节#精确字节

def 截断json字符串字节(文本,最大字节):#按JSON字节截断字符串
    """返回最长的按码点对齐前缀，使其JSON字符串编码（含两侧引号）装进最大字节。"""
    if 最大字节<2:#连引号都装不下
        return ''#空串
    字节=2#先计入两侧引号
    终点=0#可保留终点
    for 下标,字符 in enumerate(文本):#按码点前进
        成本=序列化字符字节(字符)#该字符转义成本
        if 字节+成本>最大字节:#再加就越上限
            break#停
        字节+=成本#计入
        终点=下标+1#推进终点
    return 文本 if 终点==len(文本) else 文本[0:终点]#全文或切片
