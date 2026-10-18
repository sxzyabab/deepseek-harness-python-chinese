class 会话错误(Exception):
    '本包会话适配失败'

def 拒绝未声明(种类,名册,值表):
    '贡献里出现名册没有的成员则抛'
    实际={}#没有值表就当空表
    if 值表 is not None:#有值表
        实际=值表#用调用方的表
    已声明=()#没有名册就当空名册
    if 名册 is not None:#有名册
        已声明=名册#用调用方的名册
    for 名称 in 实际.keys():#逐个贡献名
        if 名称 not in 已声明:#名册里没有
            raise 会话错误(f"uiSession.provide: undeclared {种类} '{名称}'")#未声明
