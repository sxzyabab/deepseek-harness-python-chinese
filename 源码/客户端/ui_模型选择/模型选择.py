__all__=['模型选择','样式表']#仅中文公开名

样式表='''#对齐 ModelSelect.module.css 核心
.root{position:relative;min-width:0}
.trigger{display:flex;align-items:center;gap:4px;min-width:0;max-width:220px;height:28px;padding:0 4px 0 8px;border:none;border-radius:24px;outline:none;background:transparent;color:var(--dsw-alias-label-secondary);font-size:13px;line-height:20px;font-weight:500;cursor:pointer}
.triggerLabel{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.triggerEffort{flex:0 0 auto;color:var(--dsw-alias-label-caption)}
.chevron{flex:0 0 auto;color:var(--dsw-alias-label-caption);transition:transform 120ms ease}
.chevronOpen{transform:rotate(180deg)}
.menu{position:absolute;right:0;bottom:calc(100% + 8px);z-index:20;display:flex;flex-direction:column;width:min(240px,calc(100vw - 32px));max-height:min(360px,calc(100vh - 96px));overflow:hidden;padding:4px;border:1px solid var(--dsw-alias-border-inverted);border-radius:12px;background:var(--dsw-specific-menu);box-shadow:var(--dsw-shadow-lv3)}
.cell{display:flex;align-items:center;gap:8px;width:100%;height:40px;padding:0 10px;border:none;border-radius:10px;background:transparent;cursor:pointer;text-align:left}
.option{display:flex;align-items:center;gap:8px;width:100%;min-height:38px;padding:6px 8px;border:none;border-radius:10px;background:transparent;cursor:pointer;text-align:left}
'''#样式表结束

