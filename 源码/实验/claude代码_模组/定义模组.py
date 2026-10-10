'把一份 Claude Code 模组的 register 包成 DSH 插件'

def 选项值合法(值):
    '配置值只允许字符串、数字、布尔，或字符串列表'
    if isinstance(值,bool) or isinstance(值,str):#布尔与字符串
        return True#合法
    if isinstance(值,(int,float)):#数字；布尔已在上面分开
        return True#合法
    if isinstance(值,list) and all(isinstance(项,str) for 项 in 值):#字符串列表
        return True#合法
    return False#其余拒绝

class 模组配置模式:
    '模组 options：键任意，值只能是选项值'
    def 校验数据(自身,数据=None):
        '缺省是空对象；非法值在挂载时失败'
        if 数据 is None:#没给配置
            return {}#空选项
        if not isinstance(数据,dict):#不是对象
            raise ValueError('模组配置必须是对象')#拒绝
        for 键,值 in 数据.items():#逐项
            if not isinstance(键,str) or not 选项值合法(值):#键或值不合
                raise ValueError('模组配置的值只能是字符串、数字、布尔或字符串列表')#拒绝
        return dict(数据)#交回副本

配置模式=模组配置模式()#各模组插件共用

def 定义模组(规格):
    '包成插件。组合里的 config 叠在 userConfig 上，成为 register 收到的 options'
    用户配置=dict(规格['userConfig']) if isinstance(规格.get('userConfig'),dict) else {}#缺省选项
    定义={'name':规格['name'],'options':dict(用户配置),'register':规格['register']}#桥要的定义
    if 规格.get('version') is not None:#有版本才带上
        定义['version']=规格['version']#版本
    if 规格.get('root') is not None:#有根目录才带上
        定义['root']=规格['root']#$.plugin.root
    插件名='claude-code-mod-'+规格['name']#组合里的插件名

    def 应用(上下文,配置值=None):
        '挂上这份模组。register 抛错就让这次挂载失败，拆除器由桥返回'
        合并=dict(用户配置)#先默认
        if isinstance(配置值,dict):#组合覆盖
            合并.update(配置值)#同键以后者为准
        挂上={**定义,'options':dict(合并)}#这次挂载的选项
        return 上下文.claudeCodeMods.添加(挂上)#桥负责登记与拆除

    class 模组插件:
        'Cordis 按属性读取的插件对象'
        name=插件名#插件名
        inject=['claudeCodeMods']#等桥服务
        Config=配置模式#选项校验
        definition=定义#测试与桥读取的定义
        apply=应用#挂载

    return 模组插件()#一份插件

__all__=['定义模组','模组配置模式']
