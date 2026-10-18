from ...模块.客户端.通告 import 取握手窗口
import pywebbridge#浏览器节点
from ...ui_槽位.异常 import 过期授权错误,槽位所有权错误#过期与所有权
from ..异常 import 槽组装错误#装配失败要穿透边界
from .登记表 import 标准钩子属性名#钩子座位名
from .绑定 import (#宿主与作用域栈
    宿主栈,根绑定栈,作用域绑定栈,根标准提供者,作用域提供者,
    键控可观察钩子,可缺席可观察钩子,可观察钩子,用宿主,用根绑定,用作用域绑定,
)#绑定结束

__all__=['创建槽渲染器','槽错误边界','工厂错误边界','槽出口','根出口','槽渲染器','取出口','标记已连接']#仅中文公开名

空注入属性={}#没有 inject 时的空份额
空槽注入={'props':空注入属性}#没有调度注入
出口表={}#节点身份到出口，页面对象上不挂 Python
在册=[]#尚未拆除的出口
出口栈=[]#正在画的出口
工厂帧栈=[]#正在画的工厂出现
工厂槽缓存={}#调用方到工厂渲染函数
根注入缓存={}#根 inject
会话注入缓存={}#会话 inject
可选会话注入缓存={}#可选会话 inject
槽注入缓存={}#调度方 inject
文案座位缓存={}#locale 座位
根标准缓存={}#根标准座位
会话标准缓存={}#会话标准座位
可选标准缓存={}#可选会话标准座位
作用域区域缓存={}#适配器到 SessionProvider
会话世代表={}#Context 身份到世代
下一会话世代=[0]#世代序号
提供者状态={}#子节点身份到会话提供者


def 读(对象,名):
    '字典走键，对象走属性'
    if isinstance(对象,dict):#字典
        if 名 in 对象:#有键
            return 对象[名]#值
        return None#缺席
    return getattr(对象,名,None)#属性


def 取快照(源):
    '读可观察源的当前快照'
    读快照=读(源,'getSnapshot')#读取函数
    return 读快照()#快照


def 订上(退订表,退):
    '只留下真正的退订函数'
    if callable(退):#有退订
        退订表.append(退)#记下


def 取文档(拥有方):
    '优先用调用方窗口，否则用桥上的窗口'
    窗口=None#窗口
    if isinstance(拥有方,dict) and 'window' in 拥有方:#份额里带了窗口
        窗口=拥有方['window']#调用方窗口
    if 窗口 is None:#没有单独窗口
        窗口=取握手窗口()#当前页
    return 窗口.document#文档


def 是页面节点(值):
    '桥上的页面对象。不读实例属性，避免打到页面'
    if 值 is None or isinstance(值,(str,int,float,bool,dict,list,tuple)):#普通值
        return False#不是节点
    模块=getattr(type(值),'__module__','')#类所在模块
    if isinstance(模块,str) is False:#没有模块名
        return False#不是
    return 模块.startswith('pywebbridge')#桥对象


def 取根(值):
    '页面节点用自身，界面实例用它的根'
    if 是页面节点(值):#已经是节点
        return 值#自身
    if 值 is None or isinstance(值,(str,int,float,bool,dict,list,tuple)):#没有根
        return None#无
    根=getattr(值,'根',None)#实例上的根
    if 是页面节点(根):#根是节点
        return 根#根
    return None#没有节点


def 取出口(节点):
    '按节点身份找回出口'
    if 是页面节点(节点) is False:#不是节点
        return None#无
    return 出口表.get(id(节点))#出口


def 记下出口(节点,出口):
    '记下节点与出口的对应'
    if 是页面节点(节点):#是节点
        出口表[id(节点)]=出口#写入


def 忘掉出口(节点):
    '卸下后不再按这个节点找回'
    if 是页面节点(节点):#是节点
        出口表.pop(id(节点),None)#去掉


def 挂进(父,结果):
    '把结果的节点放进父节点。已经在里面就不动'
    if 父 is None or 结果 is None:#无处可挂
        return#跳过
    if isinstance(结果,(list,tuple)):#多段
        for 项 in 结果:#逐段
            挂进(父,项)#挂上
        return#完
    根=取根(结果)#要挂的节点
    if 根 is None:#没有节点
        return#跳过
    if getattr(根,'parentNode',None) is not 父:#还不在这个父下
        父.appendChild(根)#挂上，片段会交出子节点


def 拆除对象(值):
    '有拆除方法就调用。页面节点改走它的出口'
    if 值 is None or isinstance(值,(str,int,float,bool)):#没有实例
        return#跳过
    if isinstance(值,(list,tuple)):#一组
        for 项 in 值:#逐个
            拆除对象(项)#拆除
        return#完
    if 是页面节点(值):#节点
        出口=取出口(值)#出口
        if 出口 is not None:#有出口
            出口.拆除()#卸下出口
        return#完
    拆=getattr(值,'拆除',None)#实例拆除
    if callable(拆):#有拆除
        拆()#调用


def 拆除后代出口(节点):
    '先拆子树里的出口，再拆这个节点自己的出口'
    if 是页面节点(节点) is False:#不是节点
        return#跳过
    待=[]#子节点
    子=getattr(节点,'firstChild',None)#第一个
    while 子 is not None:#还有
        待.append(子)#记下
        子=getattr(子,'nextSibling',None)#下一个
    for 项 in 待:#先走子树
        拆除后代出口(项)#递归
    出口=取出口(节点)#自身出口
    if 出口 is not None:#有
        出口.拆除()#卸下


def 标记已连接(节点):
    '已经进页面的出口记下，之后被摘掉才能拆除'
    if 是页面节点(节点) is False:#不是节点
        return#跳过
    出口=取出口(节点)#出口
    if 出口 is not None and getattr(节点,'isConnected',None) is True:#在页面上
        出口.曾连接=True#曾挂进页面
    子=getattr(节点,'firstChild',None)#子
    while 子 is not None:#逐子
        标记已连接(子)#递归
        子=getattr(子,'nextSibling',None)#下一个


def 登记出口(出口):
    '新出口入册。曾经进页面、现在已被摘掉的旧出口在这里拆除'
    留=[]#还留着的
    for 旧 in 在册:#已有出口
        if 旧.已拆:#已经卸过
            continue#丢掉
        if 旧.绘制中:#正在画，还没交给父级
            留.append(旧)#留
            continue#下一个
        盒=旧.盒#节点
        try:#旧页面的节点读不到，不能把这次挂载带崩
            摘掉了=旧.曾连接 and 盒 is not None and getattr(盒,'isConnected',None) is False
        except Exception:#连接已经断了
            旧.已拆=True#不再拆它
            continue#丢掉
        if 摘掉了:#已经不在文档里
            旧.拆除()#卸下并调用拆除
            continue#不留
        留.append(旧)#仍在
    留.append(出口)#新的
    在册.clear()#换名单
    在册.extend(留)#写回


def 建盒(文档,标签,属性名,属性值,显示):
    '创建一个带数据属性和显示方式的元素'
    盒=文档.createElement(标签)#元素
    盒.setAttribute(属性名,属性值)#数据属性
    盒.style.display=显示#显示方式
    return 盒#元素


def 锚标签(规格,声明内联):
    '内联槽用 span，其余用 div。规格卸掉后沿用声明'
    if 规格 is None:#没有活规格
        if 声明内联 is True:#声明为内联
            return 'span'#内联
        return 'div'#块
    if isinstance(规格,dict) and 规格.get('inline') is True:#活规格内联
        return 'span'#内联
    return 'div'#块


def 补画未处理(节点):
    '组件返回后，把还没画内容、也没交给提供者的包裹画上'
    if 是页面节点(节点) is False:#不是节点
        return#跳过
    出口=取出口(节点)#出口
    if 出口 is not None and 出口.已画 is False and 出口.已拆 is False:#还是空包裹
        出口.重画()#按当前绑定画
    子=getattr(节点,'firstChild',None)#子
    while 子 is not None:#逐子
        下=getattr(子,'nextSibling',None)#先记下，重画可能改兄弟
        补画未处理(子)#递归
        子=下#下一个


def 呈现(出口,标识,组件,属性):
    '同一条目同一世代复用实例并重画。换了就新建'
    已=出口.实例表.get(标识)#已有实例
    出口.本轮.add(标识)#这一轮还要
    if 已 is not None and isinstance(组件,type):#类实例还在
        更新=getattr(已,'更新',None)#更新份额
        if callable(更新):#有更新
            更新(属性)#换份额
        elif hasattr(已,'属性'):#直接写
            已.属性=属性#份额
        画=getattr(已,'渲染',None)#重画
        if callable(画):#有渲染
            画()#重画
        补画未处理(取根(已))#补上新包裹
        return 已#原实例
    if 已 is not None:#函数结果换新
        拆除对象(已)#卸下旧结果
    if isinstance(组件,type):#类
        实例=组件(属性)#构造
    else:#函数
        实例=组件(属性)#调用
    出口.实例表[标识]=实例#记下
    补画未处理(取根(实例))#补上包裹
    return 实例#实例或节点


