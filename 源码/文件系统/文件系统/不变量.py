"""本包拥有的文件系统事件数据不变量。"""
包名='@deepseek-ai/dsh-fs'
名称='fs-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','安装','应用']

def 校验目标(目标,失败):
    """断言事件携带可用的不透明目标身份。目标是 dict。"""
    if len(目标['targetKey'])==0:
        失败('filesystem event targetKey must be non-empty')
    if len(目标['displayPath'])==0:
        失败('filesystem event displayPath must be non-empty')

def 安装(上下文,失败):
    """在文件系统决策与观察事件流上安装检查。"""
    def 派发检查(_模式,事件名,参数,*其余):
        """检查文件系统事件携带可用的不透明目标身份，观察事件再校验观察载荷。"""
        if 事件名!='fs/write-intent' and 事件名!='fs/edit-intent' and 事件名!='fs/observed':
            return
        校验目标(参数[0],失败)
        if 事件名=='fs/observed':
            观察=参数[1]
            种类=观察['kind']
            if 种类=='present':
                if len(观察['version'])==0:
                    失败('fs/observed present version must be non-empty')
            elif 种类=='absent':
                return#缺失无需额外字段
            else:
                失败('fs/observed kind must be present or absent')
    上下文.监听('internal/dispatch',派发检查,{'全局':True})

def 应用(上下文):
    """注册文件系统不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文.invariants.register(包名,安装)

name=名称#Cordis插件名
inject=依赖#Cordis依赖声明
apply=应用#Cordis插件入口
default=应用#框架槽
