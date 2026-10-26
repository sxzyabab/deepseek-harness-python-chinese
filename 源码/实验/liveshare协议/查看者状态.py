'一次查看者读取可以结束的条件，以及每种条件对应的应答'
__all__=['查看者可达']

# 条件名是线路词汇，不译：share-not-found、share-stopped、share-expired、owner-offline、sign-in-expired、access-denied、relay-unreachable。
# retryable 可以再问，terminal 是对端的裁决。

查看者可达={
    'share-not-found':'terminal',
    'share-stopped':'terminal',
    'share-expired':'terminal',
    'owner-offline':'retryable',
    'sign-in-expired':'terminal',
    'access-denied':'terminal',
    'relay-unreachable':'retryable',
}
