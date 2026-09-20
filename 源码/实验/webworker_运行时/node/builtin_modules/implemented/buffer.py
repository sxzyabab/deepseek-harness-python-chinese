from buffer import Buffer,kMaxLength

__all__=['Buffer','kMaxLength','constants','__esModule','default']

globals()['Buffer']=Buffer

constants={
    'MAX_LENGTH':kMaxLength,
    'MAX_STRING_LENGTH':536_870_888,
}

__esModule=True
default={'Buffer':Buffer,'constants':constants,'kMaxLength':kMaxLength}
