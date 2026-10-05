import base64,hashlib,json
__all__=[
    '紧凑json编码','读取json文件','字节转base64url','base64url转字节','严格解码base64',
    '摘要十六进制','json转base64url令牌','base64url令牌转json','构造dataurl','解析dataurl',
]#仅中文公开名

def 紧凑json编码(值,排序键:bool=False)->str:
    '编码为无空白、保留非ASCII、拒绝NaN与无穷的JSON文本；排序键为真时键按字典序输出，便于比较与取指纹'
    return json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False,sort_keys=排序键)#紧凑编码

def 读取json文件(路径:str):
    '按UTF-8读取并解析一个JSON文件，读完即关闭文件'
    with open(路径,'r',encoding='utf-8') as 文件:#以UTF-8打开
        return json.load(文件)#解析文件内容

def 字节转base64url(数据:bytes)->str:
    '字节编码为不带填充等号的base64url文本'
    return base64.urlsafe_b64encode(数据).decode('ascii').rstrip('=')#URL安全字母表并去掉填充

def base64url转字节(文本:str)->bytes:
    '解码不带填充等号的base64url文本'
    填充个数=(4-len(文本)%4)%4#补齐到4的倍数所需的等号个数
    return base64.urlsafe_b64decode(文本+'='*填充个数)#补回填充后解码

def json转base64url令牌(值,排序键:bool=False)->str:
    '把可JSON序列化的值编码成不带填充的base64url令牌，可安全放进URL，常用于分页游标与引用；需要稳定输出时开排序键'
    return 字节转base64url(紧凑json编码(值,排序键).encode('utf-8'))#先紧凑JSON再base64url

def base64url令牌转json(令牌:str):
    '解码 json转base64url令牌 产生的令牌；令牌非法时抛出ValueError的子类'
    return json.loads(base64url转字节(令牌).decode('utf-8'))#先还原字节再解析JSON

def 构造dataurl(媒体类型:str,数据:bytes)->str:
    '构造 data:媒体类型;base64,载荷 形式的 data URL'
    return f"data:{媒体类型};base64,{base64.b64encode(数据).decode('ascii')}"#标准base64载荷

def 解析dataurl(文本:str)->tuple:
    '解析 base64 形式的 data URL，返回 (媒体类型, 字节)；不是该形式或载荷非法时抛ValueError'
    if not 文本.startswith('data:'):#缺少协议前缀
        raise ValueError('不是 data URL')
    头部,逗号,载荷=文本[len('data:'):].partition(',')#逗号之前是媒体类型与参数
    if 逗号=='' or not 头部.endswith(';base64'):#只支持base64形式
        raise ValueError('不是 base64 形式的 data URL')
    return 头部[:-len(';base64')],base64.b64decode(载荷,validate=True)#严格解码载荷

def 严格解码base64(文本:str)->bytes:
    '只接受规范的标准base64：字符集合法、填充正确、非空；否则抛ValueError'
    字节=base64.b64decode(文本,validate=True)#严格校验字符集，非法字符直接抛错
    if len(文本)==0 or base64.b64encode(字节).decode('ascii')!=文本:#空串，或再编码与原文不一致
        raise ValueError('不是规范的base64文本')#拒绝非规范写法
    return 字节#返回解码后的字节

def 摘要十六进制(数据:str|bytes,算法名:str='sha256')->str:
    '计算摘要并以小写十六进制返回；文本先按UTF-8转字节；算法名取hashlib支持的名称'
    if isinstance(数据,str):#文本需要先转为字节
        数据=数据.encode('utf-8')#按UTF-8编码
    return hashlib.new(算法名,数据).hexdigest()#按指定算法计算摘要
