# NativeBridge 0.1.0 — ferramentas de fonte

[English](README.md) · [Contrato de arquivos](../../addon/orc_native_bridge/PROJECT_CONTRACT.md) · [Licença](../../addon/orc_native_bridge/LICENSE) · [Avisos](../../addon/orc_native_bridge/THIRD_PARTY_NOTICES.md)

Complemento independente para Blender 5.0: **somente posições; NÃO VERIFICADO NO JOGO**. Incluímos os nove arquivos originais do pacote addon sem modificar seus bytes. Sem fixtures do jogo, manifesto privado original, parsers externos de referência ou segunda cópia da árvore addon. O importador Python pertence ao mantenedor; NativeBridge é outra implementação original MIT, não concessão de licença para código alheio.

## Extrair → projeto → Blender → novo arquivo → Explorer

1. No Explorer, abra seu SSG e extraia o `.edgemodel` original para uma pasta privada. Preserve o original. Sidecar de pesquisa `.orcmeta.json` opcional deve corresponder ao template; ele não é o contrato de projeto v1.
2. Na raiz do toolkit, crie pasta de projeto **nova**:
   ```text
   python tools/native_bridge/create_native_project.py "WORK/template.edgemodel" "WORK/new-project"
   ```
   Se disponível, acrescente `--sidecar "WORK/reference.orcmeta.json"`. Sem ele, não inventamos referências externas. A ajuda CLI funciona com Python padrão, sem Blender.
3. Instale o ZIP separado NativeBridge que acompanhará o **futuro release candidato**, quando publicado. Este rascunho não promete URL de download. Desenvolvedores podem montar ZIP dos nove arquivos de `addon/orc_native_bridge/`, com raiz `orc_native_bridge/`. Use perfil de teste separado: esta preparação não instalou nem atualizou o ORC Mod Tools existente.
4. No Blender 5.0, sidebar **ORC Complemento**: **Abrir projeto nativo** → escolha `project.orcmeta.json`. Edite somente posições em Edit Mode e volte a Object Mode. **Validar referência** → **Exportar NOVO edgemodel**. O painel oferece PT/EN.
5. Leia `.edgemodel.diff.json`: SHA256 de fonte/saída, IDs de bloco/vértice, bytes antes/depois e offsets alterados. Saída e diff devem ser novos; sobrescrita é rejeitada. Exportação sem mudanças preserva todos os bytes.
6. No Explorer, **Abrir pasta extraída**, escolha a pasta de saída e selecione o novo arquivo. Compare prévia/detalhes com a referência. É integração explícita por arquivos, **não menu/launcher automático ou injeção no arquivo do jogo**. Releitura comprova estrutura, não aceitação no jogo.

## Limites

Templates comprovados: FM6S v18, um grupo observado por registro de malha; stride MeshInfo 144, prefixo fixo grupo/segmento 128, strides de vértice 12/52; counts e ordem de vértices/índices constantes. Não afirma correção do parser Explorer multigrupo. FM6S v17, topologia nova, substituição arbitrária de modelos e conversão geral não são suportados.

Rejeita mudanças não suportadas de topologia/seams/IDs, UV/normals/tangents, skin/grupos/pesos, materiais/LOD, transforms, modifiers e shape keys, sem descartá-las silenciosamente. Seleção/ocultação são estado de edição. Normals e bounds nativos não são recalculados: faça alterações pequenas. Rig/skin/bind/relocation/materiais/padding/regiões desconhecidas são bytes preservados, **não novo rig vinculado ou posado**; sem Armature. Texturas/materiais externos não acompanham automaticamente. Sem repack SSG, injeção, animação ou validação de missão/deformação no jogo.

## Reproduzir sem distribuir assets

Na raiz do toolkit, substitua os placeholders por fixtures próprias e referências independentes licenciadas. Mantenha evidência privada fora do checkout.

```text
python -B -m unittest discover -s tests -p "test_*.py" -v
python -B -m unittest discover -s tools/native_bridge/tests -p "test_*.py" -v
python tools/native_bridge/run_factory_suite.py "BLENDER_EXECUTABLE" "OWNED_FIXTURES" "INDEPENDENT_REFERENCE" "NEW_PRIVATE_EVIDENCE"
```

Os quatro testes unitários bridge dão skip sem `ORC_FIXTURE` apontando a `.edgemodel` nativo próprio; não procuram pasta pessoal implícita. O runner factory exige `tweed-0.edgemodel`, `adawong-0.edgemodel`, `elitehunter-0.edgemodel` e referências externas `references/albam/hexane_edgemodel.py`/`deps/kaitaistruct.py`. Seis processos factory novos importam/salvam/reabrem, testam no-op/um vértice, parser independente novo e rejeições. Parsers são referências de teste, não runtime distribuído.

Scripts parametrizados: `tests/operator_test.py` (projeto/saída/prova após `--` Blender), `tests/ui_test.py` (caminho prova, processo gráfico factory próprio), `tests/explorer_readonly_test.py` (pasta fonte Explorer, pasta evidência factory). Não representam QA EXE congelado ou seleção física de diálogos. Runtime usa Blender/biblioteca padrão Python; releitura Explorer exige também NumPy.
