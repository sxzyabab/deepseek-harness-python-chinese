"""把 gen-cordis-api 风格的 TypeScript 对象字面量数组解析成 Python 列表。

对齐上游 `api-catalog.ts` 中 SERVICE_API / EVENT_API / TYPE_API 的数据形态；
仅解析真实原文条目，不做占位裁剪。
"""
import ast#字面量求值

__all__=['解析目录数组','抽出导出数组']#公开面

def 去掉注释(文本):#删 TS 注释，保留字符串内斜杠
    """按字符扫描去掉 // 与 /* */，字符串内原样保留。"""
    结果=[]#输出缓冲
    索引=0#扫描位置
    长度=len(文本)#总长
    while 索引<长度:#未结束
        字符=文本[索引]#当前
        if 字符 in ('"',"'"):#进入字符串
            引号=字符#配对引号
            结果.append(字符)#写入开引号
            索引+=1#前进
            while 索引<长度:#扫字符串体
                当前=文本[索引]#体字符
                结果.append(当前)#写入
                if 当前=='\\' and 索引+1<长度:#转义
                    结果.append(文本[索引+1])#写入下一字
                    索引+=2#跳过转义对
                    continue#继续体
                if 当前==引号:#收束
                    索引+=1#越过闭引号
                    break#离开字符串
                索引+=1#普通前进
            continue#下一轮
        if 字符=='/' and 索引+1<长度:#可能注释
            下一=文本[索引+1]#下一字
            if 下一=='/':#行注释
                索引+=2#跳过 //
                while 索引<长度 and 文本[索引]!='\n':#直到行尾
                    索引+=1#跳过
                continue#下一轮
            if 下一=='*':#块注释
                索引+=2#跳过 /*
                while 索引+1<长度 and not (文本[索引]=='*' and 文本[索引+1]=='/'):#直到 */
                    索引+=1#跳过
                索引=min(索引+2,长度)#越过 */
                continue#下一轮
        结果.append(字符)#普通字符
        索引+=1#前进
    return ''.join(结果)#拼回

def 给裸键加引号(文本):#TS 键 → Python 键（跳过字符串）
    """在已去注释文本上给对象裸键加单引号。"""
    结果=[]#输出
    索引=0#位置
    长度=len(文本)#总长
    while 索引<长度:#扫描
        字符=文本[索引]#当前
        if 字符 in ('"',"'"):#字符串原样拷贝
            引号=字符#配对
            结果.append(字符)#开引号
            索引+=1#前进
            while 索引<长度:#体
                当前=文本[索引]#体字符
                结果.append(当前)#写
                if 当前=='\\' and 索引+1<长度:#转义
                    结果.append(文本[索引+1])#下一字
                    索引+=2#跳过
                    continue#继续
                if 当前==引号:#结束
                    索引+=1#越过
                    break#出字符串
                索引+=1#前进
            continue#下一轮
        if (字符.isalpha() or 字符=='_') and (索引==0 or 文本[索引-1] in '{[,\n\t\r '):#可能裸键
            起点=索引#键起点
            索引+=1#前进
            while 索引<长度 and (文本[索引].isalnum() or 文本[索引]=='_'):#吃完标识符
                索引+=1#前进
            键=文本[起点:索引]#候选键
            空白起点=索引#空白起点
            while 索引<长度 and 文本[索引] in ' \t\r\n':#空白
                索引+=1#跳过
            if 索引<长度 and 文本[索引]==':' and not (索引+1<长度 and 文本[索引+1]==':'):#确为键
                结果.append(repr(键))#加引号
                结果.append(文本[空白起点:索引])#保留空白
                结果.append(':')#冒号
                索引+=1#越过冒号
                continue#下一轮
            结果.append(文本[起点:空白起点])#不是键，原样写回标识符
            索引=空白起点#回到空白处继续
            continue#下一轮
        结果.append(字符)#普通字符
        索引+=1#前进
    return ''.join(结果)#拼回