def 化身代数(出口,条目,绑定):
    '可选会话只在第一次出现时收养，换代或回到空会话才加代数'
    状态=出口.化身表.get(id(条目))#这条的化身
    if 状态 is None:#还没有
        状态={'adopted':None,'epoch':0}#首化身
    身份=None#当前 Context
    if isinstance(绑定,dict) and 绑定.get('key') is not None:#有会话
        身份=绑定.get('ctx')#用 Context，不用会话号
    收养=状态['adopted']#已收养
    代数=状态['epoch']#代数
    if 身份 is not None and 收养 is None:#第一次出现
        收养=身份#收养
    elif 收养 is not None and 身份 is not None and 身份 is not 收养:#换成另一代
        收养=身份#新代
        代数=代数+1#重挂
    elif 收养 is not None and 身份 is None:#回到没有会话
        收养=None#清空
        代数=代数+1#重挂
    状态={'adopted':收养,'epoch':代数}#写回
    出口.化身表[id(条目)]=状态#按条目
    return 代数#子键


def 会话世代键(绑定):
    '同一 Context 世代不变。同号新 Context 换世代'
    上下文=绑定.get('ctx') if isinstance(绑定,dict) else None#Context
    if 上下文 is None:#没有
        上下文=绑定#退回绑定自身
    标识=id(上下文)#身份
    键=会话世代表.get(标识)#已有世代
    if 键 is None:#新 Context
        键=下一会话世代[0]#当前号
        下一会话世代[0]=键+1#下一个
        会话世代表[标识]=键#记下
    return 键#世代


def 执行注入(条目,绑定,动作):
    '按声明把会话键和动作传给 inject'
    if isinstance(条目,dict) is False or 条目.get('inject') is None:#没有工厂
        return 空注入属性#空
    参数=[]#位置参数
    if 绑定 is not None:#有绑定
        参数.append(绑定.get('key') if isinstance(绑定,dict) else None)#会话键
    if 动作 is not None:#有动作
        参数.append(动作)#store 动作
    return 绑定注入源(条目['inject'](*参数))#绑成钩子


def 绑定注入源(面):
    'hooks 与 keyedHooks 变成座位，其余原样留下'
    if isinstance(面,dict) is False:#不是份额
        return 空注入属性#空
    源表=面.get('hooks')#普通源
    键控源=面.get('keyedHooks')#键控源
    if 源表 is None and 键控源 is None:#没有源
        return 面#原样
    绑定={}#剩下的份额
    for 键,值 in 面.items():#逐项
        if 键 not in ('hooks','keyedHooks'):#不是源表
            绑定[键]=值#留下
    if isinstance(源表,dict):#有普通源
        for 名称,源 in 源表.items():#逐源
            绑定[标准钩子属性名(名称)]=可观察钩子(源)#座位
    if isinstance(键控源,dict):#有键控源
        for 名称,源 in 键控源.items():#逐族
            绑定[标准钩子属性名(名称)]=键控可观察钩子(源)#键控座位
    return 绑定#座位


def 缓存槽注入(面):
    '按注入对象身份缓存。函数型钩子留到出现点再绑'
    if 面 is None:#没有
        return 空槽注入#空
    键=id(面)#身份
    已=槽注入缓存.get(键)#缓存
    if 已 is not None:#命中
        return 已#返回
    if isinstance(面,dict) is False:#不是字典
        已={'props':{}}#空
        槽注入缓存[键]=已#写入
        return 已#返回
    定义=面.get('hooks')#钩子定义
    if 定义 is None:#没有钩子
        已={'props':面}#整份当份额
        槽注入缓存[键]=已#写入
        return 已#返回
    属性={}#普通份额
    for 键名,值 in 面.items():#逐项
        if 键名!='hooks':#不是钩子表
            属性[键名]=值#留下
    工厂表=None#延迟工厂
    if isinstance(定义,dict):#有定义
        for 名称,定义项 in 定义.items():#逐钩子
            if callable(定义项):#延迟工厂
                if 工厂表 is None:#先建表
                    工厂表={}#表
                工厂表[名称]=定义项#工厂
            else:#可观察源
                属性[标准钩子属性名(名称)]=可观察钩子(定义项)#座位
    if 工厂表 is None:#没有延迟工厂
        已={'props':属性}#只有份额
    else:#有延迟工厂
        已={'props':属性,'slotHookFactories':工厂表}#一并缓存
    槽注入缓存[键]=已#写入
    return 已#返回


def 缓存根注入(条目,动作):
    '根条目的 inject 按条目缓存'
    键=id(条目)#条目
    属性=根注入缓存.get(键)#缓存
    if 属性 is None:#未命中
        属性=执行注入(条目,None,动作)#无会话键
        根注入缓存[键]=属性#写入
    return 属性#份额


def 缓存会话注入(条目,绑定,动作):
    '严格会话按条目和绑定缓存'
    外=会话注入缓存.get(id(条目))#按条目
    if 外 is None:#未建
        外={}#内表
        会话注入缓存[id(条目)]=外#写入
    内键=id(绑定)#绑定身份
    属性=外.get(内键)#缓存
    if 属性 is None:#未命中
        属性=执行注入(条目,绑定,动作)#带会话键
        外[内键]=属性#写入
    return 属性#份额


def 缓存可选会话注入(条目,绑定,动作):
    '可选会话按条目和绑定缓存'
    外=可选会话注入缓存.get(id(条目))#按条目
    if 外 is None:#未建
        外={}#内表
        可选会话注入缓存[id(条目)]=外#写入
    内键=id(绑定)#绑定身份
    属性=外.get(内键)#缓存
    if 属性 is None:#未命中
        属性=执行注入(条目,绑定,动作)#带会话键
        外[内键]=属性#写入
    return 属性#份额


def 文案座位(面,命名空间):
    '同一修订复用翻译函数。修订变了就换一个新函数'
    按面=文案座位缓存.get(id(面))#按面
    if 按面 is None:#未建
        按面={}#按命名空间
        文案座位缓存[id(面)]=按面#写入
    快照=取快照(面)#当前修订
    修订=快照.get('revision') if isinstance(快照,dict) else None#修订号
    缓存=按面.get(命名空间)#已有
    if 缓存 is not None and 缓存['revision']==修订:#同一修订
        return 缓存['t']#复用
    绑定=面.bind(命名空间)#命名空间翻译

    def 翻译(键,参数=None):
        '这一修订的翻译函数'
        return 绑定(键,参数)#译

    按面[命名空间]={'revision':修订,'t':翻译}#写入
    return 翻译#函数


def 物化标准绑定(绑定,可选,默认键=None):
    '把标准源变成座位。键控钩子带上默认键'
    属性=绑定.get('props') if isinstance(绑定,dict) and isinstance(绑定.get('props'),dict) else {}#普通份额
    标准=dict(属性)#拷贝
    钩子表=绑定.get('hooks') if isinstance(绑定,dict) and isinstance(绑定.get('hooks'),dict) else {}#普通源
    for 名称,源 in 钩子表.items():#逐钩子
        if 源 is None and 可选 is False:#严格缺源
            raise 槽组装错误("strict standard hook '"+str(名称)+"' has no source")#装配失败
        if 可选 is True:#允许缺席
            标准[标准钩子属性名(名称)]=可缺席可观察钩子(源)#可缺席
        else:#必须有源
            标准[标准钩子属性名(名称)]=可观察钩子(源)#普通钩子
    键控表=绑定.get('keyedHooks') if isinstance(绑定,dict) and isinstance(绑定.get('keyedHooks'),dict) else {}#键控源
    for 名称,源 in 键控表.items():#逐族
        if 源 is None and 可选 is False:#严格缺解析器
            raise 槽组装错误("strict keyed standard hook '"+str(名称)+"' has no source resolver")#装配失败
        标准[标准钩子属性名(名称)]=键控可观察钩子(源,默认键)#带默认键
    return 标准#座位


