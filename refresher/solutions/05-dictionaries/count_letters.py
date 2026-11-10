# Count letters
# Python refresher, Dictionaries
#
# Write `count_letters(word)`, which returns a dictionary that maps each letter
# in `word` to the number of times it appears.
#
#     count_letters('mississippi')   # {'m': 1, 'i': 4, 's': 4, 'p': 2}
#     count_letters('')              # {}
#
# Save the file and the refresher runs it, or run it yourself with python3.


def count_letters(word):
    ...


if __name__ == "__main__":
    # Checks. Running this file runs them.
    for word, want in [('mississippi', {'m': 1, 'i': 4, 's': 4, 'p': 2}), ('aaa', {'a': 3}), ('', {})]:
        got = count_letters(word)
        assert got == want, f"count_letters({word!r}) returned {got!r}, and the answer is {want!r}"
    print("All checks pass.")
