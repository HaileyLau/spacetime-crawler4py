
# Splits a string into tokens by whitespace, keeping all words
def tokenize_without_numbers(text: str) -> list[str]:

    tokens: list[str] = []

    # Split the text by whitespace
    words: list[str] = text.split()

    # Filter out the undesired tokens
    for word in words:

        word = word.strip()

        # Ignore short words and numbers
        if (len(word) > 2) and (not word.isnumeric()):
            tokens += word

    # Return the tokens
    return tokens

# Splits a string into tokens by whitespace, ignoring the given stopwords
def tokenize_without_stopwords(text: str, stopwords: set[str]) -> list[str]:

    tokens: list[str] = []

    # Split the text by whitespace
    words: list[str] = text.split()

    # Filter out the undesired tokens and stopwords
    for word in words:

        word = word.strip()

        # Ignore short words, numbers, and stopwords
        if (len(word) > 2) and (not word.isnumeric()) and (word not in stopwords):
            tokens += word

    # Return the list of tokens, even if the file was not read
    return tokens

# Counts the number of occurences of each token in a list of tokens
def computeWordFrequencies(tokens: list[str], frequencies: dict[str, int]) -> None:

    for token in tokens:
        if token in frequencies:
            frequencies[token] += 1
        else:
            frequencies[token] = 1
