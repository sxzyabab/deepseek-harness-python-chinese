__all__=['相对时间']

def 相对时间(时刻,现在):
    '把两个毫秒时间戳收成 now、minutes、hours、days、months、years。文案由调用方自己译'
    分=60000
    时=3600000
    日=86400000
    差=现在-时刻
    if 差<0:
        差=0
    if 差<分:
        return {'unit':'now','n':0}
    if 差<时:
        return {'unit':'minutes','n':差//分}
    if 差<日:
        return {'unit':'hours','n':差//时}
    if 差<30*日:
        return {'unit':'days','n':差//日}
    if 差<365*日:
        return {'unit':'months','n':差//(30*日)}
    return {'unit':'years','n':差//(365*日)}
