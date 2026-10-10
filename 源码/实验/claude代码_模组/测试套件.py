'测试用的模组套件：加载模组、在引擎底下登记桩、经钩子引发事件、挂上表面看它画什么。不需要会话、智能体或宿主服务'
import os#套件模组的根目录
from .元素 import 查找全部,渲染文本,树问题#表面断言
from .引擎 import 模组引擎,操作被拒错误#加载与拒绝
from .值 import 兑现#桩可以返回期约

__all__=['模拟','创建模组测试套件']

最大安全整数=9007199254740991#套件模组排在所有被测模组里面

默认引擎答案={
    'session.start':lambda 事件:{'cwd':事件['cwd']},#回工作目录
    'session.end':lambda 事件:{'sessionId':事件['sessionId']},#回会话号
    'turn.start':lambda 事件:{'turnId':事件['turnId']},#回回合号
    'turn.complete':lambda 事件:{'text':''},#空文本
    'prompt.submit':lambda 事件:{'text':事件['text'],**({} if 'context' not in 事件 else {'context':事件['context']})},#回文本
    'command.run':lambda 事件:{},#空结果
    'ui.render':lambda 事件:None,#空树
}#没登记桩时，这些引擎事件的默认答案

默认操作答案={
    'ui.invalidate':lambda 美元,事件:{'value':None},#刷新
    'ui.open':lambda 美元,事件:{'value':{'id':事件['id'],'isPlaced':False}},#窗格没摆上
    'ui.close':lambda 美元,事件:{'value':None},#关掉
}#套件自己回答的 $ 调用

def 定义来自(模组):
    '插件对象取 definition，本身就是定义则原样用'
    定义=getattr(模组,'definition',None)#插件
    if isinstance(定义,dict):#有定义
        return 定义#定义
    return 模组#已经是定义

class 模拟:
    '用内存回答一整组 $ 调用'
    @staticmethod
    def 存储(on,初始=None):
        '用一张表回答 $.store。返回这张表，测试可以读模组存了什么'
        已存=dict(初始 or {})#初始条目
        def 读取(美元,事件):
            '按键读。没有则 value 为 None'
            return {'value':已存.get(事件['key'])}#值
        def 写入(美元,事件):
            '按键写'
            已存[事件['key']]=事件.get('value')#记下
            return {'value':None}#无值
        def 删除(美元,事件):
            '按键删'
            已存.pop(事件['key'],None)#删掉
            return {'value':None}#无值
        def 键():
            '全部键'
            return {'value':list(已存)}#键列表
        on('store.get',读取)#读
        on('store.set',写入)#写
        on('store.delete',删除)#删
        on('store.keys',lambda 美元,事件:键())#键
        return 已存#活表

    @staticmethod
    def 环境(on,变量=None):
        '用固定变量回答 $.env.get，并记下 $.env.set。返回这张表'
        环境表=dict(变量 or {})#初始
        def 读取(美元,事件):
            '按名读。没有则 None'
            return {'value':环境表.get(事件['name'])}#值
        def 写入(美元,事件):
            '按名写。可以写成 None'
            环境表[事件['name']]=事件.get('value')#记下
            return {'value':None}#无值
        on('env.get',读取)#读
        on('env.set',写入)#写
        return 环境表#活表

    @staticmethod
    def 时钟(on,起始=0):
        '$.clock.now 读可改的时刻，$.clock.sleep 立刻把时刻往前拨'
        钟={'now':起始}#当前时刻
        def 前进(毫秒):
            '把 now 往前拨'
            钟['now']+=毫秒#拨
        钟['advance']=前进#测试自己拨
        def 现在(美元,事件):
            '读 now'
            return {'value':钟['now']}#时刻
        def 睡眠(美元,事件):
            '睡眠立刻完成，并把时刻拨过这段'
            钟['now']+=事件['ms']#拨
            return {'value':None}#无值
        on('clock.now',现在)#现在
        on('clock.sleep',睡眠)#睡眠
        return 钟#活时钟

