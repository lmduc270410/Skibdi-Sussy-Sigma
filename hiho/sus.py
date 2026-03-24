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
    #include<bits/stdc++.h>
#define int long long
using namespace std;
struct Node{
    int w,v;
}a[2000005];
struct node{
    int l,r;
}b[2000005];
int n,m,s,qzw[200005],qzh[200005],l=0,r=1e6,mid,ans=1e18;
signed main(){
    ios::sync_with_stdio(0),cin.tie(0),cout.tie(0);
    cin>>n>>m>>s;
    for(int i=1;i<=n;i++){
        cin>>a[i].w>>a[i].v;
    }
    for(int i=1;i<=m;i++){
        cin>>b[i].l>>b[i].r;
    }
    while(l<=r){
        mid=(l+r>>1);
        for(int i=1;i<=n;i++){
            if(a[i].w>=mid){
                qzh[i]=qzh[i-1]+1;
                qzw[i]=qzw[i-1]+a[i].v;
            }
            else{
                qzw[i]=qzw[i-1];
                qzh[i]=qzh[i-1];
            }
        }
        int sum=0;
        for(int i=1;i<=m;i++){
            sum+=(qzw[b[i].r]-qzw[b[i].l-1])*(qzh[b[i].r]-qzh[b[i].l-1]);
        }
        ans=min(abs(sum-s),ans);
        if(sum<=s){
            r=mid-1;
        }
        else{
            l=mid+1;
        }
    }
    cout<<ans;
    return 0;
}

    """

    editorial = """
    Approach
    First, it’s easy to see that binary search is applicable here, because as we bisect the values of w, the y-coordinate does not decrease as w decreases.

    At this point, our biggest challenge is how to quickly calculate the value of the ore within each interval. We realize that the sum of the values of all qualifying ores within an interval can be easily computed using prefix sums. Therefore, while performing the binary search, we simply record a prefix sum each time to calculate both the count and the total value.

    """

    tags = predict_tags(code, editorial)

    print("Detected tags:\n")
    print_tags(tags)