class 模型选择:#composer 模型座位
    """两级下拉：根行钻入模型表或力度表。"""
    def __init__(自身,属性):#构造
        """记下 props。"""
        自身.属性=属性#合成
        自身.打开=False#菜单开
        自身.面板='root'#root/model/effort
        自身.上次动作='load'#load/select
        自身.吐司=None#瞬时错误
        自身.吐司序号=0#吐司序号

    def 更新(自身,属性):#刷新
        """刷新 props。"""
        自身.属性=属性#最新

    def 切面板(自身,面):#切面板
        """记下当前面板。"""
        自身.面板=面#覆盖

    def 读状态(自身):#目录快照
        """经 directory store。"""
        目录存储=自身.属性['directory'] if 'directory' in 自身.属性 else None#存储
        if 目录存储 is None:#无
            return {'current':None,'groups':[],'failures':[],'status':'idle','error':None}#空
        return 目录存储.getSnapshot()#快照

    def 展平行(自身,状态):#分组展平为选择行
        """group+model+selection。"""
        行列表=[]#累积
        组列表=状态['groups'] if 'groups' in 状态 and 状态['groups'] is not None else []#各组
        for 组 in 组列表:#各组
            模型列表=组['models'] if 'models' in 组 and 组['models'] is not None else []#各模型
            for 模型 in 模型列表:#各模型
                选={'provider':组['id'],'model':模型['id']}#选定
                推理=模型['reasoning'] if 'reasoning' in 模型 else None#推理
                默认=推理['defaultEffort'] if 推理 is not None and 'defaultEffort' in 推理 else None#默认力度
                if 默认 is not None:#有
                    选['reasoningEffort']=默认#带上
                行列表.append({'group':组,'model':模型,'selection':选})#行
        return 行列表#全部

    def 关闭(自身):#关菜单
        """回到根面板。"""
        自身.打开=False#关
        自身.面板='root'#根

    def 打开菜单(自身):#开菜单并刷新
        """根面板并 load。"""
        自身.面板='root'#根
        自身.打开=True#开
        自身.上次动作='load'#load
        加载=自身.属性['load'] if 'load' in 自身.属性 else None#加载
        if 加载 is not None:#有
            加载()#拉

    def 重载(自身):#菜单内重载
        """标 load 再拉。"""
        自身.上次动作='load'#load
        加载=自身.属性['load'] if 'load' in 自身.属性 else None#加载
        if 加载 is not None:#有
            加载()#拉

    def 选定模型(自身,选定):#选模型
        """同路由则关；否则 select。"""
        状态=自身.读状态()#快照
        当前=状态['current'] if 'current' in 状态 else None#当前
        if (当前 is not None
            and 当前['provider']==选定['provider']
            and 当前['model']==选定['model']):#同
            自身.关闭()#关
            return#结束
        自身.上次动作='select'#select
        提交=自身.属性['select'] if 'select' in 自身.属性 else None#提交
        if 提交 is None:#无
            return#结束
        接受=提交(选定)#提交返回 bool
        if 接受:#成功
            自身.关闭()#关
            return#结束
        失败快照=自身.读状态()#失败后快照
        错=失败快照['error'] if 'error' in 失败快照 else None#错误
        翻译=自身.属性['t'] if 't' in 自身.属性 else None#翻译
        if 错 is not None and 翻译 is not None:#有错
            自身.吐司序号+=1#序号
            自身.吐司={'seq':自身.吐司序号,'text':翻译('error.action',{'message':错})}#吐司

    def 选定力度(自身,力度):#选推理力度
        """改当前选定的 reasoningEffort。"""
        状态=自身.读状态()#快照
        当前=状态['current'] if 'current' in 状态 else None#当前
        if 当前 is None:#无
            return#结束
        选={'provider':当前['provider'],'model':当前['model']}#选定
        if 力度 is not None:#有力度
            选['reasoningEffort']=力度#带上
        自身.选定模型(选)#走同一提交

    def 渲染(自身):#结构化视图
        """产出与上游 JSX 同构的结构化视图。"""
        可用=自身.属性['available'] if 'available' in 自身.属性 else None#可用
        if 可用 is not True:#不可用
            return None#不渲染
        翻译=自身.属性['t'] if 't' in 自身.属性 else None#翻译
        状态=自身.读状态()#快照
        行列表=自身.展平行(状态)#行
        当前=状态['current'] if 'current' in 状态 else None#当前
        当前行=None#当前选择行
        for 行 in 行列表:#找
            选=行['selection']#选定
            if 当前 is not None and 当前['provider']==选['provider'] and 当前['model']==选['model']:#命中
                当前行=行#记下
                break#停
        当前模型=当前行['model'] if 当前行 is not None else None#模型
        推理=当前模型['reasoning'] if 当前模型 is not None and 'reasoning' in 当前模型 else None#推理元
        有效力度=当前['reasoningEffort'] if 当前 is not None and 'reasoningEffort' in 当前 else None#当前力度
        if 有效力度 is None and 推理 is not None and 'defaultEffort' in 推理:#无则默认
            有效力度=推理['defaultEffort']#默认
        力度标签=None#力度文案
        if 推理 is not None and 翻译 is not None:#有推理
            if 有效力度 is None:#提供方默认
                力度标签=翻译('effort.providerDefault')#默认文
            else:#显式
                力度标签=有效力度#回退 id
                级列表=推理['efforts'] if 'efforts' in 推理 and 推理['efforts'] is not None else []#力度
                for 级 in 级列表:#找名
                    if 级['id']==有效力度:#命中
                        名=级['name'] if 'name' in 级 else None#名
                        力度标签=名 if 名 else 有效力度#名
                        break#停
        模型标签=当前模型['name'] if 当前模型 is not None and 'name' in 当前模型 else None#模型名
        if 模型标签 is None and 翻译 is not None:#回退
            模型标签=翻译('trigger.fallback')#回退
        态名=状态['status'] if 'status' in 状态 else None#状态
        失败=状态['failures'] if 'failures' in 状态 and 状态['failures'] is not None else []#分组失败
        锁定=自身.属性['locked'] if 'locked' in 自身.属性 else None#锁定
        return {#结构化视图
            'type':'model-select',#类型
            'open':自身.打开,#开
            'pane':自身.面板,#面板
            'locked':锁定,#锁定
            'modelLabel':模型标签,#模型标签
            'effortLabel':力度标签,#力度标签
            'busy':态名=='selecting',#忙碌
            'status':态名,#状态
            'error':状态['error'] if 自身.上次动作=='load' and 'error' in 状态 else None,#加载错
            'failures':失败,#分组失败
            'choices':行列表,#行
            'current':当前,#当前
            'reasoning':推理,#推理元
            'effectiveEffort':有效力度,#有效力度
            'toast':自身.吐司,#吐司
            'toggle':自身.打开菜单 if not 自身.打开 else 自身.关闭,#切换
            'setPane':自身.切面板,#切面板
            'choose':自身.选定模型,#选模型
            'chooseEffort':自身.选定力度,#选力度
            'reload':自身.重载,#重载
            'css':样式表,#样式
        }#视图结束

    def __call__(自身,属性=None):#组件调用
        """对齐 React 组件调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
