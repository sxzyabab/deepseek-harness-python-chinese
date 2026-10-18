'对同一次会话出现和仍在进行的回合，两次彼此独立的 Escape'

__all__=['停止序列']

class 停止序列:
    '短命的第一次按键。接受取消之前先清掉它'
    def __init__(自身,间隔毫秒,释放):
        '记下两次按键的最大间隔，以及第一次按键还握着的观察'
        自身.间隔毫秒=间隔毫秒
        自身.释放=释放
        自身.第一次=None
        自身.计时=None

    def 重置(自身):
        '清掉第一次按键和它的到期计时'
        自身.第一次=None
        if 自身.计时 is not None:
            clearTimeout(自身.计时)
            自身.计时=None
        自身.释放()

    def 按下(自身,目标):
        '用刚解析出的当前状态接受一次合格的、非重复的 Escape。这次是否请求了取消'
        第一次=自身.第一次
        自身.重置()
        if 第一次 is not None and performance.now()<=第一次['deadline'] and 第一次['target']['sessionId']==目标['sessionId'] and 第一次['target']['turn']==目标['turn'] and 第一次['target']['generation'] is 目标['generation'] and 第一次['target']['region'] is 目标['region']:
            目标['cancel']()
            return True
        自身.第一次={'target':目标,'deadline':performance.now()+自身.间隔毫秒}
        def 到期():
            '间隔过后放弃第一次按键'
            自身.重置()
        自身.计时=setTimeout(到期,自身.间隔毫秒+1)
        return False
