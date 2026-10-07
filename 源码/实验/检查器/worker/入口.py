from .服务器 import 启动检查器Worker#装配并启动

__all__=['主入口']#仅中文公开名

def 主入口(控制端口,启动数据):#主入口
    '在子进程/线程中校验启动数据并装配 Worker'
    if 控制端口 is None:#主线程误载
        raise RuntimeError('实验性检查器：Worker 入口被加载到了主线程')#主线程误载则抛错
    if not isinstance(启动数据,dict) or 'hostSourcePort' not in 启动数据:#启动数据无效
        raise RuntimeError('实验性检查器：Worker 启动数据无效')#启动数据无效
    启动包={#Worker启动包
        'hostSourcePort':启动数据['hostSourcePort'],#Host源端口
        'config':启动数据['config'],#配置（由上层已解析）
    }#boot结束
    运行时=None#已启动的运行时
    已停止=False#首次停止执行，之后直接返回

    def 停止():#停止Worker
        '惰性单次停止。关闭运行时后通知宿主；关闭失败则抛出且不再通知'
        nonlocal 已停止#首次停止时赋值
        if 已停止:#已停
            return#不再拆第二遍
        已停止=True#登记
        if 运行时 is not None:#已启动
            运行时['close']()#关闭运行时，失败直接抛出
        控制端口.postMessage({'type':'stopped'})#通知已停
        控制端口.close()#关闭控制口

    def 收控制(消息):#收到Host控制消息
        '解析并停止'
        try:#解析并停止
            if not isinstance(消息,dict) or 消息.get('type')!='stop':#非法控制
                raise ValueError('宿主控制帧无效')#校验控制帧
            停止()#触发停止，不等待结果
        except Exception as 错误:#控制帧校验或 postMessage 可能抛 ValueError/传输错误，契约未定所以收不窄
            控制端口.postMessage({'type':'failure','message':str(错误)})#回传失败

    控制端口.on('message',收控制)#消息监听
    def 启动():#启动运行时
        '装配并回传就绪'
        nonlocal 运行时#启动成功后赋值
        try:#启动
            运行时=启动检查器Worker(启动包)#装配并启动
            控制端口.postMessage({'type':'ready',**运行时['endpoint']})#就绪
        except Exception as 错误:#启动检查器Worker 装配体什么都可能抛，契约未定所以收不窄
            控制端口.postMessage({'type':'failure','message':str(错误)})#回传失败
            停止()#清理退出，不等待结果
    return 启动#返回启动工厂