def 替换字面量词(文本):#null/true/false → Python（跳过字符串）
    """只在字符串外替换 TS 字面量词。"""
    映射={'null':'None','true':'True','false':'False'}#对照
    结果=[]#输出
    索引=0#位置
    长度=len(文本)#总长
    while 索引<长度:#扫描
        字符=文本[索引]#当前
        if 字符 in ('"',"'"):#字符串原样
            引号=字符#配对
            结果.append(字符)#开
            索引+=1#前进
            while 索引<长度:#体
                当前=文本[索引]#体字符
                结果.append(当前)#写
                if 当前=='\\' and 索引+1<长度:#转义
                    结果.append(文本[索引+1])#下一
                    索引+=2#跳过
                    continue#继续
                if 当前==引号:#结束
                    索引+=1#越过
                    break#出
                索引+=1#前进
            continue#下一轮
        命中=None#候选词
        for 词,替代 in 映射.items():#试每个
            if 文本.startswith(词,索引):#前缀命中
                前界=索引==0 or not (文本[索引-1].isalnum() or 文本[索引-1]=='_')#左边界
                右=索引+len(词)#右沿
                后界=右>=长度 or not (文本[右].isalnum() or 文本[右]=='_')#右边界
                if 前界 and 后界:#完整词
                    命中=替代#记下
                    索引=右#跳过词
                    break#用这个
        if 命中 is not None:#替换
            结果.append(命中)#写入 Python 词
            continue#下一轮
        结果.append(字符)#普通
        索引+=1#前进
    return ''.join(结果)#拼回

def 匹配方括号数组(文本,开括号位置):#从 [ 找到配对 ]
    """字符串感知的方括号匹配，返回闭括号下标。"""
    if 开括号位置>=len(文本) or 文本[开括号位置]!='[':#必须是 [
        raise Exception('expected "[" at catalog array start')#失败
    深度=0#嵌套深度
    索引=开括号位置#扫描
    长度=len(文本)#总长
    while 索引<长度:#扫描
        字符=文本[索引]#当前
        if 字符 in ('"',"'"):#字符串
            引号=字符#配对
            索引+=1#进入体
            while 索引<长度:#体
                当前=文本[索引]#体字符
                if 当前=='\\' and 索引+1<长度:#转义
                    索引+=2#跳过
                    continue#继续
                if 当前==引号:#结束
                    索引+=1#越过
                    break#出
                索引+=1#前进
            continue#下一轮
        if 字符=='[':#更深
            深度+=1#加
        elif 字符==']':#更浅
            深度-=1#减
            if 深度==0:#配对完成
                return 索引#闭括号位置
        索引+=1#前进
    raise Exception('unclosed catalog array literal')#未闭合

def 解析目录数组(原文片段):#解析一个 [...] 数组
    """把 SERVICE_API / EVENT_API / TYPE_API 的数组字面量解析为 list。"""
    去注释=去掉注释(原文片段)#先去注释
    起=去注释.find('[')#数组起点
    if 起<0:#没有
        raise Exception('catalog array literal not found')#失败
    止=匹配方括号数组(去注释,起)#配对终点
    片段=给裸键加引号(去注释[起:止+1])#键加引号
    片段=替换字面量词(片段)#null/true/false
    try:#字面量求值
        值=ast.literal_eval(片段)#安全求值
    except Exception as 错:#解析失败
        raise Exception('catalog array parse failed: '+type(错).__name__+': '+str(错))#上抛
    if not isinstance(值,list):#必须是列表
        raise Exception('catalog root must be a list')#失败
    return 值#真实条目列表

def 抽出导出数组(全文,常量名):#从整份 api-catalog 抽出一个 export const
    """按常量名抽出 `export const NAME = [...]` 并解析。"""
    标记='export const '+常量名#定位标记
    起=全文.find(标记)#起点
    if 起<0:#缺失
        raise Exception('export const '+常量名+' not found')#失败
    等号=全文.find('=',起+len(标记))#等号
    if 等号<0:#畸形
        raise Exception('export const '+常量名+' has no "="')#失败
    方括号=全文.find('[',等号)#数组起点
    if 方括号<0:#畸形
        raise Exception('export const '+常量名+' has no array')#失败
    闭=匹配方括号数组(全文,方括号)#闭括号
    return 解析目录数组(全文[方括号:闭+1])#解析片段
