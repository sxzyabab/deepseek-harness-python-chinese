"""对捕获响应所载 Server-Sent Events 的增量 UTF-8 解析器。

对齐上游 `shared/network/event-source.ts`。公开面仅中文名。
"""
from .观察 import 检查器事件源消息#SSE消息

__all__=['检查器事件源解析器']#仅中文公开名

class 检查器事件源解析器:#SSE增量解析器
    """把响应字节解析为对消费者中立的 Server-Sent Event 消息。"""
    def __init__(自身):#构造
        """初始化行与字段缓冲。"""
        自身.行=''#当前行缓冲
        自身.事件名=''#事件名缓冲
        自身.事件标识=''#事件标识缓冲
        自身.数据=''#数据缓冲
        自身.回车后=False#上一字符是否为CR

    def 推入(自身,字节们):#推入字节分片
        """消费一块响应体分片。"""
        if isinstance(字节们,(bytes,bytearray)):#字节
            文本=bytes(字节们).decode('utf-8',errors='surrogatepass')#流式近似
        else:#已是文本
            文本=字节们#原样
        return 自身.消费(文本)#消费

    def 消费(自身,分片):#消费已解码文本
        """消费已解码文本。"""
        消息们=[]#本轮消息
        起点=0#当前段起点
        for 索引 in range(len(分片)):#逐字符扫换行
            if 自身.回车后 and 分片[索引]=='\n':#CRLF的LF部分
                自身.回车后=False#清CR标记
                起点=索引+1#跳过LF
                continue#下一字符
            自身.回车后=False#非LF则清标记
            if 分片[索引] not in ('\r','\n'):#非行终止
                continue#继续
            自身.行+=分片[起点:索引]#拼完整行
            消息=自身.解析行()#解析该行
            if 消息 is not None:#完整事件
                消息们.append(消息)#入列
            自身.行=''#清空行
            起点=索引+1#下一段起点
            自身.回车后=分片[索引]=='\r'#记CR以便吃掉随后LF
        自身.行+=分片[起点:]#残余并入行缓冲
        return 消息们#本轮消息

    def 解析行(自身):#解析一行字段或派发事件
        """解析一行字段或派发事件。"""
        if len(自身.行)==0:#空行：事件边界
            数据=自身.数据#取出数据
            自身.数据=''#清空数据
            事件名=自身.事件名#取出事件名
            自身.事件名=''#清空事件名
            if len(数据)==0:#无数据
                return None#无事件
            return 检查器事件源消息(事件名 or 'message',自身.事件标识,数据[:-1])#去掉末尾换行
        if 自身.行.startswith(':'):#注释行
            return None#忽略
        冒号=自身.行.find(':')#字段分隔
        字段=自身.行 if 冒号==-1 else 自身.行[:冒号]#字段名
        值='' if 冒号==-1 else 自身.行[冒号+1:]#字段值
        if 值.startswith(' '):#前导空格
            值=值[1:]#去掉一个
        if 字段=='event':#事件名
            自身.事件名=值#记事件名
            return None#未完成
        if 字段=='data':#数据
            自身.数据+=值+'\n'#追加数据行
            return None#未完成
        if 字段=='id':#标识
            if '\0' not in 值:#无NUL
                自身.事件标识=值#记id
            return None#未完成
        return None#忽略未知字段
