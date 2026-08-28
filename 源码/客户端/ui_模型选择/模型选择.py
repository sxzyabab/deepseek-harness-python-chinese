"""撰写器模型座位：两级菜单（模型 / 推理等级）。

对齐上游 `ui-model-selection/src/client/ModelSelect.tsx`。公开面仅中文名。
"""
from ...依赖 import cordis#外部依赖胶水
是否thenable=cordis.工具.是否thenable#可等待判定

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

def 读(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 解开(值):#承诺则等待
    """承诺则等待，否则原样。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待
    return 值#同步

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

    def 读状态(自身):#目录快照
        """经 directory store。"""
        仓=读(自身.属性,'directory')#仓
        if 仓 is None:#无
            return {'current':None,'groups':[],'failures':[],'status':'idle','error':None}#空
        return 仓.getSnapshot()#快照

    def 展平行(自身,状态):#分组展平为选择行
        """group+model+selection。"""
        行们=[]#累积
        for 组 in 读(状态,'groups') or []:#各组
            for 模型 in 读(组,'models') or []:#各模型
                选={'provider':读(组,'id'),'model':读(模型,'id')}#选定
                默认=读(读(模型,'reasoning'),'defaultEffort')#默认力度
                if 默认 is not None:#有
                    选['reasoningEffort']=默认#带上
                行们.append({'group':组,'model':模型,'selection':选})#行
        return 行们#全部

    def 关闭(自身):#关菜单
        """回到根面板。"""
        自身.打开=False#关
        自身.面板='root'#根

    def 打开菜单(自身):#开菜单并刷新
        """根面板并 load。"""
        自身.面板='root'#根
        自身.打开=True#开
        自身.上次动作='load'#load
        加载=读(自身.属性,'load')#加载
        if 加载 is not None:#有
            加载()#拉

    def 选定模型(自身,选定):#选模型
        """同路由则关；否则 select。"""
        状态=自身.读状态()#快照
        当前=读(状态,'current')#当前
        if 当前 is not None and 读(当前,'provider')==读(选定,'provider') and 读(当前,'model')==读(选定,'model'):#同
            自身.关闭()#关
            return#结束
        自身.上次动作='select'#select
        提交=读(自身.属性,'select')#提交
        if 提交 is None:#无
            return#结束
        接受=解开(提交(选定))#提交
        if 接受:#成功
            自身.关闭()#关
            return#结束
        错=自身.读状态().get('error')#错误
        翻译=读(自身.属性,'t')#翻译
        if 错 is not None and 翻译 is not None:#有错
            自身.吐司序号+=1#序号
            自身.吐司={'seq':自身.吐司序号,'text':翻译('error.action',{'message':错})}#吐司

    def 选定力度(自身,力度):#选推理力度
        """改当前选定的 reasoningEffort。"""
        状态=自身.读状态()#快照
        当前=读(状态,'current')#当前
        if 当前 is None:#无
            return#结束
        选={'provider':读(当前,'provider'),'model':读(当前,'model')}#选定
        if 力度 is not None:#有力度
            选['reasoningEffort']=力度#带上
        自身.选定模型(选)#走同一提交

    def 渲染(自身):#结构化视图
        """产出与上游 JSX 同构的结构化视图。"""
        if not 读(自身.属性,'available'):#不可用
            return None#不渲染
        翻译=读(自身.属性,'t')#翻译
        状态=自身.读状态()#快照
        行们=自身.展平行(状态)#行
        当前=读(状态,'current')#当前
        当前行=None#当前选择行
        for 行 in 行们:#找
            选=行['selection']#选定
            if 当前 is not None and 读(当前,'provider')==选['provider'] and 读(当前,'model')==选['model']:#命中
                当前行=行#记下
                break#停
        推理=读(读(当前行,'model') if 当前行 else None,'reasoning')#推理元
        有效力度=读(当前,'reasoningEffort') if 当前 else None#当前力度
        if 有效力度 is None and 推理 is not None:#无则默认
            有效力度=读(推理,'defaultEffort')#默认
        力度标签=None#力度文案
        if 推理 is not None and 翻译 is not None:#有推理
            if 有效力度 is None:#提供方默认
                力度标签=翻译('effort.providerDefault')#默认文
            else:#显式
                力度标签=有效力度#回退 id
                for 级 in 读(推理,'efforts') or []:#找名
                    if 读(级,'id')==有效力度:#命中
                        力度标签=读(级,'name') or 有效力度#名
                        break#停
        模型标签=读(读(当前行,'model') if 当前行 else None,'name')#模型名
        if 模型标签 is None and 翻译 is not None:#回退
            模型标签=翻译('trigger.fallback')#回退
        return {#结构化视图
            'type':'model-select',#类型
            'open':自身.打开,#开
            'pane':自身.面板,#面板
            'locked':读(自身.属性,'locked'),#锁定
            'modelLabel':模型标签,#模型标签
            'effortLabel':力度标签,#力度标签
            'busy':读(状态,'status')=='selecting',#忙碌
            'status':读(状态,'status'),#状态
            'error':读(状态,'error') if 自身.上次动作=='load' else None,#加载错
            'failures':读(状态,'failures') or [],#分组失败
            'choices':行们,#行
            'current':当前,#当前
            'reasoning':推理,#推理元
            'effectiveEffort':有效力度,#有效力度
            'toast':自身.吐司,#吐司
            'toggle':自身.打开菜单 if not 自身.打开 else 自身.关闭,#切换
            'setPane':lambda 面:setattr(自身,'面板',面),#切面板
            'choose':自身.选定模型,#选模型
            'chooseEffort':自身.选定力度,#选力度
            'reload':lambda:(setattr(自身,'上次动作','load'),读(自身.属性,'load') and 读(自身.属性,'load')()),#重载
            'css':样式表,#样式
        }#视图结束

    def __call__(自身,属性=None):#组件调用
        """对齐 React 组件调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
