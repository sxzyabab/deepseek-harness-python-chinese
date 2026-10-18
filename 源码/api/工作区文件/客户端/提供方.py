'file 协议提供方：工作区文件元数据作为 RemoteResult 帧'
from ....工具.工作区路径 import 解析文件地址#dsh-resource://file/ 地址
from ..异常 import 远程错误#客户端地址失败

__all__=['创建文件资源提供方']#仅中文公开名


def 创建文件资源提供方(远程,变更供给):
    '在远程面和变更供给上建造 file 提供方。失败是 ok 为假的帧，不往外抛'
    def 打开(地址,选项):
        '产出元数据帧。地址不是会话文件时先交一帧失败再结束'
        信号=选项['signal']#资源流的中止旗
        解析=解析文件地址(地址)#语法
        if 解析 is None:#不是本协议能认的地址
            yield {'ok':False,'error':远程错误(
                'workspace-file/unsupported-address',
                地址+' is not a dsh-resource://file/session/<sessionId>/<path> or dsh-resource://file/absolute/<path> address',
                {'address':地址},
            )}#失败帧
            return#结束
        if 解析['scope']!='session':#绝对地址没有会话可授权
            yield {'ok':False,'error':远程错误(
                'workspace-file/unknown-workspace',
                地址+' requires a dsh-resource://file/session/<sessionId>/<path> address',
                {'address':地址},
            )}#失败帧
            return#结束
        会话标识=解析['sessionId']#地址里的会话
        路径=解析['path']#原样交给宿主
        通告=变更供给.跟随(会话标识,路径,信号)#stat 挂起期间也排队

        def 已取消():
            '读取中止旗。分开调用，避免一次读取被当成始终未中止'
            return 信号.aborted#流信号

        try:#结束时一定拆除跟随
            if not 通告.就绪():#确认前跟随者已经结束
                if 已取消():#取消
                    return#不读
                结果=远程.workspaceFiles.stat(会话标识,路径,信号)#只读一次
                if not 已取消():#还活着
                    yield 结果#把这一帧交出去
                return#不再跟随
            if 已取消():#就绪后已经取消
                return#不读
            首次=远程.workspaceFiles.stat(会话标识,路径,信号)#第一帧
            if 已取消():#读完时取消
                return#丢掉
            当前=None#上次成功的状态；失败后空着，下次写入再试
            if 首次['ok']:#读到了
                通告.绑定(首次['value']['absolutePath'])#此后只收这个宿主路径
                当前=首次['value']#记下
                yield {'ok':True,'value':当前}#成功帧
            else:#第一帧失败也不结束流
                yield 首次#失败帧
            for 通知 in 通告:#后续变更或刷新
                if 已取消():#取消
                    return#停
                if 当前 is None:#还没有成功状态
                    if 通知['kind']=='absent':#仍旧缺失
                        continue#没有新内容
                elif 通知['kind']=='changed':#版本通知
                    if 通知['version']==当前['version']:#已经拿着这个版本
                        continue#消费方学不到新东西
                再次=远程.workspaceFiles.stat(会话标识,路径,信号)#重新读
                if 已取消():#读完时取消
                    return#丢掉
                if not 再次['ok']:#失败不结束流
                    当前=None#下次写入再试
                    yield 再次#失败帧
                    continue#下一条
                通告.绑定(再次['value']['absolutePath'])#路径可能变
                当前=再次['value']#更新
                yield {'ok':True,'value':当前}#成功帧
        finally:#消费方停下也要注销
            通告.拆除()#离开

    return {'protocol':'file','open':打开}#交给 resources.登记