def 标准属性(作用域,根绑定,作用域绑定):
    '根座位与作用域座位。作用域里的根键控钩子用当前键当默认键'
    根键=id(根绑定)#根身份
    根=根标准缓存.get(根键)#根缓存
    if 根 is None:#未物化
        根=物化标准绑定(根绑定,False)#没有默认键
        根标准缓存[根键]=根#写入
    if 作用域=='root':#只需要根
        return 根#根座位
    if 作用域绑定 is None:#缺绑定
        raise 槽组装错误("scope '"+str(作用域)+"' rendered without a standard-source binding")#装配失败
    缓存轴=会话标准缓存 if 作用域=='session' else 可选标准缓存#按作用域分轴
    按根=缓存轴.get(根键)#这一根下的作用域
    if 按根 is None:#未建
        按根={}#表
        缓存轴[根键]=按根#写入
    域键=id(作用域绑定)#绑定身份
    标准=按根.get(域键)#缓存
    if 标准 is not None:#命中
        return 标准#座位
    默认键=作用域绑定.get('key') if isinstance(作用域绑定,dict) else None#当前会话键
    标准={}#合并
    标准.update(物化标准绑定(根绑定,False,默认键))#根钩子带默认键
    标准.update(物化标准绑定(作用域绑定,作用域=='session-maybe'))#作用域覆盖
    按根[域键]=标准#写入
    return 标准#座位


def 拒绝重叠(主人,已有,收到):
    '后来的份额不能盖住已经发给组件的名字'
    if isinstance(收到,dict) is False:#没有键
        return#跳过
    for 名 in 收到:#逐个名字
        if 名 in 已有:#重名
            raise 槽组装错误(主人+" received duplicate prop '"+str(名)+"'")#装配失败


def 绑定子槽(宿主,主人,是工厂):
    '返回这一主人的 renderSlot 与 renderSlotChain'
    def 活着():
        '主人是否还在台账上'
        if 是工厂:#工厂
            return 宿主.isFactoryLive(主人)#工厂还在
        return 宿主.isLive(主人)#条目还在

    def 渲染子(子键,拥有方,选项,链):
        '检查声明后交出 data-slot 包裹'
        if 活着() is False:#已经卸下
            接口名='renderSlotChain' if 链 else 'renderSlot'#接口名
            if 是工厂:#工厂已卸
                raise 过期授权错误(接口名+"('"+str(子键)+"') from a disposed Factory")#过期
            raise 过期授权错误(接口名+"('"+str(子键)+"') from a disposed registration")#过期
        子表=主人.get('children') if isinstance(主人,dict) else None#子声明
        声明=子表.get(子键) if isinstance(子表,dict) else None#这一格
        if 声明 is None:#没声明
            if 是工厂:#工厂
                raise 槽位所有权错误("slot '"+str(子键)+"' is not declared by this Factory")#所有权
            raise 槽位所有权错误("slot '"+str(子键)+"' is not declared by this entry's children")#所有权
        种类=声明.get('kind') if isinstance(声明,dict) else None#种类
        if 链 is False and 种类=='chain':#普通接口不能画链
            raise 槽位所有权错误("slot '"+str(子键)+"' is declared 'chain' — use renderSlotChain")#用链接口
        if 链 is True and 种类!='chain':#链接口只能画链
            raise 槽位所有权错误("slot '"+str(子键)+"' is declared '"+str(种类)+"', not 'chain' — use renderSlot")#用普通接口
        内联=isinstance(声明,dict) and 声明.get('inline') is True#内联锚点
        出口=槽出口(子键,拥有方 if isinstance(拥有方,dict) else {},选项,内联)#新包裹
        return 出口.渲染()#返回包裹元素

    def 渲染槽(子键,拥有方,选项=None):
        '普通子槽'
        return 渲染子(子键,拥有方,选项,False)#非链

    def 渲染链(子键,拥有方,选项=None):
        '链子槽'
        return 渲染子(子键,拥有方,选项,True)#链

    return 渲染槽,渲染链#两个座位


def 子槽座位(宿主,主人,是工厂,包):
    '有子声明才放 renderSlot。含链或非根子槽时再加对应座位'
    子表=主人.get('children') if isinstance(主人,dict) else None#子声明
    if isinstance(子表,dict) is False:#没有子槽
        return#不加
    渲染槽,渲染链=绑定子槽(宿主,主人,是工厂)#绑定
    包['renderSlot']=渲染槽#普通座位
    有链=False#是否有链
    有会话=False#是否有非根子槽
    for 规格 in 子表.values():#逐个声明
        if isinstance(规格,dict) is False:#跳过坏声明
            continue#下一个
        if 规格.get('kind')=='chain':#链
            有链=True#要链座位
        if 规格.get('scope')!='root':#会话或可选会话
            有会话=True#要 SessionProvider
    if 有链:#有链
        包['renderSlotChain']=渲染链#链座位
    if 有会话:#有会话子槽
        适配器=宿主.scope('session')#会话适配器
        if 适配器 is None:#没安装
            if 是工厂:#工厂
                raise 槽组装错误("factory declares a session child without an installed 'session' scope adapter")#装配失败
            raise 槽组装错误("entry declares a session child without an installed 'session' scope adapter")#装配失败
        包['SessionProvider']=作用域区域提供者(适配器)#按传入 session 换绑定


def 放入文案(宿主,主人,包,是工厂):
    '声明了 locale 才放 t'
    文案名=主人.get('locale') if isinstance(主人,dict) else None#命名空间
    if 文案名 is None:#没声明
        return#不加
    面=宿主.locale()#已安装的面
    if 面 is None:#没安装
        if 是工厂:#工厂
            raise 槽组装错误("factory declares locale namespace '"+str(文案名)+"' but no locale face is installed")#装配失败
        raise 槽组装错误("entry declares locale namespace '"+str(文案名)+"' but no locale face is installed (locale plugin missing from the composition?)")#装配失败
    包['t']=文案座位(面,文案名)#翻译座位


def 作用域区域提供者(适配器):
    '每个适配器一个 SessionProvider。调用时按 session 换绑定'
    键=id(适配器)#适配器身份
    已有=作用域区域缓存.get(键)#缓存的调用函数
    if 已有 is not None:#已建
        return 已有#复用
    渲区=读(适配器,'renderArea')#区域渲染
    if callable(渲区) is False:#没有
        raise 槽组装错误("scope 'session' adapter does not provide its area renderer")#装配失败

    def 区域提供者组件(属性):
        '按这一次的子节点找回或建立提供者'
        子=属性.get('children') if isinstance(属性,dict) else None#子节点
        状态键=id(子) if 子 is not None else id(属性)#这一次的身份
        状态=提供者状态.get(状态键)#已有状态
        if 状态 is None or 状态.已拆:#新建
            状态=会话提供者(适配器,渲区)#一份状态
            提供者状态[状态键]=状态#记下
        return 状态.渲染(属性)#换绑定后画出

    作用域区域缓存[键]=区域提供者组件#按适配器缓存
    return 区域提供者组件#座位


class 会话提供者:
    'SessionProvider。传入 session 时改用那份绑定，卸下时退订'
    def __init__(自身,适配器,渲区):
        '记下适配器和区域渲染'
        自身.适配器=适配器#作用域适配器
        自身.渲区=渲区#区域渲染
        自身.退订=None#绑定源退订
        自身.源=None#当前绑定源
        自身.属性=None#上次份额
        自身.绑定=None#当前绑定
        自身.已拆=False#是否已卸
        自身.绘制中=False#防止订阅重入
        自身.上次=None#上次返回

    def 改订(自身,源):
        '绑定源换了才重新订阅'
        if 自身.源 is 源:#没换
            return#沿用
        if callable(自身.退订):#退掉旧的
            自身.退订()#退订
        自身.退订=None#清空
        自身.源=源#新源
        if 源 is None:#不再订阅
            return#完
        订=读(源,'subscribe')#订阅函数
        if callable(订) is False:#没有订阅
            return#完

        def 变更():
            '快照变了就按原份额再画'
            if 自身.已拆 or 自身.绘制中 or 自身.属性 is None:#不能重入
                return#跳过
            自身.渲染(自身.属性)#再画

        自身.退订=订(变更)#订上

    def 渲染(自身,属性):
        '有 session 键就用 bindingSource 的快照，否则沿用外层绑定'
        if 自身.绘制中:#重入
            return 自身.上次#上次结果
        自身.绘制中=True#占用
        自身.属性=属性#记下
        try:#画完一定放开
            显式=isinstance(属性,dict) and 'session' in 属性#调用方传入了 session
            if 显式:#按传入的会话换绑定
                取源=读(自身.适配器,'bindingSource')#解析函数
                源=取源(属性.get('session'))#这一会话或显式空会话
                绑定=取快照(源)#当前绑定
                自身.改订(源)#快照变化后再画
            else:#沿用外层
                绑定=用作用域绑定()#外层绑定
                自身.改订(None)#不另订
            自身.绑定=绑定#记下
            子=属性.get('children') if isinstance(属性,dict) else None#子节点
            出口=取出口(子)#子包裹
            作用域绑定栈.append(绑定)#子树看到这份绑定
            try:#区域渲染不负责挂载子槽
                结果=自身.渲区(绑定,属性)#空会话走 empty，有会话返回子节点
            finally:#恢复外层
                作用域绑定栈.pop()#出栈
            if 结果 is 子 and 出口 is not None:#区域留下了这个包裹
                出口.绑定覆盖=绑定#按这份绑定重画
                作用域绑定栈.append(绑定)#重画期间可见
                try:#画出已登记子项
                    出口.重画()#内容放进包裹
                finally:#恢复
                    作用域绑定栈.pop()#出栈
            elif 出口 is not None and 出口.已拆 is False:#区域不要这个子树
                出口.拆除()#卸下并调用拆除
            自身.上次=结果#记下
            return 结果#区域结果
        finally:#放开重入
            自身.绘制中=False#结束

    def 拆除(自身):
        '退掉绑定源订阅'
        if 自身.已拆:#已卸
            return#跳过
        自身.已拆=True#标记
        if callable(自身.退订):#有订阅
            自身.退订()#退订
        自身.退订=None#清空


