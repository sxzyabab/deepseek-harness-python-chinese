"""把 SSE 字节流解码成事件 data 载荷。

对齐上游 `llm-deepseek/src/sse.ts`。公开面仅中文名；无英文别名。
"""
import codecs#UTF-8增量解码
from llm import 大模型错误#LLM错误

__all__=('结束哨兵','解析服务推送')#仅中文公开名

结束哨兵='[DONE]'#流结束哨兵
取增量解码器=codecs.getincrementaldecoder#UTF-8增量解码器工厂

def 解析服务推送(流,注释回调=None):#解析服务推送字节流
    """把服务推送字节流解析成数据载荷，最后让出 [DONE]；没有哨兵则抛 STREAM_CLOSED。"""
    #按规范只在空行终止符上派发事件，EOF处未终止尾巴当作截断
    解码器=取增量解码器('utf-8')()#增量UTF-8解码
    行余=''#尚未成行的文本
    数据行=[]#当前事件的data字段
    已去bom=False#是否已剥UTF-8 BOM
    已结束=False#是否已让出哨兵
    while True:#读流
        块=流.read(8192)#读一块原始字节
        if 块:#有数据
            文本=解码器.decode(块)#增量解码
        else:#EOF
            文本=解码器.decode(b'',True)#冲刷尾字节
        if not 已去bom:#尚未剥BOM
            if 文本.startswith('\ufeff'):#有BOM
                文本=文本[1:]#剥BOM
            已去bom=True#只剥一次
        行余+=文本#接上残余
        while True:#拆行
            换行=-1#行终止位置
            跳过=1#终止符长度
            位置=0#扫描下标
            while 位置<len(行余):#找终止
                字符=行余[位置]#当前字符
                if 字符=='\n':#LF
                    换行=位置#LF
                    跳过=1#单字符
                    break#找到终止
                if 字符=='\r':#CR
                    换行=位置#CR
                    跳过=2 if 位置+1<len(行余) and 行余[位置+1]=='\n' else 1#CRLF或CR
                    break#找到终止
                位置+=1#继续扫
            if 换行<0:#没有完整行
                break#等更多字节
            行=行余[:换行]#去掉终止符的一行
            行余=行余[换行+跳过:]#吃掉终止符
            if 行.startswith(':'):#注释行
                注释=行[1:]#冒号后为注释
                if 注释.startswith(' '):#有前导空格
                    注释=注释[1:]#剥一个前导空格
                if 注释回调 is not None:#有回调
                    注释回调(注释)#报告传输活动
                continue#注释不进入载荷
            if 行=='':#空行：事件终止
                数据='\n'.join(数据行)#多条data用LF拼接
                数据行=[]#清空本事件
                yield 数据#让出data字段
                if 数据==结束哨兵:#结束哨兵
                    已结束=True#见到哨兵
                    return#停止解析
                continue#下一事件
            if ':' in 行:#有字段名
                名,值=行.split(':',1)#字段名与值
                if 值.startswith(' '):#有前导空格
                    值=值[1:]#剥一个前导空格
            else:#无冒号
                名=行#无冒号则整行是字段名
                值=''#空值
            if 名=='data':#data字段
                数据行.append(值)#累积data
        if not 块:#字节流结束
            break#离开外循环
    if not 已结束:#没有哨兵
        raise 大模型错误('SSE stream ended without [DONE]','STREAM_CLOSED')#没有哨兵则截断
