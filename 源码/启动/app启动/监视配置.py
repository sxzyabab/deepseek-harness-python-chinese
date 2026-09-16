"""精确路径监视：现场配置补丁文件可活在 Cordis 模块根之外。"""
import os,sys,threading#路径、诊断与刷新串行
__all__=['监视配置']#仅中文公开名

登记表={}#上下文身份 → 已登记规范路径集合

def 查找监视根(文件名):
    """沿缺失父目录向上走到存在的目录，记下深度。"""
    根=os.path.dirname(文件名)#起始父目录
    深度=0#向上层数
    while True:#直到找到存在的目录
        try:#探测目录
            if not os.path.isdir(根):#父不是目录
                raise OSError('config watch parent is not a directory: '+根)#拒绝
            规范根=os.path.realpath(根)#规范根
            相对=os.path.relpath(文件名,根)#相对原根
            return {'filename':os.path.normpath(os.path.join(规范根,相对)),'root':规范根,'depth':深度}#目标
        except FileNotFoundError:#父缺失
            父=os.path.dirname(根)#再上一层
            if 父==根:#已到文件系统根
                raise#原样抛出
            根=父#继续
            深度+=1#加深

def 监视配置(上下文,文件名,选项,刷新):
    """监视一条补丁路径（含缺失父目录），并把刷新回调串行化。返回拆除器。"""
    目标=查找监视根(文件名)#解析监视根
    键=id(上下文)#上下文身份
    路径集=登记表[键] if 键 in 登记表 else set()#已登记路径
    登记表[键]=路径集#写回
    if 目标['filename'] in 路径集:#重复登记
        raise OSError('config path already registered: '+文件名)#拒绝
    路径集.add(目标['filename'])#占用
    脏=threading.Event()#有待刷新
    停止=threading.Event()#拆除信号
    运行锁=threading.Lock()#刷新互斥
    上次=None#上次观测到的状态

    def 观测路径():
        """读目标文件的存在与修改时间。"""
        候选=(文件名,目标['filename'])#原路径与规范路径
        for 路径 in 候选:#逐路径
            try:#探测
                状态=os.stat(路径)#状态
                return (路径,状态.st_mtime_ns)#路径与纳秒修改时间
            except FileNotFoundError:#缺失
                continue#试下一条
        return None#均缺失

    def 刷新循环():
        """脏位串行刷新，失败记警告。"""
        while not 停止.is_set():#直到拆除
            脏.wait(0.25)#短等脏位或轮询间隔
            if 停止.is_set():#已拆
                return#退出
            当前=观测路径()#当前状态
            变化=当前!=上次#增改删
            上次状态=上次#上一拍
            if 变化:#路径变化
                上次=当前#推进
                if 上次状态 is None and 当前 is None:#仍双缺失
                    脏.clear()#清脏
                    continue#继续等
                脏.set()#标记脏
            if not 脏.is_set():#无脏
                continue#继续等
            with 运行锁:#串行刷新
                while 脏.is_set() and not 停止.is_set():#排空脏位
                    脏.clear()#先清，刷新期间再脏则再跑
                    try:#刷新
                        刷新()#同步回调
                    except BaseException as 原因:#刷新失败
                        错误=原因 if isinstance(原因,Exception) else Exception(str(原因))#收成异常
                        日志=getattr(上下文,'日志',None)#日志槽
                        if 日志 is not None:#有日志
                            日志.警告('config reload at %C failed',文件名)#路径
                            日志.警告(错误)#原因
                        else:#无日志则写标准错误
                            sys.stderr.write('config reload at '+文件名+' failed: '+str(错误)+'\n')#诊断

    线=threading.Thread(target=刷新循环,daemon=True)#后台监视
    线.start()#启动
    def 拆除():
        """关闭监视并排空当前刷新。"""
        停止.set()#停止循环
        脏.set()#唤醒等待
        线.join()#等线程退出
        路径集.discard(目标['filename'])#释放登记
        with 运行锁:#排空刷新
            pass#刷新已停
    return 上下文.副作用(拆除,'app-boot.watchConfig()')#登记拆除
