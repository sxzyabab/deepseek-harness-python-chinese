from ....工具.工作区路径 import 是否绝对工作区路径

__all__=['已记录绝对路径']

def 已记录绝对路径(元数据,字段):
    '从结果元数据读取绝对 path 或 cwd。旧记录或畸形时没有'
    if not isinstance(元数据,dict):
        return None
    值=元数据.get(字段)
    if isinstance(值,str) and 是否绝对工作区路径(值):
        return 值
    return None