def 标准工具包(宿主,条目,作用域,根绑定,作用域绑定):
    '标准座位、文案、存储、子槽和 SessionProvider'
    标准=标准属性(作用域,根绑定,作用域绑定)#标准座位
    包=dict(标准)#工具包
    包['renderFactorySlot']=绑定工厂槽(宿主,条目)#工厂座位
    放入文案(宿主,条目,包,False)#文案
    作用域键=作用域绑定.get('key') if isinstance(作用域绑定,dict) else None#会话键
    作用域存储绑定=作用域绑定 if 作用域键 is not None else None#没有键不能解析会话存储
    存储=宿主.storeOf(条目,作用域存储绑定)#存储实例
    动作=None#动作
    if 存储 is not None:#有存储
        包['useStore']=可观察钩子(存储)#存储钩子
        动作=读(存储,'actions')#动作
        包['actions']=动作#动作座位
    子槽座位(宿主,条目,False,包)#子槽
    return {'kit':包,'standard':标准,'actions':动作}#三件


def 渲染条目(槽键,条目,作用域,绑定,槽注入,拥有方,钩子上下文,有钩子上下文,世代):
    '合成份额并呈现条目。延迟钩子没有上下文就失败'
    出口=出口栈[-1]#当前包裹
    宿主=用宿主()#宿主
    根绑定=用根绑定()#根绑定
    三件=标准工具包(宿主,条目,作用域,根绑定,绑定)#工具包
    if 作用域=='root':#根
        注入=缓存根注入(条目,三件['actions'])#根注入
    elif 作用域=='session':#严格会话
        注入=缓存会话注入(条目,绑定,三件['actions'])#会话注入
    else:#可选会话
        注入=缓存可选会话注入(条目,绑定,三件['actions'])#可选注入
    槽属性=槽注入.get('props') if isinstance(槽注入,dict) else {}#调度份额
    合并={}#发给组件的份额
    合并.update(三件['kit'])#工具
    合并.update(注入 if isinstance(注入,dict) else {})#条目注入
    合并.update(槽属性 if isinstance(槽属性,dict) else {})#调度注入
    工厂表=槽注入.get('slotHookFactories') if isinstance(槽注入,dict) else None#延迟工厂
    if isinstance(工厂表,dict):#有延迟工厂
        if 有钩子上下文 is False:#没有出现点
            raise 槽组装错误("slot '"+str(槽键)+"' has contextual injected Hooks but no hookContext")#装配失败
        for 名称,工厂 in 工厂表.items():#逐个工厂
            合并[标准钩子属性名(名称)]=工厂(三件['standard'],钩子上下文)#绑到这一出现点
    合并.update(拥有方 if isinstance(拥有方,dict) else {})#拥有方最后覆盖
    if 'window' not in 合并:#这个引擎没有浏览器全局 window
        合并['window']=取握手窗口()#握手传进来的窗口
    组件=条目.get('component') if isinstance(条目,dict) else None#组件
    return 呈现(出口,(id(条目),世代),组件,合并)#呈现


class 槽错误边界:
    '条目崩溃显示 data-slot-error。装配错误继续往外抛'
    def __init__(自身,槽键,标签,条目错误时,子树):
        '记下槽、锚点标签和上报回调'
        自身.slotKey=槽键#槽名
        自身.标签=标签#锚点标签
        自身.onEntryError=条目错误时#上报
        自身.子树=子树#画出子树
        自身.失败=False#尚未失败
        自身.文档=None#文档

    def 崩溃盒(自身):
        '空的崩溃面，不写额外说明'
        return 建盒(自身.文档,自身.标签,'data-slot-error',str(自身.slotKey),'contents')#崩溃元素

    def 渲染(自身,文档):
        '成功返回子树，失败返回崩溃元素'
        自身.文档=文档#文档
        if 自身.失败:#已经失败
            return 自身.崩溃盒()#崩溃面
        try:#画子树
            return 自身.子树()#子树
        except 槽组装错误:#装配错误不吞
            raise#继续抛
        except Exception as 错误:#条目崩溃
            print("槽条目在 '"+str(自身.slotKey)+"' 崩溃:",错误)#打印
            自身.失败=True#标记
            import traceback as 栈#失败原因留在元素上
            行=栈.format_exc().strip().splitlines()
            自身.失败文='\n'.join(行[-8:])#最后几行
            自身.onEntryError(错误)#上报，遮蔽槽会退位
            盒=自身.崩溃盒()#崩溃面
            盒.setAttribute('data-error',自身.失败文)#原因
            return 盒


class 工厂错误边界:
    '工厂出现崩溃显示 data-factory-error，不退役共享定义'
    def __init__(自身,名,条目错误时,子树):
        '记下滑槽名和上报'
        自身.名=名#工厂或局部槽名
        自身.onEntryError=条目错误时#上报
        自身.子树=子树#子树
        自身.失败=False#尚未失败
        自身.文档=None#文档

    def 渲染(自身,文档):
        '成功返回子树，失败返回崩溃元素'
        自身.文档=文档#文档
        if 自身.失败:#已失败
            return 建盒(文档,'div','data-factory-error',自身.名,'contents')#崩溃面
        try:#画子树
            return 自身.子树()#子树
        except 槽组装错误:#装配错误不吞
            raise#继续抛
        except Exception as 错误:#出现崩溃
            print("槽工厂出现在 '"+str(自身.名)+"' 崩溃:",错误)#打印
            自身.失败=True#标记
            自身.onEntryError(错误)#上报
            盒=建盒(文档,'div','data-factory-error',自身.名,'contents')#崩溃面
            盒.setAttribute('data-error',str(错误))#原因
            return 盒


class 可选会话条目:
    '可选会话的化身壳。代数变了才换里面的条目'
    def __init__(自身,属性):
        '记下份额并画出'
        自身.属性=属性#份额
        自身.根=None#当前体的节点
        自身.渲染()#首画

    def 更新(自身,属性):
        '换份额'
        自身.属性=属性#新份额

    def 渲染(自身):
        '按当前化身呈现体'
        属性=自身.属性#份额
        出口=属性['出口']#包裹
        绑定=用作用域绑定()#当前绑定
        代数=化身代数(出口,属性['条目'],绑定)#化身
        体=渲染条目(#体
            属性['槽键'],属性['条目'],'session-maybe',绑定,属性['槽注入'],
            属性['拥有方'],属性['钩子上下文'],属性['有钩子上下文'],代数,
        )#呈现
        自身.根=取根(体)#节点
        return 自身.根#节点

    def 拆除(自身):
        '体由包裹的实例表拆除，壳自身没有额外订阅'
        return#无


def 条目选项键(条目):
    'options.key'
    形=条目.get('options') if isinstance(条目,dict) else None#选项
    if isinstance(形,dict) is False:#没有
        return None#无
    return 形.get('key')#键


def 条目选项标识(条目):
    'options.id'
    形=条目.get('options') if isinstance(条目,dict) else None#选项
    if isinstance(形,dict) is False:#没有
        return None#无
    return 形.get('id')#标识


def 条目选项顺序(条目):
    'options.order，缺了是 0'
    形=条目.get('options') if isinstance(条目,dict) else None#选项
    if isinstance(形,dict) is False or 'order' not in 形:#缺键
        return 0#默认
    return 形['order']#顺序


def 行顺序(项):
    '列表行按 order 排'
    return 项['order']#顺序


