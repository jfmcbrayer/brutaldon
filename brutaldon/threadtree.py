from pprint import pprint

def maketree(descendants):
    try:
        lookup = [(descendant.id, descendant) for descendant in descendants]
        print(descendants[0][0])
        lookup = dict(descendants)
    except:
        pprint(lookup)
        raise
    replies = {}
    roots = set()
    for descendant in descendants:
        pprint(descendant)
        if not descendant.in_reply_to_id:
            roots.add(descendant.id)
        if descendant.in_reply_to_id in replies:
            reps = replies[descendant.in_reply_to_id]
            reps.add(descendant.id)
        else:
            reps = set()
            replies[descendant.in_reply_to_id] = set([descendant.id])
    seen = set()
    def onelevel(reps):
        for rep in reps:
            if rep in seen: continue
            seen.add(rep)
            subreps = replies.get(rep)
            if subreps:
                yield lookup[rep], onelevel(subreps)
            else:
                yield lookup[rep], ()
    for root in roots:
        seen.add(root)
        reps = replies.get(root)
        if reps:
            yield lookup[root], onelevel(reps)
        else:
            yield lookup[root], ()
# returns (status, gen[(status, gen[(status, ...), (status, ())]), ...])

# django can't do recursion well so we'll turn the tree
# ((A, (B, C)))
# into
# (in, in, A, in, B, C, out, out, out)
class OPERATION: pass
IN = OPERATION()
OUT = OPERATION()
class POST(OPERATION):
    post = None
    def __init__(self, post):
        self.post = post

def unmaketree(tree):
    for post, children in tree:
        yield POST(post)
        if children:
            yield IN
            yield from unmaketree(children)
            yield OUT

def build(descendants):
    return unmaketree(maketree(descendants))
