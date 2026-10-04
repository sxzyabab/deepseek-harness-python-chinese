class 客户端模块错误(Exception):
    '本包模块系统失败'
    def __init__(自身,消息):
        '记下英文消息'
        super().__init__(消息)#消息原样英文

构建指示='run `pnpm run build` before launch'#构建指示（错误串，不改）

class 缺客户端包错误(客户端模块错误):
    '缺失的已构建客户端导出'
    def __init__(自身,包名,客户端路径,原因):
        '拼结构化消息；路径只做属性，不进消息'
        消息='\n'.join([#行
            'client-modules: client bundle not found; '+构建指示+':',#缺包产物
            '  package: '+包名,#包名
        ])#拼多行
        super().__init__(消息)#消息
        自身.包名=包名#包名
        自身.客户端路径=客户端路径#路径不进消息
        自身.__cause__=原因#保留原因

class 客户端包组合错误(客户端模块错误):
    '激活失败按可行动的包构建错误与无关失败分组'
    def __init__(自身,失败列表):
        '分组拼消息'
        缺包列表=[错误 for 错误 in 失败列表 if isinstance(错误,缺客户端包错误)]#缺包产物
        其余=[错误 for 错误 in 失败列表 if not isinstance(错误,缺客户端包错误)]#其余失败
        名词='package' if len(失败列表)==1 else 'packages'#单复数
        行列表=['client-modules: '+str(len(失败列表))+' client '+名词+' failed to compose:']#标题行
        if len(缺包列表)>0:#有缺包
            行列表.append('  client bundles not found; '+构建指示+':')#缺包分组头
            for 错误 in 缺包列表:#每个缺包
                行列表.append('    - package: '+错误.包名)#只报名，不写路径
        if len(其余)>0:#有其余失败
            行列表.append('  other failures:')#其余分组
            for 错误 in 其余:#逐条
                行列表.append('    - '+str(错误))#消息
        super().__init__('\n'.join(行列表))#聚合错误
        自身.失败列表=失败列表#原失败列表
