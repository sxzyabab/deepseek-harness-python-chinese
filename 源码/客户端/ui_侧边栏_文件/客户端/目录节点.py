import re
import threading
from ....基础设施.通用工具 import 启动守护线程

__all__=['已中止','目录节点']

def 已中止(信号):
    '信号是否已置位。信号是 threading.Event'
    return 信号.is_set()

def _等(线):
    '等这条线程结束。当前线程不自己等自己'
    if 线 is None or 线 is threading.current_thread():
        return
    线.join()

class 目录节点:
    '文件面板里一个展开目录的监视与读取'
    def __init__(自身,路径,加载,监视,失败,寿命,还原=None):
        '路径是绝对路径。寿命结束或关闭都会停掉这一支'
        自身.路径=路径
        自身.加载=加载
        自身.监视=监视
        自身.失败=失败
        自身.子节点={}
        自身.信号=threading.Event()
        自身.任务=None
        自身.在读=None
        自身.脏=False
        自身.已初始化=False
        自身.自动=True
        自身.还原=list(还原 or ())
        def 跟随寿命(源=寿命,目标=自身.信号):
            '外层寿命结束时，这一支也停'
            源.wait()
            目标.set()
        启动守护线程(跟随寿命)

    def 已停(自身):
        '这一支是否已经停'
        return 自身.信号.is_set()

    def 打开(自身):
        '开始观察。准备好之后会做第一次列举'
        if 自身.任务 is None:
            自身.任务=启动守护线程(自身.跟随)
        return 自身

    def 查找(自身,路径):
        '在这一支里找仍打开的目录。没有则 None'
        if 路径==自身.路径:
            return 自身
        for 子 in 自身.子节点.values():
            命中=子.查找(路径)
            if 命中 is not None:
                return 命中
        return None

    def 设展开(自身,展开表):
        '更新还没列完的目录要恢复的展开表'
        自身.还原=list(展开表)
        for 子 in 自身.子节点.values():
            子.设展开(展开表)

    def 展开(自身,路径,还原=None):
        '打开一个直接子目录。已停则 None'
        if 自身.已停():
            return None
        子=自身.子节点.get(路径)
        if 子 is None:
            子=目录节点(路径,自身.加载,自身.监视,自身.失败,自身.信号,还原 or ())
            子.自动=自身.自动
            自身.子节点[路径]=子
        return 子.打开()

    def 折叠(自身,路径):
        '去掉子目录，并等它的读取和监视结束'
        自身.还原=[项 for 项 in 自身.还原 if 项!=路径 and not 项.startswith(路径+'/')]
        子=自身.子节点.pop(路径,None)
        if 子 is not None:
            子.关闭()

    def 设自动(自身,启用):
        '改这一支是否自动重读。不结束监视'
        自身.自动=启用
        if 启用 and 自身.脏:
            自身.刷新()
        for 子 in list(自身.子节点.values()):
            子.设自动(启用)

    def 刷新(自身):
        '排一次重读。已经在读就并进同一次'
        自身.脏=True
        if 自身.在读 is None:
            自身.在读=启动守护线程(自身.读取)
        return 自身.在读

    def 刷新树(自身):
        '重读这一级，再重读仍打开的下级'
        线=自身.刷新()
        def 随后(本线=线):
            '本级列完再列仍打开的子目录'
            _等(本线)
            for 子 in list(自身.子节点.values()):
                _等(子.刷新树())
        return 启动守护线程(随后)

    def 关闭(自身):
        '停掉这一支，并等读取和监视结束'
        任务=自身.任务
        在读=自身.在读
        自身.信号.set()
        _等(任务)
        _等(在读)
        子表=list(自身.子节点.values())
        自身.子节点.clear()
        for 子 in 子表:
            子.关闭()

    def 跟随(自身):
        '跟着监视。有变化就重读。不支持监视时仍做第一次列举'
        try:
            for _事件 in 自身.监视(自身.路径,自身.信号):
                自身.脏=True
                if not 自身.已初始化 or 自身.自动:
                    自身.刷新()
        except Exception as 错误:
            if 自身.已停():
                return
            if not 自身.已初始化:
                _等(自身.刷新())
            码=getattr(错误,'code',None)
            if 码 is None and isinstance(错误,dict):
                码=错误.get('code')
            if 码!='workspace-file/watch-unsupported':
                自身.失败(自身.路径,错误)

    def 读取(自身):
        '列这一级。脏了且仍自动则再列。消失的子目录关掉，展开表里的子目录打开'
        try:
            while True:
                自身.脏=False
                层级=自身.加载(自身.路径,自身.信号)
                if 自身.已停() or 层级 is None:
                    return
                自身.已初始化=True
                根=re.sub(r'[/\\]+$','',自身.路径)
                目录=set()
                for 条目 in 层级['entries']:
                    if 条目['type']=='directory':
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
