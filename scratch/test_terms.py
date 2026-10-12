def get_query_terms(query_words):
    terms = set(query_words)
    for w in query_words:
        terms.add(w)
        if w == "matrix":
            terms.add("matrices")
        elif w == "matrices":
            terms.add("matrix")
        elif w.endswith("ies"):
            terms.add(w[:-3] + "y")
        elif w.endswith("es"):
            terms.add(w[:-2])
        elif w.endswith("s"):
            terms.add(w[:-1])
        else:
            terms.add(w + "s")
            terms.add(w + "es")
    return terms

print("Matrix terms:", get_query_terms(["matrix"]))
print("Vector terms:", get_query_terms(["vector"]))
