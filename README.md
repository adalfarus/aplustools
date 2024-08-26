[![Active Development](https://img.shields.io/badge/Maintenance%20Level-Actively%20Developed-brightgreen.svg)](https://gist.github.com/cheerfulstoic/d107229326a01ff0f333a1d3476e068d)
[![CI Test Status](https://github.com/Adalfarus/aplustools/actions/workflows/test-package.yml/badge.svg)](https://github.com/Adalfarus/aplustools/actions)
[![License: LGPL-2.1](https://img.shields.io/github/license/Adalfarus/aplustools)](https://github.com/Adalfarus/aplustools/blob/main/LICENSE)

# aplustools

aplustools is a simple, user-friendly Python library for performing amazing tasks. It simplifies complex processes, allowing you to achieve more with less code. Developed with a focus on ease of use and efficiency, aplustools is the go-to solution for Python developers looking to enhance their projects.

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

You can install aplustools via pip:

```sh
pip install aplustools[all] --upgrade
```

Or clone the repository and install manually:

```sh
git clone https://github.com/Adalfarus/aplustools.git
cd aplustools
python -m build
```

## Usage

Here are a few quick examples of how to use aplustools:

### Search Engine usage
```python
from aplustools.web.search import Search, GoogleSearchCore

# Call the `google_provider` function with a query
searcher = Search(GoogleSearchCore(advanced=True))
results = searcher.search("Cute puppies", num_results=10)

# Print the results
print(results)

from aplustools.web.utils import WebPage

web_page = WebPage(next(iter(results)).get("url"))

if web_page.crawlable:
    print(web_page.page.content)
```

### Timer usage
````python
from aplustools.package.timid import TimidTimer
from datetime import timedelta
import time

# Setting up your own timer
# Here we use the TimidTimer with the current time and a nanosecond multiplier
mySpecialTimer = TimidTimer.setup_timer_func(time.time, to_nanosecond_multiplier=1e9)

# Initialize the timer starting at 2.3 seconds
my_timer = mySpecialTimer(start_at=2.3)

# Perform some task
time.sleep(3.2)

# Print the elapsed time
print("This took:", my_timer.end())  # Expected output is approximately 1 second as we started at 2.3 seconds

# Advanced timer usage
timer = TimidTimer()

# Measure the average elapsed time over multiple iterations
for _ in range(4):
  timer.wait_ms_static(1000)  # Wait for 1 second
  timer.tock()  # Record the time
print("Average 1 second sleep extra delay:", timer.average() - timedelta(seconds=1))

# Using multiple timers within one timer object
with timer.enter(index=1):
  time.sleep(1)

# Using the timer for timed function execution
timer.start(1)  # Start the timer at index 1
timer.shoot(interval=1, function=lambda: print("Shooting", timer.tock(1, return_type="timedelta")), iterations=3)
print(timer.end())  # End the timer at index 0 which started when the timer object was created

# Defining a function with linear time complexity
def linear_time(n):
  for _ in range(n):
    pass

# Create an input generator for the linear time function
def create_simple_input_generator():
  return ((tuple([n]), {}) for n in range(1, 100_001, 100))

# Measure the average time complexity of the function
print(timer.complexity(linear_time, create_simple_input_generator()))

# Plotting the time complexity curve
from matplotlib import pyplot
print(timer.complexity(linear_time, create_simple_input_generator(), matplotlib_pyplt=pyplot))

# Define a more complex function
def complex_func(n, m, power=2):
  return sum(i ** power for i in range(n)) + sum(j ** power for j in range(m))

# Define a varying function
def varying_func(n, multiplier=1):
  return sum(i * multiplier for i in range(n))

# Create input generators for the complex functions
complex_input_generator = ((tuple([n, n // 2]), {'power': 2}) for n in range(1, 101))
varying_input_generator = ((tuple([n]), {'multiplier': (n % 3 + 1)}) for n in range(1, 101))

# Measure and print the estimated time complexity for the complex functions
print(f"Estimated Time Complexity for complex_func: {timer.complexity(complex_func, complex_input_generator, matplotlib_pyplt=pyplot)}")
print(f"Estimated Time Complexity for varying_func: {timer.complexity(varying_func, varying_input_generator, matplotlib_pyplt=pyplot)}")
````

### Security usage
````python
from aplustools.security.crypto.algorithms import Sym, ASym, MessageAuthenticationCode, KeyDerivation, HashAlgorithm
from aplustools.security.crypto import AdvancedCryptography, DigitalSigner, DataEncryptor, PasswordManager
from aplustools.security.crypto.backends import Backend
from aplustools.security import Security

ac = AdvancedCryptography(Backend.pycryptodomex)  # This backend is not yet fully supported

h = ac.hash(b"Hello World", HashAlgorithm.ARGON2, force_text_ids=True)
print(f"The hash is {h} and it is {'verified' if ac.hash_verify(b'Hello World', h, forced_text_ids=True) else 'unverified'}")

dp = ac.key_derivation(b"MySuperStrongPassword", 24, b"\x00\x01\x91\xfa", KeyDerivation.Scrypt, Security.STRONG)
print(f"Your derived password is {dp}")

aes_128 = Sym.Cipher.AES.key(128)
cipher_128 = ac.encrypt(b"ToEncrypt", aes_128, Sym.Padding.PKCS7, Sym.Operation.GCM)
print(aes_128, cipher_128, ac.decrypt(cipher_128, aes_128, Sym.Padding.PKCS7, Sym.Operation.GCM))

code = ac.generate_auth_code(MessageAuthenticationCode.HMAC, aes_128, b"MyData", Security.STRONG)
print(code == ac.generate_auth_code(MessageAuthenticationCode.HMAC, aes_128, b"MyData", Security.STRONG))

ecc_key = ASym.Cipher.ECC.ecdsa_key(ASym.Cipher.ECC.Curve.SECP256R1)
signature = ac.sign(b"DATA", ecc_key, strength=Security.STRONG)
print(ecc_key, signature, ac.sign_verify(b"DATA", signature, ecc_key, strength=Security.STRONG))

# Clean up sensitive data
del aes_128, dp, h, cipher_128, code, ecc_key, signature

# There are also easy utility classes for specific cryptographic use cases
encryptor = DataEncryptor(256)  # Encryption and Decryption with Generated Key
encrypted_data = encryptor.encrypt_data(b"Hello World")
decrypted_data = encryptor.decrypt_data(encrypted_data)
print(f"Decrypted Data: {decrypted_data}")
assert decrypted_data == b"Hello World"

key = Sym.Cipher.AES.key(256).get_key()  # Encryption and Decryption with Existing Key
encryptor_with_key = DataEncryptor(key)
encrypted_data_with_key = encryptor_with_key.encrypt_data(b"Hello World")
decrypted_data_with_key = encryptor_with_key.decrypt_data(encrypted_data_with_key)
print(f"Decrypted Data with Key: {decrypted_data_with_key}")
assert decrypted_data_with_key == b"Hello World"

retrieved_key = encryptor_with_key.get_key()  # Retrieve Key
print(f"Retrieved Key: {retrieved_key}")
assert key == retrieved_key

signer = DigitalSigner()  # Digital Signing and Verification with Generated Key Pair
signature = signer.sign_data(b"Hello World")
verification = signer.verify_signature(b"Hello World", signature)
print(f"Signature Verification: {verification}")
assert verification

retrieved_key_pair = signer.get_private_key()  # Retrieve Key Pair
print(f"Retrieved Key Pair: {retrieved_key_pair}")

signer_with_key_pair = DigitalSigner(retrieved_key_pair)  # Digital Signing and Verification with Existing Key Pair
signature_with_key_pair = signer_with_key_pair.sign_data(b"Hello World")
verification_with_key_pair = signer_with_key_pair.verify_signature(b"Hello World", signature_with_key_pair)
print(f"Signature Verification with Key Pair: {verification_with_key_pair}")
assert verification_with_key_pair
assert retrieved_key_pair == signer_with_key_pair.get_private_key()

pm = PasswordManager(backend=Backend.pycryptodomex)  # Password Hashing and Verification
hashed_pw = pm.hash_password("MySecretPassword", strength=Security.BASIC)
pw_verification = pm.verify_password("MySecretPassword", hashed_pw, strength=Security.BASIC)
print("Hashed Password:", hashed_pw)
print("Verification:", pw_verification)
assert pw_verification

# Clean up sensitive data
del (encryptor, encrypted_data, key, encryptor_with_key, encrypted_data_with_key, retrieved_key, signer, signature, 
     retrieved_key_pair, signer_with_key_pair, signature_with_key_pair, pm, hashed_pw)

# For strong and secure Message encryption, you can check out security.protocols.secure_message
from aplustools.security.protocols.control_code_protocol import ControlCodeProtocol, is_control_code
from aplustools.security.protocols.secure_message import MessageDecoder, MessageEncoder
from aplustools.security.rand import SecretsRandomGenerator
from aplustools.package.timid import TimidTimer

timer = TimidTimer()
protocol = ControlCodeProtocol()

decoder = MessageDecoder(protocol=protocol)
encoder = MessageEncoder(protocol=protocol, public_key_bytes=decoder.get_public_key_bytes())

while True:
    try:
        # Generate and add random messages
        random_messages = [SecretsRandomGenerator.generate_random_string(length=50) for _ in range(5)]

        for msg in random_messages:
            encoder.add_message(msg)

        message = encoder.flush()

        for chunk in message:
            decoder.add_chunk(chunk)

        decoded_messages = decoder.get_complete()

        # Verify the results
        correct = True
        for msg in random_messages:
            if msg not in decoded_messages:
                print(f"Missing message: {msg}")
                correct = False

        control_codes_correct = all(
            is_control_code(part) or isinstance(part, str) for part in decoded_messages
        )

        if correct and control_codes_correct:
            print("All messages and control codes are correct.")
        else:
            print("There was an error in the encoding/decoding process.")
            raise KeyboardInterrupt

        end = timer.tock()
        print("Decoded messages:", decoded_messages)
        print("Time taken:", end)
    except KeyboardInterrupt:
        print("Ending")
````

### System
````python
from aplustools.io.environment import get_system, BasicSystem


local_system = get_system()
print(type(local_system))  # This will output a specialized class

system_theme = local_system.get_system_theme()
clipboard = local_system.get_clipboard()
local_system.send_notification("Title", "Message", (), ())
local_system.schedule_event("My event", script_path="./my_script.exe", event_time="startup")

print(f"{round(BasicSystem.get_uptime(), 2)} minutes")
print(BasicSystem.measure_network_speed())

for process in BasicSystem.get_running_processes():
    print(process)
````

### PasswordGenerators
````python
from aplustools.security.passwords import QuickGeneratePasswords


input_sentence = input("Please input a sentence structure (Ww!): ")
password = QuickGeneratePasswords.generate_sentence_based_password(input_sentence)
print(f"Your password is {password}")


from aplustools.security.passwords import SecurePasswordGenerator

generator = SecurePasswordGenerator("strong")
secure_password = generator.generate_secure_password()
print(f"Secure password {secure_password}")
````
You can use the password generators like this in e.g. batch scripts:
```batch
@echo off
python -c "from aplustools.security.passwords import SecurePasswordGenerator; pw = SecurePasswordGenerator(""strong"").generate_secure_password(); print(f""{pw[""password""]}\n{pw[""extra_info""]} -> {pw[""worst_case""]}"")"
pause
```
or like this
````batch
@echo off
set /p id=Enter ID: 
python -c "from aplustools.security.passwords import SpecificPasswordGenerator; print(SpecificPasswordGenerator().generate_sentence_based_password_v3("""%id%""", random_case=True, extra_char="""_""", char_position=0, num_length=5, special_chars_length=2))"
pause
````

(If you have problems with the package please use `py -3.12 -m pip install aplustools[all] --upgrade --user`)
(Correct shortform for aplustools is aps, so please use ```import aplustools as aps``` for consistency)

### aps cli
Can currently run tests with ```aps tests run tests/ -minimal``` and show a basic help using ```aps help```.

For more detailed usage and examples, check out our [documentation](https://github.com/adalfarus/aplustools/wiki).

## Naming convention, dependencies and more
[PEP 8 -- Style Guide for Python Code](https://peps.python.org/pep-0008/#naming-conventions)

For modules I use 'lowercase', classes are 'CapitalizedWords' and functions and methods are 'lower_case_with_underscores'.

Sub-Modules that may be removed in future updates due to being hard to support or simply unneeded:
- database (maybe unneeded and hard to support if more dbs are added -> new_database is being developed)
- loggers (maybe unneeded, default logging module is just really good)

## Contributing

We welcome contributions! Please see our [contributing guidelines](https://github.com/adalfarus/aplustools/blob/main/CONTRIBUTING.md) for more details on how you can contribute to aplustools.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a pull request

### Aps Build master

You can use the aps_build_master script for your os to make your like a lot easier.
It supports running tests, installing, building and much more as well as chain together as many commands as you like.

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
