import json
import re

# =========================
# LOAD JSON FILES
# =========================

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

taxonomy = load_json("taxonomy.json")
synonyms = load_json("synonyms.json")
tricks = load_json("tricks.json")
code_patterns = load_json("code_patterns.json")

# normalize synonym keys
synonyms = {k.lower(): v for k, v in synonyms.items()}

# =========================
# UTILS
# =========================

def normalize_text(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return text

def is_valid_tag(tag):
    return any(tag in category for category in taxonomy.values())

# =========================
# TEXT (EDITORIAL) DETECTION
# =========================

def extract_from_text(text):
    text = normalize_text(text)
    tags = set()

    for phrase, tag in synonyms.items():
        if phrase in text:
            tags.add(tag)

    return tags

# =========================
# TRICK DETECTION (keyword-based for now)
# =========================

def extract_tricks(text):
    text = normalize_text(text)
    tags = set()

    for tag, description in tricks.items():
        desc = normalize_text(description)

        # simple keyword overlap check
        keywords = desc.split()
        match_count = sum(1 for w in keywords if w in text)

        # threshold (tune this later)
        if match_count >= max(2, len(keywords) // 3):
            tags.add(tag)

    return tags

# =========================
# CODE DETECTION
# =========================

def extract_from_code(code):
    code_lower = code.lower()
    tags = set()

    for tag, patterns in code_patterns.items():
        for pattern in patterns:
            if pattern in code_lower:
                tags.add(tag)
                break

    return tags

# =========================
# MAIN PIPELINE
# =========================

def predict_tags(code, editorial):
    tags = set()

    # 1. code-based detection
    tags |= extract_from_code(code)

    # 2. editorial keyword detection
    tags |= extract_from_text(editorial)

    # 3. trick detection
    tags |= extract_tricks(editorial)

    # 4. validate using taxonomy
    tags = {t for t in tags if is_valid_tag(t)}

    return tags

# =========================
# DEBUG / PRETTY PRINT
# =========================

def print_tags(tags):
    grouped = {k: [] for k in taxonomy.keys()}

    for tag in tags:
        for category, values in taxonomy.items():
            if tag in values:
                grouped[category].append(tag)

    for category, items in grouped.items():
        if items:
            print(f"{category}:")
            for t in sorted(items):
                print(f"  - {t}")

# =========================
# TEST
# =========================

if __name__ == "__main__":
    code = """
#include <iostream>
#include <cstdio>
#include <cstring>
#include <algorithm>
#include <cmath>
#include <cctype>
#include <queue>
#include <vector>

using namespace std;

inline int read()
{
    int x=0,f=1;char ch=getchar();
    while (!isdigit(ch)){if (ch=='-') f=-1;ch=getchar();}
    while (isdigit(ch)){x=x*10+ch-48;ch=getchar();}
    return x*f;
}

int n,m,a[100050],s[100050];

int main()
{
    n=read();
    for (int i=1;i<=n;i++)
        s[i]=s[i-1]+(a[i]=read());
    m=read();
    for (int i=1;i<=m;i++)
    {
        int l=read(),r=read();
        cout << s[r]-s[l-1] << endl;
    }
    return 0;
}


    """

    editorial = """
We define the prefix sum of a sequence a n as S n equals the sum from i equals 1 to n of a i, which is a 1 plus a 2 and so on up to a n.

With prefix sums, we can use differences to compute static range sums. Specifically, for an interval from l to r, the sum a l plus a l plus 1 and so on up to a r is equal to S r minus S l minus 1.

To prove this, we expand both terms. S r equals a 1 plus a 2 and so on up to a l minus 1, then plus a l, a l plus 1 and so on up to a r. Meanwhile, S l minus 1 equals a 1 plus a 2 and so on up to a l minus 1. Subtracting S l minus 1 from S r cancels the first part, leaving a l plus a l plus 1 and so on up to a r, which is exactly the desired range sum.

After preprocessing the prefix sums, each query can be answered in constant time.

    """

    tags = predict_tags(code, editorial)

    print("Detected tags:\n")
    print_tags(tags)