def 渲染链结果(文档,槽键,当选,选项,标签):
    '没有覆盖层时返回当选或回退。有覆盖层时回退留在原位'
    回退=选项.get('fallback') if isinstance(选项,dict) else None#回退
    覆盖=isinstance(选项,dict) and 选项.get('overlay') is True#覆盖层
    if 覆盖 is False:#普通链
        if 当选 is not None:#有当选
            return 当选#当选
        return 回退#回退
    显示='contents' if 当选 is None else 'none'#有当选就藏起回退
    锚=建盒(文档,标签,'data-chain-overlay-fallback',str(槽键),显示)#回退锚
    挂进(锚,回退)#回退放进锚
    片段=文档.createDocumentFragment()#不额外占一层
    片段.appendChild(锚)#回退
    挂进(片段,当选)#当选跟在后面
    return 片段#两段


def 渲染出口内容(文档,宿主,槽键,拥有方,选项,标签):
    '按 single、keyed、list、chain 把已登记子项画出来'
    规格=宿主.specOf(槽键)#活规格
    if 规格 is None:#未声明
        return None#空
    种类=规格.get('kind') if isinstance(规格,dict) else None#种类
    仅回退=isinstance(选项,dict) and 选项.get('fallbackOnly') is True#只要回退
    if 种类=='chain' and 仅回退:#不选举
        return 渲染链结果(文档,槽键,None,选项,标签)#回退
    作用域=规格.get('scope') if isinstance(规格,dict) else None#作用域
    作用域绑定=用作用域绑定()#当前绑定
    绑定键=作用域绑定.get('key') if isinstance(作用域绑定,dict) else None#键
    if 作用域=='session' and 绑定键 is None:#严格会话没有键
        raise 槽组装错误("strict session slot '"+str(槽键)+"' rendered without a scope binding")#装配失败
    条目列表=宿主.entriesOf(槽键)#全部条目
    槽注入=缓存槽注入(规格.get('inject') if isinstance(规格,dict) else None)#调度注入
    有钩=isinstance(选项,dict) and 'hookContext' in 选项#是否带出现点
    钩上下文=选项.get('hookContext') if 有钩 else None#出现点

    def 守卫(条目,世代,拥有=None):
        '每个条目各自一个错误边界'
        拥有方值=拥有方 if 拥有 is None else 拥有#拥有方

        def 条目错误时(错误):
            '遮蔽槽退位，链只报告'
            宿主.reportEntryError(槽键,条目,错误,{'abdicate':种类!='chain'})#上报

        def 子树():
            '按作用域呈现'
            if 作用域=='session':#严格会话
                绑定=用作用域绑定()#提供者换过的绑定
                if isinstance(绑定,dict) is False or 绑定.get('key') is None:#仍没有键
                    raise 槽组装错误("strict session slot '"+str(槽键)+"' rendered without a scope binding")#装配失败
                代=会话世代键(绑定)#Context 世代
                return 渲染条目(槽键,条目,'session',绑定,槽注入,拥有方值,钩上下文,有钩,代)#体
            if 作用域=='session-maybe':#可选会话
                return 呈现(出口栈[-1],(id(条目),'maybe'),可选会话条目,{#化身壳
                    '出口':出口栈[-1],#包裹
                    '条目':条目,#条目
                    '槽键':槽键,#槽
                    '槽注入':槽注入,#注入
                    '拥有方':拥有方值,#拥有方
                    '钩子上下文':钩上下文,#出现点
                    '有钩子上下文':有钩,#是否有出现点
                })#壳
            return 渲染条目(槽键,条目,'root',None,槽注入,拥有方值,钩上下文,有钩,0)#根体

        边界=槽错误边界(槽键,标签,条目错误时,子树)#边界
        return 边界.渲染(文档)#节点或实例

    def 干涸格():
        '这一格的登记都退位了'
        return 建盒(文档,标签,'data-slot-error',str(槽键),'contents')#崩溃面

    if 种类=='single':#只显示一个
        胜出=宿主.entriesOfSlot(槽键)#胜出
        条目=胜出[0] if len(胜出)>0 else None#第一个
        if 条目 is None:#没有胜出
            if len(条目列表)>0:#都退位了
                return 干涸格()#崩溃面
            return 选项.get('fallback') if isinstance(选项,dict) else None#回退
        return 守卫(条目,0)#胜出
    if 种类=='keyed':#按键挑一个
        条目键=选项.get('entryKey') if isinstance(选项,dict) else None#请求的键
        条目=None#命中
        for 项 in 宿主.entriesOfSlot(槽键):#胜出里找
            if 条目选项键(项)==条目键:#同键
                条目=项#命中
                break#停
        if 条目 is None:#没有胜出
            占用=False#是否曾占用
            for 项 in 条目列表:#全部登记
                if 条目选项键(项)==条目键:#同键
                    占用=True#退位后的空格
                    break#停
            if 占用:#干涸
                return 干涸格()#崩溃面
            return 选项.get('fallback') if isinstance(选项,dict) else None#回退
        return 守卫(条目,0)#命中
    if 种类=='chain':#按顺序选第一个有结果的
        当选=None#当选
        for 条目 in 条目列表:#按台账顺序
            try:#选择器必须纯
                选择=条目.get('select') if isinstance(条目,dict) else None#选择器
                命中=选择(拥有方) if callable(选择) else None#结果
            except Exception as 错误:#选择器崩了当谢绝
                登记方=条目.get('registrant') if isinstance(条目,dict) and 条目.get('registrant') is not None else 'unknown registrant'#登记方
                print("链选择器在 '"+str(槽键)+"' ("+str(登记方)+") 崩溃，视为谢绝:",错误)#打印
                continue#下一条
            if 命中 is not None:#选中
                带命中=dict(拥有方) if isinstance(拥有方,dict) else {}#拷贝拥有方
                带命中['matched']=命中#命中值
                当选=守卫(条目,0,带命中)#画这条
                break#停止
        return 渲染链结果(文档,槽键,当选,选项,标签)#链结果
    胜出列表=宿主.entriesOfSlot(槽键)#列表胜出
    行列表=[]#行
    行标识=set()#已有标识
    for 条目 in 胜出列表:#活行
        标识=条目选项标识(条目)#标识
        行列表.append({'entry':条目,'id':标识,'order':条目选项顺序(条目)})#活
        行标识.add(标识)#记下
    for 条目 in 条目列表:#补干涸行
        标识=条目选项标识(条目)#标识
        if 标识 in 行标识:#已有
            continue#跳过
        行标识.add(标识)#记下
        行列表.append({'entry':None,'id':标识,'order':条目选项顺序(条目)})#干涸
    行列表.sort(key=行顺序)#按顺序
    if isinstance(选项,dict) and 'only' in 选项:#只要某一标识
        仅=选项.get('only')#标识
        行列表=[项 for 项 in 行列表 if 项['id']==仅]#过滤
    if len(行列表)==0:#没有行
        return 选项.get('fallback') if isinstance(选项,dict) else None#回退
    片段=文档.createDocumentFragment()#多行不额外包一层
    for 项 in 行列表:#逐行
        if 项['entry'] is not None:#胜出
            挂进(片段,守卫(项['entry'],条目选项标识(项['entry'])))#行
        else:#干涸
            挂进(片段,干涸格())#崩溃面
    return 片段#行


