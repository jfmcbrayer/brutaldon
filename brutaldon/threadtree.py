from pprint import pprint

def maketree(descendants):
    lookup = dict((descendant.id, descendant) for descendant in descendants)
    replies = {}
    roots = set()
    def getreps(id):
        if id in replies:
            reps = replies[id]
        else:
            reps = set()
            replies[id] = reps
        return reps
    for descendant in descendants:
        if not descendant.in_reply_to_id:
            roots.add(descendant.id)
            print("ROOT", descendant.id, descendant.account.id, descendant.account.acct)
        else:
            reps = getreps(descendant.in_reply_to_id)
            reps.add(descendant.id)
            reps = getreps(descendant.in_reply_to_account_id)
            reps.add(descendant.id)
            print("REPLY", descendant.id,
                  descendant.in_reply_to_id,
                  descendant.in_reply_to_account_id)
    seen = set()
    def onelevel(reps):
        for rep in sorted(reps):
            if rep in seen: continue
            seen.add(rep)
            subreps = replies.get(rep)
            if subreps:
                yield lookup[rep], onelevel(subreps)
            else:
                yield lookup[rep], ()
    leftovers = set(lookup.keys()) - seen
    return onelevel(roots), (lookup[leftover] for leftover in leftovers)

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
    herp, derp = maketree(descendants)
    derp = tuple(derp)
    pprint(("derp?", derp))
    yield IN
    yield from unmaketree(herp)
    yield OUT
    yield IN
    for post in derp:
        yield POST(derp)
    yield OUT
