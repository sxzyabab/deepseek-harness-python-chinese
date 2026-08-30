"""终端 ANSI → 按行带样式 span。

对齐上游 `ui-primitives/src/ansi.ts` 可 Python 化段。公开面仅中文名。
剥 OSC/惰性控制；解析 CSI SGR 前景/背景/装饰；按行切开。
光标回放（\\r/退格/擦行）走列缓冲简化实现。
"""
import re#正则

__all__=['解析ansi行','净文本']#仅中文公开名

基本色令牌={#anser 基本 rgb → 主题 token
    '0,0,0':'var(--dsw-alias-label-primary)',
    '255,255,255':'var(--dsw-alias-label-primary)',
    '85,85,85':'var(--dsw-alias-label-tertiary)',
    '187,0,0':'var(--dsw-alias-state-error-primary)',
    '255,85,85':'var(--dsw-alias-state-error-secondary)',
    '0,187,0':'var(--dsw-alias-state-success-primary)',
    '0,255,0':'var(--dsw-alias-state-success-secondary)',
    '187,187,0':'var(--dsw-alias-state-warn-primary)',
    '255,255,85':'var(--dsw-alias-state-warn-secondary)',
    '0,0,187':'var(--dsw-alias-state-business-primary)',
    '85,85,255':'var(--dsw-static-blue-400)',
}#令牌结束

标准前景={#30-37 / 90-97 → rgb
    '30':'0,0,0','31':'187,0,0','32':'0,187,0','33':'187,187,0',
    '34':'0,0,187','35':'187,0,187','36':'0,187,187','37':'187,187,187',
    '90':'85,85,85','91':'255,85,85','92':'0,255,0','93':'255,255,85',
    '94':'85,85,255','95':'255,85,255','96':'85,255,255','97':'255,255,255',
}#前景结束

标准背景={#40-47 / 100-107
    '40':'0,0,0','41':'187,0,0','42':'0,187,0','43':'187,187,0',
    '44':'0,0,187','45':'187,0,187','46':'0,187,187','47':'187,187,187',
    '100':'85,85,85','101':'255,85,85','102':'0,255,0','103':'255,255,85',
    '104':'85,85,255','105':'255,85,255','106':'85,255,255','107':'255,255,255',
}#背景结束

装饰样式={#装饰名 → css
    'bold':{'fontWeight':700},'dim':{'opacity':0.7},
    'italic':{'fontStyle':'italic'},'underline':{'textDecoration':'underline'},
    'strikethrough':{'textDecoration':'line-through'},'hidden':{'visibility':'hidden'},
}#装饰结束

属性关闭={'22':('1','2'),'23':('3',),'24':('4',),'25':('5','6'),'27':('7',),'28':('8',),'29':('9',)}#关闭码
OSC串=re.compile(r'\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)?')#OSC
非CSI转义=re.compile(r'\x1b(?!\[)[\x20-\x2f]*[\x30-\x7e]?')#非 CSI
惰性控制=re.compile(r'[\x00-\x07\x0b-\x1a\x1c-\x1f\x7f]')#惰性 C0
CSI=re.compile(r'\x1b\[([\x30-\x3f]*)[\x20-\x2f]*([\x40-\x7e])')#CSI
需回放=re.compile(r'\r|\x08|\x1b\[[\x30-\x3f]*[\x20-\x2f]*K')#回车/退格/擦行
制表宽=8#制表停

def 折SGR(状态,参数):#叠 SGR
    """返回新 {fg,bg,attrs}。"""
    码们=['0'] if 参数=='' else 参数.split(';')#空=复位
    下=dict(状态)#拷
    下['attrs']=list(状态.get('attrs') or [])#属性可改
    索引=0#游标
    while 索引<len(码们):#逐码
        码=str(码们[索引])#当前
        if 码=='' or 码=='0':#复位
            下={'fg':'','bg':'','attrs':[]}#默认
            索引+=1#下
            continue#续
        if 码 in ('38','48'):#扩展色
            种=码们[索引+1] if 索引+1<len(码们) else ''#2/5
            跨=4 if 种=='2' else (2 if 种=='5' else 0)#跨度
            值=';'.join(码们[索引:索引+跨+1])#整段
            if 码=='38':#前景
                下['fg']=值#写
            else:#背景
                下['bg']=值#写
            索引+=跨+1#跳
            continue#续
        关=属性关闭.get(码)#关闭
        if 关 is not None:#关属性
            下['attrs']=[a for a in 下['attrs'] if a not in 关]#滤
            索引+=1#下
            continue#续
        if 码=='39':#默认前景
            下['fg']=''#清
            索引+=1#下
            continue#续
        if 码=='49':#默认背景
            下['bg']=''#清
            索引+=1#下
            continue#续
        if 码 in 标准前景:#标准前景
            下['fg']=码#码
            索引+=1#下
            continue#续
        if 码 in 标准背景:#标准背景
            下['bg']=码#码
            索引+=1#下
            continue#续
        if 码 not in 下['attrs']:#开属性
            下['attrs']=下['attrs']+[码]#追加
        索引+=1#下
    return 下#新态

