from aplustools.security.prot import BlackBox, SecureMemoryChunk


# memory = SecureMemoryChunk(1000)
# memory.write(b"\x10" * 100)
# memory.close()


bb = BlackBox()
bb._attrs.d = bytearray(b"\x00")


class Test:
    def link(self) -> bytes:
        return bytearray(b"\x00" * 4)


bb.link(Test())
print(bb.link_pub_key)
print(bb._attrs.bb_public_key)
print(bb._attrs._offsets)