class 槽出口:
    '子槽包裹。最外层不占布局，带 data-slot，已登记子项在里面'
    def __init__(自身,槽键,拥有方,选项,声明内联):
        '先不画。调用渲染才创建元素'
        自身.slotKey=槽键#槽名
        自身.ownerProps=拥有方 if isinstance(拥有方,dict) else {}#拥有方
        自身.opts=选项#选项
        自身.声明内联=声明内联#规格卸掉后的锚点
        自身.盒=None#包裹元素
        自身.标签='div'#锚点标签
        自身.已画=False#内容是否画过
        自身.已拆=False#是否已卸
        自身.绘制中=False#防止重入
        自身.待重画=False#画的过程中又要求重画
        自身.曾连接=False#曾经进过页面
        自身.绑定覆盖=None#提供者换上的绑定
        自身.退订表=[]#订阅
        自身.实例表={}#世代到实例
        自身.本轮=set()#这一轮还要的实例
        自身.化身表={}#可选会话化身
        自身.文档=None#文档

    def 渲染(自身):
        '创建 data-slot 包裹。严格会话还没有键时先留空，等提供者'
        if 自身.盒 is None:#第一次
            宿主=用宿主()#宿主
            自身.文档=取文档(自身.ownerProps)#文档
            规格=宿主.specOf(自身.slotKey)#规格
            自身.标签=锚标签(规格,自身.声明内联)#标签
            自身.盒=建盒(自身.文档,自身.标签,'data-slot',str(自身.slotKey),'contents')#不占布局
            记下出口(自身.盒,自身)#找回
            登记出口(自身)#入册
            自身.订阅(宿主)#登记变化后再画
        规格=用宿主().specOf(自身.slotKey)#再读规格
        作用域=规格.get('scope') if isinstance(规格,dict) else None#作用域
        绑定=用作用域绑定()#当前绑定
        键=绑定.get('key') if isinstance(绑定,dict) else None#键
        if 作用域=='session' and 键 is None:#等 SessionProvider 换绑定
            return 自身.盒#先交出空包裹
        自身.重画()#根槽和已有会话直接画
        return 自身.盒#包裹

    def 订阅(自身,宿主):
        '槽位登记或文案修订变了就重画'

        def 变更():
            '摘掉的包裹卸下，还在页面上就重画'
            if 自身.已拆 or 自身.绘制中:#不能重入
                return#跳过
            if 自身.盒 is not None and getattr(自身.盒,'isConnected',None) is True:#仍在页面
                自身.曾连接=True#记下
            if 自身.曾连接 and 自身.盒 is not None and getattr(自身.盒,'isConnected',None) is False:#已被摘掉
                自身.拆除()#调用拆除
                return#完
            if 自身.已画 is False:#还在等提供者
                return#先不画
            自身.重画()#重画

        订上(自身.退订表,宿主.subscribe(自身.slotKey,变更))#订槽
        面=宿主.locale()#文案面
        if 面 is not None:#已安装
            订上(自身.退订表,读(面,'subscribe')(变更) if callable(读(面,'subscribe')) else None)#订修订

    def 丢掉过期(自身):
        '这一轮没再呈现的实例先拆后代出口，再调用拆除'
        for 标识 in list(自身.实例表):#已有实例
            if 标识 in 自身.本轮:#还要
                continue#留
            实例=自身.实例表.pop(标识)#拿掉
            根=取根(实例)#节点
            if 根 is not None:#先拆里面的出口
                拆除后代出口(根)#后代
            拆除对象(实例)#调用拆除
            if 根 is not None and getattr(根,'parentNode',None) is not None:#还挂着
                根.remove()#摘掉

    def 清掉散子(自身):
        '留下这一轮实例的根，其余子节点拆掉'
        留=set()#要留的节点
        for 标识 in 自身.本轮:#这一轮
            根=取根(自身.实例表.get(标识))#根
            if 根 is not None:#有节点
                留.add(id(根))#留下
        子=自身.盒.firstChild#第一个
        while 子 is not None:#逐个
            下=getattr(子,'nextSibling',None)#下一个
            if id(子) not in 留:#不是实例根
                子出口=取出口(子)#出口
                if 子出口 is not None and 子出口 is not 自身:#子包裹
                    子出口.拆除()#卸下
                if getattr(子,'parentNode',None) is not None:#还在
                    子.remove()#摘掉
            子=下#继续

    def 重画(自身):
        '清掉过期子项，把当前登记画进 data-slot 包裹'
        if 自身.已拆:#已卸
            return 自身.盒#不再画
        if 自身.绘制中:#重入
            自身.待重画=True#等这一轮结束
            return 自身.盒#当前元素
        自身.绘制中=True#占用
        自身.已画=True#已经开始画
        自身.本轮=set()#清空本轮
        出口栈.append(自身)#子呈现能找到包裹
        try:#结束时出栈
            绑定=自身.绑定覆盖#提供者指定的绑定
            if 绑定 is None:#没有覆盖
                绑定=用作用域绑定()#外层绑定
            作用域绑定栈.append(绑定)#子槽看到它
            try:#按规格调度
                内容=渲染出口内容(自身.文档,用宿主(),自身.slotKey,自身.ownerProps,自身.opts,自身.标签)#子项
            finally:#恢复外层绑定
                作用域绑定栈.pop()#出栈
            自身.丢掉过期()#卸下不再呈现的实例
            自身.清掉散子()#摘掉散子
            挂进(自身.盒,内容)#子项放进包裹
            标记已连接(自身.盒)#记下已经进页面的出口
        finally:#出栈并处理补画
            出口栈.pop()#出栈
            自身.绘制中=False#放开
        if 自身.待重画 and 自身.已拆 is False:#画的时候又脏了
            自身.待重画=False#清标记
            return 自身.重画()#再画
        return 自身.盒#包裹

    def 拆除(自身):
        '退订，拆掉子实例，并调用它们的拆除'
        if 自身.已拆:#已卸
            return#跳过
        自身.已拆=True#标记
        for 退 in 自身.退订表:#逐个退订
            if callable(退):#是函数
                退()#退订
        自身.退订表=[]#清空
        自身.本轮=set()#没有要留的
        出口栈.append(自身)#丢掉过期要能走
        try:#拆实例
            自身.丢掉过期()#调用拆除
        finally:#出栈
            出口栈.pop()#出栈
        if 自身.盒 is not None:#清掉剩余节点
            while 自身.盒.firstChild is not None:#还有子
                子=自身.盒.firstChild#第一个
                子出口=取出口(子)#子出口
                if 子出口 is not None and 子出口 is not 自身:#先卸子包裹
                    子出口.拆除()#拆除
                if getattr(子,'parentNode',None) is not None:#还在
                    子.remove()#摘掉
            忘掉出口(自身.盒)#不再找回


class 根出口:
    'root 包裹。未登记是启动失败，全部退位则是崩溃面'
    def __init__(自身,拥有方):
        '记下拥有方'
        自身.ownerProps=拥有方 if isinstance(拥有方,dict) else {}#拥有方
        自身.盒=None#包裹
        自身.已拆=False#是否已卸
        自身.绘制中=False#防止重入
        自身.待重画=False#补画
        自身.曾连接=False#曾经进页面
        自身.退订表=[]#订阅
        自身.实例表={}#实例
        自身.本轮=set()#本轮
        自身.化身表={}#给子槽留的表，根自己不用
        自身.绑定覆盖=None#根没有提供者覆盖
        自身.文档=None#文档
        自身.卸作用域=False#拆除时是否弹出作用域
        自身.卸根=False#拆除时是否弹出根绑定
        自身.卸宿主=False#拆除时是否弹出宿主
        自身.留下的作用域=None#这一棵根压上的作用域绑定
        自身.留下的根=None#这一棵根压上的根绑定
        自身.留下的宿主=None#这一棵根压上的宿主

    def 渲染(自身):
        '创建 data-slot=root 的包裹并画上唯一条目'
        if 自身.盒 is None:#第一次
            自身.文档=取文档(自身.ownerProps)#文档
            自身.盒=建盒(自身.文档,'div','data-slot','root','contents')#根包裹
            记下出口(自身.盒,自身)#找回
            登记出口(自身)#入册
            宿主=用宿主()#宿主
            自身.订阅(宿主)#订 root
        自身.重画()#画条目
        return 自身.盒#包裹

    def 订阅(自身,宿主):
        'root 登记或文案变了就重画'

        def 变更():
            '摘掉则拆除，否则重画'
            if 自身.已拆 or 自身.绘制中:#不能重入
                return#跳过
            if 自身.盒 is not None and getattr(自身.盒,'isConnected',None) is True:#在页面
                自身.曾连接=True#记下
            if 自身.曾连接 and 自身.盒 is not None and getattr(自身.盒,'isConnected',None) is False:#摘掉了
                自身.拆除()#卸下
                return#完
            自身.重画()#重画

        订上(自身.退订表,宿主.subscribe('root',变更))#订 root
        面=宿主.locale()#文案
        if 面 is not None and callable(读(面,'subscribe')):#有订阅
            订上(自身.退订表,读(面,'subscribe')(变更))#订修订

    def 丢掉过期(自身):
        '拆掉这一轮没有呈现的根条目'
        for 标识 in list(自身.实例表):#已有
            if 标识 in 自身.本轮:#还要
                continue#留
            实例=自身.实例表.pop(标识)#拿掉
            根=取根(实例)#节点
            if 根 is not None:#先拆后代
                拆除后代出口(根)#后代出口
            拆除对象(实例)#调用拆除
            if 根 is not None and getattr(根,'parentNode',None) is not None:#还挂着
                根.remove()#摘掉

    def 重画(自身):
        '有胜出则放进包裹，全部退位则放崩溃面'
        if 自身.已拆:#已卸
            return 自身.盒#不再画
        if 自身.绘制中:#重入
            自身.待重画=True#稍后
            return 自身.盒#当前
        自身.绘制中=True#占用
        自身.本轮=set()#本轮
        出口栈.append(自身)#呈现使用
        try:#出栈
            宿主=用宿主()#宿主
            宿主.getVersion('root')#读版本，和订阅成对
            胜出=宿主.entriesOfSlot('root')#胜出
            条目=胜出[0] if len(胜出)>0 else None#唯一胜出
            if 条目 is None:#没有胜出
                if len(宿主.entriesOf('root'))>0:#都退位了
                    内容=建盒(自身.文档,'div','data-slot-error','root','contents')#崩溃面
                else:#根本没登记
                    raise 槽组装错误("renderSlot('root') before any 'root' registration (boot order)")#启动顺序
            else:#有条目
                def 条目错误时(错误):
                    '根条目崩溃后退位'
                    宿主.reportEntryError('root',条目,错误,{'abdicate':True})#退位

                def 子树():
                    '根条目'
                    return 渲染条目('root',条目,'root',None,空槽注入,自身.ownerProps,None,False,0)#体

                边界=槽错误边界('root','div',条目错误时,子树)#边界
                内容=边界.渲染(自身.文档)#内容
            自身.丢掉过期()#旧实例
            while 自身.盒.firstChild is not None:#清掉旧子
                子节点=自身.盒.firstChild#第一个
                if getattr(子节点,'parentNode',None) is not None:#还在
                    子节点.remove()#摘掉
            挂进(自身.盒,内容)#放进包裹
            标记已连接(自身.盒)#记下已经进页面的出口
        finally:#出栈
            出口栈.pop()#出栈
            自身.绘制中=False#放开
        if 自身.待重画 and 自身.已拆 is False:#补画
            自身.待重画=False#清
            return 自身.重画()#再画
        return 自身.盒#包裹

    def 卸栈(自身):
        '渲染根时留下的三层栈在这里弹出'
        if 自身.卸作用域 and len(作用域绑定栈)>0 and 作用域绑定栈[-1] is 自身.留下的作用域:#还是这一棵
            作用域绑定栈.pop()#弹出
        自身.卸作用域=False#只处理一次
        if 自身.卸根 and len(根绑定栈)>0 and 根绑定栈[-1] is 自身.留下的根:#还是这一棵
            根绑定栈.pop()#弹出
        自身.卸根=False#只处理一次
        if 自身.卸宿主 and len(宿主栈)>0 and 宿主栈[-1] is 自身.留下的宿主:#还是这一棵
            宿主栈.pop()#弹出
        自身.卸宿主=False#只处理一次

    def 拆除(自身):
        '退订，拆除根条目，再弹出渲染栈'
        if 自身.已拆:#已卸
            return#跳过
        自身.已拆=True#标记
        for 退 in 自身.退订表:#退订
            if callable(退):#是函数
                退()#退
        自身.退订表=[]#清空
        自身.本轮=set()#不留实例
        出口栈.append(自身)#丢掉过期
        try:#拆实例
            自身.丢掉过期()#调用拆除
        finally:#出栈
            出口栈.pop()#出栈
        if 自身.盒 is not None:#清子节点
            while 自身.盒.firstChild is not None:#还有
                子节点=自身.盒.firstChild#第一个
                子出口=取出口(子节点)#子出口
                if 子出口 is not None:#先卸
                    子出口.拆除()#拆除
                if getattr(子节点,'parentNode',None) is not None:#还在
                    子节点.remove()#摘掉
            忘掉出口(自身.盒)#忘掉
        自身.卸栈()#弹出渲染栈