def 码到rgb(码,是背景=False):#参数 → rgb 串
    """标准色表或 38/48 扩展。"""
    表=标准背景 if 是背景 else 标准前景#表
    if 码 in 表:#标准
        return 表[码]#rgb
    片=码.split(';')#扩展
    if len(片)>=3 and 片[1]=='5':#256 色粗映射：用字面灰阶近似
        try:#N
            n=int(片[2])#色号
            v=max(0,min(255,n))#夹
            return str(v)+','+str(v)+','+str(v)#灰
        except Exception:#失败
            return None#无
    if len(片)>=5 and 片[1]=='2':#真彩
        return 片[2]+','+片[3]+','+片[4]#rgb
    return None#无

def 解析样式(状态):#态 → css dict
    """无 SGR 则 None。"""
    样式={}#累
    前景码=状态.get('fg') or ''#fg
    背景码=状态.get('bg') or ''#bg
    背景rgb=码到rgb(背景码,True) if 背景码 else None#bg rgb
    if 背景rgb is not None:#有背景
        样式['backgroundColor']='rgb('+背景rgb+')'#bg
    if 前景码:#有前景
        前景rgb=码到rgb(前景码,False)#rgb
        if 前景rgb is not None:#有
            字面='rgb('+前景rgb+')'#字面
            if 背景rgb is None:#无背景走 token
                样式['color']=基本色令牌.get(前景rgb.replace(' ',''),字面)#token
            else:#有背景保字面
                样式['color']=字面#字面
    for 码 in 状态.get('attrs') or []:#装饰
        if 码=='1':#粗
            样式.update(装饰样式['bold'])#粗
        elif 码=='2':#暗
            样式.update(装饰样式['dim'])#暗
        elif 码=='3':#斜
            样式.update(装饰样式['italic'])#斜
        elif 码=='4':#下划
            样式.update(装饰样式['underline'])#下划
        elif 码=='9':#删
            样式.update(装饰样式['strikethrough'])#删
        elif 码=='8':#隐
            样式.update(装饰样式['hidden'])#隐
    return 样式 if 样式 else None#空则无

def 开SGR(状态):#态 → 规范序列
    """默认态空串。"""
    码=list(状态.get('attrs') or [])#属性
    if 状态.get('fg'):#前景
        码.append(状态['fg'])#跟
    if 状态.get('bg'):#背景
        码.append(状态['bg'])#跟
    return '' if not 码 else '\x1b['+';'.join(码)+'m'#序列

def 同SGR(甲,乙):#相等
    """比较。"""
    return (甲.get('fg')==乙.get('fg') and 甲.get('bg')==乙.get('bg')
            and list(甲.get('attrs') or [])==list(乙.get('attrs') or []))#同

默认态={'fg':'','bg':'','attrs':[]}#默认

