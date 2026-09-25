"""浏览器命令与桌面适配器共享的物理键协议；不含 DOM 或运行时状态。"""
import re#物理码校验

__all__=[#仅中文公开名
    '键名表','修饰键序','规范化绑定','绑定键','呈现绑定','Web绑定是否准入',
]#公开面结束

#键帽展示名；线协议 code 原样作键
键名表={
    'Slash':'/','Comma':',','Period':'.','Backslash':'\\','Backquote':'`','Minus':'-','Equal':'=',
    'BracketLeft':'[','BracketRight':']','Semicolon':';','Quote':"'",'Enter':'Enter',
    'Escape':'Esc','Space':'Space','Tab':'Tab','Backspace':'Backspace','Delete':'Delete',
    'ArrowUp':'↑','ArrowDown':'↓','ArrowLeft':'←','ArrowRight':'→',
}#键名表结束
修饰键序=('control','alt','shift','meta')#规范化修饰键顺序即键帽顺序
物理码模式=re.compile(r'^(Key[A-Z]|Digit[0-9]|F([1-9]|1[0-9]|2[0-4]))$')#字母数字功能键

def 规范化绑定(绑定,平台):
    """展开逻辑修饰键、去重并校验物理码；不支持的码在注册时抛错。"""
    #收集一或两个物理码并按字典序
    码表=[绑定['code']]#主码
    if 绑定.get('secondCode') is not None:#有第二键
        码表.append(绑定['secondCode'])#追加
    码表.sort()#排序使对顺序无关
    for 码 in 码表:#校验每个物理码
        if 物理码模式.match(码) is None and 码 not in 键名表:#既非标准码也非具名键
            raise ValueError('不支持的快捷键码: '+码)#拒绝
    if len(码表)==2 and 码表[0]==码表[1]:#双键相同
        raise ValueError('快捷键必须互不相同')#拒绝
    #展开 primary 并去重
    修饰集合=set()#物理修饰键集合
    for 值 in 绑定['modifiers']:#逐个声明
        if 值=='primary':#逻辑主修饰
            修饰集合.add('meta' if 平台=='macos' else 'control')#按平台展开
        else:#已是物理修饰
            修饰集合.add(值)#收入
    结果={'code':码表[0],'modifiers':[项 for 项 in 修饰键序 if 项 in 修饰集合]}#规范结果
    if len(码表)==2:#保留次码
        结果['secondCode']=码表[1]#次码
    return 结果#返回

def 绑定键(绑定):
    """由规范化绑定生成精确匹配索引，同时用于匹配与冲突检测。"""
    if 绑定.get('secondCode') is None:#单键
        码表=[绑定['code']]#仅主码
    else:#双键和弦
        码表=sorted([绑定['code'],绑定['secondCode']])#排序
    return '+'.join(list(绑定['modifiers'])+码表)#修饰+码

def 呈现绑定(绑定,平台):
    """格式化键帽与 ARIA；Windows 用加号分隔修饰键，和弦键仍相邻。"""
    if 绑定 is None:#未绑定
        return {'keys':[],'aria':None}#空
    #主键展示
    主码=绑定['code']#物理码
    键帽=键名表[主码] if 主码 in 键名表 else re.sub(r'^(Key|Digit)','',主码)#去前缀
    if 平台=='macos':#苹果符号
        符号={'control':'⌃','alt':'⌥','shift':'⇧','meta':'⌘'}#符号
    else:#其余平台文字
        符号={'control':'Ctrl','alt':'Alt','shift':'Shift','meta':'Meta'}#文字
    aria名={'control':'Control','alt':'Alt','shift':'Shift','meta':'Meta'}#ARIA 修饰名
    if 主码=='Space':#空格
        aria键='Space'#ARIA
    elif 主码=='Escape':#逃离
        aria键='Escape'#ARIA
    elif 主码.startswith('Arrow'):#方向
        aria键=主码#原码
    else:#其余用键帽
        aria键=键帽#键帽
    #次键展示
    次表=[]#次键帽
    次码=绑定.get('secondCode')#可选次码
    if 次码 is not None:#有次键
        次帽=键名表[次码] if 次码 in 键名表 else re.sub(r'^(Key|Digit)','',次码)#去前缀
        次表=[次帽]#列表
    键列=[符号[项] for 项 in 绑定['modifiers']]+[键帽]#修饰+主键
    if 平台=='windows':#Windows 插入加号
        展平=[]#展平列
        for 下标,标签 in enumerate(键列):#逐项
            if 下标==0:#首项
                展平.append(标签)#直接
            else:#其后
                展平.append('+')#加号
                展平.append(标签)#标签
        可见=展平+次表#含次键
    else:#非 Windows
        可见=键列+次表#相邻
    if 次码 is None:#单键可出 ARIA
        aria='+'.join([aria名[项] for 项 in 绑定['modifiers']]+[aria键])#ARIA 串
    else:#双键和弦 ARIA 不支持
        aria=None#省略
    return {'keys':可见,'aria':aria}#返回

def Web绑定是否准入(绑定,平台):
    """检查 Web 组合：Windows/macOS 另放行任意三或四修饰键；Linux 保留受限集合。"""
    if 绑定.get('secondCode') is not None:#和弦
        return False#Web 不收
    if 平台=='windows' or 平台=='macos':#宽平台
        if len(绑定['modifiers'])>=3:#三或四修饰
            return True#放行
        主修饰='meta' if 平台=='macos' else 'control'#逻辑主
        if len(绑定['modifiers'])==1:#单修饰特例
            唯一=绑定['modifiers'][0]#唯一修饰
            if 绑定['code'] in ('Comma','Backslash') and 唯一==主修饰:#逗号反斜杠
                return True#放行
            if 绑定['code']=='Backquote' and 唯一=='control':#反引号+Ctrl
                return True#放行
        if len(绑定['modifiers'])==2 and 主修饰 in 绑定['modifiers']:#主+另一
            if 'alt' in 绑定['modifiers'] or 'shift' in 绑定['modifiers']:#Alt 或 Shift
                return True#放行
    #Linux 与兜底：固定白名单
    for 候选 in (#受限集合
        {'code':'Slash','modifiers':['primary']},
        {'code':'Comma','modifiers':['primary','shift']},
        {'code':'Period','modifiers':['primary','shift']},
    ):#候选结束
        if 绑定键(绑定)==绑定键(规范化绑定(候选,平台)):#索引相同
            return True#准入
    return False#拒绝
