from aplustools.security.prot import BlackBox, SecureMemoryChunk


# memory = SecureMemoryChunk(1000)
# memory.write(b"\x10" * 100)
# memory.close()


bb = BlackBox()
x = bytearray(b"\x10\x12\xA2")
bb._attrs.d = x
print(x)


class Test:
    def link(self) -> bytes:
        return bytearray(b"\x01" * 4)


bb.link(Test())
print(bb.link_pub_key)
print(bb._attrs.bb_public_key)
print(bb._attrs._offsets)
