"""精确路径监视：现场配置补丁文件可活在 Cordis 模块根之外。"""
import os,sys,threading
__all__=['监视配置']

登记表={}#上下文身份 → 已登记规范路径集合

def 查找监视根(文件名):
    """沿缺失父目录向上走到存在的目录，记下深度。"""
    根=os.path.dirname(文件名)
    深度=0
    while True:
        try:
            if not os.path.exists(根):
                raise FileNotFoundError(根)
            if not os.path.isdir(根):
                raise OSError('配置监视的父路径不是目录')
            规范根=os.path.realpath(根)
            相对=os.path.relpath(文件名,根)
            return {'filename':os.path.normpath(os.path.join(规范根,相对)),'root':规范根,'depth':深度}
        except FileNotFoundError:
            父=os.path.dirname(根)
            if 父==根:
                raise
            根=父
            深度+=1

def 监视配置(上下文,文件名,选项,刷新,事务中=None):
    """监视一条补丁路径（含缺失父目录），并把刷新回调串行化。返回拆除器。"""
    if 事务中 is None:
        def 非事务():
            """默认不在事务内。"""
            return False
        事务中=非事务
    目标=查找监视根(文件名)
    键=id(上下文)
    路径集=登记表[键] if 键 in 登记表 else set()
    登记表[键]=路径集
    if 目标['filename'] in 路径集:
        raise OSError('配置路径已登记')
    路径集.add(目标['filename'])
    脏=threading.Event()
    停止=threading.Event()
    运行锁=threading.Lock()
    上次=None

    def 观测路径():
        """读目标文件的存在与修改时间。"""
        候选=(文件名,目标['filename'])
        for 路径 in 候选:
            try:
                状态=os.stat(路径)
                return (路径,状态.st_mtime_ns)
            except FileNotFoundError:
                continue
        return None

    def 刷新循环():
        """脏位串行刷新，失败记警告。"""
        while not 停止.is_set():
            脏.wait(0.25)
            if 停止.is_set():
                return
            当前=观测路径()
            变化=当前!=上次
            上次状态=上次
            if 变化:
                上次=当前
                if 上次状态 is None and 当前 is None:
                    脏.clear()
                    continue
                脏.set()
            if not 脏.is_set():
                continue
            with 运行锁:
                while 脏.is_set() and not 停止.is_set():
                    脏.clear()
                    try:
                        刷新()
                    except BaseException as 原因:
                        错误=原因 if isinstance(原因,Exception) else Exception(str(原因))
                        日志=getattr(上下文,'日志',None)
                        if 日志 is not None:
                            日志.警告('配置重载失败')
                            日志.警告(错误)
                        else:
                            sys.stderr.write('配置重载失败: '+str(错误)+'\n')

    线=threading.Thread(target=刷新循环,daemon=True)
    线.start()
    def 拆除():
        """关闭监视并按事务标志排空当前刷新。"""
        停止.set()
        脏.set()
        线.join()
        路径集.discard(目标['filename'])
        if not 事务中():
            with 运行锁:
                pass
    def 登记体():
        """交出拆除器供纤程在卸载时调用。"""
        return 拆除
    return 上下文.副作用(登记体,'hmr.watchConfig()')
