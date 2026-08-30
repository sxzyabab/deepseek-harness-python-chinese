"""本包拥有的文件系统事件数据不变量。"""
from ...依赖 import cordis#外部依赖胶水
包名='@deepseek-ai/dsh-fs'#本包的不变量所有权名
名称='fs-invariant'#配套不变量插件名
注入=['invariants']#依赖invariants服务
name=名称#Cordis插件名
inject=注入#Cordis依赖声明

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 取字段(对象,键):#读取映射或对象上的字段
    """读取映射或对象上的字段。"""
    if isinstance(对象,dict):#映射
        return 对象[键]#映射键
    return getattr(对象,键)#对象属性

def 校验目标(目标,失败):#断言事件携带可用的不透明目标身份
    """断言事件携带可用的不透明目标身份。"""
    if len(取字段(目标,'targetKey'))==0:#目标键为空
        失败('filesystem event targetKey must be non-empty')#目标键为空则失败
    if len(取字段(目标,'displayPath'))==0:#展示路径为空
        失败('filesystem event displayPath must be non-empty')#展示路径为空则失败

def 安装(上下文对象,失败):#安装文件系统事件不变量
    """在文件系统决策与观察事件流上安装检查。"""
    def 派发检查(_模式,事件名,参数,*其余):#监听内部派发以检查文件系统事件
        """检查文件系统事件携带可用的不透明目标身份，观察事件再校验观察载荷。"""
        if 事件名!='fs/write-intent' and 事件名!='fs/edit-intent' and 事件名!='fs/observed':#不是写意图、编辑意图或观察事件
            return#也不是观察事件则直接返回
        校验目标(参数[0],失败)#校验第一个参数为目标身份
        if 事件名=='fs/observed':#观察事件还需校验观察载荷
            观察=参数[1]#取出观察载荷
            种类=取字段(观察,'kind')#按观察种类分支
            if 种类=='present':#目标存在
                if len(取字段(观察,'version'))==0:#存在观察的版本为空
                    失败('fs/observed present version must be non-empty')#存在观察的版本不得为空
            elif 种类=='absent':#目标确认缺失
                return#缺失无需额外字段
            else:#未知种类
                失败('fs/observed kind must be present or absent')#种类必须是present或absent
    上下文对象.on('internal/dispatch',派发检查,{'global':True})#全局监听内部派发

def 应用(上下文对象):#应用不变量配套插件
    """注册文件系统不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记并包成立即兑现的承诺

apply=应用#Cordis插件入口
