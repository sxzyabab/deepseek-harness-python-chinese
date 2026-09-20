__all__=['消息反馈动作']#仅中文公开名

def 缺省翻译(键,_插值=None):#无文案函数
    """原样返回键。"""
    return 键#键

class 消息反馈动作:#一条消息的反馈控件
    """赞/踩对 + 可选说明编辑器。"""
    def __init__(自身,属性):#按合成 props 构造
        """记下 props。"""
        自身.属性=属性#合成 props
        自身.说明打开=False#说明编辑器
        自身.草稿=''#说明草稿
        自身.进行中=False#动作进行中
        自身.失败=None#失败文案
        自身.已播种=False#是否已 ensure
        自身.存活=True#实例是否仍挂载

    def 更新(自身,属性):#props 变更
        """刷新合成 props。"""
        自身.属性=属性#最新

    def 卸载(自身):#卸载
        """标死。"""
        自身.存活=False#死

    def 播种(自身):#首次交互加载
        """Session 反馈只读一次。"""
        if 自身.已播种:#已播种
            return#跳过
        自身.已播种=True#记下
        确保=自身.属性['ensure'] if 'ensure' in 自身.属性 else None#ensure
        if 确保 is not None:#有
            确保()#加载；控制器.ensure 已等待

    def 结算(自身,结果):#动作结算
        """更新进行中与失败文案。"""
        if not 自身.存活:#已死
            return#丢弃
        自身.进行中=False
        if 结果['ok']:#成功
            自身.失败=None
            return
        翻译=自身.属性['t'] if 't' in 自身.属性 else 缺省翻译#文案
        错=结果['error'] if 'error' in 结果 else None#错误
        码=错['code'] if 错 is not None and 'code' in 错 else None#错误码
        自身.失败=翻译('error.conflict') if 码=='version-conflict' else 翻译('error.generic')#文案

    def 评分(自身,下一):#点赞/踩
        """走 toggle。"""
        自身.播种()#确保已读
        自身.进行中=True#进行中
        自身.失败=None
        自身.说明打开=False#关说明
        切换=自身.属性['toggle'] if 'toggle' in 自身.属性 else None#toggle
        消息标识=自身.属性['messageId']#消息 id
        结果=切换(消息标识,下一) if 切换 is not None else {'ok':True}#切换；控制器.toggle 已等待
        自身.结算(结果)#结算

    def 保存说明(自身,当前评价):#保存说明
        """空草稿走 clearNote。"""
        修剪=自身.草稿.strip()#修剪
        自身.进行中=True#进行中
        自身.失败=None
        消息标识=自身.属性['messageId']#消息 id
        if 修剪=='':#空
            结果=自身.属性['clearNote'](消息标识)#清说明；已等待
        else:#有内容
            结果=自身.属性['rate'](消息标识,当前评价,修剪)#写入；已等待
        自身.结算(结果)#结算
        if 结果['ok'] and 自身.存活:#成功且存活
            自身.说明打开=False#关

    def 视图(自身):#读视图模型
        """赞/踩状态与说明编辑器。"""
        用反馈=自身.属性['useFeedback'] if 'useFeedback' in 自身.属性 else None#选择器
        消息标识=自身.属性['messageId']#消息 id
        翻译=自身.属性['t'] if 't' in 自身.属性 else 缺省翻译#文案
        if 用反馈 is None:#无
            项=None#无条目
            加载失败=False#无
        else:#有
            def 选条目(视):#选该消息条目
                """从 items 取本消息。"""
                表=视['items']#条目表
                return 表[消息标识] if 消息标识 in 表 else None#条目
            def 选失败(视):#选加载失败
                """status 是否 error。"""
                return 视['status']=='error'#失败
            项=用反馈(选条目)#条目
            加载失败=用反馈(选失败)#加载失败
        评价=项['rating'] if 项 is not None and 'rating' in 项 else None#评价
        说明=项['note'] if 项 is not None and 'note' in 项 else None#已存说明
        return {#视图
            'rating':评价,#评价
            'noteOpen':自身.说明打开,#说明开闭
            'draft':自身.草稿,#草稿
            'pending':自身.进行中,#进行中
            'failure':自身.失败 if 自身.失败 is not None else (翻译('error.load') if 加载失败 else None),#失败
            'likeLabel':翻译('action.likeActive') if 评价=='positive' else 翻译('action.like'),#赞标签
            'dislikeLabel':翻译('action.dislikeActive') if 评价=='negative' else 翻译('action.dislike'),#踩标签
            'note':说明,#已存说明
        }#视图结束

    def __call__(自身,属性=None):#组件调用形
        """组件调用形；返回视图。"""
        if 属性 is not None:#有新 props
            自身.更新(属性)#刷新
        return 自身.视图()#视图
