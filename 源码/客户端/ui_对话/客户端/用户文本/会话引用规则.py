'原文里的会话候选。显式线文和已知标签里取最长的'
import re

__all__=['会话引用规则']

def 匹配会话(文本,从,上下文):
    '最近的会话引用。裸标签只在非线文的 @ 处读事实'
    标签=None
    已读=False
    线=re.compile(r'@\[([^\]\n]+)\]\(dsh-session:[^)\s]+\)')
    起点=文本.find('@',从)
    while 起点>=0:
        显式=线.match(文本,起点)
        if 显式 is not None:
            return {
                'id':'session',
                'start':起点,
                'end':起点+len(显式.group(0)),
                'data':{'label':显式.group(1)},
            }
        if not 已读:
            标签=上下文['read']('sessionLabels')
            已读=True
        最佳=None
        for 名 in 标签 or []:
            if 名=='' or not 文本.startswith(名,起点+1):
                continue
            止=起点+len(名)+1
            if 最佳 is None or 止>最佳['end']:
                最佳={'id':'session','start':起点,'end':止,'data':{'label':名}}
        if 最佳 is not None:
            return 最佳
        起点=文本.find('@',起点+1)
    return None

会话引用规则={
    'id':'session',
    'order':10,
    'match':匹配会话,
}
