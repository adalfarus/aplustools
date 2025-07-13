[![Active Development](https://img.shields.io/badge/Maintenance%20Level-Actively%20Developed-brightgreen.svg)](https://gist.github.com/cheerfulstoic/d107229326a01ff0f333a1d3476e068d)
[![CI Test Status](https://github.com/Adalfarus/aplustools/actions/workflows/test-package.yml/badge.svg)](https://github.com/Adalfarus/aplustools/actions)
[![License: LGPL-2.1](https://img.shields.io/github/license/Adalfarus/aplustools)](https://github.com/Adalfarus/aplustools/blob/main/LICENSE)
[![PyPI Downloads](https://static.pepy.tech/badge/aplustools)](https://pepy.tech/projects/aplustools)
![coverage](./coverage-badge.svg)

# aplustools2

aplustools2 is a simple, user-friendly Python library for performing amazing tasks. It simplifies complex processes, allowing you to achieve more with less code. Developed with a focus on ease of use and efficiency, aplustools is the go-to solution for Python developers looking to enhance their projects.

## Compatibility
🟩 (Works perfectly); 🟨 (Untested); 🟧 (Some Issues); 🟥 (Unusable)

| OS                       | UX & README instructions | Tests | More Complex Functionalities |
|--------------------------|--------------------------|-------|------------------------------|
| Windows                  | 🟩                       | 🟩    | 🟩                           |
| MacOS                    | 🟨                       | 🟩    | 🟨                           |
| Linux (Ubuntu 22.04 LTS) | 🟩                       | 🟩    | 🟨                           |

## Features

- Easy to use for beginners, but not lacking for experts
- Pretty efficient
- Supports the three main platforms
- Regular updates and support
- Comprehensive documentation

## Installation

You can install aplustools2 via pip:

```sh
pip install aplustools[all] --pre --upgrade
```

Or clone the repository and install manually:

```sh
git clone https://github.com/Adalfarus/aplustools.git
cd aplustools
python -m build
```

(If you have problems with the package please use `py -m pip install aplustools[all] --pre --upgrade --user`)
(The standard shortform for aplustools is aps, so please use ```import aplustools as aps``` for consistency)

## 📦 Usage

Here are a few quick examples of how to use `aplustools`.

---

### 🔁 `auto_repr`: Auto-generate clean `__repr__`

```python
from aplustools.io.env import auto_repr

@auto_repr
class Person:
    def __init__(self, name: str, age: int, email: str):
        self.name = name
        self.age = age
        self.email = email
        self._internal = "should be hidden"

p = Person("Alice", 30, "alice@example.com")
print(p)  # Person(name=Alice, age=30, email=alice@example.com)
```

---

### 🔁 `auto_repr_with_privates`: Show private fields too

```python
from aplustools.io.env import auto_repr_with_privates

class Person:
    def __init__(self, name: str, age: int):
        self.name = name
        self._age = age  # Will be shown in __repr__

auto_repr_with_privates(Person, use_repr=True)
print(Person("Bob", 42))  # Person(name='Bob', _age=42)
```

---

## 🔐 File Locking (Cross-Platform)

### ✅ Manual file locking via `get_system()`

```python
from aplustools.io.env import get_system

fd = get_system().lock_file("test.lock", blocking=True)
print(get_system().is_file_locked("test.lock"))  # True
get_system().unlock_file(fd)
```

---

### ✅ Context-managed locking via `OSFileLock`

```python
from aplustools.io.fileio import OSFileLock

with OSFileLock("test.lock") as fd:
    print(f"Locked with fd={fd}")
# Lock is automatically released here
```

---

### ✅ Pythonic locking with `os_open` (like `open()`)

```python
from aplustools.io.fileio import os_open

with os_open("example.txt", "w") as file:
    file.write("Hello, safely locked world!\n")
```

> Internally uses `OSFileLock` for safe, exclusive access across platforms (Unix/Windows).

---

## 🔢 Binary Encoding Utilities (`aplustools.data.bintools`)

Efficient tools for working with binary formats and structured bytes.

---

### 📏 Measure bit and byte length

```python
from aplustools.data.bintools import bit_length, bytes_length

print(bit_length(42))      # 6
print(bytes_length(1000))  # 2
```

---

### 🔁 Encode/Decode integers

```python
from aplustools.data.bintools import encode_integer, decode_integer

encoded = encode_integer(123456)
print(encoded)             # b'\x01\xe2@'

decoded = decode_integer(encoded)
print(decoded)             # 123456
```

---

### 🔁 Encode/Decode floats

```python
from aplustools.data.bintools import encode_float, decode_float

f_bytes = encode_float(3.14159, precision="single")
print(decode_float(f_bytes, precision="single"))  # ~3.14159
```

---

### 📦 Variable-length integer encoding

```python
from aplustools.data.bintools import to_varint_length, read_varint_length
import io

data = to_varint_length(300)
length = read_varint_length(io.BytesIO(data))
print(length)  # 300
```

---

### 📏 Human-readable size formatting

```python
from aplustools.data.bintools import bytes_to_human_readable_binary_iec

print(bytes_to_human_readable_binary_iec(1024))      # 1.0 KiB
print(bytes_to_human_readable_binary_iec(1048576))   # 1.0 MiB
```

---

## 🔐 Secure Password Generation (`aplustools.security.passwords`)

Create readable, secure, and crack-resistant passwords.

---

### 🔑 Generate secure passwords easily

```python
from aplustools.security.passwords import SecurePasswordGenerator

generator = SecurePasswordGenerator(security="super_strong")
pw_data = generator.passphrase()

print(pw_data["password"])     # Actual password
print(pw_data["extra_info"])   # Generation method metadata
```

---

### 🔧 Available styles

```python
generator.sentence()         # Readable sentence
generator.pattern()          # Format like Aa99##
generator.complex_pattern()  # Pattern + random word mix
generator.complex()          # High entropy, mixed format
generator.mnemonic()         # Easy to remember
```

---

### 🧠 Estimate worst-case crack time

```python
pw_data = generator.generate_secure_password(return_worst_case=True)
print(pw_data["worst_case"])  # e.g., "centuries"
```

---

## ⏱ Basic Timing (`aplustools.package.chronokit`)

Measure elapsed time with nanosecond resolution.

---

### ⏲ Use `BasicTimer` for simple measurements

```python
from aplustools.package.chronokit import BasicTimer
import time

timer = BasicTimer(auto_start=True)
time.sleep(0.123)
timer.stop()

print(timer.get())          # timedelta
print(timer.get_readable()) # Human-readable
```

---

### 📏 Create precise deltas

```python
from aplustools.package.chronokit import PreciseTimeDelta

delta = PreciseTimeDelta(seconds=1.5, microseconds=250)
print(str(delta))           # 0:00:01.500250
print(delta.to_readable())  # "1.500s"
```

---

## ⏱ Flexible Timing with `FlexTimer`

Advanced control for performance tracking, interval measurements, and benchmarking.

---

### 🧪 Measure CPU-only time (ignores sleep)

```python
from aplustools.package.chronokit import CPUFTimer

with CPUFTimer():
    sum(i * i for i in range(100_000))
```

> Ideal for benchmarking with minimal system interference.

---

### 🔄 Manual start/stop and waiting

```python
from aplustools.package.chronokit import FlexTimer

t = FlexTimer(start_now=False)
t.start(start_at=1.2)
t.wait(0.8)
t.stop()

print(t.get().to_clock_string())  # e.g., 00:00:02.00
```

---

### ⏱ Record laps (interval checkpoints)

```python
t = FlexTimer()
# ... task 1 ...
t.lap()
# ... task 2 ...
t.lap()

print(t.show_laps())  # List of lap durations
```

---

### 🪄 Time entire functions with a decorator

```python
@FlexTimer().time()
def compute():
    return [x**2 for x in range(1_000_000)]

compute()  # Prints execution time
```

---

### 🕒 Schedule callbacks after a delay

```python
def on_done():
    print("Finished!")

FlexTimer().after(2, on_done)
```

---

### 🧵 Run functions at intervals

```python
def tick():
    print("Tick!")

FlexTimer().interval(1, count=5, callback=tick)
```

---

### 📈 Estimate time complexity of a function

```python
def fn(n):
    return [i ** 2 for i in range(n)]

def gen_inputs():
    for i in range(1000, 50000, 1000):
        yield ((i,), {})

from aplustools.package.chronokit import FlexTimer
print(FlexTimer.complexity(fn, gen_inputs()))  # e.g., "O(N)"
```

---

## ⚙️ Concurrency and Shared Memory (`aplustools.io.concurrency`)

Smart thread pools and safe process-shared memory.

---

### 🧵 Dynamic thread pool with auto-scaling

```python
from aplustools.io.concurrency import LazyDynamicThreadPoolExecutor
import time

def task(i):
    time.sleep(0.5)
    return f"Task {i}"

with LazyDynamicThreadPoolExecutor(min_workers=2, max_workers=10) as pool:
    results = [f.result() for f in [pool.submit(task, i) for i in range(5)]]

print(results)
```

---

### 🧠 Share memory across processes with `SharedStruct`

```python
from aplustools.io.concurrency import SharedStruct
from multiprocessing import Process

def increment(ref, count):
    shared = ref.dereference()
    for _ in range(count):
        with shared:
            val = shared.get_field(0)
            shared.set_field(0, val + 1)
    shared.close()

if __name__ == "__main__":
    counter = SharedStruct("i", create=True)
    counter.set_field(0, 0)

    p1 = Process(target=increment, args=(counter.reference(), 1000))
    p2 = Process(target=increment, args=(counter.reference(), 1000))
    p1.start(); p2.start(); p1.join(); p2.join()

    print("Final:", counter.get_field(0))  # 2000
    counter.close()
    counter.unlink()
```

---

### 📎 Struct format reference

* `"i"` — one 4-byte integer
* `"if"` — integer + float
* `"i10s"` — integer + 10-byte string

```python
with SharedStruct("if", create=True) as stats:
    stats.set_data(42, 3.14)
    print(stats.get_data())  # (42, 3.14)
```

---

## 🌐 Web Requests (`aplustools.web.request`)

Make web requests in sync or async mode — single or batch.

---

### 🔹 Quick HTTPS fetch

```python
from aplustools.web.request import fetch

data = fetch("https://httpbin.org/get")
print(data.decode())
```

---

### 🔸 Threaded batch requests with `BatchRequestHandler`

```python
from aplustools.web.request import BatchRequestHandler

handler = BatchRequestHandler(min_workers=2, max_workers=10)

# Single request
print(handler.request("https://httpbin.org/get").decode())

# Multiple (sync)
urls = ["https://httpbin.org/get"] * 5
print(len(handler.request_many(urls)))

# Multiple (async)
result = handler.request_many(urls, async_mode=True)
print(len(result.no_into().no_into_results))

handler.shutdown()
```

💡 The thread pool can be reused via `handler.pool`.

---

### ⚡ High-performance async requests with `AioHttpRequestHandler`

```python
from aplustools.web.request import AioHttpRequestHandler

aio = AioHttpRequestHandler()

print(aio.request("https://httpbin.org/get").decode())
print(len(aio.request_many(["https://httpbin.org/get"] * 5)))

aio.shutdown()
```

> Sync interface, but internally async. Great for sync environments that want async speed.

## 🔐 `aplustools.security.crypto`

This section demonstrates the flexible, backend-agnostic cryptography interface provided by `aplustools`. The section includes standard hashing, key derivation, and post-quantum encryption/signing using modern algorithms.

### 📦 Setup and Imports

```python
from aplustools.security.crypto.algos import (
    Sym,
    Asym,
    HashAlgorithm,
    KeyDerivationFunction,
)
from aplustools.security.crypto.exceptions import NotSupportedError
from aplustools.security.crypto import set_backend, Backend
import os
```

Set the std lib cryptography backend (you can later switch to advanced libraries like `cryptography`, `argon2-cffi`, etc.):

```python
set_backend()  # Uses Backend.std_lib
```

### 🔍 Hashing with Standard Algorithms

Most `HashAlgorithm` variants support `.hash()`, `.verify()`, and `.std_verify()`.

```python
# MD5
h = HashAlgorithm.MD5.hash(b"hello world")
print("MD5:", h.hex())
print("Verify:", HashAlgorithm.MD5.verify(b"hello world", h))
print("Std-Verify:", HashAlgorithm.std_verify(b"hello world", h))

# SHA1
h = HashAlgorithm.SHA1.hash(b"hello world")
print("SHA1:", h.hex())
print("Verify:", HashAlgorithm.SHA1.verify(b"hello world", h))
print("Std-Verify:", HashAlgorithm.std_verify(b"hello world", h))

# SHA256
h = HashAlgorithm.SHA2.SHA256.hash(b"hello world")
print("SHA256:", h.hex())
print("Verify:", HashAlgorithm.SHA2.SHA256.verify(b"hello world", h))
print("Std-Verify:", HashAlgorithm.std_verify(b"hello world", h))

# SHA3-256
h = HashAlgorithm.SHA3.SHA256.hash(b"hello world")
print("SHA3-256:", h.hex())
print("Verify:", HashAlgorithm.SHA3.SHA256.verify(b"hello world", h))
print("Std-Verify:", HashAlgorithm.std_verify(b"hello world", h))
```

### ⚖️ Hashing with Variable-Length and Specialized Algorithms

Some algorithms require an output length (e.g., SHAKE128, BLAKE2s):

```python
# SHAKE128 (8 bytes)
h = HashAlgorithm.SHA3.SHAKE128.hash(b"hello", 8)
print("SHAKE128:", h.hex())
print("Verify:", HashAlgorithm.SHA3.SHAKE128.verify(b"hello", h))
print("Std-Verify:", HashAlgorithm.std_verify(b"hello", h))

# BLAKE2s (8 bytes)
h = HashAlgorithm.BLAKE2.BLAKE2s.hash(b"hello", 8)
print("BLAKE2s:", h.hex())
print("Verify:", HashAlgorithm.BLAKE2.BLAKE2s.verify(b"hello", h))
print("Std-Verify:", HashAlgorithm.std_verify(b"hello", h))
```

Some algorithms are optional in std lib:

```python
# RIPEMD160
try:
    h = HashAlgorithm.RIPEMD160.hash(b"hello")
    print("RIPEMD160:", h.hex())
    print("Verify:", HashAlgorithm.RIPEMD160.verify(b"hello", h))
    print("Std-Verify:", HashAlgorithm.std_verify(b"hello", h))
except Exception as e:
    print("RIPEMD160 unsupported in std_lib:", e)
```

### 🔑 Key Derivation Functions (KDFs)

All KDFs support `.derive(password, salt, ...)` and produce fixed-length binary output:

```python
password = b"my-password"
salt = os.urandom(16)

print("PBKDF2HMAC:", KeyDerivationFunction.PBKDF2HMAC.derive(password, salt=salt).hex())
print("PBKDF1    :", KeyDerivationFunction.PBKDF1.derive(password, salt=salt, length=16).hex())
print("Scrypt    :", KeyDerivationFunction.Scrypt.derive(password, salt=salt, length=16).hex())
print("HKDF      :", KeyDerivationFunction.HKDF.derive(password, salt=salt).hex())
print("ConcatKDF :", KeyDerivationFunction.ConcatKDF.derive(password, otherinfo=b"my-info").hex())
```

### 🛠 Switch to Advanced Backends

Enable advanced features like post-quantum crypto and better hashing support:

```python
set_backend(
    [
        Backend.cryptography_alpha,  # Currently only supports hashes like SHA3
        Backend.quantcrypt,          # To enable post-quantum cryptography
        Backend.argon2_cffi,         # Required for Argon2
        Backend.bcrypt,              # Required for BCrypt
        Backend.std_lib,             # Fallback
    ]
)
```

### 🧂 Argon2 Hashing and Verification

```python
# Hash a password/message using Argon2
hashed = HashAlgorithm.ARGON2.hash(b"Ha", os.urandom(16))
print("\nArgon2 Hash:", hashed.decode())

# Verify the hash
is_valid = HashAlgorithm.ARGON2.verify(b"Ha", hashed)
print("Argon2 Valid:", is_valid)

try:
    print(
        "Std-Verify",
        HashAlgorithm.std_verify(
            b"Ha", hashed, fallback_algorithm="argon2", text_ids=False
        ),
    )  # Std-Verify can't decode special algos like argon2 or bcrypt
except NotSupportedError:
    print("Std-Verify failed")
```

### 🔐 BCrypt Hashing and Verification

```python
# Hash a password with BCrypt
bcrypt_hash = HashAlgorithm.BCRYPT.hash(b"my-secret-password")
print("BCrypt Hash:", bcrypt_hash.decode())

# Verify the password against the hash
is_valid = HashAlgorithm.BCRYPT.verify(b"my-secret-password", bcrypt_hash)
print("BCrypt Valid:", is_valid)
```

### 🔑 Argon2 / BCrypt for Secure Key Derivation

```python
# Derive a key using Argon2 KDF
derived_key = KeyDerivationFunction.ARGON2.derive(b"my-password", salt=os.urandom(16))
print("Argon2 Derived Key:", derived_key.hex())

# Derive a key using BCrypt KDF
bcrypt_key = KeyDerivationFunction.BCRYPT.derive(b"my-password", salt=os.urandom(16))
print("BCrypt Derived Key:", bcrypt_key.hex())
```

## 🔐 Asymmetric Encryption: Kyber (Post-Quantum KEM)

This demonstrates a Kyber key exchange using encapsulation (sender) and decapsulation (recipient):

```python
# Recipient generates a keypair
recipient_key = Asym.Cipher.KYBER.keypair.new("kyber1024")

# Extract public key from recipient and share it with the sender
pub_key_bytes = recipient_key.encode_public_key()
# Keys can't be regenerated and try: except: takes more space; 
# This can only happen if you do not pass one of the keys when using .decode( ... )
if pub_key_bytes is None:
    raise ValueError("recipient_key has no public key")

# Sender receives the public key and creates a key object with only the public key
sender_key = Asym.Cipher.KYBER.keypair.decode("kyber1024", public_key=pub_key_bytes)
# Sender encapsulates a shared secret for the recipient
ciphertext, shared_secret_sender = sender_key.encapsulate()

# Recipient decapsulates to recover the shared secret
shared_secret_recipient = recipient_key.decapsulate(ciphertext)

print("\n=== Kyber KEM Flow ===")
print(f"Ciphertext             : {ciphertext.hex()}")
print(f"Sender Shared Secret   : {shared_secret_sender.hex()}")
print(f"Recipient Shared Secret: {shared_secret_recipient.hex()}")
assert shared_secret_sender == shared_secret_recipient, "Shared secrets do not match!"
```

## ✍️ Asymmetric Signing: Dilithium (Post-Quantum Signature)

This demonstrates secure message signing and verification using the Dilithium signature algorithm:

```python
# Generate the signing keypair (private + public)
sign_key = Asym.Cipher.DILITHIUM.keypair.new("dilithium5")

# Sign a message using the private key
message = b"Hello World"
signature = sign_key.sign(message)

# Extract and share only the public key
pub_key_bytes = sign_key.encode_public_key()
# Keys can't be regenerated and try: except: takes more space; 
# This can only happen if you do not pass one of the keys when using .decode( ... )
if pub_key_bytes is None:
    raise ValueError("sign_key has no public key")

# Create a new key object with only the public key for verification
verify_key = Asym.Cipher.DILITHIUM.keypair.decode(
    "dilithium5", public_key=pub_key_bytes
)
# Verify the signature using the public key
is_valid = verify_key.sign_verify(message, signature)

print("\n=== Dilithium Signature Flow ===")
print(f"Signature     : {signature.hex()}")
print(f"Signature Valid? {is_valid}")
assert is_valid, "Signature verification failed!"
```

### aps cli
Can currently run tests with ```aps tests run tests/ -minimal``` and show a basic help using ```aps help```.

For more detailed usage and examples, check out our [documentation](https://github.com/adalfarus/aplustools/wiki).

## Naming convention, dependencies and library information
[PEP 8 -- Style Guide for Python Code](https://peps.python.org/pep-0008/#naming-conventions)

For modules I use 'lowercase', classes are 'CapitalizedWords' and functions and methods are 'lower_case_with_underscores'.

### Information
- Additional information will be added in the full release.

## Contributing

We welcome contributions! Please see our [contributing guidelines](https://github.com/adalfarus/aplustools/blob/main/CONTRIBUTING.md) for more details on how you can contribute to aplustools.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a pull request

### Aps Build master

You can use the aps_build_master script for your os to make your like a lot easier.
It supports running tests, installing, building and much more as well as chaining together as many commands as you like.

This example runs test, build the project and then installs it
````commandline
call .\aps_build_master.bat 234
````

````shell
sudo apt install python3-pip
sudo apt install python3-venv
chmod +x ./aps_build_master.sh
./aps_build_master.sh 234
````

## License

aplustools is licensed under the LGPL-2.1 License - see the [LICENSE](https://github.com/adalfarus/aplustools/blob/main/LICENSE) file for details.