def 回放一行(行,进入态):#列缓冲回放
    """处理 \\r / 退格 / 擦行 / 制表。"""
    列=[]#稀疏格 {sgr,char,spacer?}
    光标=0#列
    态=dict(进入态)#当前
    态['attrs']=list(进入态.get('attrs') or [])#拷属性
    位=0#源下标

    def 清(索引,填):#清一格
        """宽对伙伴一并。"""
        while len(列)<=索引:#扩
            列.append(None)#空
        格=列[索引]#现
        if 格 and 格.get('spacer') and 索引>0:#尾半
            列[索引-1]={'sgr':dict(态),'char':填}#前导
        elif 格 and len(格.get('char') or '')>0:#可能宽
            if 索引+1<len(列) and 列[索引+1] and 列[索引+1].get('spacer'):#有尾
                列[索引+1]={'sgr':dict(态),'char':填}#尾
        列[索引]={'sgr':dict(态),'char':填}#本格

    def 消费(段):#写正文
        """逐字符。"""
        nonlocal 光标,态#改
        for 字 in 段:#逐字
            if 字=='\r':#回车
                光标=0#回
                continue#续
            if 字=='\x08':#退格
                光标=max(0,光标-1)#退
                continue#续
            if 字=='\t':#制表
                停=光标+制表宽-(光标%制表宽)#停
                while 光标<停:#填
                    while len(列)<=光标:#扩
                        列.append(None)#空
                    if 列[光标] is None:#未写
                        列[光标]={'sgr':dict(态),'char':' '}#空格
                    光标+=1#进
                continue#续
            清(光标,' ')#先清
            while len(列)<=光标:#扩
                列.append(None)#空
            列[光标]={'sgr':dict(态),'char':字}#写
            光标+=1#进

    for 匹配 in CSI.finditer(行):#逐 CSI
        消费(行[位:匹配.start()])#前正文
        位=匹配.end()#跳
        参数=匹配.group(1) or ''#参数
        终=匹配.group(2) or ''#终字
        if 终=='K':#擦行
            模=(参数.split(';')[0] if 参数 else '')#模式
            if 模=='1':#到光标
                for i in range(0,光标+1):#清
                    清(i,' ')#空格
            elif 模=='2':#整行
                列[:]=[]#空
            else:#光标到尾
                del 列[光标:]#丢
            continue#续
        if 终!='m':#非 SGR
            continue#忽略
        态=折SGR(态,参数)#折
    消费(行[位:])#尾
    出=''#重放
    活=dict(进入态)#已开
    活['attrs']=list(进入态.get('attrs') or [])#拷
    for 索引 in range(len(列)):#逐列
        格=列[索引] or {'sgr':dict(默认态),'char':' '}#缺省空格
        格态=格['sgr']#态
        if not 同SGR(格态,活):#变
            if not 同SGR(活,默认态):#离开非默认
                出+='\x1b[0m'#复位
            出+=开SGR(格态)#开
            活=格态#记
        if 格.get('spacer'):#尾半
            出+=' '#空格保列
        else:#字
            出+=格.get('char') or ''#字
    if not 同SGR(活,态):#末态
        if not 同SGR(活,默认态):#复位
            出+='\x1b[0m'#复位
        出+=开SGR(态)#开末
    return {'text':出,'sgr':态}#结果

def 应用光标(文本):#逐行回放
    """跨行贯穿 SGR。"""
    回=[]#行
    态=dict(默认态)#跨行
    for 原 in 文本.split('\n'):#切行
        行=re.sub(r'\r+$','',原)#剥 CRLF 尾 \\r
        if 需回放.search(行):#需缓冲
            果=回放一行(行,态)#回放
            回.append(果['text'])#文
            态=果['sgr']#末
        else:#只折 SGR
            回.append(行)#原
            for 匹配 in CSI.finditer(行):#CSI
                if 匹配.group(2)=='m':#SGR
                    态=折SGR(态,匹配.group(1) or '')#折
    return '\n'.join(回)#拼

def 净文本(文本):#剥无色转义
    """OSC/非 CSI/惰性 C0；光标先回放。"""
    已=OSC串.sub('',文本)#去 OSC
    已=非CSI转义.sub('',已)#去非 CSI
    return 惰性控制.sub('',应用光标(已))#回放后再剥

def 解析ansi行(文本):#→ [[span...], ...]
    """至少一行；span={text,style}。"""
    净=净文本(文本)#净
    当前=[]#当前行 spans
    行们=[当前]#至少一行
    态=dict(默认态)#当前态
    位=0#下标
    for 匹配 in CSI.finditer(净):#逐 CSI
        段=净[位:匹配.start()]#正文
        if 段:#有文
            for 片索引,片 in enumerate(段.split('\n')):#按行
                if 片索引>0:#换行
                    当前=[]#新行
                    行们.append(当前)#挂
                if 片!='':#非空
                    当前.append({'text':片,'style':解析样式(态)})#span
        位=匹配.end()#跳
        if 匹配.group(2)=='m':#SGR
            态=折SGR(态,匹配.group(1) or '')#折
    尾=净[位:]#尾巴
    if 尾 or not 行们[0]:#有尾或保底
        for 片索引,片 in enumerate(尾.split('\n')):#切
            if 片索引>0:#换行
                当前=[]#新
                行们.append(当前)#挂
            if 片!='':#非空
                当前.append({'text':片,'style':解析样式(态)})#span
    return 行们#按行
