from grammar import Grammar

grammar1: dict[str, list[list[str]]] = {
    "A": [["B", "C"], ["ant", "A", "all"]],
    "B": [["big", "C"], ["bus", "A", "boss"], ["ε"]],
    "C": [["cat"], ["cow"]],
}


grammar2: dict[str, list[list[str]]] = {
    "S": [["A", "B","C"]],
    "A": [["a"],["ε"]],
    "B": [["b"], ["ε"]],
    "C": [["c"]]
}



if __name__ == "__main__":
    
    myGrammar = Grammar(grammar1)
    myGrammar.process_grammar()
    predict = myGrammar.get_predict_set()
    is_LL1= myGrammar.check_LL1_condition()
    for pred in predict.items():
        print(pred)

    print(f"is LL1?: {is_LL1}")
    #for NT, T in follow.items():
     #   print(NT, T)
