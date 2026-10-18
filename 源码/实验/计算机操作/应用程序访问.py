'在原生观察和输入之前核对应用程序同意'
import threading
from ...内核.智能体循环.中止与并发 import 中止控制器,合成信号
from ...交互.用户提问.异常 import 用户提问错误
from .原生客户端 import 原生错误,若已中止则抛出

__all__=['应用程序访问']

class 应用程序访问:
    '拥有应用程序同意，并在保存的访问被去掉时取消操作'

    def __init__(自身,上下文,选项):
        '监听易失配置，并在本纤程拆除时取消同意等待'
        自身._上下文=上下文#宿主上下文
        自身._选项=选项#grants 与可选 save
        自身._客户端={}#原生客户端到已选句柄
        自身._拒绝={}#智能体到被拒绝的身份
        自身._活动=[]#进行中的操作
        自身._选择锁=threading.Lock()#选择表
        自身._选择中={}#同一智能体同一身份串行
        自身._寿命=中止控制器()#整份访问的寿命
        自身._变更锁=threading.Lock()#保存串行
        自身._释放锁=threading.Lock()#释放只做一次
        自身._已释放=False#已经释放
        def 易失更新(*位置参数):
            '保存的许可变了就核对仍在使用的选择'
            自身._调和()#核对
        上下文.监听('loader/volatile-update',易失更新)#易失更新
        def 挂拆除():
            '纤程拆除时释放'
            def 拆除():
                '取消同意等待并等操作结束'
                自身.释放()#释放
            return 拆除#拆除器
        上下文.副作用(挂拆除,'cua-application-access.dispose')#随纤程

    def 释放(自身):
        '取消同意等待，并等到拥有的操作结束'
        with 自身._释放锁:#只开始一次
            if 自身._已释放:#已经在释放
                开始=False#不再开始
            else:#第一次
                自身._已释放=True#记下
                开始=True#这一次负责等
        if not 开始:#后来的调用者也要等到结束
            return#已经有人在等
        自身._寿命.中止()#拒绝新的保存
        自身._变更锁.acquire()#等当前保存结束
        自身._变更锁.release()#不占着锁
        for 操作 in list(自身._活动):#等进行中的操作
            操作['完成'].wait()#结束
        自身._客户端.clear()#丢掉句柄
        自身._拒绝.clear()#丢掉拒绝

    def 选择(自身,智能体,客户端,句柄,身份,信号):
        '为新选出的原生句柄取得同意。自由文本不能授权'
        def 做():
            '在这次操作的寿命里完成选择'
            def 体内(寿命):
                '核对已有选择，否则向人提问'
                若已中止则抛出(寿命)#已取消
                现有=自身._客户端.get(客户端)#这个客户端
                已选=None if 现有 is None else 现有['句柄'].get(句柄)#这个句柄
                if not 客户端.已释放 and 已选 is not None and 自身._允许(已选):#仍然允许
                    return#不用再问
                已保存=身份['persistable'] and any(项['id']==身份['id'] for 项 in 自身._选项['grants']())#长期许可还在
                范围='persistent'#缺省长期
                拒绝表=自身._拒绝.get(id(智能体))#这个任务拒绝过的
                if not 已保存 and 拒绝表 is not None and 身份['id'] in 拒绝表:#这个任务已经拒绝
                    raise 自身._拒绝错误(身份)#不再问
                if 客户端.已释放:#辅助进程已经关了
                    raise 原生错误('NATIVE_CLOSED','Helper is closed; acquire fresh application handles')#换句柄
                if not 已保存:#需要人回答
                    范围=自身._询问(智能体,身份,寿命)#任务或长期
                若已中止则抛出(寿命)#回答期间取消
                if 客户端.已释放:#回答期间辅助进程关了
                    raise 原生错误('NATIVE_CLOSED','Helper is closed; acquire fresh application handles')#换句柄
                状态=自身._客户端.get(客户端)#可能要新建
                if 状态 is None:#这个客户端还没有选择
                    状态={'agent':智能体,'句柄':{}}#新的
                授予={'id':身份['id'],'name':身份['name'],'executablePath':身份['executablePath']}#不保存 persistable
                for 先前,先前状态 in list(自身._客户端.items()):#同一任务换了客户端
                    if 先前状态['agent'] is 智能体 and 先前 is not 客户端:#旧客户端
                        for 选择项 in 先前状态['句柄'].values():#旧句柄
                            选择项['寿命'].中止()#取消
                        del 自身._客户端[先前]#丢掉
                状态['句柄'][句柄]={'identity':授予,'scope':范围,'寿命':中止控制器()}#记下选择
                自身._客户端[客户端]=状态#挂上
                if 拒绝表 is not None:#这次同意了
                    拒绝表.pop(身份['id'],None)#去掉拒绝
            自身._在操作中(智能体,客户端,身份,信号,体内)#包进活动操作
        自身._按序(智能体,身份['id'],做)#同一身份串行

    def 运行(自身,客户端,句柄,信号,派发):
        '在真正发出原生工作时核对仍然有效的同意'
        状态=自身._客户端.get(客户端)#客户端
        已选=None if 状态 is None else 状态['句柄'].get(句柄)#句柄
        if 状态 is None or 已选 is None:#没有选择
            raise 原生错误('APP_ACCESS_REQUIRED','Select the application with getApp and obtain user consent before reading or controlling it')#先选择
        if not 自身._允许(已选):#许可没了
            if not 已选['寿命'].信号.is_set():#还没标记取消
                自身._作废(已选['identity']['id'],状态['agent'])#作废
            raise 原生错误('APP_ACCESS_REVOKED','Application access was revoked; stop using this application')#停止使用
        if 客户端.已释放:#辅助进程关了
            raise 原生错误('NATIVE_CLOSED','Helper is closed; acquire fresh application handles')#换句柄
        寿命=合成信号(信号,已选['寿命'].信号)#调用方或撤销
        return 自身._在操作中(状态['agent'],客户端,已选['identity'],寿命,派发)#一次操作

    def 忘记(自身,智能体):
        '丢掉已拆除任务的临时决定和已选句柄'
        for 客户端,状态 in list(自身._客户端.items()):#逐个客户端
            if 状态['agent'] is 智能体:#这个任务的
                del 自身._客户端[客户端]#丢掉
        自身._拒绝.pop(id(智能体),None)#丢掉拒绝

    def _按序(自身,智能体,标识,选择):
        '同一个任务对同一个应用程序的选择排成一队'
        with 自身._选择锁:#建锁
            表=自身._选择中.get(id(智能体))#这个任务
            if 表 is None:#第一次
                表={}#新表
                自身._选择中[id(智能体)]=表#挂上
            锁=表.get(标识)#这个身份
            if 锁 is None:#第一次
                锁=threading.Lock()#新锁
                表[标识]=锁#挂上
        with 锁:#串行，失败也占用到结束
            选择()#执行

    def _在操作中(自身,智能体,客户端,身份,信号,派发):
        '登记活动操作。撤销会中止交给派发的信号'
        控制器=中止控制器()#这次操作自己的取消
        操作={'agent':智能体,'client':客户端,'identity':身份,'controller':控制器,'完成':threading.Event()}#活动记录
        自身._活动.append(操作)#登记
        寿命=合成信号(信号,自身._寿命.信号,控制器.信号)#三路任一中止
        try:#执行
            若已中止则抛出(寿命)#已取消
            结果=派发(寿命)#一次原生工作
            若已中止则抛出(寿命)#返回前又取消
            return 结果#结果
        finally:#无论成败都结束
            if 操作 in 自身._活动:#还在
                自身._活动.remove(操作)#摘掉
            操作['完成'].set()#等释放的人可以走

    def _询问(自身,智能体,身份,信号):
        '向人要同意。返回 task 或 persistent'
        提问=自身._上下文.获取服务('userQuestions',False)#提问服务
        if 提问 is None:#没有人回答
            raise 原生错误('APP_APPROVAL_UNAVAILABLE','No human answerer is available for application access')#不能授权
        选项=[{'label':'Allow for this task'},{'label':'Deny'}]#任务或拒绝
        保存=自身._写入器()#每次重新看设置里有没有这一条
        if 身份['persistable'] and 保存 is not None:#可以长期保存
            选项.append({'label':'Always allow'})#长期
        问题='Allow Computer Use to launch if needed, read, capture, and control '+身份['name']+'?'#问题
        细节='Application: '+身份['executablePath']+'\nTask access applies to the selected application instance, including its launch if needed. macOS permissions and approval of sensitive actions remain separate. Saved access can be revoked by removing its allowedApps entry from this provider configuration. Task access ends with the task.'#细节
        try:#等待回答
            结果=等到(提问.ask(提问请求(智能体,信号,问题,细节,选项)))#回答
        except 用户提问错误 as 错误:#提问通道的失败
            if 错误.code=='ASK_CANCELLED':#人取消了
                自身._作废(身份['id'],智能体)#记成拒绝
                raise 自身._拒绝错误(身份)#拒绝
            if 错误.code=='DELEGATED_CALLER':#委托任务没有人
                raise 原生错误('APP_APPROVAL_UNAVAILABLE','Application approval is unavailable in delegated tasks; ask the main task to perform this operation')#让主任务做
            raise#其余原样抛
        若已中止则抛出(信号)#回答后取消
        答案=None#这一题
        for 项 in 结果.answers if hasattr(结果,'answers') else 结果['answers']:#找这一题
            if 项['id']=='cua-app-access':#对上
                答案=项#记下
                break#停
        自定义=''#自由文本
        已选=[]#选中的标签
        if 答案 is not None:#有答案
            自定义=答案['custom'] if 'custom' in 答案 and 答案['custom'] is not None else ''#自由文本
            已选=答案['selected'] if 'selected' in 答案 and 答案['selected'] is not None else []#选中
        选中=已选[0] if 自定义.strip()=='' and len(已选)==1 else None#只有唯一选项才算
        if 选中=='Allow for this task':#只这一次
            return 'task'#任务范围
        if 选中=='Always allow' and 身份['persistable'] and 保存 is not None:#长期
            授予={'id':身份['id'],'name':身份['name'],'executablePath':身份['executablePath']}#不写 persistable
            def 更新(现有):
                '换掉同一身份的旧记录'
                若已中止则抛出(信号)#保存前取消
                return [项 for 项 in 现有 if 项['id']!=身份['id']]+[授予]#新列表
            自身._持久化(更新)#写入
            return 'persistent'#长期
        自身._作废(身份['id'],智能体)#拒绝或其他回答
        raise 自身._拒绝错误(身份)#拒绝

    def _允许(自身,选择):
        '任务范围只看这次寿命；长期范围还要仍在保存的许可里'
        if 选择['寿命'].信号.is_set():#已经取消
            return False#不允许
        if 选择['scope']=='task':#任务范围
            return True#还在
        return any(项['id']==选择['identity']['id'] for 项 in 自身._选项['grants']())#长期许可还在

    def _拒绝错误(自身,身份):
        '人拒绝之后不能重试，也不能换工具绕过'
        return 原生错误('APP_ACCESS_DENIED','The user denied access to '+身份['name']+'. Do not retry or use another tool to bypass this decision.')#拒绝

    def _记下拒绝(自身,智能体,身份):
        '这个任务对这个身份的拒绝留到任务结束'
        表=自身._拒绝.get(id(智能体))#已有
        if 表 is None:#第一次
            表={}#新表
            自身._拒绝[id(智能体)]=表#挂上
        表[身份['id']]={'id':身份['id'],'name':身份['name'],'executablePath':身份['executablePath']}#只留展示字段

    def _作废(自身,标识,智能体=None):
        '取消这个身份上还在进行的选择和操作，并让原生句柄失效'
        客户端们=[]#要作废的客户端
        for 客户端,状态 in list(自身._客户端.items()):#逐个选择
            for 选择项 in 状态['句柄'].values():#逐个句柄
                if 选择项['identity']['id']!=标识:#不是这个身份
                    continue#跳过
                if 智能体 is not None and 状态['agent'] is not 智能体:#限定任务
                    continue#跳过
                选择项['寿命'].中止(原生错误('APP_ACCESS_REVOKED','Application access was revoked; stop using this application'))#取消选择
                自身._记下拒绝(状态['agent'],选择项['identity'])#记下拒绝
                if 客户端 not in 客户端们:#每个客户端一次
                    客户端们.append(客户端)#要作废
        for 操作 in list(自身._活动):#进行中的操作
            if 操作['identity']['id']!=标识:#不是这个身份
                continue#跳过
            if 智能体 is not None and 操作['agent'] is not 智能体:#限定任务
                continue#跳过
            自身._记下拒绝(操作['agent'],操作['identity'])#记下拒绝
            操作['controller'].中止(自身._拒绝错误(操作['identity']))#用拒绝错误取消操作
            if 操作['client'] not in 客户端们:#客户端
                客户端们.append(操作['client'])#要作废
        for 客户端 in 客户端们:#句柄失效
            客户端.作废()#关闭这条连接上的句柄

    def _调和(自身):
        '长期许可从配置里消失时取消仍在使用的选择'
        for 状态 in list(自身._客户端.values()):#逐个客户端
            for 选择项 in list(状态['句柄'].values()):#逐个选择
                if not 选择项['寿命'].信号.is_set() and not 自身._允许(选择项):#配置里没了
                    自身._作废(选择项['identity']['id'])#不限定任务

    def _写入器(自身):
        'save 是零参数函数，返回当前的写入器或空'
        提供=自身._选项.get('save')#提供函数
        if 提供 is None:#这个组合没有保存
            return None#不能长期授权
        return 提供()#当前写入器

    def _持久化(自身,更新):
        '串行保存。没有写入器就失败'
        with 自身._变更锁:#串行
            若已中止则抛出(自身._寿命.信号)#已经释放
            保存=自身._写入器()#写入器
            if 保存 is None:#这个组合不能保存
                raise Exception('Application permissions cannot be saved in this composition')#失败
            等到(保存(更新(自身._选项['grants']())))#写入当前许可

def 提问请求(智能体,信号,问题,细节,选项):
    '组装用户提问服务要的请求对象'
    from ...交互.用户提问 import 询问用户问题请求#避免循环引用时提前加载
    return 询问用户问题请求([{#一题
        'id':'cua-app-access',#稳定题号
        'question':问题,#问题
        'detail':细节,#应用程序路径和范围说明
        'options':选项,#选项
    }],智能体,信号)#智能体和取消信号

def 等到(值):
    '同步结果原样返回。期约则阻塞到结算'
    然后=getattr(值,'然后',None)#期约
    if not callable(然后):#不是期约
        return 值#原样
    完成=threading.Event()#结算
    盒子={}#结果
    def 成功(结果=None):
        '兑现'
        盒子['值']=结果#值
        完成.set()#唤醒
    def 失败(错误=None):
        '拒绝'
        盒子['错误']=错误#错误
        完成.set()#唤醒
    然后(成功,失败)#接上
    完成.wait()#阻塞
    if '错误' in 盒子 and 盒子['错误'] is not None:#失败
        错误=盒子['错误']#错误
        if isinstance(错误,BaseException):#异常
            raise 错误#抛出
        raise RuntimeError(str(错误))#包成异常
    return 盒子.get('值')#成功值
