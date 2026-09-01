'''dulwich单文件中文封装：把pypi包dulwich的常用git操作包装成中文接口'''
from io import BytesIO as 字节流#承接dulwich流式输出的内存缓冲区
from time import localtime as 本地时间,strftime as 格式化时间#提交时间戳转本地可读文本
from dulwich.client import get_transport_and_path as 建立远程传输#按地址创建远程客户端
from dulwich.repo import Repo as 仓库类#仓库对象，构造参数为工作区路径
from dulwich.porcelain import (
    init as 底层初始化,
    clone as 底层克隆,
    add as 底层添加,
    remove as 底层移除,
    commit as 底层提交,
    status as 底层状态,
    reset as 底层重置,
    branch_create as 底层创建分支,
    branch_delete as 底层删除分支,
    branch_list as 底层分支列表,
    active_branch as 底层当前分支,
    checkout_branch as 底层切换分支,
    tag_create as 底层创建标签,
    tag_delete as 底层删除标签,
    tag_list as 底层标签列表,
    remote_add as 底层添加远程,
    push as 底层推送,
    pull as 底层拉取,
    fetch as 底层抓取,
    ls_files as 底层跟踪文件,
    check_ignore as 底层检查忽略,
    diff_tree as 底层树差异,
)

#==============================仓库生命周期==============================

def 打开仓库(仓库路径:str):
    '''打开已存在的git仓库，返回仓库对象，后续函数的第一个参数都用它'''
    return 仓库类(仓库路径)#dulwich仓库对象

def 初始化仓库(仓库路径:str,裸仓库:bool=False):
    '''在指定路径新建git仓库，裸仓库为真时不生成工作区，返回仓库对象'''
    return 底层初始化(仓库路径,bare=裸仓库)#新建后的仓库对象

def 克隆仓库(远程地址:str,目标路径:str,分支:str=None,深度:int=None,用户名:str=None,密码:str=None):
    '''克隆远程仓库到目标路径，分支为空取远程默认分支，深度为空取完整历史，返回仓库对象'''
    认证参数={'username':用户名,'password':密码} if 用户名 else {}#http基本认证参数
    return 底层克隆(远程地址,目标路径,branch=分支.encode('utf-8') if 分支 else None,
        depth=深度,**认证参数)#克隆完成后的仓库对象

def 关闭仓库(仓库):
    '''释放仓库占用的文件句柄，长时间运行的程序用完必须调用'''
    仓库.close()#关闭对象存储与索引文件

#==============================暂存与提交==============================

def 添加文件(仓库,路径列表:list)->dict:
    '''把文件加入暂存区，路径须为绝对路径或相对当前工作目录，返回加入与被忽略两份清单'''
    已加入,被忽略=底层添加(仓库,路径列表)#dulwich同时返回被.gitignore拦下的路径
    return {'已加入':list(已加入),'被忽略':list(被忽略)}#两份相对路径清单

def 移除文件(仓库,路径列表:list):
    '''从暂存区与工作区删除文件，路径规则同添加文件'''
    底层移除(仓库,路径列表)#删除工作区文件并更新索引

def 提交(仓库,提交信息:str,作者:str=None,提交者:str=None)->str:
    '''把暂存区内容写成一次提交，作者与提交者格式为“姓名 <邮箱>”，为空时读取git配置，返回提交号'''
    提交号=底层提交(仓库,message=提交信息.encode('utf-8'),#提交说明按utf8编码写入
        author=作者.encode('utf-8') if 作者 else None,#作者身份
        committer=提交者.encode('utf-8') if 提交者 else None)#提交者身份
    return 提交号.decode('utf-8')#40位十六进制提交号

def 仓库状态(仓库)->dict:
    '''读取工作区状态，分为已暂存三类、未暂存、未跟踪'''
    状态=底层状态(仓库)#dulwich状态三元组
    return {'已暂存新增':[路径.decode('utf-8') for 路径 in 状态.staged['add']],#新纳入暂存区的文件
        '已暂存删除':[路径.decode('utf-8') for 路径 in 状态.staged['delete']],#暂存区标记删除的文件
        '已暂存修改':[路径.decode('utf-8') for 路径 in 状态.staged['modify']],#暂存区内容变更的文件
        '未暂存':[路径.decode('utf-8') for 路径 in 状态.unstaged],#工作区已改但未暂存的文件
        '未跟踪':list(状态.untracked)}#从未纳入版本控制的文件

def 重置(仓库,目标提交:str='HEAD',模式:str='hard'):
    '''把索引与工作区回退到目标提交，模式取hard时连工作区文件一起覆盖'''
    底层重置(仓库,模式,目标提交.encode('utf-8'))#按模式重置到指定提交

def 跟踪文件列表(仓库)->list:
    '''列出索引中已被版本控制的全部文件路径'''
    return [路径.decode('utf-8') for 路径 in 底层跟踪文件(仓库)]#索引内的相对路径

def 检查忽略(仓库,路径列表:list)->list:
    '''筛出会被.gitignore规则忽略的路径'''
    return list(底层检查忽略(仓库,路径列表))#命中忽略规则的路径

#==============================历史与差异==============================

def 当前提交(仓库)->str:
    '''读取HEAD指向的提交号'''
    return 仓库.head().decode('utf-8')#当前提交号

def 提交历史(仓库,最大数量:int=20)->list:
    '''按时间倒序读取提交记录，返回含提交号、作者、时间、信息的字典列表'''
    记录列表=[]#提交记录结果
    for 游走项 in 仓库.get_walker(max_entries=最大数量):#游走器按日期倒序产出提交
        提交对象=游走项.commit#本条记录对应的提交对象
        记录列表.append({'提交号':提交对象.id.decode('utf-8'),#40位十六进制提交号
            '作者':提交对象.author.decode('utf-8'),#作者姓名与邮箱
            '时间':格式化时间('%Y-%m-%d %H:%M:%S',本地时间(提交对象.commit_time)),#提交时间本地文本
            '信息':提交对象.message.decode('utf-8')})#提交说明原文
    return 记录列表#完整提交记录

