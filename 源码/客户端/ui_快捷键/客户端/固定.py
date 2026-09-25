"""产品快捷键速查集成贡献的菜单预留项。"""

__all__=['固定命令']

def 固定命令(翻译):
    """描述共享菜单动作，供展示与冲突检查；返回只读动作与其占用的物理组合。"""
    行表=[
        {'id':'move','keys':['↑','↓'],'bindings':[{'code':'ArrowUp','modifiers':[]},{'code':'ArrowDown','modifiers':[]}],'group':'menus'},
        {'id':'select','keys':['Enter'],'bindings':[{'code':'Enter','modifiers':[]}],'group':'menus'},
        {'id':'dismiss','keys':['Esc'],'bindings':[{'code':'Escape','modifiers':[]}],'group':'menus'},
    ]
    结果=[]
    for 行 in 行表:
        标识='fixed.'+行['id']
        def 标签(键=行['id']):
            """按固定行 id 取文案。"""
            return 翻译(键)
        结果.append({
            'id':标识,
            'keys':行['keys'],
            'bindings':行['bindings'],
            'group':行['group'],
            'label':标签,
        })
    return 结果

fixedCommands=固定命令
