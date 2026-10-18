'只在已经确认的区间里认出命令，区间外的同样拼写仍是普通文字'
import re#斜杠与空白

__all__=['目标命令引用规则']

斜杠表达式=re.compile(r'(?<!\S)/')#空白边界上的斜杠
空白表达式=re.compile(r'\s')#一个空白


def 匹配命令(文本,起点,上下文):
    '从起点起取最近、同起点时最长的一条确认命令'
    if 斜杠表达式.search(文本,起点) is None:#后面没有边界斜杠
        return None#不读事实
    命令列=上下文['read']('commands')#确认过的区间
    if 命令列 is None:#没有事实
        命令列=[]#当空
    最佳=None#还没有命中
    for 项 in 命令列:#逐段
        起=项['start']#起点
        止=项['end']#终点
        名=项['name']#不带斜杠的名字
        if 起<起点 or 止>len(文本) or 文本[起:止]!='/'+名:#对不上原文
            continue#下一段
        if 起!=0 and 空白表达式.search(文本[起-1:起]) is None:#左边不是空白
            continue#下一段
        if 止!=len(文本) and 空白表达式.search(文本[止:止+1]) is None:#右边不是空白
            continue#下一段
        if 最佳 is None or 起<最佳['start'] or (起==最佳['start'] and 止>最佳['end']):#更近或更长
            最佳={'id':'command','start':起,'end':止,'data':{'name':名}}#记下
    return 最佳#可能没有


目标命令引用规则={#原文里的命令
    'id':'command',#规则标识
    'order':20,#顺序
    'match':匹配命令,#匹配
}#规则结束
