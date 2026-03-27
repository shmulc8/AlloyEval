"""
Alloy language quick-reference guide injected into the LLM system prompt
for the *_guided task variants.
"""

ALLOY_GUIDE = """\
## Alloy Language Quick Reference

### Signatures & Fields
    sig Node { adj: set Node }    -- directed graph
    sig A extends B { }           -- inheritance

### Core Set / Relational Operators
    r + s      union
    r - s      difference
    r & s      intersection
    r -> s     Cartesian product (builds a relation)
    r . s      relational join  (a.(r.s) == (a.r).s)
    ~r         transpose / converse  (~adj = adj^-1)
    ^r         transitive closure   (one or more hops)
    *r         reflexive transitive closure  (zero or more hops)
    r[S]       image of set S through r  (same as S.r)

### Special Atoms / Relations
    iden       identity relation  { x->x | x in univ }
    univ       set of all atoms
    none       empty set

### Quantifiers (predicate body)
    all  x: T | P    -- P holds for every x in T
    some x: T | P    -- at least one x in T satisfies P
    no   x: T | P    -- no x in T satisfies P
    one  x: T | P    -- exactly one x in T satisfies P
    lone x: T | P    -- zero or one x in T satisfies P
    some r           -- r is non-empty  (shorthand)
    no   r           -- r is empty      (shorthand)

### Logical Connectives
    P && Q   (or: P and Q)
    P || Q   (or: P or Q)
    !P       (or: not P)
    P => Q   (or: P implies Q)
    P <=> Q  (or: P iff Q)

### Membership & Cardinality
    x in S       x is a member of S
    S in T       S is a subset of T
    S = T        set equality
    #S = n       cardinality equals n
    #S > 0       equivalent to: some S

### Common Graph / Relation Patterns
    -- Reflexive on Node.adj:
    all x: Node | x in x.adj
    -- equivalently:  Node <: iden in adj   or   iden in adj

    -- Irreflexive (no self-loops):
    no iden & adj

    -- Symmetric:
    adj = ~adj

    -- Antisymmetric:
    adj & ~adj in iden

    -- Transitive:
    adj.adj in adj

    -- Acyclic (no cycles of length >= 1):
    no iden & ^adj

    -- DAG (acyclic directed graph):
    no iden & ^adj

    -- Strongly connected:
    Node -> Node in *adj

    -- Total / connex (all pairs comparable):
    Node -> Node in adj + ~adj + iden
"""
