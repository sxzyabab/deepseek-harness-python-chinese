'把标签上的文件地址译成会话和路径，并绑定分页读取'
import base64
from ....工具.工作区路径 import 解析文件地址

__all__=['宿主文件','创建分页读','文档文件字节']

def 宿主文件(地址):
    '一个 dsh-resource://file/… 地址所命名的会话与路径。不是会话地址就抛错'
    解析=解析文件地址(地址)
    if not isinstance(解析,dict) or 解析.get('scope')!='session':
        raise ValueError('ui-sidebar-documentpreview: not a session file address "'+str(地址)+'"')
    return {'sessionId':解析['sessionId'],'path':解析['path']}

def 文档文件字节(文件):
    '把 Remote 字节结果里的 base64 解成 bytes。已经是字节则原样留下'
    数据=文件['data']
    if isinstance(数据,str):
        数据=base64.b64decode(数据)
    elif isinstance(数据,bytearray):
        数据=bytes(数据)
    结果=dict(文件)
    结果['data']=数据
    return 结果

def 创建分页读(远程):
    '把分页读取绑到一份 Remote 面。页长是 Host 配置上限，因此不传 limit'
    def 读页(会话标识,路径,偏移,信号):
        '读一页。返回带 ok 的结果，失败在结果里'
        return 远程.workspaceFiles.read(会话标识,路径,{'offset':偏移},信号)
    return 读页
