"""解析本包 TYPE 紧凑行格式：`名称|声明`（声明内保留 \\n / \\' 等 TS 转义）。"""

__all__=['解析类型紧凑文本','解码声明转义']#公开面

def 解码声明转义(原文):#TS 单引号串体 → Python str
    """把 api-catalog 里 declaration 的转义序列还原成真实字符。"""
    结果=[]#缓冲
    索引=0#位置
    长度=len(原文)#总长
    while 索引<长度:#扫描
        字=原文[索引]#当前
        if 字!='\\' or 索引+1>=长度:#非转义
            结果.append(字)#原样
            索引+=1#前进
            continue#下一
        下一=原文[索引+1]#转义目标
        if 下一=='n':#换行
            结果.append('\n')#换行
        elif 下一=='r':#回车
            结果.append('\r')#回车
        elif 下一=='t':#制表
            结果.append('\t')#制表
        elif 下一=='\\':#反斜杠
            结果.append('\\')#反斜杠
        elif 下一=="'":#单引号
            结果.append("'")#单引号
        elif 下一=='"':#双引号
            结果.append('"')#双引号
        else:#未知转义原样保留下一字
            结果.append(下一)#保留
        索引+=2#跳过转义对
    return ''.join(结果)#拼回

def 解析类型紧凑文本(文本):#多行 name|declaration
    """跳过空行与 # 注释行；每行一条类型。"""
    条目们=[]#结果
    for 行 in 文本.splitlines():#逐行
        条=行.strip()#去空白
        if 条=='' or 条.startswith('#'):#空或注释
            continue#跳过
        竖=条.find('|')#分隔
        if 竖<=0:#畸形
            raise Exception('TYPE 紧凑行缺少名称：'+条[:80])#失败
        名=条[:竖]#类型名
        声明原文=条[竖+1:]#声明转义体
        条目们.append({'name':名,'declaration':解码声明转义(声明原文)})#收入
    return 条目们#列表
