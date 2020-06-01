from pprint import pprint

def maketree(mastodon, root, descendants):
    lookup = dict((descendant.id, descendant) for descendant in descendants)
    lookup[root.id] = root
    replies = {}
    roots = set([root.id])
    def lookup_or_fetch(id):
        if not id in lookup:
            lookup[id] = mastodon.status(id)
        return lookup[id]
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
    seen.add(root.id)
    def onelevel(reps):
        for rep in sorted(reps):
            if rep in seen: continue
            seen.add(rep)
            subreps = replies.get(rep)
            if subreps:
                yield lookup_or_fetch(rep), onelevel(subreps)
            else:
                yield lookup_or_fetch(rep), ()
    def leftovers():
        for leftover in set(lookup.keys()) - seen:
            yield lookup_or_fetch(leftover)
    return onelevel(roots), leftovers

# returns (status, gen[(status, gen[(status, ...), (status, ())]), ...])

# django can't do recursion well so we'll turn the tree
# ((A, (B, C)))
# into
# (in, in, A, in, B, C, out, out, out)

IN = 0
OUT = 1
class TOOT:
    toot = None
    def __init__(self, toot):
        self.toot = toot

def unmaketree(tree):
    for toot, children in tree:
        yield TOOT(toot)
        if children:
            yield IN
            yield from unmaketree(children)
            yield OUT

def build(mastodon, root, descendants):
    tree, leftover = maketree(mastodon, root, descendants)
    yield IN
    yield from unmaketree(tree)
    yield OUT
    yield IN
    leftover = tuple(leftover())
    for toot in leftover:
        yield TOOT(toot)
    yield OUT
