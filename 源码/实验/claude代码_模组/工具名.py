'Claude Code 工具名与宿主工具名的双向对照'
__all__=['默认工具别名','创建工具名别名']

默认工具别名={
    'Bash':'bash',
    'Read':'read',
    'Edit':'edit',
    'Write':'write',
    'Glob':'glob',
    'Grep':'grep',
    'WebFetch':'web_fetch',
    'WebSearch':'web_search',
    'Task':'subagent',
    'TodoWrite':'todo_write',
    'AskUserQuestion':'ask_user_question',
    'ExitPlanMode':'exit_plan_mode',
    'Skill':'skill',
}#两边都有的内置工具

class 工具名别名:
    '双向翻译：模组看见的名字，和注册表认识的名字'
    def __init__(自身,正向,反向):
        '记下两张表'
        自身._正向=正向#模组名到宿主名
        自身._反向=反向#宿主名到模组名

    def toMod(自身,宿主名):
        '宿主工具在模组侧的名字；没有别名就用宿主名本身'
        if 宿主名 in 自身._反向:#有别名
            return 自身._反向[宿主名]#模组名
        return 宿主名#原名

    def toHarness(自身,模组名):
        '模组点的名字对应的宿主工具；没有别名就用这个名字本身'
        if 模组名 in 自身._正向:#有别名
            return 自身._正向[模组名]#宿主名
        return 模组名#原名

def 创建工具名别名(覆盖=None):
    '内置表加上部署覆盖。覆盖是 Claude Code 名到宿主名'
    合并=dict(默认工具别名)#先抄内置
    if 覆盖 is not None:#有覆盖
        合并.update(覆盖)#同名替换
    反向={}#宿主名到模组名
    for 模组名,宿主名 in 合并.items():#后写的宿主名覆盖先前的反向
        反向[宿主名]=模组名#反向一条
    return 工具名别名(合并,反向)#双向表