def 创建模组测试套件(选项=None):
    '加载模组并返回套件。每份模组的 register 已经跑过'
    if 选项 is None:#没给
        选项={}#空
    报告=[]#引擎记的诊断
    桩表={}#事件名到桩
    绑定={}#测试没有智能体
    信号=None#不取消
    套件模组={'name':'claude-code-testing','version':None,'root':os.getcwd(),'options':{},'order':最大安全整数}#排在最里面，只用来做 $
    def 操作桩(操作,桩):
        '把桩包成引擎行为。桩要返回 { value } 或 { deny }'
        def 核心(输入,上下文):
            '跑桩。拒绝变成操作被拒'
            答案=兑现(桩(引擎.接口(套件模组,None,绑定,信号),输入))#桩的答案
            if not isinstance(答案,dict):#不是对象
                raise RuntimeError(操作+'：桩既没返回 { value } 也没返回 { deny }')#不能用
            if isinstance(答案.get('deny'),str):#拒绝
                raise 操作被拒错误(答案['deny'])#引擎会变成调用失败
            if 'value' not in 答案:#缺 value
                raise RuntimeError(操作+'：桩既没返回 { value } 也没返回 { deny }')#不能用
            return 答案['value']#值，可以是 None
        return 核心#行为
    引擎=模组引擎({
        'ops':lambda 操作:None if (桩表.get(操作) or 默认操作答案.get(操作)) is None else 操作桩(操作,桩表.get(操作) or 默认操作答案[操作]),#桩优先，其次套件默认
        'stateKey':lambda 绑定: 'test',#测试只有一个状态键
        'budgetMs':选项.get('budgetMs',5000),#钩子时限，Claude Code 测试默认 5 秒
        'catchBudgetMs':1000,#catch
        'report':lambda 行:报告.append(行),#收进报告
    })#引擎
    覆盖=选项.get('options') if isinstance(选项.get('options'),dict) else {}#按插件名盖选项
    for 条目 in 选项.get('mods') or []:#按链的顺序加载
        定义=定义来自(条目)#定义
        合并=dict(定义.get('options') or {})#模组自己的
        再盖=覆盖.get(定义['name'])#测试覆盖
        if isinstance(再盖,dict):#有
            合并.update(再盖)#同键以后者为准
        挂上=dict(定义)#拷贝
        挂上['options']=合并#这次的选项
        引擎.添加(挂上)#跑 register
    def 引发(事件,输入):
        '经模组钩子引发。最底是桩、内置默认，或没有实现'
        def 核心(事件值):
            '桩返回事件结果本身。没有桩就用默认表'
            桩=桩表.get(事件)#这个事件的桩
            if 桩 is not None:#有桩
                答案=兑现(桩(引擎.接口(套件模组,None,绑定,信号),事件值))#答案
                if not isinstance(答案,(dict,list)):#null 和标量都不是结果；列表可以是一棵树
                    raise RuntimeError(事件+'：桩没有返回结果')#不能用
                return 答案#结果
            回落=默认引擎答案.get(事件)#内置
            if 回落 is None:#没有
                raise RuntimeError('没有 '+事件+' 的实现')#点名
            return 回落(事件值)#默认
        return 引擎.发起(事件,输入,核心,{'binding':绑定,'signal':信号})#结果
    次数={'n':0}#测试工具调用号
    def 调用工具(输入):
        '发一次 tool.call。没给调用号时用 test-序号，给了就用给的'
        次数['n']+=1#每次都计
        入={'tool_use_id':'test-'+str(次数['n'])}#默认号
        入.update(输入)#调用方可以改号
        return 引发('tool.call',入)#结果
    def 跑命令(输入):
        '发一次 command.run。来源固定是作曲器'
        入=dict(输入)#拷贝
        入['origin']={'kind':'composer'}#固定来源
        return 引发('command.run',入)#结果
    已挂=set()#已经挂上的表面键
    def 绘制(参数):
        '按挂载参数引发 ui.render，树不合法就失败'
        属性=dict(参数.get('props') or {})#宿主会给的属性
        列数=属性['bodyColumns'] if isinstance(属性.get('bodyColumns'),(int,float)) and not isinstance(属性.get('bodyColumns'),bool) else 80#默认 80 列
        入={
            'component':参数['component'],#组件
            'surface':参数['requestId'] if 参数.get('requestId') is not None else 参数['component'],#表面名
            'props':属性,#属性
            'viewport':{'columns':列数},#视口
        }#绘制入参
        if 参数.get('requestId') is not None:#窗格才有
            入['requestId']=参数['requestId']#请求号
        树=引发('ui.render',入)#钩子的树
        问题=树问题(树)#校验
        if 问题 is not None:#不合法
            raise RuntimeError('ui.render 返回的树没通过校验：'+问题)#失败
        return 树#树
    def 挂上元素(元素,重画):
        '一个找到的元素，以及测试对它能做的动作'
        def 按下():
            '跑 Button 的 onPress 并重画'
            回调=元素['props'].get('onPress') if isinstance(元素.get('props'),dict) else None#回调
            if 元素.get('type')!='Button' or not callable(回调):#不是按钮
                raise RuntimeError('按下需要带 onPress 的 Button，不是 '+str(元素.get('type')))#拒绝
            兑现(回调())#跑
            重画()#重画
        return {'element':元素,'type':元素['type'],'text':渲染文本(元素),'press':按下}#元素
    def 挂载(参数):
        '挂上一块表面。每次读取都重新经 ui.render 画'
        键=参数['requestId'] if 参数.get('requestId') is not None else 参数['component']#一块一个键
        if 键 in 已挂:#已经挂过
            raise RuntimeError('表面 '+str(键)+' 已经挂上')#拒绝
        已挂.add(键)#记下
        def 重画():
            '再画一次当前参数'
            return 绘制(参数)#树
        重画()#挂上时先画一次
        def 文本():
            '顶层一行一块'
            return 渲染文本(重画())#文本
        def 查找(图案):
            '第一个符合图案的元素。没有则 None'
            找到=查找全部(重画(),图案)#全部
            if len(找到)==0:#没有
                return None#没有
            return 挂上元素(找到[0],重画)#第一个
        def 查找们(图案):
            '全部符合图案的元素，按绘制顺序'
            return [挂上元素(元素,重画) for 元素 in 查找全部(重画(),图案)]#全部
        def 卸下():
            '卸掉这块表面'
            已挂.discard(键)#去掉
        return {'tree':重画,'text':文本,'find':查找,'findAll':查找们,'unmount':卸下}#表面
    美元={
        'tool':{'call':调用工具},#工具调用
        'command':{'run':跑命令},#命令
        'prompt':{'submit':lambda 输入:引发('prompt.submit',{'wait':False,'origin':{'kind':'composer'},**输入})},#提示
        'session':{
            'start':lambda 输入=None:引发('session.start',{'cwd':os.getcwd(),'surface':None,'isInteractive':True,**(输入 or {})}),#开始
            'end':lambda 输入=None:引发('session.end',{'reason':'other','sessionId':'test',**(输入 or {})}),#结束
        },
        'turn':{
            'start':lambda 输入:引发('turn.start',{'text':'',**输入}),#开始
            'complete':lambda 输入=None:引发('turn.complete',{'turnId':'1','answer':'','durationMs':0,'isAborted':False,'reason':'answer',**(输入 or {})}),#完成
        },
        'ui':{'mount':挂载},#表面
    }#引发器
    def 登记(事件,桩):
        '登记一个桩，回答这个事件，并压在所有模组底下'
        桩表[事件]=桩#后来的盖住先前的
    def 丢弃():
        '卸掉登记并关掉模组定时器'
        引擎.丢弃()#全部
    return 模组测试套件面(登记,引发,美元,报告,lambda:引擎.注册表.列出(),丢弃)#可点属性

class 模组测试套件面:
    '已加载的测试套件'
    def __init__(自身,登记,引发,美元,报告,列出,丢弃):
        '各面在创建时已经接好'
        自身.on=登记#登记桩
        自身.引发=引发#引发任意事件
        自身.美元=美元#分面引发器
        自身.报告=报告#诊断，是同一张表
        自身._列出=列出#读当前模组
        自身.丢弃=丢弃#卸掉登记并关定时器

    @property
    def mods(自身):
        '已加载模组，按链的顺序'
        return 自身._列出()#当前列表
