import language_tool_python

with language_tool_python.LanguageTool("pt-BR") as tool:
    texto = "Foram beneficiado os prisioneiros."
    ocorrencias = tool.check(texto)

    for ocorrencia in ocorrencias:
        print("Mensagem:", ocorrencia.message)
        print("Sugestões:", ocorrencia.replacements)
        print("Trecho:", ocorrencia.context)
        print()

