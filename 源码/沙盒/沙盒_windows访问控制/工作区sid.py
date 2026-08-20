"""按工作区的写入身份：从规范工作区路径确定性推导的 `S-1-4-x-y` SID。临时目录使用分开的身份，避免兄弟会话写入彼此的临时树。"""
import hashlib#SHA-256

def 工作区写入SID(工作区根):#推导工作区写入SID
    """推导工作区的写入 SID（`S-1-4-x-y`；子权威 30 位）。"""
    摘要=hashlib.sha256(工作区根.encode('utf-8')).digest()#对规范路径做SHA-256
    第一=(int.from_bytes(摘要[0:4],'little')%(2**30-1))+1#第一段30位子权威，避开0
    第二=(int.from_bytes(摘要[4:8],'little')%(2**30-1))+1#第二段30位子权威，避开0
    return 'S-1-4-'+str(第一)+'-'+str(第二)#两段子权威的SDDL

def 临时写入SID(临时目录):#推导临时目录写入SID
    """推导私有临时目录的写入 SID；固定第三段与工作区 SID 域分离。"""
    摘要=hashlib.sha256(b'temp\0'+临时目录.encode('utf-8')).digest()#域分离前缀再哈希路径
    第一=(int.from_bytes(摘要[0:4],'little')%(2**30-1))+1#第一段30位子权威，避开0
    第二=(int.from_bytes(摘要[4:8],'little')%(2**30-1))+1#第二段30位子权威，避开0
    return 'S-1-4-'+str(第一)+'-'+str(第二)+'-1'#第三段固定为1
