"""`@deepseek-ai/dsh-host-directory-picker-auto` 的本包拥有不变量配套（中文名包）。

实现尚未迁入；保留安装入口形状。
"""
包名='@deepseek-ai/dsh-host-directory-picker-auto'#npm 包名
名称='directory-picker-auto-invariants'#不变量插件名
注入=[]#无硬依赖

def 安装(上下文,失败):#InvariantInstaller
    """本包暂无启动检查。"""
    return#空

def 应用(上下文):#Cordis apply
    """登记本包不变量安装器（占位）。"""
    return#空

__all__=['包名','名称','注入','安装','应用']#仅中文公开名