def 绑定工厂槽(宿主,调用方):
    '每个调用方一个稳定的 renderFactorySlot'
    键=id(调用方)#调用方
    已有=工厂槽缓存.get(键)#缓存
    if 已有 is not None:#已有
        return 已有#复用

    def 渲染工厂(名,属性=None,选项=None):
        '画出这一次工厂出现'
        输入=属性 if isinstance(属性,dict) else {}#输入份额
        局部=None#局部槽
        回退=None#没有定义时的回退
        if isinstance(选项,dict):#有选项
            局部=选项.get('slots')#局部组件
            回退=选项.get('fallback')#回退
        出口=工厂出口(名,输入,局部 if isinstance(局部,dict) else {},回退,调用方,宿主)#出现
        return 出口.渲染()#节点

    工厂槽缓存[键]=渲染工厂#缓存
    return 渲染工厂#座位


def 工厂工具包(宿主,定义,根绑定,作用域绑定,出现):
    '工厂出现的标准座位、存储、子槽和 useFactorySlot'
    作用域=定义.get('scope') if isinstance(定义,dict) else 'root'#作用域
    标准=标准属性(作用域,根绑定,作用域绑定)#标准
    登记包={}#登记座位
    登记包['renderFactorySlot']=绑定工厂槽(宿主,定义)#还能再画工厂
    放入文案(宿主,定义,登记包,True)#文案
    作用域键=作用域绑定.get('key') if isinstance(作用域绑定,dict) else None#键
    存储绑定=作用域绑定 if 作用域键 is not None else None#会话存储绑定
    存储=宿主.factoryStoreOf(定义,存储绑定,出现)#这一出现的存储
    动作=None#动作
    if 存储 is not None:#有存储
        登记包['useStore']=可观察钩子(存储)#钩子
        动作=读(存储,'actions')#动作
        登记包['actions']=动作#座位
    子槽座位(宿主,定义,True,登记包)#子槽
    登记包['useFactorySlot']=用工厂槽#局部槽
    包=dict(标准)#先标准
    包.update(登记包)#再登记座位
    return {'kit':包,'registrationKit':登记包,'actions':动作,'standard':标准}#四件


def 用工厂槽(名,回退):
    '只能在工厂出现里取局部组件'
    if len(工厂帧栈)==0:#不在工厂里
        raise 槽组装错误('useFactorySlot() called outside a Factory occurrence')#装配失败
    帧=工厂帧栈[-1]#当前出现
    宿主=帧['宿主']#宿主
    定义=帧['定义']#定义
    if 宿主.isFactoryLive(定义) is False:#定义已卸
        raise 过期授权错误("useFactorySlot('"+str(名)+"') from a disposed Factory")#过期
    局部表=定义.get('slots') if isinstance(定义,dict) else None#局部声明
    声明=局部表.get(名) if isinstance(局部表,dict) else None#这一格
    if 声明 is None:#没声明
        raise 槽位所有权错误("local slot '"+str(名)+"' is not declared by factory '"+str(定义.get('name'))+"'")#所有权
    选中=帧['局部'].get(名) if isinstance(帧['局部'],dict) else None#调用方选的组件
    组件=选中 if 选中 is not None else 回退#没有就用回退
    用回退=选中 is None#是否回退

    def 局部组件(局部属性):
        '在工厂出现里画出局部组件'
        if 宿主.isFactoryLive(定义) is False:#已卸
            raise 过期授权错误("local slot '"+str(名)+"' from a disposed Factory")#过期
        if len(工厂帧栈)==0 or 工厂帧栈[-1]['定义'] is not 定义:#跑出了这间工厂
            raise 槽位所有权错误("local slot '"+str(名)+"' rendered outside factory '"+str(定义.get('name'))+"'")#所有权
        范围=声明.get('scope') if isinstance(声明,dict) else 'root'#局部作用域
        绑定=用作用域绑定()#当前绑定
        if 范围=='session' and (isinstance(绑定,dict) is False or 绑定.get('key') is None):#严格局部槽
            raise 槽组装错误("strict session local slot '"+str(名)+"' from factory '"+str(定义.get('name'))+"' rendered without a scope binding")#装配失败
        根绑定=用根绑定()#根
        标准=标准属性(范围,根绑定,绑定)#标准座位
        主人=定义 if 用回退 else 帧['调用方']#回退算定义方
        登记包=dict(帧['登记包'])#拷贝
        登记包['renderFactorySlot']=绑定工厂槽(宿主,主人)#按主人再绑
        拒绝重叠("factory '"+str(定义.get('name'))+"' local slot '"+str(名)+"'",登记包,标准)#座位不能重名
        已有=dict(登记包)#合并
        已有.update(标准)#标准
        拒绝重叠("factory '"+str(定义.get('name'))+"' local slot '"+str(名)+"'",已有,局部属性 if isinstance(局部属性,dict) else {})#输入不能重名
        合并=dict(已有)#发给组件
        if isinstance(局部属性,dict):#有输入
            合并.update(局部属性)#输入最后
        文档=帧['文档']#文档

        def 子树():
            '调用局部组件'
            if isinstance(组件,type):#类
                return 组件(合并)#构造
            return 组件(合并)#函数

        def 上报(错误):
            '局部槽崩溃只报告这一出现'
            宿主.reportFactoryError(定义.get('name'),主人,错误)#上报

        边界=工厂错误边界(str(定义.get('name'))+':'+str(名),上报,子树)#边界
        return 边界.渲染(文档)#节点

    return 局部组件#局部组件


