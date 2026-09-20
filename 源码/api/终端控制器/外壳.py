from ...子进程.子进程 import 可执行未找到错误#查找失败

__all__=['解析外壳','发现外壳']#仅中文公开名

def 剖面(路径):#按可执行名填参数
    """cmd 无参，PowerShell -NoLogo，其余 -i。"""
    斜=路径.rfind('/')#POSIX
    反=路径.rfind('\\')#Windows
    名=路径[max(斜,反)+1:]#基名
    种=名.lower()#小写
    if 种.endswith('.exe'):#去后缀
        种=种[:-4]#去
    if 种=='cmd':#cmd
        参数=[]#无
    elif 种=='pwsh' or 种=='powershell':#PowerShell
        参数=['-NoLogo']#无徽标
    else:#交互
        参数=['-i']#交互
    return {'path':路径,'name':名,'args':参数}#壳

def 解析外壳(子进程,已配置,信号):#配置或环境默认
    """已声明默认无法解析则拒绝。"""
    壳=已配置
    if 壳 is None:#无配置
        环境=子进程.终端环境(信号)#环境
        默认=环境.get('defaultShell') if isinstance(环境,dict) else None#默认
        平台=环境.get('platform') if isinstance(环境,dict) else None#平台
        路径=默认 if 默认 is not None else ('cmd.exe' if 平台=='windows' else '/bin/sh')#回落
        壳=剖面(路径)#剖面
    路径=子进程.解析可执行文件(壳['path'],None,信号)#核验
    结果=dict(壳)#拷
    结果['path']=路径#已核验
    return 结果#壳

def 发现外壳(子进程,已配置,候选,信号):#已安装候选，默认在前
    """传输失败拒绝；未找到的候选省略。"""
    首选=解析外壳(子进程,已配置,信号)#默认
    找到=[]#候选结果
    for 项 in 候选:#逐个
        try:#解析
            找到.append(解析外壳(子进程,剖面(项),信号))#核验
        except 可执行未找到错误:#省略
            找到.append(None)#空
    壳表={}#路径去重
    for 壳 in [首选,*找到]:#默认在前
        if 壳 is None:#省略
            continue#跳
        键=壳['path'].lower() if '\\' in 壳['path'] else 壳['path']#Windows 大小写
        if 键 not in 壳表:#未见
            壳表[键]=壳#收下
    return list(壳表.values())#列表
