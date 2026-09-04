"""为已记录会话测试捕获可读、路径稳定的工作区状态。

对齐上游 `session-snapshot/src/workspace.ts`。公开面仅中文名。
"""
import os#目录遍历与读文件

__all__=['空工作区标记','捕获工作区快照','捕获期望工作区快照']#仅中文公开名

空工作区标记='.empty'#空目录标记名

def 文本内容(字节):#尝试文本解码
    """往返一致的 UTF-8 才算文本。"""
    if b'\x00' in 字节:#含 NUL
        return None#非文本
    try:#解码
        文本=字节.decode('utf-8')#按 utf8 解码
    except UnicodeDecodeError:#失败
        return None#非文本
    return 文本 if 文本.encode('utf-8')==字节 else None#往返一致才算文本

def 捕获工作区快照(根,选项=None):#捕获工作区快照
    """捕获一个工作区，不解析链接、不依赖主机路径分隔符。"""
    if 选项 is None:#缺省
        选项={}#空
    忽略=set(选项.get('ignoredRootEntries') or [])#忽略集
    def 访问(目录,段们):#递归访问
        """递归收集条目。"""
        名称们=sorted(os.listdir(目录),key=lambda 名:名.encode('utf-8'))#按字节名排序
        捕获=[]#收集结果
        for 名 in 名称们:#逐项
            if len(段们)==0 and 名 in 忽略:#根层过滤
                continue#跳过
            子段=[*段们,名]#相对段
            路径='/'.join(子段)#POSIX 相对路径
            绝对=os.path.join(目录,名)#绝对路径
            if os.path.islink(绝对):#符号链接
                捕获.append({'path':路径,'kind':'symlink','target':os.readlink(绝对)})#符号链接
            elif os.path.isdir(绝对):#目录
                子们=访问(绝对,子段)#递归
                if len(子们)==0:#空目录
                    捕获.append({'path':路径,'kind':'empty-directory'})#空目录
                else:#有子
                    捕获.extend(子们)#展开
            elif os.path.isfile(绝对):#文件
                with open(绝对,'rb') as 句柄:#读字节
                    字节=句柄.read()#读
                内容=文本内容(字节)#尝试文本
                if 内容 is None:#二进制
                    import base64#编码
                    捕获.append({'path':路径,'kind':'binary','base64':base64.b64encode(字节).decode('ascii')})#二进制
                else:#文本
                    捕获.append({'path':路径,'kind':'text','content':内容})#文本
        return 捕获#返回
    return 访问(根,[])#从根遍历

def 捕获期望工作区快照(根):#捕获期望工作区
    """捕获已提交的 workspace.expected/ 树，排除仅 Git 用的空标记。"""
    return 捕获工作区快照(根,{'ignoredRootEntries':[空工作区标记]})#忽略空标记

EMPTY_WORKSPACE_MARKER=空工作区标记#上游名
captureWorkspaceSnapshot=捕获工作区快照#上游名
captureExpectedWorkspaceSnapshot=捕获期望工作区快照#上游名