class 工厂出口:
    '一次工厂出现。卸下时调用保留拆除器'
    def __init__(自身,名,输入,局部,回退,调用方,宿主):
        '记下这一次出现的输入'
        自身.名=名#工厂名
        自身.输入=输入#输入份额
        自身.局部=局部#局部组件
        自身.回退=回退#回退
        自身.调用方=调用方#谁画的
        自身.宿主=宿主#宿主
        自身.出现=object()#出现身份
        自身.盒=None#包一层，方便卸下时找到
        自身.已拆=False#是否已卸
        自身.已画=True#补画只处理还没画的槽包裹
        自身.绘制中=False#重入
        自身.曾连接=False#曾经进页面
        自身.退订表=[]#订阅
        自身.保留拆除=None#retain 返回的拆除器
        自身.文档=None#文档
        自身.实例=None#组件实例

    def 渲染(自身):
        '没有定义时返回回退。有定义则把组件放进不占布局的一层'
        if 自身.盒 is None:#第一次
            自身.文档=取文档(自身.输入)#文档
            自身.盒=自身.文档.createElement('div')#出现层
            自身.盒.style.display='contents'#不占布局
            记下出口(自身.盒,自身)#找回
            登记出口(自身)#入册
            订上(自身.退订表,自身.宿主.subscribeFactory(自身.名,自身.变更))#定义变化
        自身.重画()#画组件
        return 自身.盒#节点

    def 变更(自身):
        '定义换了就重画。节点已被摘掉就拆除'
        if 自身.已拆 or 自身.绘制中:#不能重入
            return#跳过
        if 自身.盒 is not None and getattr(自身.盒,'isConnected',None) is True:#在页面
            自身.曾连接=True#记下
        if 自身.曾连接 and 自身.盒 is not None and getattr(自身.盒,'isConnected',None) is False:#摘掉了
            自身.拆除()#卸下
            return#完
        自身.重画()#重画

    def 调用保留(自身):
        '提交这一出现的独占存储，返回的拆除器留到卸下'
        if callable(自身.保留拆除):#换定义前先卸旧的
            自身.保留拆除()#拆除旧保留
            自身.保留拆除=None#清空
        定义=自身.宿主.factoryOf(自身.名)#当前定义
        if 定义 is None:#没有定义
            return#不保留
        拆=自身.宿主.retainFactoryOccurrence(定义,自身.出现)#保留
        if callable(拆):#有拆除器
            自身.保留拆除=拆#卸下时调用

    def 重画(自身):
        '按作用域画出工厂组件'
        if 自身.已拆:#已卸
            return 自身.盒#不再画
        if 自身.绘制中:#重入
            return 自身.盒#当前
        自身.绘制中=True#占用
        try:#放开
            宿主=自身.宿主#宿主
            宿主.getFactoryVersion(自身.名)#读版本
            定义=宿主.factoryOf(自身.名)#定义
            while 自身.盒.firstChild is not None:#清掉旧内容
                子=自身.盒.firstChild#第一个
                子出口=取出口(子)#子出口
                if 子出口 is not None and 子出口 is not 自身:#先卸
                    子出口.拆除()#拆除
                if getattr(子,'parentNode',None) is not None:#还在
                    子.remove()#摘掉
            if 自身.实例 is not None:#旧组件
                拆除对象(自身.实例)#调用拆除
                自身.实例=None#清空
            if 定义 is None:#没有定义
                if callable(自身.保留拆除):#卸下旧的存储保留
                    自身.保留拆除()#调用拆除
                    自身.保留拆除=None#清空
                挂进(自身.盒,自身.回退)#回退
                return 自身.盒#回退
            for 帧 in 工厂帧栈:#祖先
                if 帧['名']==自身.名:#递归
                    raise 槽位所有权错误("recursive render of factory '"+str(自身.名)+"'")#所有权
            if isinstance(自身.局部,dict):#检查局部槽
                for 局部名 in 自身.局部:#逐个
                    局部表=定义.get('slots') if isinstance(定义,dict) else None#声明
                    if isinstance(局部表,dict) is False or 局部名 not in 局部表:#没声明
                        raise 槽位所有权错误("local slot '"+str(局部名)+"' is not declared by factory '"+str(自身.名)+"'")#所有权
            绑定=用作用域绑定()#当前绑定
            作用域=定义.get('scope') if isinstance(定义,dict) else 'root'#作用域
            if 作用域=='session' and (isinstance(绑定,dict) is False or 绑定.get('key') is None):#严格工厂
                raise 槽组装错误("strict session factory '"+str(自身.名)+"' rendered without a scope binding")#装配失败
            根绑定=用根绑定()#根
            三件=工厂工具包(宿主,定义,根绑定,绑定,自身.出现)#工具
            注入=执行注入(定义,绑定 if 作用域!='root' else None,三件['actions'])#注入
            拒绝重叠("factory '"+str(自身.名)+"' inject",三件['kit'],注入)#注入不能重名
            已有=dict(三件['kit'])#工具
            已有.update(注入 if isinstance(注入,dict) else {})#注入
            拒绝重叠("factory '"+str(自身.名)+"' occurrence",已有,自身.输入)#输入不能重名
            合并=dict(已有)#发给组件
            合并.update(自身.输入)#输入
            帧={#这一出现
                '名':自身.名,#名字
                '宿主':宿主,#宿主
                '定义':定义,#定义
                '局部':自身.局部,#局部组件
                '调用方':自身.调用方,#调用方
                '登记包':三件['registrationKit'],#局部槽要的座位
                '文档':自身.文档,#文档
            }#帧
            工厂帧栈.append(帧)#局部槽能读到
            try:#画组件
                组件=定义.get('component') if isinstance(定义,dict) else None#组件

                def 子树():
                    '构造或调用工厂组件'
                    if isinstance(组件,type):#类
                        return 组件(合并)#构造
                    return 组件(合并)#函数

                def 上报(错误):
                    '出现崩溃'
                    宿主.reportFactoryError(自身.名,定义,错误)#上报

                边界=工厂错误边界(str(自身.名),上报,子树)#边界
                结果=边界.渲染(自身.文档)#结果
                自身.实例=结果#留到卸下
                挂进(自身.盒,结果)#放进出现层
                补画未处理(取根(结果))#补子槽
            finally:#退出工厂帧
                工厂帧栈.pop()#出栈
            自身.调用保留()#提交存储，卸下时拆
            标记已连接(自身.盒)#记下已经进页面的出口
            return 自身.盒#节点
        finally:#放开
            自身.绘制中=False#结束

    def 拆除(自身):
        '调用保留拆除器，再拆除组件'
        if 自身.已拆:#已卸
            return#跳过
        自身.已拆=True#标记
        for 退 in 自身.退订表:#退订
            if callable(退):#是函数
                退()#退
        自身.退订表=[]#清空
        if callable(自身.保留拆除):#存储保留
            自身.保留拆除()#拆除
            自身.保留拆除=None#清空
        if 自身.实例 is not None:#组件
            根=取根(自身.实例)#节点
            if 根 is not None:#后代出口
                拆除后代出口(根)#拆
            拆除对象(自身.实例)#调用拆除
            自身.实例=None#清空
        if 自身.盒 is not None:#忘掉节点
            忘掉出口(自身.盒)#不再找回


class 槽渲染器:
    '安装进槽登记表的渲染器'
    def renderRoot(自身,宿主,拥有方):
        '压上宿主和根作用域，返回 root 的 data-slot 包裹'
        宿主栈.append(宿主)#宿主留到根拆除
        出口盒=[None]#成功后的节点

        def 画根():
            '创建根出口并标上卸栈责任'
            出口=根出口(拥有方)#根
            出口.卸作用域=True#弹出作用域
            出口.卸根=True#弹出根绑定
            出口.卸宿主=True#弹出宿主
            出口.留下的作用域=作用域绑定栈[-1] if len(作用域绑定栈)>0 else None#这一层作用域
            出口.留下的根=根绑定栈[-1] if len(根绑定栈)>0 else None#这一层根绑定
            出口.留下的宿主=宿主栈[-1] if len(宿主栈)>0 else None#这一层宿主
            盒=出口.渲染()#包裹
            出口盒[0]=盒#记下
            return 盒#节点

        def 画作用域():
            'session-maybe 包住根'
            return 作用域提供者('session-maybe',画根).渲染(True)#保留栈

        try:#失败时把已经压上的栈弹回
            return 根标准提供者(画作用域).渲染(True)#保留根绑定
        except Exception:#装配失败
            if 出口盒[0] is not None:#根已经建出来
                已有=取出口(出口盒[0])#根出口
                if 已有 is not None:#卸掉
                    已有.拆除()#含卸栈
            elif len(宿主栈)>0 and 宿主栈[-1] is 宿主:#宿主还压着
                宿主栈.pop()#弹回
            raise#继续抛


def 创建槽渲染器():
    '构建安装进槽登记表的渲染器'
    return 槽渲染器()#实例