def 提交差异(仓库,旧提交号:str,新提交号:str)->str:
    '''输出两个提交之间的统一格式差异文本'''
    旧树=仓库[旧提交号.encode('utf-8')].tree#旧提交指向的目录树编号
    新树=仓库[新提交号.encode('utf-8')].tree#新提交指向的目录树编号
    差异缓冲=字节流()#承接差异输出
    底层树差异(仓库,旧树,新树,差异缓冲)#把差异写入缓冲
    return 差异缓冲.getvalue().decode('utf-8')#差异文本

#==============================分支与标签==============================

def 当前分支(仓库)->str:
    '''读取HEAD所在的本地分支名，处于游离头指针状态时报错'''
    return 底层当前分支(仓库).decode('utf-8')#不含refs/heads/前缀的分支名

def 分支列表(仓库)->list:
    '''列出全部本地分支名'''
    return [分支.decode('utf-8') for 分支 in 底层分支列表(仓库)]#本地分支名清单

def 创建分支(仓库,分支名:str,起点:str=None,强制:bool=False):
    '''新建本地分支，起点为空时以当前HEAD为起点，强制为真时覆盖同名分支'''
    底层创建分支(仓库,分支名.encode('utf-8'),objectish=起点,force=强制)#写入refs/heads下的引用

def 删除分支(仓库,分支名:str):
    '''删除本地分支引用'''
    底层删除分支(仓库,分支名.encode('utf-8'))#移除refs/heads下的引用

def 切换分支(仓库,分支名:str,强制:bool=False):
    '''切换工作区到指定本地分支，强制为真时丢弃未提交改动'''
    底层切换分支(仓库,分支名.encode('utf-8'),force=强制)#更新HEAD并刷新工作区

def 标签列表(仓库)->list:
    '''列出全部标签名'''
    return [标签.decode('utf-8') for 标签 in 底层标签列表(仓库)]#标签名清单

def 创建标签(仓库,标签名:str,目标:str='HEAD',附注信息:str=None,作者:str=None):
    '''给指定提交打标签，附注信息非空时创建带说明的附注标签'''
    底层创建标签(仓库,标签名.encode('utf-8'),objectish=目标,#标签指向的提交
        message=附注信息.encode('utf-8') if 附注信息 else None,#附注标签的说明文本
        author=作者.encode('utf-8') if 作者 else None,#附注标签的作者身份
        annotated=附注信息 is not None)#有说明才建附注标签，否则建轻量标签

def 删除标签(仓库,标签名:str):
    '''删除标签引用'''
    底层删除标签(仓库,标签名.encode('utf-8'))#移除refs/tags下的引用

#==============================远程交互==============================

def 添加远程(仓库,远程名:str,远程地址:str):
    '''在仓库配置里登记一个远程地址'''
    底层添加远程(仓库,远程名,远程地址)#写入config中的remote段

def 远程引用(远程地址:str,用户名:str=None,密码:str=None)->dict:
    '''不下载对象，直接读取远程仓库的引用表，键为引用全名值为提交号'''
    认证参数={'username':用户名,'password':密码} if 用户名 else {}#http基本认证参数
    远程客户端,远程路径=建立远程传输(远程地址,**认证参数)#按地址协议选择客户端
    引用表=远程客户端.get_refs(远程路径)#远程引用字典
    return {引用名.decode('utf-8'):提交号.decode('utf-8') for 引用名,提交号 in 引用表.items()}

def 抓取(仓库,远程地址:str='origin',深度:int=None,用户名:str=None,密码:str=None)->dict:
    '''只下载远程对象不合并，返回远程引用表'''
    认证参数={'username':用户名,'password':密码} if 用户名 else {}#http基本认证参数
    抓取结果=底层抓取(仓库,远程地址,depth=深度,**认证参数)#执行抓取
    return {引用名.decode('utf-8'):提交号.decode('utf-8') for 引用名,提交号 in 抓取结果.refs.items()}

def 拉取(仓库,远程地址:str='origin',引用规格:str=None,快进:bool=True,用户名:str=None,密码:str=None)->str:
    '''抓取远程并更新本地引用与工作区，引用规格为空时取当前分支，返回过程文本'''
    认证参数={'username':用户名,'password':密码} if 用户名 else {}#http基本认证参数
    过程缓冲=字节流()#承接拉取过程提示
    底层拉取(仓库,远程地址,引用规格.encode('utf-8') if 引用规格 else None,#待拉取的引用规格
        outstream=字节流(),errstream=过程缓冲,fast_forward=快进,**认证参数)#执行拉取
    return 过程缓冲.getvalue().decode('utf-8')#拉取过程文本

def 推送(仓库,远程地址:str='origin',引用规格:str=None,强制:bool=False,用户名:str=None,密码:str=None)->str:
    '''把本地提交推送到远程，引用规格为空时推送当前分支，返回过程文本'''
    认证参数={'username':用户名,'password':密码} if 用户名 else {}#http基本认证参数
    过程缓冲=字节流()#承接推送过程提示
    底层推送(仓库,远程地址,引用规格.encode('utf-8') if 引用规格 else None,#待推送的引用规格
        outstream=字节流(),errstream=过程缓冲,force=强制,**认证参数)#执行推送
    return 过程缓冲.getvalue().decode('utf-8')#推送过程文本