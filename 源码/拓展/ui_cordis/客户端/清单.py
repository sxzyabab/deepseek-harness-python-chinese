import threading#后台观察清单读取

__all__=['创建清单源']#仅中文公开名

def 创建清单源(端口,报错):#创建清单源
    """行可观察对象 + refresh/retire/reset；读取单飞，reset 作废飞行中读取。"""
    监听集合=set()#订阅者
    快照={'rows':[],'removed':set(),'read':False}#初始
    飞行=None#飞行中
    世代=0#世代

    def 发布(下一):#发布
        """换快照并通知。"""
        nonlocal 快照#闭包
        快照=下一#换
        for 监听器 in list(监听集合):#通知
            监听器()#触发

    def 刷新():#刷新
        """已有读取在飞则跳过。"""
        nonlocal 飞行,世代#闭包
        if 飞行 is not None:#在飞
            return#跳过
        发出=世代#本世代
        def 成功(行列表):#成功
            """过期则丢。"""
            nonlocal 飞行#闭包
            if 发出!=世代:#过期
                return#丢
            已移=set(快照['removed'])#拷
            现场={行['pluginId'] for 行 in 行列表 if 'pluginId' in 行}#现场
            for 前 in 快照['rows']:#上一份
                标识=前['pluginId'] if 'pluginId' in 前 else None#id
                if 标识 not in 现场:#消失
                    已移.add(标识)#记
            发布({'rows':行列表,'removed':已移,'read':True})#成功
            if 发出==世代:#本世代
                飞行=None#清槽

        def 失败(错误):#失败
            """保留旧行并说明原因。"""
            nonlocal 飞行#闭包
            if 发出!=世代:#过期
                return#丢
            报错(错误)#报告
            文=str(错误) if 错误 else 'reading the cordis inventory failed'#文本
            发布({#失败快照
                'rows':快照['rows'],'removed':快照['removed'],
                'read':快照['read'],'error':文,
            })#发布
            if 发出==世代:#本世代
                飞行=None#清槽

        原始=端口.inventory()#拉清单
        if hasattr(原始,'等待'):#可等待
            飞行=原始#记下
            def 观察():#观察读取
                """成败分别更新快照。"""
                try:#成功臂
                    成功(原始.等待())#等待
                except BaseException as 错误:#失败臂
                    失败(错误)#失败
            threading.Thread(target=观察,daemon=True).start()#挂观察
        else:#同步
            try:#成功
                飞行=True#占槽
                成功(原始)#成功
            except Exception as 错误:#失败
                飞行=True#占槽
                失败(错误)#失败

    def 退役(插件标识):#退役
        """记下移除并立刻丢掉现场行。"""
        已移=set(快照['removed'])#拷
        已移.add(插件标识)#记
        发布({**快照,'rows':[r for r in 快照['rows'] if not ('pluginId' in r and r['pluginId']==插件标识)],'removed':已移})#发布

    def 重置():#重置
        """作废飞行中读取。"""
        nonlocal 世代,飞行#闭包
        世代+=1#作废
        飞行=None#腾槽
        发布({'rows':[],'removed':快照['removed'],'read':False})#空白

    def 取快照():
        """当前清单快照。"""
        return 快照#快照
    def 订阅(监听器):
        """登记监听，返回取消函数。"""
        监听集合.add(监听器)#登记
        def 取消():
            """去掉监听。"""
            监听集合.discard(监听器)#取消
        return 取消#拆除器
    return {#清单面
        'getSnapshot':取快照,#快照
        'subscribe':订阅,#订阅
        'refresh':刷新,#刷新
        'retire':退役,#退役
        'reset':重置,#重置
    }#结束
