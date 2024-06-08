import re

# Variable part that should be matched exactly
variable_part = "a4lXzWuMmk5lIw792npa4Jh5FMwqqZxYCDyQkANqhmlaR9EmLA"

# Construct the regex pattern using the variable part
pattern = re.compile(r'(' + re.escape("[") + re.escape(variable_part) + r'::.*?[^\\]' + re.escape("]") + ')')

text = '[a4lXzWuMmk5lIw792npa4Jh5FMwqqZxYCDyQkANqhmlaR9EmLA::NEWLINE]Meow'

matches = pattern.finditer(text)

# Initial positions
last_end = 0
results = []

for match in matches:
    start, end = match.span()
    # Append everything before the current match that hasn't been matched yet
    if start > last_end:
        results.append(text[last_end:start])
    # Append the current match
    results.append(match.group(0))
    last_end = end

# Append any remaining part of the text after the last match
if last_end < len(text):
    results.append(text[last_end:])

print(results)
