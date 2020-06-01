from pprint import pprint

def maketree(descendants):
    lookup = dict((descendant.id, descendant) for descendant in descendants)
    replies = {}
    roots = set()
    for descendant in descendants:
        if not descendant.in_reply_to_id:
            roots.add(descendant.id)
            print("ROOT", descendant.id, descendant.account.id, descendant.account.acct)
        elif descendant.in_reply_to_id in replies:
            reps = replies[descendant.in_reply_to_id]
            reps.add(descendant.id)
            print("REPLY", descendant.id,
                  descendant.in_reply_to_id,
                  descendant.in_reply_to_account_id,
                  descendant.in_reply_to_id in lookup)
        else:
            reps = set()
            print("NEWREPLY", descendant.id,
                  descendant.in_reply_to_id,
                  descendant.in_reply_to_id in lookup)
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
    derp = tuple(maketree(descendants))
    pprint(("derp?", derp))
    yield IN
    yield from unmaketree(derp)
    yield OUT
