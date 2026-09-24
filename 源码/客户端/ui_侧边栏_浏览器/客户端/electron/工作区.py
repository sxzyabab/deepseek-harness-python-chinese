__all__=['浏览器工作区']

def 已中止(信号):
    if 信号 is None:
        return False
    return 信号.is_set()

def 若已中止则抛出(信号):
    if 已中止(信号):
        raise RuntimeError('aborted')

def 浏览器工作区(源,会话标识,信号):
    """用工作区规范 cwd 作存储账户；未分组会话仍隔离。"""
    若已中止则抛出(信号)
    if 源.getSnapshot()['phase']!='ready':
        完成=[False]
        def 推进():
            if 源.getSnapshot()['phase']!='ready':
                return
            完成[0]=True
        退=源.subscribe(推进)
        while not 完成[0] and not 已中止(信号):
            信号.wait(0.05)
        退()
        if 已中止(信号):
            raise RuntimeError('aborted')
    若已中止则抛出(信号)
    for 项 in 源.getSnapshot()['items']:
        for 标识 in 项['sessionIds']:
            if 标识==会话标识:
                return 'cwd:'+项['path']
    return 'session:'+会话标识
