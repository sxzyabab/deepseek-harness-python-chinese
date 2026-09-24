import threading

__all__=['目录节点']

def 已中止(信号):
    if 信号 is None:
        return False
    return 信号.is_set()

class 目录节点:
    """文件面板展开目录树的监视与读取归属。"""
    def __init__(自身,路径,加载,监视,失败,寿命,还原=None):
        自身.路径=路径
        自身.加载=加载
        自身.监视=监视
        自身.失败=失败
        自身.子节点={}
        自身.本控=threading.Event()
        自身.寿命=寿命
        自身.任务=None
        自身.在读=None
        自身.脏=False
        自身.已初始化=False
        自身.自动=True
        自身.还原=list(还原 or ())

    def 已停(自身):
        return 已中止(自身.寿命) or 自身.本控.is_set()

    def 打开(自身):
        if 自身.任务 is None:
            自身.任务=threading.Thread(target=自身.跟随,daemon=True)
            自身.任务.start()
        return 自身

    def 查找(自身,路径):
        if 路径==自身.路径:
            return 自身
        for 子 in 自身.子节点.values():
            命中=子.查找(路径)
            if 命中 is not None:
                return 命中
        return None

    def 设展开(自身,展开表):
        自身.还原=list(展开表)
        for 子 in 自身.子节点.values():
            子.设展开(展开表)

    def 展开(自身,路径,还原=None):
        if 自身.已停():
            return None
        子=自身.子节点.get(路径)
        if 子 is None:
            子=目录节点(路径,自身.加载,自身.监视,自身.失败,自身.寿命,还原 or ())
            子.自动=自身.自动
            自身.子节点[路径]=子
        return 子.打开()

    def 折叠(自身,路径):
        自身.还原=[项 for 项 in 自身.还原 if 项!=路径 and not 项.startswith(路径+'/')]
        子=自身.子节点.pop(路径,None)
        if 子 is not None:
            子.关闭()

    def 设自动(自身,启用):
        自身.自动=启用
        if 启用 and 自身.脏:
            自身.刷新()
        for 子 in 自身.子节点.values():
            子.设自动(启用)

    def 刷新(自身):
        自身.脏=True
        if 自身.在读 is None:
            自身.在读=threading.Thread(target=自身.读取,daemon=True)
            自身.在读.start()
        return 自身.在读

    def 刷新树(自身):
        自身.刷新()
        for 子 in list(自身.子节点.values()):
            子.刷新树()

    def 关闭(自身):
        自身.本控.set()
        for 子 in list(自身.子节点.values()):
            子.关闭()
        自身.子节点.clear()

    def 跟随(自身):
        try:
            for _事件 in 自身.监视(自身.路径,自身.寿命):
                if 自身.已停():
                    return
                自身.脏=True
                if not 自身.已初始化 or 自身.自动:
                    自身.刷新()
        except Exception as 错误:
            if 自身.已停():
                return
            if not 自身.已初始化:
                自身.刷新()
            码=错误.code if hasattr(错误,'code') else (错误.get('code') if isinstance(错误,dict) else None)
            if 码!='workspace-file/watch-unsupported':
                自身.失败(自身.路径,错误)

    def 读取(自身):
        try:
            while True:
                自身.脏=False
                层级=自身.加载(自身.路径,自身.寿命)
                if 自身.已停() or 层级 is None:
                    return
                自身.已初始化=True
                根=自身.路径.rstrip('/\\')
                目录=set()
                for 条目 in 层级.get('entries') or ():
                    if isinstance(条目,dict) and 条目.get('type')=='directory':
                        目录.add(根+'/'+条目['name'])
                for 路径 in list(自身.子节点.keys()):
                    if 路径 not in 目录:
                        自身.折叠(路径)
                for 路径 in 目录:
                    if 路径 in 自身.还原:
                        自身.展开(路径,自身.还原)
                自身.还原=[]
                if not (自身.脏 and 自身.自动 and not 自身.已停()):
                    return
        finally:
            自身.在读=None
